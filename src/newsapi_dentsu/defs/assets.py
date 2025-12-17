import pandas as pd
import dagster as dg
from datetime import datetime, timedelta, timezone
from typing import Optional

from eventregistry import EventRegistry, QueryArticlesIter, QueryItems


api_key = dg.EnvVar("NEWSAPI_KEY").get_value()
er = EventRegistry(apiKey=api_key)


def get_last_fetch_timestamp(
    context: dg.AssetExecutionContext, asset_key: str
) -> Optional[str]:
    """Get the last fetch timestamp from the previous materialization"""
    # Parse asset_key string into list for AssetKey constructor
    # e.g., "raw/ai_marketing_news_raw" -> ["raw", "ai_marketing_news_raw"]
    asset_key_parts = asset_key.split("/")
    last_run = context.instance.get_latest_materialization_event(
        dg.AssetKey(asset_key_parts)
    )

    context.log.info(f"Last run event: {last_run}")
    if last_run and last_run.asset_materialization:
        metadata = last_run.asset_materialization.metadata
        if "last_fetch_timestamp" in metadata:
            # Extract the timestamp value
            ts_value = metadata["last_fetch_timestamp"].value
            context.log.info(
                f"Timestamp value type: {type(ts_value)}, value: {ts_value}"
            )

            if isinstance(ts_value, datetime):
                # Already a datetime object, format it
                return ts_value.strftime("%Y-%m-%d")
            elif isinstance(ts_value, float):
                # Convert Unix timestamp to ISO format for News API
                return datetime.fromtimestamp(ts_value).strftime("%Y-%m-%d")

    # Default: fetch from 7 days ago if no previous run
    return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")


################# Assets #################
@dg.asset(group_name="raw_news", key_prefix=["raw"])
def ai_marketing_news_raw(context: dg.AssetExecutionContext) -> pd.DataFrame:
    """
    Fetch news articles that contain BOTH AI and Marketing keywords using newsapi.ai.
    Uses incremental loading based on last fetch timestamp.
    """
    # Get last fetch time for incremental loading
    from_date = get_last_fetch_timestamp(context, "raw/ai_marketing_news_raw")

    context.log.info(f"Fetching articles about AI and Marketing since {from_date}")

    # Fetch articles from newsapi.ai using eventregistry
    try:
        # Query for articles that mention both AI and marketing concepts
        q = QueryArticlesIter(
            categoryUri=QueryItems.AND(
                [
                    "dmoz/Computers/Artificial_Intelligence",
                    "dmoz/Business/Marketing_and_Advertising",
                ]
            ),
            lang="eng",
            dateStart=from_date,
        )

        articles = []
        for article in q.execQuery(er, sortBy="relevance", maxItems=100):
            articles.append(article)

        context.log.info(f"Fetched {len(articles)} articles about AI and Marketing")

        # Convert to DataFrame
        df = pd.DataFrame(articles)

        if not df.empty:
            # Add metadata columns
            df["fetched_at"] = datetime.now()

            # Map eventregistry fields to consistent schema
            if "uri" in df.columns:
                df["article_id"] = df["uri"]
            if "url" not in df.columns and "uri" in df.columns:
                df["url"] = df["uri"]
            if "dateTime" in df.columns:
                df["publishedAt"] = pd.to_datetime(df["dateTime"])
            elif "date" in df.columns:
                df["publishedAt"] = pd.to_datetime(df["date"])

            # Handle source information
            if "source" in df.columns:
                df["source_name"] = df["source"].apply(
                    lambda x: x.get("title")
                    if isinstance(x, dict)
                    else str(x)
                    if x
                    else None
                )
                df["source_uri"] = df["source"].apply(
                    lambda x: x.get("uri") if isinstance(x, dict) else None
                )

        # Log metadata
        context.add_output_metadata(
            {
                "num_articles": len(df),
                "last_fetch_timestamp": dg.MetadataValue.timestamp(
                    datetime.now(timezone.utc)
                ),
                "from_date": from_date,
                "preview": dg.MetadataValue.md(
                    df[["title", "source_name", "publishedAt"]].head(5).to_markdown()
                    if not df.empty
                    and all(
                        col in df.columns
                        for col in ["title", "source_name", "publishedAt"]
                    )
                    else df.head(5).to_markdown()
                    if not df.empty
                    else "No articles"
                ),
            }
        )

        return df

    except Exception as e:
        context.log.error(f"Error fetching news: {str(e)}")
        # Return empty DataFrame on error
        return pd.DataFrame()


@dg.asset(
    group_name="processed_news",
    key_prefix=["processed"],
    ins={
        "ai_marketing_news_raw": dg.AssetIn(
            key=dg.AssetKey(["raw", "ai_marketing_news_raw"])
        ),
    },
)
def processed_news(
    context: dg.AssetExecutionContext,
    ai_marketing_news_raw: pd.DataFrame,
) -> pd.DataFrame:
    """
    Process AI and Marketing news articles.
    Removes duplicates based on URL and standardizes the data format.
    Accumulates processed articles over time instead of overwriting.
    """
    context.log.info(f"Processing {len(ai_marketing_news_raw)} raw articles")

    if ai_marketing_news_raw.empty:
        context.log.info("No raw articles to process")
        return ai_marketing_news_raw

    # Load existing processed articles from database
    existing_processed = pd.DataFrame()
    try:
        import duckdb

        db_path = (
            context.resources.io_manager.database
            if hasattr(context.resources.io_manager, "database")
            else "data/news.duckdb"
        )

        try:
            conn = duckdb.connect(db_path)
            existing_tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'raw' AND table_name = 'processed_news'
            """).fetchall()

            if existing_tables:
                existing_processed = conn.execute(
                    "SELECT * FROM raw.processed_news"
                ).fetchdf()
                context.log.info(
                    f"Loaded {len(existing_processed)} existing processed articles"
                )
            conn.close()
        except Exception as e:
            context.log.info(f"No existing processed data found: {str(e)}")
    except Exception as e:
        context.log.info(f"Could not load existing processed data: {str(e)}")

    # Process the raw data (remove duplicates within current batch)
    initial_count = len(ai_marketing_news_raw)
    processed = ai_marketing_news_raw.drop_duplicates(subset=["url"], keep="first")
    duplicates_in_batch = initial_count - len(processed)

    context.log.info(f"Removed {duplicates_in_batch} duplicates within current batch")

    # Merge with existing processed data
    if not existing_processed.empty:
        # Combine existing and newly processed data
        combined = pd.concat([existing_processed, processed], ignore_index=True)

        # Remove duplicates globally (keep first occurrence = older articles)
        before_dedup = len(combined)
        combined = combined.drop_duplicates(subset=["url"], keep="first")
        global_duplicates = before_dedup - len(combined)

        context.log.info(
            f"Combined {len(existing_processed)} existing + {len(processed)} new = {len(combined)} total (removed {global_duplicates} duplicates)"
        )
        final_processed = combined
    else:
        context.log.info(f"First run: storing {len(processed)} processed articles")
        final_processed = processed

    # Log metadata
    context.add_output_metadata(
        {
            "total_articles": len(final_processed),
            "new_articles_processed": len(processed),
            "duplicates_removed": duplicates_in_batch,
            "existing_articles": len(existing_processed),
            "date_range": f"{final_processed['publishedAt'].min()} to {final_processed['publishedAt'].max()}"
            if not final_processed.empty and "publishedAt" in final_processed.columns
            else "N/A",
        }
    )

    return final_processed


@dg.asset(
    group_name="final_news",
    key_prefix=["final"],
    ins={
        "processed_news": dg.AssetIn(key=dg.AssetKey(["processed", "processed_news"]))
    },
)
def filtered_news(
    context: dg.AssetExecutionContext, processed_news: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply filtering and cleaning logic to processed news:
    - Remove articles without title or body/description
    - Remove articles with [Removed] content
    - Validate published dates
    - Sort by publication date
    Accumulates filtered articles over time instead of overwriting.
    """
    context.log.info(f"Filtering {len(processed_news)} processed articles")

    initial_count = len(processed_news)

    if processed_news.empty:
        context.log.info("No processed articles to filter")
        return processed_news

    # Load existing filtered articles from database
    existing_filtered = pd.DataFrame()
    try:
        import duckdb

        db_path = (
            context.resources.io_manager.database
            if hasattr(context.resources.io_manager, "database")
            else "data/news.duckdb"
        )

        try:
            conn = duckdb.connect(db_path)
            existing_tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'raw' AND table_name = 'filtered_news'
            """).fetchall()

            if existing_tables:
                existing_filtered = conn.execute(
                    "SELECT * FROM raw.filtered_news"
                ).fetchdf()
                context.log.info(
                    f"Loaded {len(existing_filtered)} existing filtered articles"
                )
            conn.close()
        except Exception as e:
            context.log.info(f"No existing filtered data found: {str(e)}")
    except Exception as e:
        context.log.info(f"Could not load existing filtered data: {str(e)}")

    # Determine which content field to use (eventregistry uses 'body' instead of 'description')
    content_field = "body" if "body" in processed_news.columns else "description"

    # Filter out articles without essential content
    filter_conditions = processed_news["title"].notna()
    if content_field in processed_news.columns:
        filter_conditions = (
            filter_conditions
            & processed_news[content_field].notna()
            & processed_news[content_field].str.strip().ne("")
            & (processed_news["title"] != "[Removed]")
            & processed_news["title"].str.strip().ne("")
            & (processed_news[content_field] != "[Removed]")
        )

    filtered = processed_news[filter_conditions].copy()

    # Convert publishedAt to datetime if not already
    if "publishedAt" in filtered.columns:
        filtered["publishedAt"] = pd.to_datetime(
            filtered["publishedAt"], errors="coerce"
        )
        # Remove articles with invalid dates
        filtered = filtered[filtered["publishedAt"].notna()]

    removed_count = initial_count - len(filtered)
    context.log.info(f"Removed {removed_count} invalid articles from current batch")

    # Merge with existing filtered data
    if not existing_filtered.empty:
        # Combine existing and newly filtered data
        combined = pd.concat([existing_filtered, filtered], ignore_index=True)

        # Remove duplicates by URL (keep first occurrence)
        before_dedup = len(combined)
        combined = combined.drop_duplicates(subset=["url"], keep="first")
        global_duplicates = before_dedup - len(combined)

        context.log.info(
            f"Combined {len(existing_filtered)} existing + {len(filtered)} new = {len(combined)} total (removed {global_duplicates} duplicates)"
        )
        final_filtered = combined
    else:
        context.log.info(f"First run: storing {len(filtered)} filtered articles")
        final_filtered = filtered

    # Sort by publication date (newest first)
    if "publishedAt" in final_filtered.columns:
        final_filtered = final_filtered.sort_values("publishedAt", ascending=False)

    # Prepare preview columns
    preview_cols = ["title", "source_name", "publishedAt"]
    available_preview_cols = [
        col for col in preview_cols if col in final_filtered.columns
    ]

    # Log metadata
    context.add_output_metadata(
        {
            "total_articles": len(final_filtered),
            "new_articles_filtered": len(filtered),
            "removed_articles": removed_count,
            "existing_articles": len(existing_filtered),
            "date_range": f"{final_filtered['publishedAt'].min()} to {final_filtered['publishedAt'].max()}"
            if not final_filtered.empty and "publishedAt" in final_filtered.columns
            else "N/A",
            "preview": dg.MetadataValue.md(
                final_filtered[available_preview_cols].head(10).to_markdown()
                if not final_filtered.empty and available_preview_cols
                else "No articles"
            ),
        }
    )

    return final_filtered

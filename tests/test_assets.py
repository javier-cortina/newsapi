"""
Unit tests for the news pipeline assets.

Tests cover filtering, deduplication, date parsing, and error handling.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch

# Import functions from assets
from newsapi_dentsu.defs.assets import (
    processed_news,
    filtered_news,
    get_last_fetch_timestamp,
)


class TestProcessedNews:
    """Tests for the processed_news asset (deduplication logic)"""

    def test_deduplication_removes_duplicate_urls(
        self, mock_dagster_context, duplicate_articles_df
    ):
        """Test that duplicate URLs are removed, keeping the first occurrence"""
        # Verify we start with duplicates
        assert len(duplicate_articles_df) == 2
        assert (
            duplicate_articles_df["url"].iloc[0] == duplicate_articles_df["url"].iloc[1]
        )

        # Add publishedAt column (required by the function)
        duplicate_articles_df["publishedAt"] = pd.to_datetime(
            duplicate_articles_df["dateTime"]
        )

        # Process the DataFrame
        result = processed_news(mock_dagster_context, duplicate_articles_df)

        # Should have only 1 article after deduplication
        assert len(result) == 1
        # Should keep the first occurrence
        assert result.iloc[0]["title"] == "Duplicate Article - First Occurrence"

    def test_deduplication_preserves_unique_articles(
        self, mock_dagster_context, valid_articles_df
    ):
        """Test that articles with unique URLs are all preserved"""
        # Add publishedAt column
        valid_articles_df["publishedAt"] = pd.to_datetime(valid_articles_df["dateTime"])

        result = processed_news(mock_dagster_context, valid_articles_df)

        # All unique articles should be preserved
        assert len(result) == len(valid_articles_df)

    def test_empty_dataframe_handling(self, mock_dagster_context, empty_dataframe):
        """Test that empty DataFrames are handled gracefully"""
        result = processed_news(mock_dagster_context, empty_dataframe)

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestFilteredNews:
    """Tests for the filtered_news asset (filtering and cleaning logic)"""

    def test_filter_removes_articles_without_title(
        self, mock_dagster_context, sample_news_df
    ):
        """Test that articles without titles are removed"""
        # Add publishedAt column
        sample_news_df["publishedAt"] = pd.to_datetime(
            sample_news_df["dateTime"], errors="coerce"
        )

        result = filtered_news(mock_dagster_context, sample_news_df)

        # Check that no articles have empty titles
        assert result["title"].notna().all()
        assert (result["title"].str.strip() != "").all()

    def test_filter_removes_articles_without_body(
        self, mock_dagster_context, sample_news_df
    ):
        """Test that articles without body content are removed"""
        # Add publishedAt column
        sample_news_df["publishedAt"] = pd.to_datetime(
            sample_news_df["dateTime"], errors="coerce"
        )

        result = filtered_news(mock_dagster_context, sample_news_df)

        # Check that no articles have empty body
        assert result["body"].notna().all()
        assert (result["body"].str.strip() != "").all()

    def test_filter_removes_removed_content(self, mock_dagster_context, sample_news_df):
        """Test that articles with '[Removed]' content are filtered out"""
        # Add publishedAt column
        sample_news_df["publishedAt"] = pd.to_datetime(
            sample_news_df["dateTime"], errors="coerce"
        )

        result = filtered_news(mock_dagster_context, sample_news_df)

        # Check that no articles contain [Removed]
        assert not (result["title"] == "[Removed]").any()
        assert not (result["body"] == "[Removed]").any()

    def test_date_parsing_handles_invalid_dates(
        self, mock_dagster_context, sample_news_df
    ):
        """Test that invalid date formats are handled gracefully"""
        # Add publishedAt column with some invalid dates
        sample_news_df["publishedAt"] = pd.to_datetime(
            sample_news_df["dateTime"], errors="coerce"
        )

        result = filtered_news(mock_dagster_context, sample_news_df)

        # All remaining articles should have valid dates
        assert result["publishedAt"].notna().all()
        # Check that dates are datetime objects
        assert pd.api.types.is_datetime64_any_dtype(result["publishedAt"])

    def test_articles_sorted_by_date_descending(
        self, mock_dagster_context, valid_articles_df
    ):
        """Test that articles are sorted by publication date (newest first)"""
        # Add publishedAt column
        valid_articles_df["publishedAt"] = pd.to_datetime(valid_articles_df["dateTime"])

        result = filtered_news(mock_dagster_context, valid_articles_df)

        # Check that dates are in descending order
        dates = result["publishedAt"].tolist()
        assert dates == sorted(dates, reverse=True)

    def test_empty_dataframe_handling(self, mock_dagster_context, empty_dataframe):
        """Test that empty DataFrames are handled without errors"""
        result = filtered_news(mock_dagster_context, empty_dataframe)

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_valid_articles_pass_all_filters(
        self, mock_dagster_context, valid_articles_df
    ):
        """Test that valid articles pass through all filters"""
        # Add publishedAt column
        valid_articles_df["publishedAt"] = pd.to_datetime(valid_articles_df["dateTime"])

        result = filtered_news(mock_dagster_context, valid_articles_df)

        # All valid articles should pass filters (3 valid articles in fixture)
        assert len(result) == 3


class TestGetLastFetchTimestamp:
    """Tests for the get_last_fetch_timestamp helper function"""

    def test_returns_default_when_no_previous_run(self, mock_dagster_context):
        """Test that default date (7 days ago) is returned when no previous materialization"""
        # Mock the instance to return None for latest materialization
        mock_dagster_context.instance.get_latest_materialization_event = Mock(
            return_value=None
        )

        result = get_last_fetch_timestamp(mock_dagster_context, "test_asset")

        # Should return a date string in YYYY-MM-DD format
        assert isinstance(result, str)
        assert len(result) == 10  # YYYY-MM-DD format

        # Verify it's approximately 7 days ago
        from datetime import datetime, timedelta

        expected_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        assert result == expected_date

    def test_returns_previous_timestamp_when_available(self, mock_dagster_context):
        """Test that previous timestamp is returned when available"""
        # Mock a previous materialization with timestamp metadata
        mock_event = Mock()
        mock_event.asset_materialization.metadata = {
            "last_fetch_timestamp": Mock(value=1702800000.0)  # Dec 17, 2023
        }
        mock_dagster_context.instance.get_latest_materialization_event = Mock(
            return_value=mock_event
        )

        result = get_last_fetch_timestamp(mock_dagster_context, "test_asset")

        # Should return the date from the timestamp
        assert isinstance(result, str)
        assert result == "2023-12-17"


class TestIntegrationScenarios:
    """Integration tests for common pipeline scenarios"""

    def test_full_pipeline_with_mixed_articles(
        self, mock_dagster_context, sample_news_df
    ):
        """Test the full pipeline flow with a mix of valid and invalid articles"""
        # Step 1: Process (deduplicate)
        sample_news_df["publishedAt"] = pd.to_datetime(
            sample_news_df["dateTime"], errors="coerce"
        )
        processed = processed_news(mock_dagster_context, sample_news_df)

        # Should remove 1 duplicate (8 unique URLs out of 10 total)
        assert len(processed) == 9  # 10 - 1 duplicate

        # Step 2: Filter and clean
        filtered = filtered_news(mock_dagster_context, processed)

        # Should keep only valid articles:
        # - 3 valid articles
        # - 1 valid article with predictive analytics
        # - Remove: 1 no title, 1 no body, 1 [Removed], 1 invalid date, 1 duplicate (already removed)
        assert len(filtered) >= 4  # At least the valid articles

        # All results should have required fields
        assert filtered["title"].notna().all()
        assert filtered["body"].notna().all()
        assert filtered["publishedAt"].notna().all()

    def test_pipeline_handles_all_invalid_data(self, mock_dagster_context):
        """Test that pipeline handles datasets with only invalid articles"""
        # Create DataFrame with only invalid articles
        invalid_data = pd.DataFrame(
            [
                {
                    "title": "",
                    "url": "http://example.com/1",
                    "body": "Content",
                    "dateTime": "2024-12-15",
                },
                {
                    "title": "Title",
                    "url": "http://example.com/2",
                    "body": "",
                    "dateTime": "2024-12-15",
                },
                {
                    "title": "[Removed]",
                    "url": "http://example.com/3",
                    "body": "[Removed]",
                    "dateTime": "2024-12-15",
                },
            ]
        )

        invalid_data["publishedAt"] = pd.to_datetime(
            invalid_data["dateTime"], errors="coerce"
        )

        # Process
        processed = processed_news(mock_dagster_context, invalid_data)
        assert len(processed) == 3  # No duplicates to remove

        # Filter
        filtered = filtered_news(mock_dagster_context, processed)

        # All should be filtered out
        assert len(filtered) == 0

import dagster as dg


# Schedule to fetch news every 6 hours
# This respects the newsapi.ai rate limits
# Single API call fetches articles about both AI and marketing
news_fetch_schedule = dg.ScheduleDefinition(
    name="news_fetch_schedule",
    target=dg.AssetSelection.groups("raw_news"),
    cron_schedule="0 */6 * * *",  # Every 6 hours: 00:00, 06:00, 12:00, 18:00
    default_status=dg.DefaultScheduleStatus.RUNNING,
)


# Schedule to process and filter news every 6 hours (after raw data fetch)
# Uses a slight delay to ensure raw data is available
news_processing_schedule = dg.ScheduleDefinition(
    name="news_processing_schedule",
    target=dg.AssetSelection.groups("processed_news", "final_news"),
    cron_schedule="15 */6 * * *",  # 15 minutes after raw fetch
    default_status=dg.DefaultScheduleStatus.RUNNING,
)

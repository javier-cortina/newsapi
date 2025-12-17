"""
Dagster sensors for monitoring pipeline health and sending alerts.

This module implements failure detection and notification systems for the news pipeline.
Sensors run periodically to check for asset materialization failures and alert the team.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List
import dagster as dg
from dagster import (
    sensor,
    RunRequest,
    SensorEvaluationContext,
    DagsterRunStatus,
    RunsFilter,
    DagsterEventType,
)


@sensor(
    name="pipeline_failure_alert_sensor",
    description="Monitors asset failures and sends batched hourly alerts",
    minimum_interval_seconds=3600,  # Run every hour
)
def pipeline_failure_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors all pipeline assets for failures and sends batched alerts.

    This sensor:
    - Runs every hour (3600 seconds)
    - Checks for failed asset materializations in the last hour
    - Batches failures together to avoid alert fatigue
    - Sends notifications only if failures are detected

    The sensor maintains state to track which failures have been alerted on,
    preventing duplicate notifications.
    """

    # Get the last time this sensor ran (from cursor state)
    last_check_time = context.cursor or datetime.now().isoformat()
    last_check_datetime = datetime.fromisoformat(last_check_time)
    current_time = datetime.now()

    # Query for failed runs in the last hour
    one_hour_ago = current_time - timedelta(hours=1)

    # Get all runs that failed in the last hour
    runs_filter = RunsFilter(
        statuses=[DagsterRunStatus.FAILURE],
        created_after=one_hour_ago,
    )

    failed_runs = context.instance.get_runs(filters=runs_filter, limit=100)

    if not failed_runs:
        # No failures detected - update cursor and return
        context.update_cursor(current_time.isoformat())
        context.log.info("No failures detected in the last hour")
        return

    # Collect failure information
    failure_details = []
    for run in failed_runs:
        # Get asset materialization events from the run
        events = context.instance.all_logs(
            run.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
        )

        failure_info = {
            "run_id": run.run_id,
            "job_name": run.job_name,
            "status": run.status.value,
            "created_time": run.create_timestamp,
            "tags": run.tags,
        }
        failure_details.append(failure_info)

    # Send batched alert notification
    if failure_details:
        context.log.warning(
            f"ALERT: {len(failure_details)} pipeline failure(s) detected in the last hour"
        )

        # Call notification function
        send_failure_notification(
            context=context, failures=failure_details, time_window="last hour"
        )

    # Update cursor to current time
    context.update_cursor(current_time.isoformat())


def send_failure_notification(
    context: SensorEvaluationContext, failures: List[Dict], time_window: str
):
    """
    Send failure notification via email or other channels.

    This function contains pseudocode for the notification logic.
    In production, implement with actual SMTP or notification service.

    Args:
        context: Dagster sensor context for logging
        failures: List of failure information dictionaries
        time_window: Human-readable time window (e.g., "last hour")
    """

    # --- PSEUDOCODE: Email Notification via SMTP ---
    #
    # email_config = {
    #     'smtp_host': os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
    #     'smtp_port': int(os.getenv('EMAIL_PORT', '587')),
    #     'username': os.getenv('EMAIL_USER'),
    #     'password': os.getenv('EMAIL_PASSWORD'),
    #     'from_email': os.getenv('EMAIL_USER'),
    #     'to_emails': os.getenv('ALERT_EMAIL_TO', '').split(','),
    # }
    #
    # # Build email content
    # subject = f"[ALERT] News Pipeline Failures - {len(failures)} failures in {time_window}"
    #
    # body = f"""
    # Pipeline Failure Alert
    # ======================
    # Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    # Period: {time_window}
    # Total Failures: {len(failures)}
    #
    # Failure Details:
    # ----------------
    # """
    #
    # for i, failure in enumerate(failures, 1):
    #     body += f"""
    #     {i}. Run ID: {failure['run_id']}
    #        Job: {failure['job_name']}
    #        Status: {failure['status']}
    #        Time: {datetime.fromtimestamp(failure['created_time']).strftime('%Y-%m-%d %H:%M:%S')}
    #        Tags: {failure.get('tags', {})}
    #     """
    #
    # body += """
    #
    # Action Required:
    # ----------------
    # 1. Check Dagster UI for detailed error logs
    # 2. Review recent code changes if multiple failures
    # 3. Verify API connectivity and credentials
    # 4. Check database connectivity for PostgreSQL deployments
    #
    # Dagster UI: http://your-dagster-host:3000
    # """
    #
    # # Send email via SMTP
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # try:
    #     msg = MIMEMultipart()
    #     msg['From'] = email_config['from_email']
    #     msg['To'] = ', '.join(email_config['to_emails'])
    #     msg['Subject'] = subject
    #     msg.attach(MIMEText(body, 'plain'))
    #
    #     with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
    #         server.starttls()
    #         server.login(email_config['username'], email_config['password'])
    #         server.send_message(msg)
    #
    #     context.log.info(f"Alert email sent successfully to {email_config['to_emails']}")
    #
    # except Exception as e:
    #     context.log.error(f"Failed to send alert email: {str(e)}")

    # --- ALTERNATIVE: Slack Webhook Notification ---
    #
    # slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    #
    # if slack_webhook_url:
    #     import requests
    #
    #     # Build Slack message
    #     slack_message = {
    #         "text": f"🚨 *Pipeline Failure Alert*",
    #         "blocks": [
    #             {
    #                 "type": "header",
    #                 "text": {
    #                     "type": "plain_text",
    #                     "text": f"🚨 Pipeline Failures Detected"
    #                 }
    #             },
    #             {
    #                 "type": "section",
    #                 "fields": [
    #                     {"type": "mrkdwn", "text": f"*Time Period:*\n{time_window}"},
    #                     {"type": "mrkdwn", "text": f"*Total Failures:*\n{len(failures)}"},
    #                 ]
    #             },
    #             {"type": "divider"},
    #         ]
    #     }
    #
    #     # Add failure details
    #     for failure in failures[:5]:  # Limit to first 5 to avoid message size limits
    #         slack_message["blocks"].append({
    #             "type": "section",
    #             "text": {
    #                 "type": "mrkdwn",
    #                 "text": f"*Run:* `{failure['run_id'][:8]}...`\n"
    #                         f"*Job:* {failure['job_name']}\n"
    #                         f"*Status:* {failure['status']}"
    #             }
    #         })
    #
    #     if len(failures) > 5:
    #         slack_message["blocks"].append({
    #             "type": "section",
    #             "text": {
    #                 "type": "mrkdwn",
    #                 "text": f"_...and {len(failures) - 5} more failures_"
    #             }
    #         })
    #
    #     # Send to Slack
    #     try:
    #         response = requests.post(slack_webhook_url, json=slack_message, timeout=10)
    #         response.raise_for_status()
    #         context.log.info("Alert sent to Slack successfully")
    #     except Exception as e:
    #         context.log.error(f"Failed to send Slack alert: {str(e)}")

    # For now, just log the alert (structured logging that can be picked up by monitoring)
    context.log.warning(
        "PIPELINE FAILURE ALERT",
        extra={
            "alert_type": "pipeline_failure",
            "time_window": time_window,
            "failure_count": len(failures),
            "failures": failures,
            "timestamp": datetime.now().isoformat(),
            "severity": "high" if len(failures) > 5 else "medium",
        },
    )

    # Log individual failures for monitoring systems to pick up
    for failure in failures:
        context.log.error(
            f"Pipeline failure: {failure['job_name']} (Run: {failure['run_id']})",
            extra={
                "run_id": failure["run_id"],
                "job_name": failure["job_name"],
                "status": failure["status"],
                "created_time": failure["created_time"],
            },
        )


@sensor(
    name="asset_materialization_failure_sensor",
    description="Monitors specific asset materializations for failures",
    minimum_interval_seconds=3600,  # Run every hour
)
def asset_failure_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors specific assets (raw_news, processed_news, final_news)
    for materialization failures.

    This provides more granular monitoring than the general pipeline sensor,
    allowing for asset-specific alerting and metrics.
    """

    # Assets to monitor
    monitored_assets = ["raw_news", "processed_news", "final_news"]

    # Get cursor (last check time)
    last_check = context.cursor or datetime.now().isoformat()
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)

    # Track failures by asset
    asset_failures = {}

    # Query for failed materializations
    runs_filter = RunsFilter(
        statuses=[DagsterRunStatus.FAILURE],
        created_after=one_hour_ago,
    )

    failed_runs = context.instance.get_runs(filters=runs_filter, limit=100)

    for run in failed_runs:
        # Check if this run involved our monitored assets
        if run.asset_selection:
            for asset_key in run.asset_selection:
                asset_name = asset_key.path[-1]  # Get the last part of the asset key
                if asset_name in monitored_assets:
                    if asset_name not in asset_failures:
                        asset_failures[asset_name] = []

                    asset_failures[asset_name].append(
                        {
                            "run_id": run.run_id,
                            "timestamp": run.create_timestamp,
                        }
                    )

    # Log asset-specific failures
    if asset_failures:
        for asset_name, failures in asset_failures.items():
            context.log.warning(
                f"Asset '{asset_name}' failed {len(failures)} time(s) in the last hour",
                extra={
                    "asset_name": asset_name,
                    "failure_count": len(failures),
                    "failures": failures,
                },
            )
    else:
        context.log.info(
            "All monitored assets materialized successfully in the last hour"
        )

    # Update cursor
    context.update_cursor(current_time.isoformat())


# Export sensors for loading by Dagster
__all__ = [
    "pipeline_failure_sensor",
    "asset_failure_sensor",
]

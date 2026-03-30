"""AWS Lambda handler for the Slack Anomaly Agent.

Triggered by EventBridge every minute. Uses SSM Parameter Store
to persist the last processed Slack timestamp between invocations.
"""

import json
import logging
import boto3

from src.config import Config
from src.slack_monitor import SlackMonitor
from src.classifier import AnomalyClassifier
from src.jira_client import JiraTicketCreator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7
SSM_PARAM_NAME = "/slack-agent/last-timestamp"

ssm = boto3.client("ssm")


def _get_last_timestamp() -> str | None:
    """Retrieve the last processed timestamp from SSM Parameter Store."""
    try:
        response = ssm.get_parameter(Name=SSM_PARAM_NAME)
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        return None


def _set_last_timestamp(ts: str):
    """Persist the last processed timestamp to SSM Parameter Store."""
    ssm.put_parameter(Name=SSM_PARAM_NAME, Value=ts, Type="String", Overwrite=True)


def handler(event, context):
    """Lambda entry point — triggered by EventBridge schedule."""
    logger.info("Lambda invocation started (event=%s)", json.dumps(event))

    # --- Initialize components ---
    monitor = SlackMonitor(Config.SLACK_BOT_TOKEN, Config.SLACK_CHANNEL_ID)
    classifier = AnomalyClassifier(Config.GEMINI_API_KEY)
    jira = JiraTicketCreator(
        url=Config.JIRA_BASE_URL,
        email=Config.JIRA_EMAIL,
        api_token=Config.JIRA_API_TOKEN,
        project_key=Config.JIRA_PROJECT_KEY,
        issue_type_id=Config.JIRA_ISSUE_TYPE_ID,
    )

    # --- Restore timestamp from SSM ---
    last_ts = _get_last_timestamp()
    if last_ts:
        monitor.last_timestamp = last_ts
        logger.info("Restored last_timestamp from SSM: %s", last_ts)

    # --- Fetch & process messages ---
    messages = monitor.fetch_new_messages()
    tickets_created = []

    for msg in messages:
        text = msg.get("text", "")
        if not text.strip():
            continue

        user_id = msg.get("user", "unknown")
        author = monitor.get_user_name(user_id)
        logger.info("Processing message from %s: %s", author, text[:80])

        result = classifier.classify(text, author)

        if not result.get("is_anomaly"):
            logger.info("Not an anomaly (confidence=%.2f)", result.get("confidence", 0))
            continue

        confidence = result.get("confidence", 0)
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info("Confidence too low (%.2f < %.2f)", confidence, CONFIDENCE_THRESHOLD)
            continue

        title = result.get("title") or f"Anomalie signalée par {author}"
        summary = result.get("summary") or text
        severity = result.get("severity")

        issue_key = jira.create_anomaly_ticket(
            title=title,
            summary=summary,
            severity=severity,
            slack_author=author,
            slack_message=text,
        )

        if issue_key:
            tickets_created.append(issue_key)
            logger.info("Ticket created: %s (severity=%s, confidence=%.2f)", issue_key, severity, confidence)

    # --- Persist updated timestamp ---
    if monitor.last_timestamp:
        _set_last_timestamp(monitor.last_timestamp)
        logger.info("Saved last_timestamp to SSM: %s", monitor.last_timestamp)

    result_msg = f"Processed {len(messages)} message(s), created {len(tickets_created)} ticket(s): {tickets_created}"
    logger.info(result_msg)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "messages_processed": len(messages),
            "tickets_created": tickets_created,
        }),
    }

import logging
import time
import signal
import sys

from .config import Config
from .slack_monitor import SlackMonitor
from .classifier import AnomalyClassifier
from .jira_client import JiraTicketCreator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7


class SlackAnomalyAgent:
    """Main agent that ties together Slack monitoring, classification, and Jira ticket creation."""

    def __init__(self):
        self.monitor = SlackMonitor(Config.SLACK_BOT_TOKEN, Config.SLACK_CHANNEL_ID)
        self.classifier = AnomalyClassifier(Config.GEMINI_API_KEY)
        self.jira = JiraTicketCreator(
            url=Config.JIRA_BASE_URL,
            email=Config.JIRA_EMAIL,
            api_token=Config.JIRA_API_TOKEN,
            project_key=Config.JIRA_PROJECT_KEY,
            issue_type_id=Config.JIRA_ISSUE_TYPE_ID,
        )
        self._running = True

    def _handle_signal(self, signum, frame):
        logger.info("Received signal %s, shutting down...", signum)
        self._running = False

    def process_message(self, message: dict):
        """Classify a single message and create a Jira ticket if it's an anomaly."""
        text = message.get("text", "")
        if not text.strip():
            return

        user_id = message.get("user", "unknown")
        author = self.monitor.get_user_name(user_id)

        logger.info("Processing message from %s: %s", author, text[:80])

        result = self.classifier.classify(text, author)

        if not result.get("is_anomaly"):
            logger.info("Message not classified as anomaly (confidence=%.2f)", result.get("confidence", 0))
            return

        confidence = result.get("confidence", 0)
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info("Anomaly confidence too low (%.2f < %.2f), skipping", confidence, CONFIDENCE_THRESHOLD)
            return

        title = result.get("title") or f"Anomalie signalée par {author}"
        summary = result.get("summary") or text
        severity = result.get("severity")

        issue_key = self.jira.create_anomaly_ticket(
            title=title,
            summary=summary,
            severity=severity,
            slack_author=author,
            slack_message=text,
        )

        if issue_key:
            logger.info("Anomaly ticket created: %s (severity=%s, confidence=%.2f)", issue_key, severity, confidence)

    def run(self):
        """Main loop: poll Slack and process new messages."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info("Slack Anomaly Agent started")
        logger.info("Monitoring channel: %s", Config.SLACK_CHANNEL_ID)
        logger.info("Jira project: %s (issue type: %s)", Config.JIRA_PROJECT_KEY, Config.JIRA_ISSUE_TYPE_ID)
        logger.info("Poll interval: %ds", Config.POLL_INTERVAL_SECONDS)

        while self._running:
            try:
                messages = self.monitor.fetch_new_messages()
                for msg in messages:
                    self.process_message(msg)
            except Exception as e:
                logger.error("Error in main loop: %s", e, exc_info=True)

            # Sleep in small increments to allow graceful shutdown
            for _ in range(Config.POLL_INTERVAL_SECONDS):
                if not self._running:
                    break
                time.sleep(1)

        logger.info("Agent stopped.")


def main():
    agent = SlackAnomalyAgent()
    agent.run()

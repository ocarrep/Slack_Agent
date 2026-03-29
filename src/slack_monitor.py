import logging
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackMonitor:
    """Monitors a Slack channel for new messages."""

    def __init__(self, token: str, channel_id: str):
        self.client = WebClient(token=token)
        self.channel_id = channel_id
        self.last_timestamp: str | None = None

    def _initialize_timestamp(self):
        """Set the initial timestamp to now so we only process future messages."""
        self.last_timestamp = str(time.time())
        logger.info("Initialized monitoring from timestamp %s", self.last_timestamp)

    def fetch_new_messages(self) -> list[dict]:
        """Fetch messages posted after the last known timestamp."""
        if self.last_timestamp is None:
            self._initialize_timestamp()
            return []

        try:
            response = self.client.conversations_history(
                channel=self.channel_id,
                oldest=self.last_timestamp,
                limit=100,
            )
        except SlackApiError as e:
            logger.error("Slack API error: %s", e.response["error"])
            return []

        messages = response.get("messages", [])
        # Filter out bot messages, thread replies, and channel join/leave events
        user_messages = [
            m for m in messages
            if m.get("subtype") is None
            and "bot_id" not in m
            and m.get("ts") != self.last_timestamp
        ]

        if user_messages:
            # Update timestamp to the most recent message
            self.last_timestamp = max(m["ts"] for m in user_messages)
            logger.info("Fetched %d new message(s)", len(user_messages))

        return user_messages

    def get_user_name(self, user_id: str) -> str:
        """Resolve a Slack user ID to a display name."""
        try:
            result = self.client.users_info(user=user_id)
            profile = result["user"]["profile"]
            return profile.get("real_name") or profile.get("display_name") or user_id
        except SlackApiError:
            return user_id

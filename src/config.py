import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Slack
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "C0170HD1ASU")

    # Jira
    JIRA_BASE_URL = os.environ["JIRA_BASE_URL"]
    JIRA_EMAIL = os.environ["JIRA_EMAIL"]
    JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
    JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "HELP")
    JIRA_ISSUE_TYPE_ID = os.environ.get("JIRA_ISSUE_TYPE_ID", "10142")

    # Anthropic
    ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

    # Agent
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))

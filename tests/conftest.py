import os
import sys

# Pre-set environment variables before any imports
os.environ["SLACK_BOT_TOKEN"] = "xoxb-dummy-token"
os.environ["SLACK_CHANNEL_ID"] = "C12345678"
os.environ["JIRA_BASE_URL"] = "https://dummy-jira.atlassian.net"
os.environ["JIRA_EMAIL"] = "dummy@example.com"
os.environ["JIRA_API_TOKEN"] = "dummy-api-token"
os.environ["JIRA_PROJECT_KEY"] = "HELP"
os.environ["JIRA_ISSUE_TYPE_ID"] = "10142"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy-key"
os.environ["POLL_INTERVAL_SECONDS"] = "1"

import pytest

@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Dummy fixture as env vars are already set."""
    pass

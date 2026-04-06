import pytest
from slack_sdk.errors import SlackApiError
from src.slack_monitor import SlackMonitor

def test_fetch_new_messages_first_run(mocker):
    """Test first run of monitor sets initial timestamp and returns no messages."""
    mocker.patch("time.time", return_value=123456789.0)
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")

    monitor = SlackMonitor("token", "C123")
    messages = monitor.fetch_new_messages()

    assert messages == []
    assert monitor.last_timestamp == "123456789.0"
    mock_web_client.return_value.conversations_history.assert_not_called()

def test_fetch_new_messages_success(mocker):
    """Test successful message fetching and filtering."""
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")
    mock_client_instance = mock_web_client.return_value

    # Mock some messages
    mock_messages = [
        {"ts": "123456790.0", "text": "Valid message", "user": "U123"},
        {"ts": "123456791.0", "text": "Bot message", "bot_id": "B123"},
        {"ts": "123456792.0", "text": "Thread reply", "subtype": "thread_broadcast", "user": "U123"},
        {"ts": "123456793.0", "text": "Another valid message", "user": "U456"}
    ]
    mock_client_instance.conversations_history.return_value = {"messages": mock_messages}

    monitor = SlackMonitor("token", "C123")
    monitor.last_timestamp = "123456789.0"

    messages = monitor.fetch_new_messages()

    assert len(messages) == 2
    assert messages[0]["text"] == "Valid message"
    assert messages[1]["text"] == "Another valid message"
    assert monitor.last_timestamp == "123456793.0"

    mock_client_instance.conversations_history.assert_called_once_with(
        channel="C123",
        oldest="123456789.0",
        limit=100
    )

def test_fetch_new_messages_api_error(mocker):
    """Test Slack API error during message fetching."""
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")
    mock_client_instance = mock_web_client.return_value
    mock_client_instance.conversations_history.side_effect = SlackApiError(
        message="error",
        response={"error": "channel_not_found"}
    )

    monitor = SlackMonitor("token", "C123")
    monitor.last_timestamp = "123456789.0"

    messages = monitor.fetch_new_messages()
    assert messages == []

def test_get_user_name_success(mocker):
    """Test successful user name resolution."""
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")
    mock_client_instance = mock_web_client.return_value
    mock_client_instance.users_info.return_value = {
        "user": {"profile": {"real_name": "John Doe", "display_name": "johnny"}}
    }

    monitor = SlackMonitor("token", "C123")
    name = monitor.get_user_name("U123")

    assert name == "John Doe"

def test_get_user_name_fallback_to_display_name(mocker):
    """Test fallback to display_name if real_name is missing."""
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")
    mock_client_instance = mock_web_client.return_value
    mock_client_instance.users_info.return_value = {
        "user": {"profile": {"display_name": "johnny"}}
    }

    monitor = SlackMonitor("token", "C123")
    name = monitor.get_user_name("U123")

    assert name == "johnny"

def test_get_user_name_fallback_to_id(mocker):
    """Test fallback to user ID on API error."""
    mock_web_client = mocker.patch("src.slack_monitor.WebClient")
    mock_client_instance = mock_web_client.return_value
    mock_client_instance.users_info.side_effect = SlackApiError(
        message="error",
        response={"error": "user_not_found"}
    )

    monitor = SlackMonitor("token", "C123")
    name = monitor.get_user_name("U123")

    assert name == "U123"

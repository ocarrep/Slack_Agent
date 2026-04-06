import pytest
from src.agent import SlackAnomalyAgent

def test_process_message_anomaly_high_confidence(mocker):
    """Test message processing when an anomaly is detected with high confidence."""
    # Mock dependencies
    mock_monitor = mocker.patch("src.agent.SlackMonitor").return_value
    mock_classifier = mocker.patch("src.agent.AnomalyClassifier").return_value
    mock_jira = mocker.patch("src.agent.JiraTicketCreator").return_value

    mock_monitor.get_user_name.return_value = "John Doe"
    mock_classifier.classify.return_value = {
        "is_anomaly": True,
        "confidence": 0.85,
        "title": "Bug Title",
        "summary": "Bug Summary",
        "severity": "high"
    }
    mock_jira.create_anomaly_ticket.return_value = "HELP-123"

    agent = SlackAnomalyAgent()
    message = {"text": "I found a bug!", "user": "U123"}
    agent.process_message(message)

    mock_monitor.get_user_name.assert_called_once_with("U123")
    mock_classifier.classify.assert_called_once_with("I found a bug!", "John Doe")
    mock_jira.create_anomaly_ticket.assert_called_once_with(
        title="Bug Title",
        summary="Bug Summary",
        severity="high",
        slack_author="John Doe",
        slack_message="I found a bug!"
    )

def test_process_message_not_anomaly(mocker):
    """Test message processing when no anomaly is detected."""
    mock_monitor = mocker.patch("src.agent.SlackMonitor").return_value
    mock_classifier = mocker.patch("src.agent.AnomalyClassifier").return_value
    mock_jira = mocker.patch("src.agent.JiraTicketCreator").return_value

    mock_classifier.classify.return_value = {
        "is_anomaly": False,
        "confidence": 0.1
    }

    agent = SlackAnomalyAgent()
    message = {"text": "Hello world", "user": "U123"}
    agent.process_message(message)

    mock_jira.create_anomaly_ticket.assert_not_called()

def test_process_message_low_confidence(mocker):
    """Test message processing when confidence is below threshold."""
    mock_monitor = mocker.patch("src.agent.SlackMonitor").return_value
    mock_classifier = mocker.patch("src.agent.AnomalyClassifier").return_value
    mock_jira = mocker.patch("src.agent.JiraTicketCreator").return_value

    mock_classifier.classify.return_value = {
        "is_anomaly": True,
        "confidence": 0.5,  # < 0.7
        "title": "Maybe bug",
        "summary": "Summary",
        "severity": "low"
    }

    agent = SlackAnomalyAgent()
    message = {"text": "Is this a bug?", "user": "U123"}
    agent.process_message(message)

    mock_jira.create_anomaly_ticket.assert_not_called()

def test_process_message_empty_text(mocker):
    """Test message processing with empty text."""
    mock_monitor = mocker.patch("src.agent.SlackMonitor").return_value
    mock_classifier = mocker.patch("src.agent.AnomalyClassifier").return_value

    agent = SlackAnomalyAgent()
    agent.process_message({"text": "", "user": "U123"})
    agent.process_message({"text": "  ", "user": "U123"})

    mock_classifier.classify.assert_not_called()

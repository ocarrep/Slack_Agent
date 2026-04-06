import pytest
from src.jira_client import JiraTicketCreator

def test_create_anomaly_ticket_success(mocker):
    """Test successful Jira ticket creation."""
    mock_jira_class = mocker.patch("src.jira_client.Jira")
    mock_jira_client = mock_jira_class.return_value
    mock_jira_client.issue_create.return_value = {"key": "HELP-123"}

    creator = JiraTicketCreator(
        url="https://dummy-jira.net",
        email="user@test.com",
        api_token="fake-token",
        project_key="HELP",
        issue_type_id="10142"
    )

    issue_key = creator.create_anomaly_ticket(
        title="Title from IA",
        summary="Summary from IA",
        severity="critical",
        slack_author="john.doe",
        slack_message="App crashed!"
    )

    assert issue_key == "HELP-123"

    # Check field mapping
    mock_jira_client.issue_create.assert_called_once()
    fields = mock_jira_client.issue_create.call_args[1]["fields"]

    assert fields["project"]["key"] == "HELP"
    assert fields["summary"] == "Title from IA"
    assert fields["issuetype"]["id"] == "10142"
    assert fields["priority"]["name"] == "Highest"  # 'critical' mapped to 'Highest'
    assert "john.doe" in fields["description"]
    assert "{quote}App crashed!{quote}" in fields["description"]

def test_create_anomaly_ticket_no_severity(mocker):
    """Test Jira ticket creation without severity."""
    mock_jira_class = mocker.patch("src.jira_client.Jira")
    mock_jira_client = mock_jira_class.return_value
    mock_jira_client.issue_create.return_value = {"key": "HELP-456"}

    creator = JiraTicketCreator(
        url="https://dummy-jira.net",
        email="user@test.com",
        api_token="fake-token",
        project_key="HELP",
        issue_type_id="10142"
    )

    issue_key = creator.create_anomaly_ticket(
        title="No severity bug",
        summary="A bug with unknown severity",
        severity=None,
        slack_author="jane.doe",
        slack_message="Buggy behavior"
    )

    assert issue_key == "HELP-456"
    fields = mock_jira_client.issue_create.call_args[1]["fields"]
    assert "priority" not in fields

def test_create_anomaly_ticket_error(mocker):
    """Test Jira ticket creation with API error."""
    mock_jira_class = mocker.patch("src.jira_client.Jira")
    mock_jira_client = mock_jira_class.return_value
    mock_jira_client.issue_create.side_effect = Exception("API Error")

    creator = JiraTicketCreator(
        url="https://dummy-jira.net",
        email="user@test.com",
        api_token="fake-token",
        project_key="HELP",
        issue_type_id="10142"
    )

    issue_key = creator.create_anomaly_ticket(
        title="Bug!",
        summary="Summary",
        severity="low",
        slack_author="user",
        slack_message="Message"
    )

    assert issue_key is None

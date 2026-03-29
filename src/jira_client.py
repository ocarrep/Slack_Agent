import logging
from atlassian import Jira

logger = logging.getLogger(__name__)

SEVERITY_TO_PRIORITY = {
    "critical": "Highest",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


class JiraTicketCreator:
    """Creates anomaly tickets in Jira Cloud."""

    def __init__(self, url: str, email: str, api_token: str, project_key: str, issue_type_id: str):
        self.jira = Jira(url=url, username=email, password=api_token, cloud=True)
        self.project_key = project_key
        self.issue_type_id = issue_type_id

    def create_anomaly_ticket(
        self,
        title: str,
        summary: str,
        severity: str | None,
        slack_author: str,
        slack_message: str,
    ) -> str | None:
        """Create a Jira issue of type 'Anomalie' and return the issue key."""
        description = (
            f"*Anomalie détectée automatiquement depuis Slack (#sap)*\n\n"
            f"*Auteur Slack :* {slack_author}\n"
            f"*Message original :*\n{{quote}}{slack_message}{{quote}}\n\n"
            f"*Résumé IA :*\n{summary}\n\n"
            f"*Sévérité estimée :* {severity or 'non définie'}\n\n"
            f"---\n_Ticket créé automatiquement par Slack Agent_"
        )

        fields = {
            "project": {"key": self.project_key},
            "summary": title,
            "description": description,
            "issuetype": {"id": self.issue_type_id},
        }

        # Add priority if severity is mapped
        priority_name = SEVERITY_TO_PRIORITY.get(severity or "")
        if priority_name:
            fields["priority"] = {"name": priority_name}

        try:
            result = self.jira.issue_create(fields=fields)
            issue_key = result.get("key")
            logger.info("Created Jira ticket: %s", issue_key)
            return issue_key
        except Exception as e:
            logger.error("Failed to create Jira ticket: %s", e)
            return None

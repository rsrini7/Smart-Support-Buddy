import pytest
from app.services import jira_service


def test_get_jira_ticket_mock(mocker):
    mock_client = mocker.patch("app.services.jira_service.get_jira_client")
    mock_jira = mock_client.return_value
    mock_issue = mock_jira.issue.return_value
    mock_issue.fields.summary = "Test Summary"
    mock_issue.fields.description = "Test Description"
    mock_issue.fields.status.name = "Open"
    mock_issue.fields.created = "2024-01-01T00:00:00.000+0000"
    mock_issue.fields.updated = "2024-01-01T00:00:00.000+0000"
    mock_issue.fields.assignee = None
    mock_issue.fields.reporter = None
    mock_issue.fields.priority = None
    mock_issue.fields.resolution = None
    mock_issue.fields.components = []
    mock_issue.fields.labels = []
    mock_issue.fields.comment.comments = []

    ticket = jira_service.get_jira_ticket("PROJ-123")
    assert ticket["summary"] == "Test Summary"
    assert ticket["status"] == "Open"

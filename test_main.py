import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'

from main import app, fetch_open_tasks

client = TestClient(app)

# Test the Slack endpoint with proper mocking
@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
def test_slack_valid_request(mock_llm, mock_fetch_tasks, mock_requests_post):
    # Mock the fetch_open_tasks function
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    
    # Mock the LLM prediction
    mock_llm.predict.return_value = "Here are your tasks for today"
    
    # Mock the requests.post call
    mock_requests_post.return_value.status_code = 200
    
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "What do I need to do today?",
            "channel": "fake_channel",
            "subtype": None
        }
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_slack_invalid_request():
    # This test expects a ValidationError to be raised
    # since the SlackMessage model requires 'type' and 'event' fields
    import pytest
    from pydantic_core import ValidationError
    
    with pytest.raises(ValidationError):
        response = client.post("/slack", json={})

def test_slack_empty_body():
    response = client.post("/slack", data="")
    assert response.status_code == 400

# Test the fetch_open_tasks function with proper mocking
@patch('main.notion')
def test_fetch_open_tasks(mock_notion):
    # Mock the notion client response
    mock_response = {
        "results": [
            {"properties": {"Task": {"title": [{"text": {"content": "Task 1"}}]}}},
            {"properties": {"Task": {"title": [{"text": {"content": "Task 2"}}]}}}
        ]
    }
    mock_notion.databases.query.return_value = mock_response
    
    tasks = fetch_open_tasks()
    assert tasks == ["Task 1", "Task 2"]
    
    # Verify that the notion client was called with correct parameters
    mock_notion.databases.query.assert_called_once()

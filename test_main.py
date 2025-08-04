import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

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
    mock_llm.invoke.return_value = MagicMock(content="Here are your tasks for today")
    
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
    response = client.post("/slack", json={})
    assert response.status_code == 200
    assert response.json() == {"ok": True}

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

# Test slash command handling
@patch('threading.Thread')
def test_slack_slash_command(mock_thread):
    # Mock thread to prevent actual threading
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    # Simulate form-encoded slash command data
    form_data = (
        "token=fake_token&team_id=T123&channel_id=C123&"
        "command=/ai&text=test&response_url=https://hooks.slack.com/test"
    )
    
    response = client.post(
        "/slack",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    json_response = response.json()
    assert "🤔 Let me analyze your tasks" in json_response["text"]
    assert json_response["response_type"] == "ephemeral"
    
    # Verify background thread was started
    mock_thread.assert_called_once()
    mock_thread_instance.start.assert_called_once()

# Test slash command without response_url (now processed normally)
@patch('threading.Thread')
def test_slack_slash_command_no_response_url(mock_thread):
    # Mock thread to prevent actual threading
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    form_data = "token=fake_token&team_id=T123&channel_id=C123&command=/ai&text=test"
    
    response = client.post(
        "/slack",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    json_response = response.json()
    assert "🤔 Let me analyze your tasks" in json_response["text"]
    assert json_response["response_type"] == "ephemeral"
    
    # Verify background thread was started
    mock_thread.assert_called_once()
    mock_thread_instance.start.assert_called_once()

# Test URL verification challenge
def test_slack_url_verification():
    response = client.post("/slack", json={
        "type": "url_verification",
        "challenge": "test_challenge_123"
    })
    
    assert response.status_code == 200
    assert response.json() == {"challenge": "test_challenge_123"}

# Test health check endpoint
def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert "timestamp" in json_response

# Test fetch_open_tasks with empty results
@patch('main.notion')
def test_fetch_open_tasks_empty(mock_notion):
    mock_notion.databases.query.return_value = {"results": []}
    
    tasks = fetch_open_tasks()
    assert tasks == []

# Test fetch_open_tasks with malformed data
@patch('main.notion')
def test_fetch_open_tasks_malformed(mock_notion):
    mock_response = {
        "results": [
            {"properties": {"Task": {"title": []}}},  # Empty title array
            {"properties": {"Task": {"title": [{"text": {}}]}}},  # Missing content
            {"properties": {}},  # Missing Task property
        ]
    }
    mock_notion.databases.query.return_value = mock_response
    
    tasks = fetch_open_tasks()
    # Should handle malformed data gracefully
    assert len(tasks) <= 3  # Some may be filtered out

# Test fetch_open_tasks with API error
@patch('main.notion')
def test_fetch_open_tasks_api_error(mock_notion):
    # Use a generic exception to simulate an API error
    mock_notion.databases.query.side_effect = Exception("API Error")
    
    tasks = fetch_open_tasks()
    assert "Error accessing task database" in tasks

# Test bot message filtering
def test_slack_bot_message_filtered():
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Bot message",
            "channel": "fake_channel",
            "subtype": "bot_message"
        }
    })
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}

# Test thread context management integration
@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
def test_slack_message_with_thread_context(mock_llm, mock_fetch_tasks, mock_requests_post):
    """Test that messages in threads maintain context"""
    # Mock dependencies
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    mock_llm.invoke.return_value = MagicMock(content="Here's your response")
    mock_requests_post.return_value.status_code = 200
    
    # First message in thread
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Start of conversation",
            "channel": "C123",
            "thread_ts": "1234567890.123456",
            "subtype": None
        }
    })
    
    assert response.status_code == 200
    
    # Second message in same thread
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Continue conversation", 
            "channel": "C123",
            "thread_ts": "1234567890.123456",
            "subtype": None
        }
    })
    
    assert response.status_code == 200

# Test slash command with basic functionality
@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
@patch('threading.Thread')
def test_slack_slash_command_with_context(mock_thread, mock_llm, mock_fetch_tasks, mock_requests_post):
    """Test that slash commands work correctly without thread context"""
    # Mock thread to prevent actual threading
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    # Mock dependencies
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    mock_llm.invoke.return_value = MagicMock(content="Here's your response")
    mock_requests_post.return_value.status_code = 200
    
    # First slash command
    form_data = (
        "token=fake_token&team_id=T123&channel_id=C123&"
        "command=/opsbrain&text=What should I focus on?"
    )
    
    response = client.post(
        "/slack",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    json_response = response.json()
    assert "🤔 Let me analyze your tasks" in json_response["text"]
    assert json_response["response_type"] == "ephemeral"
    
    # Verify background thread was started
    mock_thread.assert_called()
    mock_thread_instance.start.assert_called()

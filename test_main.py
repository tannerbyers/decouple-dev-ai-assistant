import os
import pytest
import signal
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

@pytest.fixture(autouse=True)
def setup_timeout():
    """Setup timeout for all tests"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout
    yield
    signal.alarm(0)  # Cancel alarm

# Setup test environment
from test_utils import setup_test_environment
setup_test_environment()

from main import app, fetch_open_tasks, analyze_business_request, handle_task_backlog_request, BusinessGoal, GoalStatus, Priority, BusinessArea, NotionDBInfo, generate_task_backlog, bulk_create_notion_tasks, parse_database_request, execute_database_action, generate_ceo_insights

client = TestClient(app)


@pytest.fixture
def business_goals_fixture():
    return {
        "sales_1": BusinessGoal(
            id="sales_1",
            title="Increase Sales",
            description="Increase sales by 20%",
            area=BusinessArea.SALES,
            status=GoalStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            target_date="2025-12-31",
            progress=50,
            weekly_actions=["Action 1"],
            daily_actions=["Action 2"],
            success_metrics={"metric": "value"},
            created_date="2025-01-01",
            last_updated="2025-08-01"
        )
    }

def test_analyze_business_request_task_backlog():
    user_text = "create all tasks for the first customer"
    analysis = analyze_business_request(user_text)
    assert analysis['request_type'] == 'task_backlog'

def test_analyze_business_request_various_task_backlog_keywords():
    """Test that task backlog keywords are detected correctly"""
    task_backlog_cases = [
        "task backlog",
        "generate tasks", 
        "missing tasks",
        "all the tasks",
        "missing items"
    ]
    
    for text in task_backlog_cases:
        analysis = analyze_business_request(text)
        assert analysis['request_type'] == 'task_backlog', f"Failed for text: '{text}'"

def test_analyze_business_request_task_cleanup_keywords():
    """Test that task cleanup keywords are detected correctly"""
    task_cleanup_cases = [
        "review all tasks",
        "clean up tasks",
        "remove irrelevant tasks",
        "doesn't make sense",
        "remove tasks that don't make sense"
    ]
    
    for text in task_cleanup_cases:
        analysis = analyze_business_request(text)
        assert analysis['request_type'] == 'task_cleanup', f"Failed for text: '{text}'"

# Test the Slack endpoint with proper mocking
@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
def test_slack_valid_request(mock_llm, mock_fetch_tasks, mock_requests_post):
    # Mock the fetch_open_tasks function
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    
    # Mock the LLM prediction with CEO-style response
    mock_llm.invoke.return_value = MagicMock(content="Focus on revenue-generating activities first. Complete client calls by 2pm.")
    
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

# Test CEO-level parsing for Trello commands
def test_parse_database_request_trello_done():
    """Test parsing of CEO-style Trello done commands"""
    test_cases = [
        "Set AI agent status to done",
        "Mark AI agent as done", 
        "Move AI agent to done",
        "AI agent task done"
    ]
    
    for text in test_cases:
        result = parse_database_request(text)
        assert result['action'] == 'trello_done', f"Failed for text: '{text}'"
        assert result['requires_db_action'] is True
        assert 'task_name' in result['params']

def test_parse_database_request_add_business_tasks():
    """Test parsing of comprehensive business task requests"""
    test_cases = [
        "add missing tasks",
        "create all tasks", 
        "missing business tasks"
    ]
    
    for text in test_cases:
        result = parse_database_request(text)
        assert result['action'] == 'add_business_tasks', f"Failed for text: '{text}'"
        assert result['requires_db_action'] is True
        assert 'areas' in result['params']
        assert len(result['params']['areas']) == 5  # All business areas

# Test CEO insights generation
def test_generate_ceo_insights_concise_style(business_goals_fixture):
    """Test that CEO insights generate concise, action-oriented prompts"""
    user_text = "What should I focus on today?"
    tasks = ["Task 1", "Task 2", "Task 3"]
    analysis = {'detected_areas': ['sales'], 'request_type': 'general', 'is_ceo_focused': True}
    
    prompt = generate_ceo_insights(user_text, tasks, analysis)
    
    # Verify CEO-style prompt characteristics
    assert "CEO-level AI assistant" in prompt
    assert "RESPONSE STYLE" in prompt or "RESPONSE RULES" in prompt
    assert "Task completed" in prompt
    assert "Issue:" in prompt
    assert "Maximum 2 sentences" in prompt
    assert "revenue" in prompt.lower() or "efficiency" in prompt.lower()

@patch('main.trello_client')
def test_execute_database_action_trello_done_success(mock_trello_client):
    """Test successful Trello task completion"""
    mock_trello_client.is_configured.return_value = True
    mock_trello_client.move_task_to_done.return_value = True
    
    result = execute_database_action('trello_done', task_name='ai agent')
    
    assert result['success'] is True
    assert result['message'] == "Task completed"
    assert result['action'] == 'trello_done'
    mock_trello_client.move_task_to_done.assert_called_once_with('ai agent')

@patch('main.trello_client')
def test_execute_database_action_trello_done_failure(mock_trello_client):
    """Test failed Trello task completion"""
    mock_trello_client.is_configured.return_value = True
    mock_trello_client.move_task_to_done.return_value = False
    
    result = execute_database_action('trello_done', task_name='nonexistent task')
    
    assert result['success'] is False
    assert "Issue: Could not find or move task" in result['message']
    assert result['action'] == 'trello_done'

@patch('main.trello_client')
def test_execute_database_action_trello_not_configured(mock_trello_client):
    """Test Trello actions when not configured"""
    mock_trello_client.is_configured.return_value = False
    
    result = execute_database_action('trello_done', task_name='ai agent')
    
    assert result['success'] is False
    assert result['message'] == "Issue: Trello not configured"

@patch('main.trello_client')
def test_execute_database_action_add_business_tasks(mock_trello_client):
    """Test comprehensive business task creation"""
    mock_trello_client.is_configured.return_value = True
    mock_trello_client.add_missing_business_tasks.return_value = 25
    
    areas = ['sales', 'delivery', 'financial', 'operations', 'team']
    result = execute_database_action('add_business_tasks', areas=areas)
    
    assert result['success'] is True
    assert result['message'] == "Added 25 business tasks"
    mock_trello_client.add_missing_business_tasks.assert_called_once_with(areas)

# Test CEO-style Slack responses with database actions
@patch('main.trello_client')
@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
def test_slack_ceo_trello_command(mock_llm, mock_fetch_tasks, mock_requests_post, mock_trello_client):
    """Test CEO-style Trello command processing"""
    # Mock Trello success
    mock_trello_client.is_configured.return_value = True
    mock_trello_client.move_task_to_done.return_value = True
    
    # Mock other dependencies
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    mock_llm.invoke.return_value = MagicMock(content="Done")
    mock_requests_post.return_value.status_code = 200
    
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Set AI agent status to done",
            "channel": "fake_channel",
            "subtype": None
        }
    })
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    # Verify Trello was called
    mock_trello_client.move_task_to_done.assert_called_once_with('ai agent')

def test_analyze_business_request_ceo_focused():
    """Test detection of CEO-focused requests"""
    ceo_keywords = [
        "What's the revenue impact?",
        "Business strategy question", 
        "How do we grow faster?",
        "CEO priorities"
    ]
    
    for text in ceo_keywords:
        analysis = analyze_business_request(text)
        assert analysis['is_ceo_focused'] is True, f"Failed to detect CEO focus in: '{text}'"

def test_generate_dashboard_response():
    """Test CEO dashboard generation"""
    dashboard = {
        'overview': {
            'total_goals': 5,
            'completed': 2,
            'in_progress': 2,
            'blocked': 1,
            'completion_rate': 40.0
        },
        'area_progress': {
            'sales': 60.0,
            'delivery': 80.0
        },
        'high_priority_actions': [
            {'area': 'sales', 'action': 'Call prospects', 'priority': 4},
            {'area': 'delivery', 'action': 'Review quality', 'priority': 3}
        ]
    }
    
    # Import the function
    from main import generate_dashboard_response
    
    response = generate_dashboard_response(dashboard)
    
    assert "📊 **CEO Dashboard Summary**" in response
    assert "5 total • 40.0% complete" in response
    assert "2 in progress • 1 blocked" in response
    assert "Sales: 60.0%" in response
    assert "Delivery: 80.0%" in response
    assert "revenue-generating activities" in response

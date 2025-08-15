import os
import pytest
import signal
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient

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

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

# Add parent directory to sys.path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from main import app

client = TestClient(app)

class TestMessageVisibility:
    """Test that messages are properly visible in Slack channels."""
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    @patch('main.get_user_name')
    def test_slash_command_shows_original_message_in_channel(self, mock_get_user_name, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test that slash command shows the original user message in the channel."""
        # Mock dependencies
        mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
        mock_llm.invoke.return_value = MagicMock(content="Here's your analysis")
        mock_get_user_name.return_value = "User U123"
        
        # Mock successful Slack API responses
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response
        
        # Send slash command
        response = client.post(
            "/slack",
            data="command=/ai&text=What should I work on today?&channel_id=C123&user_id=U123",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Verify immediate response (critical for Slack timeout protection)
        assert response.status_code == 200
        assert response.json()["response_type"] == "ephemeral"
        assert "🤔 Let me analyze your tasks" in response.json()["text"]
        
        # Give background thread time to execute
        import time
        time.sleep(0.1)
        
        # Verify that requests.post was called for background processing
        mock_requests_post.assert_called()
        calls = mock_requests_post.call_args_list
        
        # Background processing should make 2 calls:
        # 1. Post the original user command to make it visible  
        # 2. Post the AI response
        assert len(calls) >= 2, f"Should have at least 2 Slack API calls, got {len(calls)}"
        
        # First call should post the original command with user name
        original_command_call = calls[0]
        assert "*User U123* used `/ai`: What should I work on today?" in str(original_command_call)
        
        # Second call should post the AI response
        ai_response_call = calls[1]
        assert "Here's your analysis" in str(ai_response_call)
        # Should also contain version timestamp
        assert "_OpsBrain v" in str(ai_response_call)
        
        # Verify both calls are to the correct channel
        for call in calls:
            assert "'channel': 'C123'" in str(call)
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    def test_event_message_is_visible(self, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test that event messages are properly handled and responses are visible."""
        # Mock dependencies
        mock_fetch_tasks.return_value = ["Task 1"]
        mock_llm.invoke.return_value = MagicMock(content="Response to event")
        mock_requests_post.return_value.ok = True
        
        # Send event message
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "What's my priority?",
                "channel": "C123",
                "user": "U123"
            }
        })
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        
        # Verify response was posted
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args
        
        # Check the message content includes the response and version timestamp
        message_text = call_args[1]['json']['text']
        assert "Response to event" in message_text
        assert "_OpsBrain v" in message_text
        assert "Updated:" in message_text
        assert call_args[1]['json']['channel'] == "C123"

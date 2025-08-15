import os
import pytest
import signal
from unittest.mock import patch, MagicMock
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

class TestEndToEndIntegration:
    """Test end-to-end integration of business goal features."""
    
    @patch('threading.Thread')
    @patch('main.execute_database_action')
    @patch('main.generate_ceo_insights')
    def test_slash_command_with_database_action(self, mock_insights, mock_db_action, mock_thread):
        """Test slash command that triggers database action."""
        # Mock thread to prevent actual threading
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock database action
        mock_db_action.return_value = {
            'success': True,
            'message': "Task 'Test Task' created successfully",
            'action': 'create_task'
        }
        
        # Mock insights generation
        mock_insights.return_value = "Here's your strategic advice"
        
        form_data = (
            "token=fake_token\u0026team_id=T123\u0026channel_id=C123\u0026"
            "command=/ai\u0026text=create task: Test new feature"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        json_response = response.json()
        assert "🤔 Let me analyze your tasks" in json_response["text"]
        
        # Verify background thread was created
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    def test_help_command_integration(self, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test help command integration through event system."""
        mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
        mock_requests_post.return_value.status_code = 200
        
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "help",
                "channel": "C123",
                "subtype": None
            }
        })
        
        assert response.status_code == 200
        
        # The help command should not invoke the LLM since it returns a direct response
        mock_llm.invoke.assert_not_called()

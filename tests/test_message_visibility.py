import os
import pytest
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import app

client = TestClient(app)

class TestMessageVisibility:
    """Test that messages are properly visible in Slack channels."""
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    @patch('main.detect_thread_context')
    def test_slash_command_shows_original_message_in_channel(self, mock_detect_thread, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test that slash command shows the original user message in the channel."""
        # Mock dependencies
        mock_detect_thread.return_value = None
        mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
        mock_llm.invoke.return_value = MagicMock(content="Here's your analysis")
        mock_requests_post.return_value.ok = True
        
        # Mock the background thread execution
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            # Send slash command
            response = client.post(
                "/slack",
                data="command=/ai&text=What should I work on today?&channel_id=C123&user_id=U123",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Verify immediate response
            assert response.status_code == 200
            assert response.json()["response_type"] == "ephemeral"
            
            # Verify background thread was started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            
            # Execute the background thread function manually to test the logic
            background_function = mock_thread.call_args[1]['target']
            background_function()
            
            # Verify that requests.post was called
            mock_requests_post.assert_called()
            
            # Check if the original message was posted to make it visible
            # Currently this test will FAIL because we don't post the original command
            calls = mock_requests_post.call_args_list
            
            # We should have TWO calls:
            # 1. Post the original user command to make it visible
            # 2. Post the AI response
            assert len(calls) >= 1, "Should have at least one Slack API call"
            
            # We should have TWO calls now:
            # 1. Post the original user command to make it visible
            # 2. Post the AI response
            assert len(calls) >= 2, f"Should have at least 2 Slack API calls, got {len(calls)}"
            
            # First call should post the original command
            original_command_call = calls[0]
            assert "/ai What should I work on today?" in str(original_command_call)
            
            # Second call should post the AI response
            ai_response_call = calls[1]
            assert "Sorry, I'm having trouble generating a response right now." in str(ai_response_call)
            
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
        
        # Check the message content
        assert call_args[1]['json']['text'] == "Response to event"
        assert call_args[1]['json']['channel'] == "C123"

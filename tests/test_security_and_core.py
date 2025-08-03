import os
import pytest
import time
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import hmac
import hashlib
import requests

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import app, verify_slack_signature, fetch_open_tasks

client = TestClient(app)

@pytest.fixture
def setup_environment():
    """Clean up any test state before each test."""
    yield


# === SECURITY TESTS ===

class TestSlackSignatureVerification:
    """Test Slack signature verification security."""
    
    def test_valid_signature(self):
        """Test that valid signatures are accepted."""
        body = b"test_body"
        timestamp = str(int(time.time()))  # Use current timestamp
        secret = "fake_signing_secret"
        
        # Generate valid signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        with patch('main.SLACK_SIGNING_SECRET', secret):
            assert verify_slack_signature(body, timestamp, signature) is True
    
    def test_invalid_signature(self):
        """Test that invalid signatures are rejected."""
        body = b"test_body"
        timestamp = str(int(time.time()))  # Use current timestamp
        invalid_signature = "v0=invalid_signature_hash"
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            assert verify_slack_signature(body, timestamp, invalid_signature) is False
    
    def test_missing_signature(self):
        """Test that missing signatures are rejected."""
        body = b"test_body"
        timestamp = str(int(time.time()))  # Use current timestamp
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            assert verify_slack_signature(body, timestamp, None) is False
            assert verify_slack_signature(body, timestamp, "") is False
    
    def test_missing_timestamp(self):
        """Test that missing timestamps are rejected."""
        body = b"test_body"
        signature = "v0=some_signature"
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            assert verify_slack_signature(body, None, signature) is False
            assert verify_slack_signature(body, "", signature) is False
    
    def test_old_timestamp_rejected(self):
        """Test that old timestamps are rejected (prevents replay attacks)."""
        body = b"test_body"
        old_timestamp = str(int(time.time()) - 400)  # 6+ minutes old
        signature = "v0=some_signature"
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            assert verify_slack_signature(body, old_timestamp, signature) is False
    
    def test_future_timestamp_rejected(self):
        """Test that future timestamps are rejected."""
        body = b"test_body"
        future_timestamp = str(int(time.time()) + 400)  # 6+ minutes in future
        signature = "v0=some_signature"
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            assert verify_slack_signature(body, future_timestamp, signature) is False
    
    def test_malformed_signature(self):
        """Test that malformed signatures are rejected."""
        body = b"test_body"
        timestamp = str(int(time.time()))  # Use current timestamp
        
        malformed_signatures = [
            "invalid_format",
            "v1=wrong_version",
            "v0=",  # Empty hash
            "v0=not_hex_chars!",
        ]
        
        with patch('main.SLACK_SIGNING_SECRET', 'fake_signing_secret'):
            for sig in malformed_signatures:
                assert verify_slack_signature(body, timestamp, sig) is False
    
    def test_no_signing_secret(self):
        """Test that verification fails when no signing secret is configured."""
        body = b"test_body"
        timestamp = str(int(time.time()))  # Use current timestamp
        signature = "v0=some_signature"
        
        with patch('main.SLACK_SIGNING_SECRET', None):
            assert verify_slack_signature(body, timestamp, signature) is False


class TestEndpointSecurity:
    """Test security of HTTP endpoints."""
    
    def test_empty_body_rejected(self):
        """Test that empty request bodies are rejected."""
        response = client.post("/slack", data="")
        assert response.status_code == 400
        assert "Empty request body" in response.json()["detail"]
    
    def test_invalid_json_rejected(self):
        """Test that invalid JSON is rejected."""
        response = client.post(
            "/slack",
            data="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]
    
    def test_invalid_form_data_rejected(self):
        """Test that malformed form data is handled gracefully."""
        # Send malformed form data that will cause parse_qs to fail
        response = client.post(
            "/slack",
            data=bytes([0xFF, 0xFE, 0xFD]),  # Invalid UTF-8 bytes
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 400
        assert "Invalid form data" in response.json()["detail"]
    
    @patch('main.TEST_MODE', create=True)
    @patch('main.verify_slack_signature')
    def test_signature_verification_enforced_in_production(self, mock_verify, mock_test_mode):
        """Test that signature verification is enforced in production mode."""
        with patch.dict('os.environ', {'TEST_MODE': 'false'}):
            mock_verify.return_value = False
            
            response = client.post("/slack", json={"test": "data"})
            assert response.status_code == 403
            assert "Invalid Slack signature" in response.json()["detail"]
            mock_verify.assert_called_once()
    
    def test_challenge_bypasses_signature_verification(self):
        """Test that URL verification challenges bypass signature verification."""
        response = client.post("/slack", json={
            "challenge": "test_challenge_123"
        })
        assert response.status_code == 200
        assert response.json() == {"challenge": "test_challenge_123"}


# === CORE FUNCTIONALITY TESTS ===

class TestErrorHandling:
    """Test error handling in core functionality."""
    
    @patch('main.notion')
    def test_notion_api_error_handling(self, mock_notion):
        """Test graceful handling of Notion API errors."""
        from notion_client.errors import APIResponseError
        
        # Simulate Notion API error
        mock_notion.databases.query.side_effect = APIResponseError(
            response=MagicMock(status_code=400),
            message="Database not found",
            code="object_not_found"
        )
        
        tasks = fetch_open_tasks()
        assert "Unable to fetch tasks from Notion" in tasks
    
    @patch('main.notion')
    def test_notion_generic_error_handling(self, mock_notion):
        """Test handling of generic errors from Notion."""
        mock_notion.databases.query.side_effect = Exception("API token is invalid.")
        
        tasks = fetch_open_tasks()
        assert "Error accessing task database" in tasks
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    def test_slack_api_error_handling(self, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test handling of Slack API errors when posting responses."""
        mock_fetch_tasks.return_value = ["Task 1"]
        mock_llm.invoke.return_value = MagicMock(content="Response")
        
        # Simulate Slack API error
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "channel_not_found"
        mock_requests_post.return_value = mock_response
        
        # This should not raise an exception
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "test",
                "channel": "invalid_channel"
            }
        })
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    @patch('main.requests.post')
    @patch('main.fetch_open_tasks')
    @patch('main.llm')
    def test_openai_error_handling(self, mock_llm, mock_fetch_tasks, mock_requests_post):
        """Test handling of OpenAI API errors."""
        mock_fetch_tasks.return_value = ["Task 1"]
        mock_requests_post.return_value.status_code = 200
        
        # Simulate OpenAI error
        mock_llm.invoke.side_effect = Exception("Rate limit exceeded")
        
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "test",
                "channel": "C123"
            }
        })
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    def test_bot_message_filtering(self):
        """Test that bot messages are filtered out."""
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Bot message",
                "channel": "C123",
                "subtype": "bot_message"
            }
        })
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    def test_unknown_request_format_handling(self):
        """Test handling of unknown request formats."""
        response = client.post("/slack", json={
            "unknown_field": "unknown_value"
        })
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestDataValidation:
    """Test validation of input data."""
    
    @patch('main.notion')
    def test_malformed_notion_data_handling(self, mock_notion):
        """Test handling of malformed data from Notion."""
        mock_response = {
            "results": [
                {"properties": {"Task": {"title": []}}},  # Empty title
                {"properties": {"Task": {"title": [{"text": {}}]}}},  # Missing content
                {"properties": {}},  # Missing Task property
                # Valid Task entry
                {"properties": {"Task": {"title": [{"text": {"content": "Valid Task"}}]}}}
            ]
        }
        mock_notion.databases.query.return_value = mock_response
        
        tasks = fetch_open_tasks()
        # Should handle malformed data gracefully and return valid tasks
        assert "Valid Task" in tasks
        assert len([t for t in tasks if t.strip()]) >= 1  # At least one valid task
    
    def test_missing_event_fields_handling(self):
        """Test handling of events with missing required fields."""
        # Missing 'text' field
        response = client.post("/slack", json={
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123"
                # Missing 'text' field
            }
        })
        
        # Should not crash, return OK
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    def test_slash_command_missing_fields(self):
        """Test handling of slash commands with missing fields."""
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            # Missing some optional fields
            response = client.post(
                "/slack",
                data="command=/ai&channel_id=C123",  # Missing text, user_id, etc.
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["response_type"] == "ephemeral"


class TestConcurrencyAndRateHandling:
    """Test handling of concurrent requests and rate limiting scenarios."""
    
    def test_concurrent_health_checks(self):
        """Test that multiple concurrent health checks work correctly."""
        import concurrent.futures
        
        def make_request():
            return client.get("/")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    @patch('threading.Thread')
    def test_concurrent_slash_commands(self, mock_thread):
        """Test handling of concurrent slash commands."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        import concurrent.futures
        
        def make_slash_request():
            return client.post(
                "/slack",
                data="command=/ai&text=test&channel_id=C123&user_id=U123",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_slash_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed with ephemeral responses
        for response in responses:
            assert response.status_code == 200
            assert response.json()["response_type"] == "ephemeral"
        
        # Should have started background threads
        assert mock_thread.call_count == 5

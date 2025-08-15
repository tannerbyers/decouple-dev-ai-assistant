import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import os
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Setup test environment
from test_utils import setup_test_environment
setup_test_environment()

from main import app, llm, analyze_and_remove_irrelevant_tasks

client = TestClient(app)


class TimeoutError(Exception):
    """Custom timeout error for tests"""
    pass


def mock_slow_llm_invoke(prompt):
    """Simulate a slow LLM response that times out"""
    time.sleep(70)  # Sleep longer than our timeout
    return MagicMock(content="This should not be reached due to timeout")


def mock_slow_notion_fetch():
    """Simulate a slow Notion API response"""
    time.sleep(70)  # Sleep longer than our timeout
    return []


def test_slack_command_timeout_protection():
    """Test that Slack slash commands don't hang due to slow LLM responses"""
    
    # Mock the LLM to be very slow - patch at module level since ChatOpenAI is immutable
    with patch('main.llm') as mock_llm:
        mock_llm.invoke.side_effect = mock_slow_llm_invoke
        with patch('main.fetch_open_tasks', return_value=["Test task"]):
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=review all tasks and tell me what to remove&"
                "response_url=https://hooks.slack.com/test"
            )
            
            # The initial response should be immediate (< 3 seconds)
            start_time = time.time()
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response_time = time.time() - start_time
            
            # Ensure immediate response is fast
            assert response.status_code == 200
            assert response_time < 3.0  # Slack requires response within 3 seconds
            
            json_response = response.json()
            assert "🤔 Let me analyze your tasks" in json_response["text"]
            assert json_response["response_type"] == "ephemeral"


@patch('main.requests.post')
def test_background_thread_timeout_handling(mock_requests):
    """Test that background thread processing handles timeouts correctly"""
    
    # Mock successful Slack API calls
    mock_requests.return_value.ok = True
    mock_requests.return_value.status_code = 200
    
    # Track thread completion
    thread_completed = threading.Event()
    thread_error = None
    
    def mock_slow_analyze_tasks(user_text, channel):
        """Mock function that simulates timeout in task analysis"""
        time.sleep(70)  # Longer than our timeout
        return "Should not reach here"
    
    # Mock the async function to be slow
    with patch('main.analyze_and_remove_irrelevant_tasks', side_effect=mock_slow_analyze_tasks):
        with patch('main.fetch_open_tasks', return_value=["Test task"]):
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=review all tasks and remove irrelevant ones"
            )
            
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Should get immediate response
            assert response.status_code == 200
            
            # Wait a bit to see if background thread handles timeout
            time.sleep(2)
            
            # Verify that Slack API was called (for initial response)
            assert mock_requests.called


def test_timeout_detection_in_llm_calls():
    """Test that LLM timeouts are properly detected and handled"""
    
    def slow_llm_response(*args, **kwargs):
        time.sleep(50)  # Longer than LLM timeout (45 seconds)
        return MagicMock(content="Should timeout")
    
    with patch('main.llm') as mock_llm:
        mock_llm.invoke.side_effect = slow_llm_response
        with patch('main.fetch_open_tasks', return_value=["Test task"]):
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=what should I focus on today"
            )
            
            start_time = time.time()
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response_time = time.time() - start_time
            
            # Should still get immediate response regardless of background timeout
            assert response.status_code == 200
            assert response_time < 3.0


@patch('main.requests.post')
def test_notion_api_timeout_handling(mock_requests):
    """Test that Notion API timeouts don't crash the application"""
    
    mock_requests.return_value.ok = True
    mock_requests.return_value.status_code = 200
    
    # Mock slow Notion API
    with patch('main.notion.databases.query', side_effect=lambda **kwargs: time.sleep(30) or {'results': []}):
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=show me my tasks"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should still respond immediately
        assert response.status_code == 200


def test_concurrent_timeout_scenarios():
    """Test multiple concurrent requests with timeout scenarios"""
    
    def make_request():
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=help me prioritize tasks"
        )
        
        return client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    
    with patch('main.fetch_open_tasks', return_value=["Task 1", "Task 2"]):
        with patch('main.llm') as mock_llm:
            mock_llm.invoke.side_effect = lambda p: time.sleep(60) or MagicMock(content="Timeout test")
            
            # Execute multiple requests concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(3)]
                
                # All requests should complete quickly with immediate responses
                for future in futures:
                    try:
                        response = future.result(timeout=5)  # 5 second timeout for test
                        assert response.status_code == 200
                    except FuturesTimeoutError:
                        pytest.fail("Request took too long - timeout handling not working")


@patch('main.requests.post')
def test_error_recovery_after_timeout(mock_requests):
    """Test that the system recovers properly after timeout errors"""
    
    mock_requests.return_value.ok = True
    mock_requests.return_value.status_code = 200
    
    call_count = 0
    def alternating_llm_response(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call times out
            time.sleep(50)
            return MagicMock(content="Should timeout")
        else:
            # Second call succeeds
            return MagicMock(content="Success after timeout")
    
    with patch('main.llm') as mock_llm:
        mock_llm.invoke.side_effect = alternating_llm_response
        with patch('main.fetch_open_tasks', return_value=["Test task"]):
            
            # First request (should timeout in background)
            form_data1 = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=first request"
            )
            
            response1 = client.post(
                "/slack",
                data=form_data1,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            assert response1.status_code == 200
            
            # Second request (should work normally)
            form_data2 = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=second request"
            )
            
            response2 = client.post(
                "/slack",
                data=form_data2,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            assert response2.status_code == 200


def test_memory_cleanup_during_timeout():
    """Test that memory is properly cleaned up during timeout scenarios"""
    
    # Monitor memory usage during timeout scenario
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    with patch('main.llm') as mock_llm:
        mock_llm.invoke.side_effect = lambda p: time.sleep(50) or MagicMock(content="Timeout")
        with patch('main.fetch_open_tasks', return_value=["Task"] * 100):  # Many tasks
            
            # Make multiple requests that will timeout
            for i in range(5):
                form_data = (
                    f"token=fake_token&team_id=T123&channel_id=C{i}&"
                    f"command=/ai&text=request {i}"
                )
                
                response = client.post(
                    "/slack",
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                assert response.status_code == 200
    
    # Give some time for cleanup
    time.sleep(1)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 100MB)
    assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"


if __name__ == "__main__":
    # Run specific timeout tests
    pytest.main([__file__, "-v", "--tb=short"])

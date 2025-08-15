import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Setup test environment
from test_utils import setup_test_environment
setup_test_environment()

from main import app

client = TestClient(app)


def test_slack_immediate_response_timing():
    """Test that Slack slash commands return immediate responses within 3 seconds"""
    
    # Mock all external calls to ensure they don't affect timing
    with patch('main.fetch_open_tasks', return_value=["Test task"]):
        with patch('main.get_user_name', return_value="TestUser"):
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=what should I do today&"
                "user_id=U123"
            )
            
            # Measure response time
            start_time = time.time()
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response_time = time.time() - start_time
            
            # Ensure immediate response is fast (Slack requirement)
            assert response.status_code == 200
            assert response_time < 3.0, f"Response took {response_time:.2f} seconds, should be under 3"
            
            json_response = response.json()
            assert "🤔 Let me analyze your tasks" in json_response["text"]
            assert json_response["response_type"] == "ephemeral"


@patch('main.requests.post')
def test_background_processing_isolation(mock_requests):
    """Test that background processing doesn't block the main response"""
    
    # Mock successful Slack API calls
    mock_requests.return_value.ok = True
    mock_requests.return_value.status_code = 200
    
    with patch('main.fetch_open_tasks', return_value=["Test task"]):
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=help me with tasks"
        )
        
        # Measure response time to ensure it's not blocked by background processing
        start_time = time.time()
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_time = time.time() - start_time
        
        # Should get immediate response
        assert response.status_code == 200
        assert response_time < 3.0, f"Response took {response_time:.2f}s - likely blocked by background processing"


def test_concurrent_requests_dont_block():
    """Test that multiple concurrent requests don't block each other"""
    
    def make_request(request_id):
        form_data = (
            f"token=fake_token&team_id=T123&channel_id=C{request_id}&"
            f"command=/ai&text=request {request_id}"
        )
        
        start_time = time.time()
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_time = time.time() - start_time
        
        return response, response_time
    
    with patch('main.fetch_open_tasks', return_value=["Task 1", "Task 2"]):
        
        # Execute multiple requests concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            
            # All requests should complete quickly
            for i, future in enumerate(futures):
                try:
                    response, response_time = future.result(timeout=5)
                    assert response.status_code == 200
                    assert response_time < 3.0, f"Request {i} took {response_time:.2f}s"
                except FuturesTimeoutError:
                    pytest.fail(f"Request {i} took too long - likely blocked by other requests")


def test_notion_api_timeout_fallback():
    """Test that slow Notion API calls don't block responses"""
    
    def slow_notion_query(**kwargs):
        # Simulate a slow Notion API call
        time.sleep(2)  # 2 second delay
        return {'results': []}
    
    with patch('main.notion.databases.query', side_effect=slow_notion_query):
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=show me tasks"
        )
        
        start_time = time.time()
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_time = time.time() - start_time
        
        # Should still respond immediately despite slow Notion call
        assert response.status_code == 200
        assert response_time < 3.0, f"Response blocked by Notion API: {response_time:.2f}s"


def test_error_handling_doesnt_timeout():
    """Test that error scenarios don't cause timeouts"""
    
    # Test with invalid Notion API response
    with patch('main.notion.databases.query', side_effect=Exception("Notion API Error")):
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=check my tasks"
        )
        
        start_time = time.time()
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_time = time.time() - start_time
        
        # Should handle error gracefully and respond quickly
        assert response.status_code == 200
        assert response_time < 3.0, f"Error handling took too long: {response_time:.2f}s"


def test_memory_usage_under_load():
    """Test that memory usage stays reasonable under load"""
    
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    with patch('main.fetch_open_tasks', return_value=["Task"] * 50):
        
        # Make many requests rapidly
        for i in range(20):
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
    
    # Check memory usage after requests
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    memory_mb = memory_increase / 1024 / 1024
    
    # Memory increase should be reasonable (less than 50MB for 20 requests)
    assert memory_mb < 50, f"Memory increased by {memory_mb:.1f}MB - potential memory leak"


def test_thread_cleanup():
    """Test that background threads are properly cleaned up"""
    
    import threading
    initial_thread_count = threading.active_count()
    
    with patch('main.fetch_open_tasks', return_value=["Test task"]):
        
        # Make several requests that start background threads
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
    
    # Wait a bit for threads to potentially complete
    time.sleep(1)
    
    final_thread_count = threading.active_count()
    thread_increase = final_thread_count - initial_thread_count
    
    # Thread count shouldn't increase dramatically (daemon threads should clean up)
    assert thread_increase <= 5, f"Thread count increased by {thread_increase} - potential thread leak"


@patch('main.requests.post')
def test_slack_api_timeout_handling(mock_requests):
    """Test handling of slow Slack API responses"""
    
    # Mock slow Slack API response
    def slow_slack_response(*args, **kwargs):
        time.sleep(1)  # 1 second delay
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        return mock_response
    
    mock_requests.side_effect = slow_slack_response
    
    with patch('main.fetch_open_tasks', return_value=["Test task"]):
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=test command"
        )
        
        start_time = time.time()
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response_time = time.time() - start_time
        
        # Initial response should still be fast
        assert response.status_code == 200
        assert response_time < 3.0, f"Blocked by slow Slack API: {response_time:.2f}s"


if __name__ == "__main__":
    # Run production timeout tests
    pytest.main([__file__, "-v", "--tb=short"])

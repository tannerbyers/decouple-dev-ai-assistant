#!/usr/bin/env python3
"""
Performance tests to ensure Slack timeout requirements are met.
"""
import os
import time
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Setup test environment
from test_utils import setup_test_environment
setup_test_environment()

from main import app

client = TestClient(app)

def test_health_check_performance():
    """Health check should be very fast."""
    start_time = time.time()
    response = client.get("/")
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Health check response time: {elapsed:.3f}s")
    
    assert response.status_code == 200
    assert elapsed < 0.1  # Should be under 100ms

@patch('threading.Thread')
def test_slash_command_response_time(mock_thread):
    """Slash commands must respond within 3 seconds."""
    # Mock thread to prevent actual background processing
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    form_data = (
        "token=fake_token&team_id=T123&channel_id=C123&"
        "command=/ai&text=test&response_url=https://hooks.slack.com/test"
    )
    
    start_time = time.time()
    response = client.post(
        "/slack",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Slash command response time: {elapsed:.3f}s")
    
    assert response.status_code == 200
    assert elapsed < 3.0  # Must be under 3 seconds
    assert elapsed < 1.0  # Should actually be much faster
    
    # Verify it returns immediate response
    json_response = response.json()
    assert "🤔 Let me analyze your tasks" in json_response["text"]
    assert json_response["response_type"] == "ephemeral"

def test_url_verification_performance():
    """URL verification should be very fast."""
    start_time = time.time()
    response = client.post("/slack", json={
        "type": "url_verification",
        "challenge": "test_challenge_123"
    })
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"URL verification response time: {elapsed:.3f}s")
    
    assert response.status_code == 200
    assert elapsed < 0.1  # Should be under 100ms
    assert response.json() == {"challenge": "test_challenge_123"}

@patch('main.requests.post')
@patch('main.fetch_open_tasks')
@patch('main.llm')
def test_event_subscription_performance(mock_llm, mock_fetch_tasks, mock_requests_post):
    """Event subscriptions can take longer but should still be reasonable."""
    # Mock the functions to simulate fast responses
    mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
    mock_llm.invoke.return_value = MagicMock(content="Here are your tasks")
    mock_requests_post.return_value.status_code = 200
    
    start_time = time.time()
    response = client.post("/slack", json={
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "What should I work on?",
            "channel": "fake_channel",
            "subtype": None
        }
    })
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Event subscription response time: {elapsed:.3f}s")
    
    assert response.status_code == 200
    assert elapsed < 5.0  # Should be reasonable even with mocked API calls

def test_error_handling_performance():
    """Error responses should be fast."""
    start_time = time.time()
    response = client.post("/slack", data="")
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Error handling response time: {elapsed:.3f}s")
    
    assert response.status_code == 400
    assert elapsed < 0.1  # Error responses should be very fast

def test_concurrent_requests():
    """Test handling multiple requests simultaneously."""
    import concurrent.futures
    import threading
    
    def make_health_request():
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        return response.status_code, end_time - start_time
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All should succeed and be fast
    for status_code, elapsed in results:
        assert status_code == 200
        assert elapsed < 1.0
    
    avg_time = sum(elapsed for _, elapsed in results) / len(results)
    print(f"Average concurrent request time: {avg_time:.3f}s")

if __name__ == "__main__":
    print("🚀 Running performance tests...")
    print()
    
    test_health_check_performance()
    test_slash_command_response_time()
    test_url_verification_performance()
    test_event_subscription_performance() 
    test_error_handling_performance()
    test_concurrent_requests()
    
    print()
    print("✅ All performance tests passed!")
    print("📝 Key requirements met:")
    print("- Slash commands respond within 3 seconds")
    print("- Health checks are very fast")
    print("- Error handling is immediate")
    print("- Concurrent requests are handled well")

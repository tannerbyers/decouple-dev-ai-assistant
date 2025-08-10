#!/usr/bin/env python3
"""
Timeout protection tests to ensure the application handles slow operations gracefully
and catches timeout issues before deployment.
"""
import os
import time
import threading
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pytest

# Set test environment
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import app

client = TestClient(app)

def test_slow_notion_api_call():
    """Test handling of slow Notion API calls."""
    
    def slow_fetch_tasks():
        """Simulate a slow Notion API call."""
        time.sleep(5)  # Simulate 5-second delay
        return ["Task 1", "Task 2"]
    
    with patch('main.fetch_open_tasks', side_effect=slow_fetch_tasks):
        start_time = time.time()
        
        # Test slash command with slow Notion API
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=test&response_url=https://hooks.slack.com/test"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        elapsed = time.time() - start_time
        print(f"Slow Notion API test response time: {elapsed:.3f}s")
        
        # Should still respond quickly with immediate acknowledgment
        assert response.status_code == 200
        assert elapsed < 3.0  # Must be under 3 seconds for Slack
        
        # Should return ephemeral response
        json_response = response.json()
        assert "🤔 Let me analyze your tasks" in json_response["text"]

def test_slow_openai_api_call():
    """Test handling of slow OpenAI API calls."""
    
    def slow_llm_invoke(prompt):
        """Simulate a slow OpenAI API call."""
        time.sleep(8)  # Simulate 8-second delay
        mock_response = MagicMock()
        mock_response.content = "Here's your strategic insight after a long delay."
        return mock_response
    
    with patch('main.fetch_open_tasks', return_value=["Task 1", "Task 2"]):
        with patch('main.llm') as mock_llm:
            mock_llm.invoke.side_effect = slow_llm_invoke
            
            start_time = time.time()
            
            # Test slash command with slow OpenAI API
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=strategic advice&response_url=https://hooks.slack.com/test"
            )
            
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            elapsed = time.time() - start_time
            print(f"Slow OpenAI API test response time: {elapsed:.3f}s")
            
            # Should still respond quickly with immediate acknowledgment
            assert response.status_code == 200
            assert elapsed < 3.0  # Must be under 3 seconds for Slack

def test_notion_api_timeout():
    """Test handling of Notion API timeouts."""
    
    def timeout_fetch_tasks():
        """Simulate a Notion API timeout."""
        import requests
        raise requests.exceptions.Timeout("Notion API timeout")
    
    with patch('main.fetch_open_tasks', side_effect=timeout_fetch_tasks):
        start_time = time.time()
        
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=test&response_url=https://hooks.slack.com/test"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        elapsed = time.time() - start_time
        print(f"Notion API timeout test response time: {elapsed:.3f}s")
        
        # Should still respond quickly
        assert response.status_code == 200
        assert elapsed < 3.0

def test_openai_api_timeout():
    """Test handling of OpenAI API timeouts."""
    
    def timeout_llm_invoke(prompt):
        """Simulate an OpenAI API timeout."""
        import requests
        raise requests.exceptions.Timeout("OpenAI API timeout")
    
    with patch('main.fetch_open_tasks', return_value=["Task 1", "Task 2"]):
        with patch('main.llm') as mock_llm:
            mock_llm.invoke.side_effect = timeout_llm_invoke
            
            start_time = time.time()
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&"
                "command=/ai&text=strategic advice&response_url=https://hooks.slack.com/test"
            )
            
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            elapsed = time.time() - start_time
            print(f"OpenAI API timeout test response time: {elapsed:.3f}s")
            
            # Should still respond quickly
            assert response.status_code == 200
            assert elapsed < 3.0

def test_background_thread_cleanup():
    """Test that background threads are properly managed."""
    
    original_thread_count = threading.active_count()
    
    # Make multiple slash command requests
    for i in range(5):
        form_data = (
            f"token=fake_token&team_id=T123&channel_id=C123&"
            f"command=/ai&text=test{i}&response_url=https://hooks.slack.com/test"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
    
    # Give threads time to start and potentially clean up
    time.sleep(2)
    
    current_thread_count = threading.active_count()
    print(f"Thread count - Original: {original_thread_count}, Current: {current_thread_count}")
    
    # We should have some background threads, but not too many
    # (daemon threads should be cleaned up automatically)
    assert current_thread_count <= original_thread_count + 10  # Allow some leeway

@patch('main.requests.post')
def test_slack_api_slow_response(mock_post):
    """Test handling of slow Slack API responses in background tasks."""
    
    def slow_slack_response(*args, **kwargs):
        """Simulate slow Slack API response."""
        time.sleep(10)  # Very slow response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        return mock_response
    
    mock_post.side_effect = slow_slack_response
    
    with patch('main.fetch_open_tasks', return_value=["Task 1"]):
        with patch('main.llm') as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="Quick response")
            
            start_time = time.time()
            
            form_data = (
                "token=fake_token&team_id=T123&channel_id=C123&user_id=U123&"
                "command=/ai&text=test&response_url=https://hooks.slack.com/test"
            )
            
            response = client.post(
                "/slack",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            elapsed = time.time() - start_time
            print(f"Slow Slack API test response time: {elapsed:.3f}s")
            
            # Initial response should still be fast
            assert response.status_code == 200
            assert elapsed < 3.0

def test_memory_usage_under_load():
    """Test that memory usage doesn't grow excessively under load."""
    import psutil
    import gc
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Make many requests to simulate load
    for i in range(20):
        form_data = (
            f"token=fake_token&team_id=T123&channel_id=C123&"
            f"command=/ai&text=load_test_{i}&response_url=https://hooks.slack.com/test"
        )
        
        response = client.post(
            "/slack",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
    
    # Force garbage collection
    gc.collect()
    time.sleep(1)
    
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    memory_growth_mb = memory_growth / 1024 / 1024
    
    print(f"Memory growth under load: {memory_growth_mb:.2f} MB")
    
    # Memory growth should be reasonable (less than 100MB for 20 requests)
    assert memory_growth_mb < 100

def test_event_subscription_with_delays():
    """Test event subscriptions handle delays gracefully."""
    
    with patch('main.fetch_open_tasks') as mock_fetch:
        with patch('main.llm') as mock_llm:
            with patch('main.requests.post') as mock_post:
                
                # Simulate some delay in processing
                def delayed_fetch():
                    time.sleep(2)
                    return ["Task 1", "Task 2"]
                
                def delayed_llm(prompt):
                    time.sleep(3)
                    mock_response = MagicMock()
                    mock_response.content = "Strategic insight"
                    return mock_response
                
                mock_fetch.side_effect = delayed_fetch
                mock_llm.invoke.side_effect = delayed_llm
                mock_post.return_value.ok = True
                
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
                
                elapsed = time.time() - start_time
                print(f"Event subscription with delays response time: {elapsed:.3f}s")
                
                assert response.status_code == 200
                # Event subscriptions can take longer, but should still be reasonable
                assert elapsed < 10.0

def test_slack_3_second_timeout_compliance():
    """Test that slash commands respond within 3 seconds even with multiple slow operations."""
    
    def super_slow_operations():
        """Simulate multiple slow operations that might occur together."""
        time.sleep(6)  # Simulate very slow Notion + OpenAI combination
        return ["Task 1", "Task 2"]
    
    def slow_user_lookup(*args, **kwargs):
        """Simulate slow user name lookup from Slack API."""
        time.sleep(2)
        return "Test User"
    
    with patch('main.fetch_open_tasks', side_effect=super_slow_operations):
        with patch('main.get_user_name', side_effect=slow_user_lookup):
            with patch('main.llm') as mock_llm:
                mock_llm.invoke.side_effect = lambda prompt: type('obj', (object,), {'content': 'Strategic response'})()
                
                start_time = time.time()
                
                # Test slash command with multiple slow operations
                form_data = (
                    "token=fake_token&team_id=T123&channel_id=C123&user_id=U123&"
                    "command=/ai&text=strategic advice&response_url=https://hooks.slack.com/test"
                )
                
                response = client.post(
                    "/slack",
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                elapsed = time.time() - start_time
                print(f"Multiple slow operations test response time: {elapsed:.3f}s")
                
                # CRITICAL: Must respond within Slack's 3-second timeout regardless of slow operations
                assert response.status_code == 200
                assert elapsed < 3.0, f"Response took {elapsed:.3f}s, must be under 3.0s for Slack"
                
                # Should return immediate ephemeral acknowledgment
                json_response = response.json()
                assert "🤔 Let me analyze your tasks" in json_response["text"]
                assert json_response["response_type"] == "ephemeral"

if __name__ == "__main__":
    print("🛡️  Running timeout protection tests...")
    print()
    
    test_slow_notion_api_call()
    test_slow_openai_api_call()
    test_notion_api_timeout()
    test_openai_api_timeout()
    test_background_thread_cleanup()
    test_slack_api_slow_response()
    test_memory_usage_under_load()
    test_event_subscription_with_delays()
    test_slack_3_second_timeout_compliance()
    
    print()
    print("✅ All timeout protection tests passed!")
    print("🎯 Key protections verified:")
    print("- Slash commands respond within Slack's 3-second timeout")
    print("- Slow external API calls don't block immediate responses")
    print("- API timeouts are handled gracefully")  
    print("- Background threads are properly managed")
    print("- Memory usage stays reasonable under load")
    print("- Both slash commands and events handle delays well")

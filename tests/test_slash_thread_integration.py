import os
import pytest
import responses
import time
from unittest.mock import patch

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import app, detect_thread_context, get_thread_context, update_thread_context, thread_conversations
from fastapi.testclient import TestClient

# Prepare test client
client = TestClient(app)

@pytest.fixture
def setup_environment():
    """Clean up thread conversations before each test."""
    thread_conversations.clear()
    yield
    thread_conversations.clear()


@responses.activate
def test_detect_thread_context_with_recent_message():
    """Test detecting thread context when user has recent thread messages."""
    current_time = time.time()
    responses.add(
        responses.GET,
        "https://slack.com/api/conversations.history",
        json={
            "ok": True,
            "messages": [
                {"user": "U123", "thread_ts": "150", "ts": str(current_time - 60), "text": "A recent thread message"},
                {"user": "U456", "thread_ts": "150", "ts": str(current_time - 120), "text": "Another message"}
            ]
        },
        status=200
    )


    thread_ts = detect_thread_context("C123", "U123")
    assert thread_ts == "150"


@responses.activate  
def test_detect_thread_context_with_old_message():
    """Test that old thread messages are not detected."""
    old_time = time.time() - 400  # 6+ minutes ago
    responses.add(
        responses.GET,
        "https://slack.com/api/conversations.history",
        json={
            "ok": True,
            "messages": [
                {"user": "U123", "thread_ts": "150", "ts": str(old_time), "text": "An old thread message"}
            ]
        },
        status=200
    )
    
    thread_ts = detect_thread_context("C123", "U123")
    assert thread_ts is None


@responses.activate
def test_detect_thread_context_api_failure():
    """Test graceful handling when Slack API fails."""
    responses.add(
        responses.GET,
        "https://slack.com/api/conversations.history",
        json={"ok": False, "error": "channel_not_found"},
        status=200
    )
    
    thread_ts = detect_thread_context("C123", "U123")
    assert thread_ts is None


@responses.activate
def test_slash_command_with_thread_detection(setup_environment):
    """Test slash command with thread context detection."""
    current_time = time.time()
    
    # Mock Slack API calls
    responses.add(
        responses.GET,
        "https://slack.com/api/conversations.history",
        json={
            "ok": True,
            "messages": [
                {"user": "U123", "thread_ts": "150", "ts": str(current_time - 60), "text": "Thread message"}
            ]
        },
        status=200
    )
    
    responses.add(
        responses.POST,
        "https://slack.com/api/chat.postMessage",
        json={"ok": True},
        status=200
    )

    # Simulate a slash command
    response = client.post(
        "/slack",
        data="command=/ai&text=what+is+my+current+context&channel_id=C123&user_id=U123",
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    # Check that the initial response is ephemeral
    assert response.json()["response_type"] == "ephemeral"
    assert "analyze your tasks" in response.json()["text"]


def test_thread_context_continuation(setup_environment):
    """Test that thread context is properly maintained across messages."""
    # First message in thread
    context1 = get_thread_context("150", "C123", "How's it going?")
    assert len(context1['messages']) == 1
    assert context1['messages'][0] == "User: How's it going?"
    
    # Update with AI response
    update_thread_context("150", "C123", "It's going well!")
    
    # Second message in same thread
    context2 = get_thread_context("150", "C123", "What should I do next?")
    assert len(context2['messages']) == 3
    assert context2['messages'][0] == "User: How's it going?"
    assert context2['messages'][1] == "OpsBrain: It's going well!"
    assert context2['messages'][2] == "User: What should I do next?"


def test_slash_command_without_thread(setup_environment):
    """Test slash command when no thread context is detected."""
    context = get_thread_context(None, "C123", "Hello AI")
    assert len(context['messages']) == 1
    assert context['messages'][0] == "User: Hello AI"
    
    # Ensure no thread key is created
    assert len(thread_conversations) == 0

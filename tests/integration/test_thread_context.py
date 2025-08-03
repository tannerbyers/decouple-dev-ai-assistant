import os
import pytest

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import get_thread_context, update_thread_context, thread_conversations, cleanup_old_threads

@pytest.fixture
def setup_environment():
    # Cleanup before each test
    thread_conversations.clear()
    yield
    # Cleanup after each test
    thread_conversations.clear()


def test_get_thread_context_creates_context_for_new_thread(setup_environment):
    context = get_thread_context("12345", "C123", "Hello, how are you?")
    assert len(context['messages']) == 1
    assert context['messages'][0] == "User: Hello, how are you?"
    assert f"C123:12345" in thread_conversations


def test_get_thread_context_adds_to_existing_thread(setup_environment):
    # Simulate existing thread
    thread_conversations['C123:12345'] = {
        'messages': ["User: Existing message."],
        'created_at': 1704067200.0
    }
    context = get_thread_context("12345", "C123", "Another message!")
    assert len(context['messages']) == 2
    assert context['messages'][0] == "User: Existing message."
    assert context['messages'][1] == "User: Another message!"


def test_update_thread_context_appends_ai_response(setup_environment):
    # Simulate existing thread
    thread_conversations['C123:12345'] = {
        'messages': ["User: Hello!"],
        'created_at': 1704067200.0
    }
    update_thread_context("12345", "C123", "Hi there!")
    context = thread_conversations['C123:12345']
    assert len(context['messages']) == 2
    assert context['messages'][1] == "OpsBrain: Hi there!"


def test_cleanup_old_threads_removes_old_conversations(setup_environment):
    import time
    
    # Simulate existing threads
    thread_conversations['C123:12345'] = {
        'messages': ["User: Old message."],
        'created_at': 0  # Very old timestamp
    }
    thread_conversations['C123:67890'] = {
        'messages': ["User: Recent message."],
        'created_at': time.time()  # Current time - should not be cleaned up
    }
    cleanup_old_threads()
    assert 'C123:12345' not in thread_conversations
    assert 'C123:67890' in thread_conversations

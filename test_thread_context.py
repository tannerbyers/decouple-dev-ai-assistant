import os
import pytest
import time
from unittest.mock import patch, MagicMock

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import get_thread_context, update_thread_context, cleanup_old_threads, thread_contexts

def test_get_thread_context_new_thread():
    """Test creating a new thread context"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Create new context
    context = get_thread_context(None, "C123", "Hello world")
    
    # Verify new context was created
    assert context['messages'] == ['User: Hello world']
    assert 'created_at' in context
    assert len(thread_contexts) == 1
    assert 'C123' in thread_contexts

def test_get_thread_context_existing_thread():
    """Test retrieving and updating existing thread context"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Create first context
    context1 = get_thread_context("1234567890.123456", "C123", "First message")
    
    # Add another message to same thread
    context2 = get_thread_context("1234567890.123456", "C123", "Second message")
    
    # Verify it's the same context with both messages
    assert len(thread_contexts) == 1
    assert context2['messages'] == [
        'User: First message',
        'User: Second message'
    ]
    assert context1 is context2

def test_update_thread_context():
    """Test updating thread context with AI responses"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Create context
    get_thread_context("1234567890.123456", "C123", "Hello")
    
    # Update with AI response
    update_thread_context("1234567890.123456", "C123", "Hello! How can I help?")
    
    # Verify response was added
    thread_key = "C123:1234567890.123456"
    context = thread_contexts[thread_key]
    assert context['messages'] == [
        'User: Hello',
        'OpsBrain: Hello! How can I help?'
    ]

def test_message_limit():
    """Test that message history is limited to 10 messages"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Add 15 messages
    for i in range(15):
        get_thread_context("1234567890.123456", "C123", f"Message {i}")
        update_thread_context("1234567890.123456", "C123", f"Response {i}")
    
    # Check that only last 10 messages are kept
    thread_key = "C123:1234567890.123456"
    context = thread_contexts[thread_key]
    assert len(context['messages']) == 10
    
    # Check that it contains the most recent messages
    assert 'Message 14' in context['messages'][-2]
    assert 'Response 14' in context['messages'][-1]

def test_cleanup_old_threads():
    """Test cleanup of old thread contexts"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Create a thread context with old timestamp (25 hours ago)
    old_time = time.time() - (25 * 60 * 60)  # 25 hours ago
    thread_contexts["C123:old_thread"] = {
        'messages': ['User: Old message'],
        'created_at': old_time
    }
    
    # Create a recent thread context manually to avoid triggering cleanup
    recent_time = time.time()
    thread_contexts["C123:1234567890.123456"] = {
        'messages': ['User: Recent message'],
        'created_at': recent_time
    }
    
    # Verify we have 2 contexts
    assert len(thread_contexts) == 2
    
    # Run cleanup
    cleanup_old_threads()
    
    # Verify old context was removed, recent one remains
    assert len(thread_contexts) == 1
    assert "C123:old_thread" not in thread_contexts
    assert "C123:1234567890.123456" in thread_contexts

def test_non_threaded_messages():
    """Test handling of non-threaded messages (channel-level conversations)"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Create context for non-threaded message (thread_ts = None)
    context = get_thread_context(None, "C123", "Direct message")
    
    # Verify context uses channel as key
    assert "C123" in thread_contexts
    assert context['messages'] == ['User: Direct message']

def test_update_nonexistent_thread():
    """Test updating a thread context that doesn't exist"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Try to update non-existent thread (should log warning but not crash)
    update_thread_context("1234567890.123456", "C123", "Response to nothing")
    
    # Verify no context was created
    assert len(thread_contexts) == 0

if __name__ == "__main__":
    # Run tests
    test_get_thread_context_new_thread()
    test_get_thread_context_existing_thread()
    test_update_thread_context()
    test_message_limit()
    test_cleanup_old_threads()
    test_non_threaded_messages()
    test_update_nonexistent_thread()
    
    print("✅ All thread context tests passed!")

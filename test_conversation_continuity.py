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

from main import get_thread_context, update_thread_context, thread_contexts

def test_conversation_continuity_example():
    """Test a complete conversation flow that demonstrates context retention"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    # Simulate the conversation from your example
    channel = "C123456"
    thread_ts = "1234567890.123456"  # Same thread
    
    # User asks to remove all tasks
    context1 = get_thread_context(thread_ts, channel, "go through and remove all my current tasks")
    update_thread_context(thread_ts, channel, "To proceed with your request, I'll need your confirmation to permanently remove all your pending tasks. Please be aware that this action cannot be undone.")
    
    # User confirms deletion
    context2 = get_thread_context(thread_ts, channel, "I confirm I want all my tasks deleted")
    update_thread_context(thread_ts, channel, "To ensure I understand your request fully, you would like all current pending tasks to be deleted. This action is irreversible. Confirm if you want to proceed?")
    
    # User says confirm again
    context3 = get_thread_context(thread_ts, channel, "confirm")
    
    # Verify all contexts are the same object (conversation continuity)
    assert context1 is context2 is context3
    
    # Verify the conversation history contains all messages
    expected_messages = [
        'User: go through and remove all my current tasks',
        'OpsBrain: To proceed with your request, I\'ll need your confirmation to permanently remove all your pending tasks. Please be aware that this action cannot be undone.',
        'User: I confirm I want all my tasks deleted', 
        'OpsBrain: To ensure I understand your request fully, you would like all current pending tasks to be deleted. This action is irreversible. Confirm if you want to proceed?',
        'User: confirm'
    ]
    
    assert context3['messages'] == expected_messages
    
    # At this point, the AI should understand the full context
    # It knows that:
    # 1. User wants to delete all tasks
    # 2. User has confirmed twice
    # 3. It should proceed with deletion instead of asking for more details
    
    print("✅ Conversation context is maintained across messages!")
    print("Current conversation:")
    for i, msg in enumerate(context3['messages'], 1):
        print(f"  {i}. {msg}")

def test_different_threads_different_contexts():
    """Test that different threads maintain separate contexts"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    channel = "C123456"
    thread1 = "1111111111.111111"
    thread2 = "2222222222.222222"
    
    # Create contexts in different threads
    context1 = get_thread_context(thread1, channel, "Hello from thread 1")
    context2 = get_thread_context(thread2, channel, "Hello from thread 2")
    
    # Verify they're different contexts
    assert context1 is not context2
    assert len(thread_contexts) == 2
    
    # Verify each has its own message
    assert context1['messages'] == ['User: Hello from thread 1']
    assert context2['messages'] == ['User: Hello from thread 2']
    
    print("✅ Different threads maintain separate contexts!")

def test_non_threaded_vs_threaded():
    """Test that non-threaded and threaded messages have separate contexts"""
    # Clear any existing contexts
    thread_contexts.clear()
    
    channel = "C123456"
    thread_ts = "1234567890.123456"
    
    # Non-threaded message (channel-level conversation)
    context1 = get_thread_context(None, channel, "Direct message to channel")
    
    # Threaded message
    context2 = get_thread_context(thread_ts, channel, "Message in thread")
    
    # Verify they're different contexts
    assert context1 is not context2
    assert len(thread_contexts) == 2
    
    # Verify thread keys are different
    assert channel in thread_contexts  # Non-threaded
    assert f"{channel}:{thread_ts}" in thread_contexts  # Threaded
    
    print("✅ Threaded and non-threaded messages have separate contexts!")

if __name__ == "__main__":
    test_conversation_continuity_example()
    test_different_threads_different_contexts()
    test_non_threaded_vs_threaded()
    print("\n🎉 All conversation continuity tests passed!")

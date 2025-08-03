#!/usr/bin/env python3
"""
Test script to measure response times for Slack command handling.
"""
import time
import requests
import json
from urllib.parse import urlencode

# Test data that mimics a Slack slash command
test_data = {
    'token': 'test_token',
    'team_id': 'T098RS8BJ84',
    'team_domain': 'test',
    'channel_id': 'C099CAA08HW',
    'channel_name': 'ai-assistant',
    'user_id': 'U098RS8C39A',
    'user_name': 'test_user',
    'command': '/ai',
    'text': 'test',
    'api_app_id': 'A099CEH0DB2',
    'is_enterprise_install': 'false',
    'response_url': 'https://hooks.slack.com/commands/test/response',
    'trigger_id': 'test_trigger'
}

def test_local_timing():
    """Test the timing of our local server."""
    print("Testing local server timing...")
    
    # Convert to form data like Slack sends
    form_data = urlencode(test_data)
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': str(int(time.time())),
        'X-Slack-Signature': 'v0=test_signature'
    }
    
    start_time = time.time()
    
    try:
        # Test against local server
        response = requests.post(
            'http://localhost:8000/slack',
            data=form_data,
            headers=headers,
            timeout=10
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✅ Response time: {elapsed:.3f} seconds")
        print(f"✅ Status code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        
        if elapsed < 3.0:
            print("🎉 SUCCESS: Response time is under 3 seconds!")
        else:
            print("❌ TIMEOUT: Response took longer than 3 seconds")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_production_timing():
    """Test the timing of production server."""
    print("\nTesting production server timing...")
    
    # Convert to form data like Slack sends
    form_data = urlencode(test_data)
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': str(int(time.time())),
        'X-Slack-Signature': 'v0=test_signature'
    }
    
    start_time = time.time()
    
    try:
        # Test against production server
        response = requests.post(
            'https://decouple-ai.onrender.com/slack',
            data=form_data,
            headers=headers,
            timeout=10
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✅ Response time: {elapsed:.3f} seconds")
        print(f"✅ Status code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        
        if elapsed < 3.0:
            print("🎉 SUCCESS: Response time is under 3 seconds!")
        else:
            print("❌ TIMEOUT: Response took longer than 3 seconds")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Slack command response timing\n")
    
    # Test local server first
    test_local_timing()
    
    # Test production server
    test_production_timing()
    
    print("\n📝 Notes:")
    print("- Slack requires responses within 3 seconds")
    print("- Times over 3s will show 'operation timed out' to users")
    print("- Use immediate acknowledgment + delayed response for long operations")

"""
Shared test utilities for consistent test environment setup across all test files.
"""
import os
import hmac
import hashlib
import time
from typing import Dict, Any

def setup_test_environment():
    """Setup test environment variables before importing main modules."""
    test_env = {
        'SLACK_BOT_TOKEN': 'fake_slack_token',
        'SLACK_SIGNING_SECRET': 'fake_slack_signing_secret',
        'NOTION_API_KEY': 'fake_notion_key',
        'NOTION_DB_ID': 'fake_db_id',
        'OPENAI_API_KEY': 'fake_openai_key',
        'TEST_MODE': 'true',
        'TRELLO_API_KEY': 'fake_trello_key',
        'TRELLO_TOKEN': 'fake_trello_token',
        'TRELLO_BOARD_ID': 'fake_board_id',
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    return test_env

def create_valid_slack_signature(body: str, timestamp: str = None, secret: str = None) -> Dict[str, str]:
    """Create valid Slack signature headers for testing."""
    if timestamp is None:
        timestamp = str(int(time.time()))
    
    if secret is None:
        secret = os.getenv('SLACK_SIGNING_SECRET', 'fake_slack_signing_secret')
    
    # Create signature
    sig_basestring = f"v0:{timestamp}:{body}"
    signature = 'v0=' + hmac.new(
        secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "x-slack-request-timestamp": timestamp,
        "x-slack-signature": signature
    }

def get_slack_form_data_with_signature(form_data: str) -> tuple[str, Dict[str, str]]:
    """Get form data with valid Slack signature headers."""
    headers = create_valid_slack_signature(form_data)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    return form_data, headers

def get_slack_json_data_with_signature(json_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, str]]:
    """Get JSON data with valid Slack signature headers."""
    import json
    json_body = json.dumps(json_data)
    headers = create_valid_slack_signature(json_body)
    headers["Content-Type"] = "application/json"
    return json_data, headers

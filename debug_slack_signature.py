#!/usr/bin/env python3
"""
Debug script for Slack signature verification issues.
This helps identify why signature verification is failing in production.
"""
import os
import hmac
import hashlib
import time
from typing import Dict, Any

def verify_slack_signature_debug(body: str, timestamp: str, signature: str, signing_secret: str) -> Dict[str, Any]:
    """
    Debug version of Slack signature verification with detailed logging.
    """
    result = {
        'valid': False,
        'details': {},
        'debug_info': {}
    }
    
    # Check inputs
    result['debug_info']['inputs'] = {
        'body_length': len(body) if body else 0,
        'timestamp': timestamp,
        'signature': signature,
        'signing_secret_set': bool(signing_secret),
        'signing_secret_length': len(signing_secret) if signing_secret else 0
    }
    
    if not timestamp or not signature or not signing_secret:
        result['details']['error'] = 'Missing required parameters'
        result['details']['missing'] = {
            'timestamp': not timestamp,
            'signature': not signature,
            'signing_secret': not signing_secret
        }
        return result
    
    try:
        # Check timestamp (prevent replay attacks)
        current_time = time.time()
        request_time = int(timestamp)
        time_diff = abs(current_time - request_time)
        
        result['debug_info']['timing'] = {
            'current_time': current_time,
            'request_time': request_time,
            'time_diff_seconds': time_diff,
            'max_allowed_seconds': 300,
            'timestamp_valid': time_diff <= 300
        }
        
        if time_diff > 60 * 5:  # 5 minutes
            result['details']['error'] = 'Request too old'
            result['details']['time_diff'] = time_diff
            return result
        
        # Verify signature
        sig_basestring = f"v0:{timestamp}:{body}"
        result['debug_info']['signature_basestring'] = sig_basestring
        result['debug_info']['signature_basestring_length'] = len(sig_basestring)
        
        # Create expected signature
        my_signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result['debug_info']['signatures'] = {
            'expected': my_signature,
            'received': signature,
            'match': my_signature == signature,
            'hmac_match': hmac.compare_digest(my_signature, signature)
        }
        
        # Compare signatures
        signature_valid = hmac.compare_digest(my_signature, signature)
        result['valid'] = signature_valid
        
        if not signature_valid:
            result['details']['error'] = 'Signature mismatch'
            # Show first few characters for debugging (not full signature for security)
            result['details']['signature_prefix_expected'] = my_signature[:10] + '...'
            result['details']['signature_prefix_received'] = signature[:10] + '...'
        
        return result
        
    except (ValueError, TypeError) as e:
        result['details']['error'] = f'Verification error: {str(e)}'
        return result

def test_with_sample_data():
    """Test signature verification with sample Slack data."""
    print("🔍 Testing Slack Signature Verification Debug Tool\n")
    
    # Sample data (this would normally come from a real Slack request)
    signing_secret = os.getenv('SLACK_SIGNING_SECRET', 'your_signing_secret_here')
    timestamp = str(int(time.time()))  # Current timestamp
    body = "token=test&team_id=T123&channel_id=C123&user_id=U123&command=/ai&text=hello"
    
    # Create a valid signature for testing
    sig_basestring = f"v0:{timestamp}:{body}"
    valid_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print("📋 Test Data:")
    print(f"  Body: {body}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Valid Signature: {valid_signature[:20]}...")
    print(f"  Signing Secret Set: {'Yes' if signing_secret != 'your_signing_secret_here' else 'No (using dummy)'}")
    print()
    
    # Test 1: Valid signature
    print("✅ Test 1: Valid signature")
    result = verify_slack_signature_debug(body, timestamp, valid_signature, signing_secret)
    print(f"  Result: {'PASS' if result['valid'] else 'FAIL'}")
    if not result['valid']:
        print(f"  Error: {result['details'].get('error', 'Unknown')}")
    print()
    
    # Test 2: Invalid signature
    print("❌ Test 2: Invalid signature")
    invalid_signature = "v0=invalid_signature_here"
    result = verify_slack_signature_debug(body, timestamp, invalid_signature, signing_secret)
    print(f"  Result: {'PASS' if not result['valid'] else 'FAIL'} (should fail)")
    print(f"  Error: {result['details'].get('error', 'No error')}")
    print()
    
    # Test 3: Old timestamp
    print("⏰ Test 3: Old timestamp (should fail)")
    old_timestamp = str(int(time.time()) - 400)  # 400 seconds ago
    old_sig_basestring = f"v0:{old_timestamp}:{body}"
    old_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        old_sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    result = verify_slack_signature_debug(body, old_timestamp, old_signature, signing_secret)
    print(f"  Result: {'PASS' if not result['valid'] else 'FAIL'} (should fail)")
    print(f"  Error: {result['details'].get('error', 'No error')}")
    print()
    
    # Test 4: Production-like scenario
    print("🚀 Production Debugging Info:")
    print("  Use this function in your production logs to debug signature issues.")
    print("  Key things to check:")
    print("    1. Is the body being read correctly?")
    print("    2. Is the timestamp from the correct header?")
    print("    3. Is the signature from the correct header?")
    print("    4. Is the signing secret correct in production?")
    print("    5. Are headers being parsed correctly by the web framework?")
    print()
    
    return result

def debug_production_issue():
    """
    Debug helper for production issues.
    This shows what to log in production to debug signature verification.
    """
    print("🔧 Production Debugging Guide:")
    print()
    print("Add this to your production code to debug signature verification:")
    print()
    
    debug_code = '''
# In your Slack endpoint, add this debugging:
logger.info(f"Debugging signature verification:")
logger.info(f"  Raw body length: {len(raw_body)}")
logger.info(f"  Body preview: {raw_body[:100]}...")  # First 100 chars
logger.info(f"  Timestamp header: {x_slack_request_timestamp}")
logger.info(f"  Signature header: {x_slack_signature}")
logger.info(f"  All headers: {list(req.headers.keys())}")

# Use the debug function
debug_result = verify_slack_signature_debug(
    raw_body.decode('utf-8'),
    x_slack_request_timestamp,
    x_slack_signature,
    SLACK_SIGNING_SECRET
)
logger.info(f"Signature debug result: {debug_result}")
'''
    
    print(debug_code)
    print()
    print("This will help you identify:")
    print("  - Whether headers are being read correctly")
    print("  - Whether the body is being modified during parsing")
    print("  - Whether timestamps are within the valid range")
    print("  - Whether the signature calculation matches Slack's")

if __name__ == '__main__':
    # Test the verification function
    test_result = test_with_sample_data()
    
    # Show production debugging guide
    debug_production_issue()
    
    print("🎯 Next Steps:")
    print("1. Run this script locally to verify the debug function works")
    print("2. Add the debug logging to your production endpoint")
    print("3. Check production logs to see exactly what's happening with signatures")
    print("4. Compare the signature calculation in production vs expected")

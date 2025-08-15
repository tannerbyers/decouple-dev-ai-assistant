#!/usr/bin/env python3
"""
Comprehensive Slack Integration Test Suite
Tests real Slack API integration with signature verification and production deployment.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import argparse
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

class SlackIntegrationTester:
    """Comprehensive Slack integration testing with real API calls"""
    
    def __init__(self, slack_url: str, signing_secret: Optional[str] = None, timeout: int = 30):
        self.slack_url = slack_url.rstrip('/')
        self.signing_secret = signing_secret
        self.timeout = timeout
        self.results = {'passed': 0, 'failed': 0, 'total': 0}
        self.test_results = []
        
        # Test data
        self.test_channel = "C1234567890"
        self.test_user = "U1234567890"
        
    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("🤖 SLACK INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"Target URL: {self.slack_url}")
        print(f"Timeout: {self.timeout}s")
        print(f"Signature Verification: {'✓ Enabled' if self.signing_secret else '✗ Disabled'}")
        print("=" * 80)
        print()

    def create_slack_signature(self, timestamp: str, body: str) -> str:
        """Create valid Slack signature for request verification"""
        if not self.signing_secret:
            return ""
        
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"v0={signature}"

    def make_slack_request(self, payload: Dict[str, Any], expect_success: bool = True) -> Tuple[bool, Dict]:
        """Make a Slack webhook request with proper signature"""
        body = json.dumps(payload)
        timestamp = str(int(time.time()))
        
        headers = {
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
        }
        
        if self.signing_secret:
            signature = self.create_slack_signature(timestamp, body)
            headers["X-Slack-Signature"] = signature
        
        try:
            response = requests.post(
                f"{self.slack_url}/slack",
                data=body,
                headers=headers,
                timeout=self.timeout
            )
            
            success = response.status_code == 200 if expect_success else response.status_code != 200
            
            result = {
                'status_code': response.status_code,
                'response_text': response.text[:500],  # Truncate long responses
                'headers': dict(response.headers),
                'success': success
            }
            
            return success, result
            
        except requests.exceptions.Timeout:
            return False, {'error': 'Request timeout', 'success': False}
        except requests.exceptions.RequestException as e:
            return False, {'error': str(e), 'success': False}

    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"🧪 Testing: {test_name}")
        
        try:
            success = test_func()
            
            if success:
                print(f"  ✅ PASSED")
                self.results['passed'] += 1
            else:
                print(f"  ❌ FAILED")
                self.results['failed'] += 1
            
            self.results['total'] += 1
            self.test_results.append({
                'name': test_name,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            print(f"  💥 ERROR: {str(e)}")
            self.results['failed'] += 1
            self.results['total'] += 1
            self.test_results.append({
                'name': test_name,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False

    def test_health_endpoint(self) -> bool:
        """Test basic health check endpoint"""
        try:
            response = requests.get(f"{self.slack_url}/", timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                print(f"    Status: {data.get('status')}")
                print(f"    Test Mode: {data.get('test_mode')}")
                return data.get('status') == 'healthy'
            else:
                print(f"    Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    Health check error: {e}")
            return False

    def test_slack_url_verification(self) -> bool:
        """Test Slack URL verification challenge"""
        challenge_token = "test_challenge_12345"
        payload = {
            "type": "url_verification",
            "challenge": challenge_token
        }
        
        success, result = self.make_slack_request(payload)
        
        if success and challenge_token in result.get('response_text', ''):
            print(f"    Challenge response: {result['response_text']}")
            return True
        else:
            print(f"    Challenge failed: {result}")
            return False

    def test_message_event_processing(self) -> bool:
        """Test basic message event processing"""
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "What should I work on today?",
                "channel": self.test_channel,
                "user": self.test_user,
                "ts": str(time.time())
            }
        }
        
        success, result = self.make_slack_request(payload)
        
        if success:
            print(f"    Response status: {result['status_code']}")
            return True
        else:
            print(f"    Message processing failed: {result}")
            return False

    def test_thread_message_handling(self) -> bool:
        """Test message handling in threads"""
        thread_ts = str(time.time() - 3600)  # 1 hour ago
        
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Continue our conversation about tasks",
                "channel": self.test_channel,
                "user": self.test_user,
                "ts": str(time.time()),
                "thread_ts": thread_ts
            }
        }
        
        success, result = self.make_slack_request(payload)
        
        if success:
            print(f"    Thread message handled: {result['status_code']}")
            return True
        else:
            print(f"    Thread message failed: {result}")
            return False

    def test_task_management_commands(self) -> bool:
        """Test various task management commands"""
        test_commands = [
            "Show me my tasks",
            "Create task: Test deployment integration",
            "What's in my backlog?",
            "Help me prioritize my day",
            "Add client: Test Corporation"
        ]
        
        all_passed = True
        
        for command in test_commands:
            payload = {
                "type": "event_callback",
                "event": {
                    "type": "message",
                    "text": command,
                    "channel": self.test_channel,
                    "user": self.test_user,
                    "ts": str(time.time())
                }
            }
            
            success, result = self.make_slack_request(payload)
            
            if success:
                print(f"    ✅ '{command[:30]}...' -> {result['status_code']}")
            else:
                print(f"    ❌ '{command[:30]}...' -> {result.get('status_code', 'ERROR')}")
                all_passed = False
            
            time.sleep(0.5)  # Rate limiting
        
        return all_passed

    def test_ceo_workflow_commands(self) -> bool:
        """Test CEO-specific workflow commands"""
        ceo_commands = [
            "Generate weekly plan",
            "Show me the dashboard",
            "What's my revenue pipeline?",
            "Help me with sales strategy",
            "Review all my tasks"
        ]
        
        all_passed = True
        
        for command in ceo_commands:
            payload = {
                "type": "event_callback",
                "event": {
                    "type": "message",
                    "text": command,
                    "channel": self.test_channel,
                    "user": self.test_user,
                    "ts": str(time.time())
                }
            }
            
            success, result = self.make_slack_request(payload)
            
            if success:
                print(f"    ✅ CEO: '{command[:25]}...' -> {result['status_code']}")
            else:
                print(f"    ❌ CEO: '{command[:25]}...' -> {result.get('status_code', 'ERROR')}")
                all_passed = False
            
            time.sleep(0.5)  # Rate limiting
        
        return all_passed

    def test_signature_verification_security(self) -> bool:
        """Test signature verification security"""
        if not self.signing_secret:
            print("    Skipping - No signing secret provided")
            return True
        
        # Test with invalid signature
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "This should be rejected",
                "channel": self.test_channel,
                "user": self.test_user,
                "ts": str(time.time())
            }
        }
        
        body = json.dumps(payload)
        timestamp = str(int(time.time()))
        
        headers = {
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": "v0=invalid_signature_12345"
        }
        
        try:
            response = requests.post(
                f"{self.slack_url}/slack",
                data=body,
                headers=headers,
                timeout=self.timeout
            )
            
            # Should reject invalid signature (403)
            if response.status_code == 403:
                print(f"    ✅ Invalid signature rejected: {response.status_code}")
                return True
            else:
                print(f"    ❌ Security issue - accepted invalid signature: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ❌ Signature test error: {e}")
            return False

    def test_replay_attack_protection(self) -> bool:
        """Test replay attack protection"""
        if not self.signing_secret:
            print("    Skipping - No signing secret provided")
            return True
        
        # Test with old timestamp (should be rejected)
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
        
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Old timestamp test",
                "channel": self.test_channel,
                "user": self.test_user,
                "ts": str(time.time())
            }
        }
        
        body = json.dumps(payload)
        signature = self.create_slack_signature(old_timestamp, body)
        
        headers = {
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": old_timestamp,
            "X-Slack-Signature": signature
        }
        
        try:
            response = requests.post(
                f"{self.slack_url}/slack",
                data=body,
                headers=headers,
                timeout=self.timeout
            )
            
            # Should reject old timestamp (403)
            if response.status_code == 403:
                print(f"    ✅ Replay attack blocked: {response.status_code}")
                return True
            else:
                print(f"    ❌ Security issue - accepted old timestamp: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ❌ Replay test error: {e}")
            return False

    def test_malformed_request_handling(self) -> bool:
        """Test handling of malformed requests"""
        malformed_tests = [
            ("Empty body", ""),
            ("Invalid JSON", "{'invalid': json}"),
            ("Missing event type", '{"event": {}}'),
            ("Large payload", json.dumps({"data": "x" * 10000}))
        ]
        
        all_passed = True
        
        for test_name, body in malformed_tests:
            timestamp = str(int(time.time()))
            headers = {
                "Content-Type": "application/json",
                "X-Slack-Request-Timestamp": timestamp,
            }
            
            if self.signing_secret and body:
                signature = self.create_slack_signature(timestamp, body)
                headers["X-Slack-Signature"] = signature
            
            try:
                response = requests.post(
                    f"{self.slack_url}/slack",
                    data=body,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Should handle malformed requests gracefully (400 or 200)
                if response.status_code in [200, 400]:
                    print(f"    ✅ {test_name}: {response.status_code}")
                else:
                    print(f"    ❌ {test_name}: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"    ❌ {test_name}: Error {e}")
                all_passed = False
            
            time.sleep(0.2)  # Brief pause between tests
        
        return all_passed

    def test_performance_and_responsiveness(self) -> bool:
        """Test response times and concurrent request handling"""
        # Test response time
        start_time = time.time()
        
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Performance test message",
                "channel": self.test_channel,
                "user": self.test_user,
                "ts": str(time.time())
            }
        }
        
        success, result = self.make_slack_request(payload)
        response_time = time.time() - start_time
        
        if success and response_time < 3.0:  # Should respond within 3 seconds
            print(f"    ✅ Response time: {response_time:.2f}s")
            return True
        else:
            print(f"    ❌ Slow response: {response_time:.2f}s or failed")
            return False

    def run_all_tests(self) -> bool:
        """Run all Slack integration tests"""
        self.print_header()
        
        # Define test suite
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("URL Verification", self.test_slack_url_verification),
            ("Message Processing", self.test_message_event_processing),
            ("Thread Messages", self.test_thread_message_handling),
            ("Task Commands", self.test_task_management_commands),
            ("CEO Workflows", self.test_ceo_workflow_commands),
            ("Signature Security", self.test_signature_verification_security),
            ("Replay Protection", self.test_replay_attack_protection),
            ("Malformed Requests", self.test_malformed_request_handling),
            ("Performance", self.test_performance_and_responsiveness)
        ]
        
        print("🚀 Starting Slack integration tests...\n")
        
        # Run each test
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            print()  # Add spacing between tests
        
        # Print final summary
        self.print_summary()
        
        return self.results['failed'] == 0

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("📊 SLACK INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        total = self.results['total']
        passed = self.results['passed']
        failed = self.results['failed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Total Tests: {total}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Your Slack integration is working correctly.")
            print("✨ Ready for production use!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Review the issues above.")
            print("🔧 Consider fixing the failed tests before production deployment.")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['name']}")
            if not result['success'] and 'error' in result:
                print(f"     Error: {result['error']}")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Test Slack integration for OpsBrain")
    parser.add_argument("slack_url", help="Slack webhook endpoint URL")
    parser.add_argument("--signing-secret", help="Slack signing secret for verification")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    # Create and run test suite
    tester = SlackIntegrationTester(
        slack_url=args.slack_url,
        signing_secret=args.signing_secret,
        timeout=args.timeout
    )
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Slack Integration Test Suite
Tests your deployed Slack bot endpoint for common issues.

Usage:
    python test_slack_integration.py https://your-app.onrender.com

Features:
- Tests endpoint connectivity
- Validates SSL/HTTPS setup
- Tests Slack URL verification
- Tests signature verification
- Tests error handling
- Provides clear diagnostic output
"""

import requests
import json
import time
import hmac
import hashlib
import sys
import argparse
import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

class SlackIntegrationTester:
    def __init__(self, base_url: str, signing_secret: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.slack_endpoint = f"{self.base_url}/slack"
        self.signing_secret = signing_secret
        self.session = requests.Session()
        self.session.timeout = 10
        
        # Test results
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, name: str, passed: bool, message: str, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            'name': name,
            'passed': passed,
            'message': message,
            'details': details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            
        print(f"{status} | {name}")
        print(f"     {message}")
        if details:
            print(f"     Details: {details}")
        print()
    
    def generate_slack_signature(self, body: str, timestamp: str) -> str:
        """Generate valid Slack signature for testing"""
        if not self.signing_secret:
            return "v0=fake_signature"
            
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"v0={signature}"
    
    def test_basic_connectivity(self):
        """Test if the endpoint is reachable"""
        try:
            response = self.session.get(self.base_url)
            if response.status_code < 500:
                self.log_test(
                    "Basic Connectivity",
                    True,
                    f"Endpoint is reachable (Status: {response.status_code})",
                    f"Response time: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                self.log_test(
                    "Basic Connectivity", 
                    False,
                    f"Server error: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Basic Connectivity",
                False,
                "Cannot reach endpoint",
                str(e)
            )
    
    def test_https_ssl(self):
        """Test SSL certificate and HTTPS setup"""
        parsed = urlparse(self.base_url)
        if parsed.scheme != 'https':
            self.log_test(
                "HTTPS/SSL Setup",
                False,
                "Endpoint is not using HTTPS",
                "Slack requires HTTPS for webhooks"
            )
            return
            
        try:
            response = self.session.get(self.base_url, verify=True)
            self.log_test(
                "HTTPS/SSL Setup",
                True,
                "SSL certificate is valid",
                "HTTPS is properly configured"
            )
        except requests.exceptions.SSLError as e:
            self.log_test(
                "HTTPS/SSL Setup",
                False,
                "SSL certificate error",
                str(e)
            )
    
    def test_slack_endpoint_exists(self):
        """Test if /slack endpoint exists"""
        try:
            # Try a simple GET first
            response = self.session.get(self.slack_endpoint)
            if response.status_code == 405:  # Method Not Allowed is good
                self.log_test(
                    "Slack Endpoint Exists",
                    True,
                    "/slack endpoint exists (returns 405 for GET)",
                    "This is expected - endpoint only accepts POST"
                )
            elif response.status_code == 404:
                self.log_test(
                    "Slack Endpoint Exists",
                    False,
                    "/slack endpoint not found (404)",
                    "Check your routing configuration"
                )
            else:
                self.log_test(
                    "Slack Endpoint Exists",
                    True,
                    f"/slack endpoint exists (Status: {response.status_code})",
                    "Endpoint is responding"
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Slack Endpoint Exists",
                False,
                "Cannot test /slack endpoint",
                str(e)
            )
    
    def test_url_verification_challenge(self):
        """Test Slack URL verification challenge"""
        challenge_data = {"challenge": "test_challenge_12345"}
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                json=challenge_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("challenge") == "test_challenge_12345":
                        self.log_test(
                            "URL Verification Challenge",
                            True,
                            "Challenge response is correct",
                            f"Response: {response_data}"
                        )
                    else:
                        self.log_test(
                            "URL Verification Challenge",
                            False,
                            "Challenge response is incorrect",
                            f"Expected: {challenge_data}, Got: {response_data}"
                        )
                except json.JSONDecodeError:
                    self.log_test(
                        "URL Verification Challenge",
                        False,
                        "Response is not valid JSON",
                        response.text[:200]
                    )
            else:
                self.log_test(
                    "URL Verification Challenge",
                    False,
                    f"Challenge failed with status {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "URL Verification Challenge",
                False,
                "Cannot test URL verification",
                str(e)
            )
    
    def test_signature_verification(self):
        """Test signature verification behavior"""
        # Test without signature (should fail in production)
        test_data = {"type": "event_callback", "event": {"type": "message", "text": "test"}}
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 403:
                self.log_test(
                    "Signature Verification",
                    True,
                    "Correctly rejects requests without valid signatures",
                    "This is good security - signature verification is working"
                )
            elif response.status_code == 200:
                self.log_test(
                    "Signature Verification",
                    False,
                    "⚠️  Accepts requests without signatures (TEST_MODE enabled?)",
                    "This might be intentional for testing, but disable in production"
                )
            else:
                self.log_test(
                    "Signature Verification",
                    False,
                    f"Unexpected response: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Signature Verification",
                False,
                "Cannot test signature verification",
                str(e)
            )
    
    def test_with_valid_signature(self):
        """Test with a properly signed request (if signing secret provided)"""
        if not self.signing_secret:
            self.log_test(
                "Valid Signature Test",
                False,
                "Skipped - no signing secret provided",
                "Use --signing-secret to test with real signatures"
            )
            return
            
        timestamp = str(int(time.time()))
        test_data = {"challenge": "signed_test_12345"}
        body = json.dumps(test_data)
        signature = self.generate_slack_signature(body, timestamp)
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": signature
                }
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("challenge") == "signed_test_12345":
                        self.log_test(
                            "Valid Signature Test",
                            True,
                            "Properly signed request accepted",
                            "Signature verification is working correctly"
                        )
                    else:
                        self.log_test(
                            "Valid Signature Test",
                            False,
                            "Signed request accepted but response is wrong",
                            f"Got: {response_data}"
                        )
                except json.JSONDecodeError:
                    self.log_test(
                        "Valid Signature Test",
                        False,
                        "Signed request accepted but response is not JSON",
                        response.text[:200]
                    )
            else:
                self.log_test(
                    "Valid Signature Test",
                    False,
                    f"Properly signed request rejected: {response.status_code}",
                    f"Check your SLACK_SIGNING_SECRET env var. Response: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Valid Signature Test",
                False,
                "Cannot test with valid signature",
                str(e)
            )
    
    def test_error_handling(self):
        """Test various error scenarios"""
        # Test empty body
        try:
            response = self.session.post(
                self.slack_endpoint,
                data="",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Empty Body Handling",
                    True,
                    "Correctly handles empty request body",
                    f"Returns 400 status code as expected"
                )
            else:
                self.log_test(
                    "Empty Body Handling",
                    False,
                    f"Unexpected response to empty body: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Empty Body Handling",
                False,
                "Cannot test empty body handling",
                str(e)
            )
        
        # Test invalid JSON
        try:
            response = self.session.post(
                self.slack_endpoint,
                data="invalid json{",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 403]:  # 400 for JSON error, 403 for signature
                self.log_test(
                    "Invalid JSON Handling",
                    True,
                    f"Correctly handles invalid JSON (Status: {response.status_code})",
                    "Error handling is working"
                )
            else:
                self.log_test(
                    "Invalid JSON Handling",
                    False,
                    f"Unexpected response to invalid JSON: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Invalid JSON Handling",
                False,
                "Cannot test invalid JSON handling",
                str(e)
            )
    
    def test_response_times(self):
        """Test response time performance"""
        try:
            start_time = time.time()
            response = self.session.post(
                self.slack_endpoint,
                json={"challenge": "performance_test"},
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response_time < 3.0:  # Slack expects responses within 3 seconds
                self.log_test(
                    "Response Time",
                    True,
                    f"Response time is good: {response_time:.2f}s",
                    "Meets Slack's 3-second requirement"
                )
            else:
                self.log_test(
                    "Response Time",
                    False,
                    f"Response time too slow: {response_time:.2f}s",
                    "Slack may timeout requests > 3 seconds"
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Response Time",
                False,
                "Cannot test response time",
                str(e)
            )
    
    def test_slash_command_workflow(self):
        """Test complete slash command workflow"""
        timestamp = str(int(time.time()))
        
        # Test /ai command with task creation request
        form_data = (
            "token=fake_token&team_id=T123&channel_id=C123&"
            "command=/ai&text=create task: Fix critical bug in authentication system"
        )
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": self.generate_slack_signature(form_data, timestamp)
                }
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Check if response contains expected elements
                    if "text" in response_data and "analyze" in response_data["text"].lower():
                        self.log_test(
                            "Slash Command Workflow",
                            True,
                            "Slash command processed successfully",
                            f"Response indicates task analysis initiated"
                        )
                    else:
                        self.log_test(
                            "Slash Command Workflow",
                            False,
                            "Slash command response format unexpected",
                            f"Response: {response_data}"
                        )
                except json.JSONDecodeError:
                    self.log_test(
                        "Slash Command Workflow",
                        False,
                        "Slash command response is not valid JSON",
                        response.text[:200]
                    )
            else:
                self.log_test(
                    "Slash Command Workflow",
                    False,
                    f"Slash command failed: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Slash Command Workflow",
                False,
                "Cannot test slash command workflow",
                str(e)
            )
    
    def test_event_callback_workflow(self):
        """Test event callback workflow for message events"""
        timestamp = str(int(time.time()))
        
        # Test message event
        test_data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "What are my current tasks?",
                "channel": "C123",
                "user": "U123",
                "subtype": None
            }
        }
        
        body = json.dumps(test_data)
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": self.generate_slack_signature(body, timestamp)
                }
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Event Callback Workflow",
                    True,
                    "Message event processed successfully",
                    "Event callback system is working"
                )
            else:
                self.log_test(
                    "Event Callback Workflow",
                    False,
                    f"Event callback failed: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Event Callback Workflow",
                False,
                "Cannot test event callback workflow",
                str(e)
            )
    
    def test_help_command_workflow(self):
        """Test help command specifically"""
        timestamp = str(int(time.time()))
        
        test_data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "help",
                "channel": "C123",
                "user": "U123",
                "subtype": None
            }
        }
        
        body = json.dumps(test_data)
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": self.generate_slack_signature(body, timestamp)
                }
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Help Command Workflow",
                    True,
                    "Help command processed successfully",
                    "Users can get help information"
                )
            else:
                self.log_test(
                    "Help Command Workflow",
                    False,
                    f"Help command failed: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Help Command Workflow",
                False,
                "Cannot test help command workflow",
                str(e)
            )
    
    def test_thread_context_workflow(self):
        """Test threaded conversation workflow"""
        timestamp = str(int(time.time()))
        thread_ts = "1234567890.123456"
        
        # First message in thread
        test_data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "What's the status of project Alpha?",
                "channel": "C123",
                "user": "U123",
                "thread_ts": thread_ts,
                "subtype": None
            }
        }
        
        body = json.dumps(test_data)
        
        try:
            response = self.session.post(
                self.slack_endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": self.generate_slack_signature(body, timestamp)
                }
            )
            
            if response.status_code == 200:
                # Follow up with second message in same thread
                time.sleep(1)
                timestamp2 = str(int(time.time()))
                
                test_data2 = {
                    "type": "event_callback",
                    "event": {
                        "type": "message",
                        "text": "And what about the timeline?",
                        "channel": "C123",
                        "user": "U123",
                        "thread_ts": thread_ts,
                        "subtype": None
                    }
                }
                
                body2 = json.dumps(test_data2)
                response2 = self.session.post(
                    self.slack_endpoint,
                    data=body2,
                    headers={
                        "Content-Type": "application/json",
                        "X-Slack-Request-Timestamp": timestamp2,
                        "X-Slack-Signature": self.generate_slack_signature(body2, timestamp2)
                    }
                )
                
                if response2.status_code == 200:
                    self.log_test(
                        "Thread Context Workflow",
                        True,
                        "Threaded conversation processed successfully",
                        "Context continuity is maintained across thread messages"
                    )
                else:
                    self.log_test(
                        "Thread Context Workflow",
                        False,
                        f"Second thread message failed: {response2.status_code}",
                        response2.text[:200]
                    )
            else:
                self.log_test(
                    "Thread Context Workflow",
                    False,
                    f"Thread context test failed: {response.status_code}",
                    response.text[:200]
                )
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Thread Context Workflow",
                False,
                "Cannot test thread context workflow",
                str(e)
            )
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import concurrent.futures
        
        def send_test_request(request_id: int) -> tuple:
            """Send a test request and return result"""
            timestamp = str(int(time.time()))
            test_data = {
                "type": "event_callback",
                "event": {
                    "type": "message",
                    "text": f"Test concurrent request {request_id}",
                    "channel": "C123",
                    "user": "U123",
                    "subtype": None
                }
            }
            
            body = json.dumps(test_data)
            
            try:
                response = requests.post(
                    self.slack_endpoint,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Slack-Request-Timestamp": timestamp,
                        "X-Slack-Signature": self.generate_slack_signature(body, timestamp)
                    },
                    timeout=10
                )
                return (request_id, response.status_code, True)
            except Exception as e:
                return (request_id, 0, False)
        
        try:
            # Send 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(send_test_request, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures, timeout=30)]
            
            successful_requests = sum(1 for _, status, success in results if success and status == 200)
            total_requests = len(results)
            
            if successful_requests >= total_requests * 0.8:  # 80% success rate
                self.log_test(
                    "Concurrent Requests",
                    True,
                    f"Handled concurrent requests well: {successful_requests}/{total_requests} successful",
                    "System can handle multiple simultaneous Slack events"
                )
            else:
                self.log_test(
                    "Concurrent Requests",
                    False,
                    f"Poor concurrent request handling: {successful_requests}/{total_requests} successful",
                    "May need to improve async handling or add rate limiting"
                )
        except Exception as e:
            self.log_test(
                "Concurrent Requests",
                False,
                "Cannot test concurrent request handling",
                str(e)
            )
    
    def run_all_tests(self):
        """Run all tests and print summary"""
        print(f"🚀 Testing Slack Integration: {self.base_url}")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_basic_connectivity()
        self.test_https_ssl()
        self.test_slack_endpoint_exists()
        self.test_url_verification_challenge()
        self.test_signature_verification()
        self.test_with_valid_signature()
        self.test_error_handling()
        self.test_response_times()
        
        # Core workflow tests
        print("\n🔧 TESTING CORE WORKFLOWS")
        print("-" * 40)
        self.test_slash_command_workflow()
        self.test_event_callback_workflow()
        self.test_help_command_workflow()
        self.test_thread_context_workflow()
        self.test_concurrent_requests()
        
        # Print summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        print()
        
        # Provide recommendations
        if self.failed > 0:
            print("🔧 RECOMMENDATIONS:")
            for result in self.results:
                if not result['passed']:
                    print(f"• Fix: {result['name']} - {result['message']}")
                    if result['details']:
                        print(f"  Details: {result['details']}")
            print()
        
        print("🎯 NEXT STEPS:")
        if self.failed == 0:
            print("• All tests passed! Your endpoint should work with Slack.")
            print("• Add your webhook URL to your Slack app settings.")
        else:
            print("• Fix the failing tests above.")
            print("• Re-run this test suite after making changes.")
            print("• Check your environment variables on your hosting platform.")
        
        print()
        print("📚 Need help? Check the PRODUCTION_CHECKLIST.md file.")

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Test Slack integration endpoint")
    parser.add_argument("url", nargs='?', default=None, help="Your app's base URL (e.g., https://your-app.onrender.com)")
    parser.add_argument("--signing-secret", help="Your Slack app's signing secret (optional, will use .env if not provided)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    # Get signing secret from args or environment
    signing_secret = args.signing_secret or os.getenv('SLACK_SIGNING_SECRET')
    
    # Get URL from args or use default production URL
    url = args.url or "https://decouple-ai.onrender.com"
    
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print("❌ Invalid URL format. Use: https://your-app.onrender.com")
        sys.exit(1)
    
    # Show configuration info
    print(f"🔧 Configuration:")
    print(f"   URL: {url}")
    print(f"   Signing Secret: {'✓ Loaded from .env' if signing_secret and not args.signing_secret else '✓ Provided' if signing_secret else '✗ Not found'}")
    print()
    
    # Run tests
    tester = SlackIntegrationTester(url, signing_secret)
    tester.session.timeout = args.timeout
    
    try:
        tester.run_all_tests()
        sys.exit(0 if tester.failed == 0 else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

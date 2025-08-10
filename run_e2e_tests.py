#!/usr/bin/env python3
"""
Comprehensive E2E Test Runner
Runs both UI and Slack API tests to ensure core workflows work correctly.
"""

import os
import sys
import argparse
import subprocess
import time
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

class E2ETestRunner:
    """Orchestrates end-to-end testing for the entire application"""
    
    def __init__(self, slack_url: Optional[str] = None, signing_secret: Optional[str] = None):
        self.slack_url = slack_url or "http://localhost:8000"
        self.signing_secret = signing_secret
        self.ui_port = 8501
        self.results = {
            'ui_tests': {'passed': 0, 'failed': 0, 'total': 0},
            'slack_tests': {'passed': 0, 'failed': 0, 'total': 0},
            'integration_tests': {'passed': 0, 'failed': 0, 'total': 0}
        }
        
    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("🚀 CEO OPERATOR E2E TEST SUITE")
        print("=" * 80)
        print(f"Testing UI Dashboard and Slack Integration")
        print(f"Slack URL: {self.slack_url}")
        print(f"UI Port: {self.ui_port}")
        print(f"Signing Secret: {'✓ Provided' if self.signing_secret else '✗ Not provided'}")
        print("=" * 80)
        print()
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            ('streamlit', 'pip install streamlit'),
            ('selenium', 'pip install selenium'),
            ('requests', 'pip install requests'),
            ('webdriver_manager', 'pip install webdriver-manager')
        ]
        
        missing_packages = []
        
        for package, install_cmd in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package} - installed")
            except ImportError:
                print(f"  ❌ {package} - missing")
                missing_packages.append((package, install_cmd))
        
        if missing_packages:
            print("\n❌ Missing required packages:")
            for package, install_cmd in missing_packages:
                print(f"  Install {package}: {install_cmd}")
            return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def run_fastapi_server(self) -> subprocess.Popen:
        """Start the FastAPI server for testing"""
        print("🚀 Starting FastAPI server...")
        
        # Set test environment
        env = os.environ.copy()
        env.update({
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'fake_test_token',
            'SLACK_SIGNING_SECRET': 'fake_test_secret',
            'NOTION_API_KEY': 'fake_test_notion_key',
            'NOTION_DB_ID': 'fake_test_db_id',
            'OPENAI_API_KEY': 'fake_test_openai_key',
        })
        
        try:
            # Start FastAPI with uvicorn
            process = subprocess.Popen([
                'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            import requests
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get("http://localhost:8000", timeout=2)
                    if response.status_code < 500:
                        print("✅ FastAPI server started successfully")
                        return process
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            print("❌ FastAPI server failed to start")
            process.terminate()
            return None
            
        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {e}")
            return None
    
    def run_ui_tests(self) -> bool:
        """Run UI E2E tests"""
        print("\n📱 RUNNING UI E2E TESTS")
        print("-" * 50)
        
        try:
            cmd = [
                'python', 'test_e2e_ui.py',
                '--port', str(self.ui_port),
                '--timeout', '60'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Parse results from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Passed:' in line and 'Failed:' in line:
                    # Extract numbers from "✅ Passed: X" and "❌ Failed: Y" format
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'Passed:' and i + 1 < len(parts):
                            self.results['ui_tests']['passed'] = int(parts[i + 1])
                        elif part == 'Failed:' and i + 1 < len(parts):
                            self.results['ui_tests']['failed'] = int(parts[i + 1])
            
            self.results['ui_tests']['total'] = (
                self.results['ui_tests']['passed'] + 
                self.results['ui_tests']['failed']
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ UI tests timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ UI tests failed with exception: {e}")
            return False
    
    def run_slack_tests(self) -> bool:
        """Run Slack integration tests"""
        print("\n💬 RUNNING SLACK INTEGRATION TESTS")
        print("-" * 50)
        
        try:
            cmd = [
                'python', 'test_slack_integration.py',
                self.slack_url,
                '--timeout', '30'
            ]
            
            if self.signing_secret:
                cmd.extend(['--signing-secret', self.signing_secret])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Parse results from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Passed:' in line and 'Failed:' in line:
                    # Extract numbers from "✅ Passed: X" and "❌ Failed: Y" format
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'Passed:' and i + 1 < len(parts):
                            self.results['slack_tests']['passed'] = int(parts[i + 1])
                        elif part == 'Failed:' and i + 1 < len(parts):
                            self.results['slack_tests']['failed'] = int(parts[i + 1])
            
            self.results['slack_tests']['total'] = (
                self.results['slack_tests']['passed'] + 
                self.results['slack_tests']['failed']
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Slack tests timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Slack tests failed with exception: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run existing pytest integration tests"""
        print("\n🔧 RUNNING INTEGRATION TESTS")
        print("-" * 50)
        
        try:
            # Set test environment
            env = os.environ.copy()
            env.update({
                'TEST_MODE': 'true',
                'SLACK_BOT_TOKEN': 'fake_test_token',
                'SLACK_SIGNING_SECRET': 'fake_test_secret',
                'NOTION_API_KEY': 'fake_test_notion_key',
                'NOTION_DB_ID': 'fake_test_db_id',
                'OPENAI_API_KEY': 'fake_test_openai_key',
            })
            
            cmd = [
                'python', '-m', 'pytest',
                'tests/integration/',
                '-v',
                '--tb=short'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Parse pytest results
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'passed' in line and 'failed' in line:
                    # Look for pytest summary like "2 passed, 1 failed"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed,' and i > 0:
                            try:
                                self.results['integration_tests']['passed'] = int(parts[i - 1])
                            except (ValueError, IndexError):
                                pass
                        elif part == 'failed' and i > 0:
                            try:
                                self.results['integration_tests']['failed'] = int(parts[i - 1])
                            except (ValueError, IndexError):
                                pass
                elif 'passed' in line and 'failed' not in line:
                    # Look for "X passed" format
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed' and i > 0:
                            try:
                                self.results['integration_tests']['passed'] = int(parts[i - 1])
                                self.results['integration_tests']['failed'] = 0
                            except (ValueError, IndexError):
                                pass
            
            self.results['integration_tests']['total'] = (
                self.results['integration_tests']['passed'] + 
                self.results['integration_tests']['failed']
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Integration tests timed out after 3 minutes")
            return False
        except Exception as e:
            print(f"❌ Integration tests failed with exception: {e}")
            return False
    
    def print_final_summary(self, ui_success: bool, slack_success: bool, integration_success: bool):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 80)
        
        # Individual test suite results
        test_suites = [
            ("UI Tests", ui_success, self.results['ui_tests']),
            ("Slack Tests", slack_success, self.results['slack_tests']),
            ("Integration Tests", integration_success, self.results['integration_tests'])
        ]
        
        total_passed = 0
        total_failed = 0
        total_tests = 0
        all_success = True
        
        for suite_name, success, results in test_suites:
            passed = results['passed']
            failed = results['failed']
            total = results['total']
            
            status = "✅ PASS" if success else "❌ FAIL"
            success_rate = (passed / total * 100) if total > 0 else 0
            
            print(f"{status} | {suite_name:20} | {passed:3}/{total:3} passed ({success_rate:5.1f}%)")
            
            total_passed += passed
            total_failed += failed
            total_tests += total
            
            if not success:
                all_success = False
        
        print("-" * 80)
        
        # Overall summary
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅ PASS" if all_success else "❌ FAIL"
        
        print(f"{overall_status} | {'OVERALL':20} | {total_passed:3}/{total_tests:3} passed ({overall_success_rate:5.1f}%)")
        print()
        
        # Recommendations
        if not all_success:
            print("🔧 RECOMMENDATIONS:")
            if not ui_success:
                print("• Fix UI dashboard issues - check Streamlit dependencies and browser compatibility")
            if not slack_success:
                print("• Fix Slack integration issues - check endpoint connectivity and signatures")
            if not integration_success:
                print("• Fix integration test failures - check business logic and mock data")
            print()
        
        # Next steps
        print("🎯 NEXT STEPS:")
        if all_success:
            print("• All E2E tests passed! ✨")
            print("• Your application is ready for production deployment")
            print("• Consider setting up automated CI/CD testing")
        else:
            print("• Address the failing tests above")
            print("• Re-run tests after fixes: python run_e2e_tests.py")
            print("• Check logs for detailed error information")
        
        print()
        
        return all_success
    
    def run_all_tests(self) -> bool:
        """Run the complete E2E test suite"""
        self.print_header()
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Start FastAPI server for testing
        fastapi_process = self.run_fastapi_server()
        if not fastapi_process:
            return False
        
        try:
            # Run all test suites
            ui_success = self.run_ui_tests()
            slack_success = self.run_slack_tests()
            integration_success = self.run_integration_tests()
            
            # Print final summary
            overall_success = self.print_final_summary(ui_success, slack_success, integration_success)
            
            return overall_success
            
        finally:
            # Clean up FastAPI process
            if fastapi_process:
                print("🛑 Stopping FastAPI server...")
                fastapi_process.terminate()
                try:
                    fastapi_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    fastapi_process.kill()

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run comprehensive E2E tests for CEO Operator")
    parser.add_argument(
        "--slack-url", 
        default=None,
        help="Slack endpoint URL to test (default: auto-detect from production)"
    )
    parser.add_argument(
        "--signing-secret",
        help="Slack signing secret for signature verification tests (will use .env if not provided)"
    )
    parser.add_argument(
        "--ui-port",
        type=int,
        default=8501,
        help="Port for Streamlit UI testing (default: 8501)"
    )
    
    args = parser.parse_args()
    
    # Get signing secret from args or environment
    signing_secret = args.signing_secret or os.getenv('SLACK_SIGNING_SECRET')
    
    # Get URL from args or use default production URL
    slack_url = args.slack_url or "https://decouple-ai.onrender.com"
    
    # Create and run test suite
    runner = E2ETestRunner(
        slack_url=slack_url,
        signing_secret=signing_secret
    )
    runner.ui_port = args.ui_port
    
    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error in test runner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

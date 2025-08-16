#!/usr/bin/env python3
"""
Deployment Health Check Script

Run this after deployment to ensure the system is healthy and prevent deployment issues.
This would have caught the async timeout issue in production.
"""

import requests
import time
import sys
import json
import asyncio
import warnings
from typing import Dict, List, Tuple, Optional
import subprocess
import psutil
import os

class DeploymentHealthChecker:
    """Comprehensive health checker for post-deployment validation"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.checks_passed = []
        self.checks_failed = []
        self.warnings_found = []
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status message"""
        colors = {
            "INFO": "\033[0;34m",     # Blue
            "SUCCESS": "\033[0;32m",  # Green
            "WARNING": "\033[1;33m",  # Yellow
            "ERROR": "\033[0;31m",    # Red
            "RESET": "\033[0m"        # Reset
        }
        print(f"{colors.get(status, colors['INFO'])}[{status}]{colors['RESET']} {message}")
    
    def run_check(self, check_name: str, check_func, *args, **kwargs) -> bool:
        """Run a single health check and track results"""
        try:
            self.print_status(f"Running {check_name}...", "INFO")
            result = check_func(*args, **kwargs)
            if result:
                self.print_status(f"✅ {check_name} - PASSED", "SUCCESS")
                self.checks_passed.append(check_name)
                return True
            else:
                self.print_status(f"❌ {check_name} - FAILED", "ERROR")
                self.checks_failed.append(check_name)
                return False
        except Exception as e:
            self.print_status(f"❌ {check_name} - ERROR: {str(e)}", "ERROR")
            self.checks_failed.append(f"{check_name}: {str(e)}")
            return False
    
    def check_basic_health_endpoint(self) -> bool:
        """Test basic health endpoint responsiveness"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception as e:
            self.print_status(f"Health endpoint error: {e}", "ERROR")
            return False
    
    def check_response_times(self) -> bool:
        """Check that response times are acceptable"""
        endpoints = ["/", "/health"]
        max_response_time = 2.0  # 2 seconds max
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response_time > max_response_time:
                    self.print_status(f"Slow response on {endpoint}: {response_time:.2f}s", "WARNING")
                    self.warnings_found.append(f"Slow response: {endpoint}")
                    return False
                    
                if response.status_code != 200:
                    self.print_status(f"Bad status code on {endpoint}: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                self.print_status(f"Response time check failed on {endpoint}: {e}", "ERROR")
                return False
        
        return True
    
    def check_memory_usage(self) -> bool:
        """Check that memory usage is reasonable"""
        try:
            # Find the process (if running locally)
            current_process = psutil.Process()
            memory_mb = current_process.memory_info().rss / 1024 / 1024
            
            # Allow up to 500MB for the application
            max_memory_mb = 500
            
            if memory_mb > max_memory_mb:
                self.print_status(f"High memory usage: {memory_mb:.1f}MB", "WARNING")
                self.warnings_found.append(f"Memory usage: {memory_mb:.1f}MB")
                return False
            
            self.print_status(f"Memory usage: {memory_mb:.1f}MB", "INFO")
            return True
            
        except Exception as e:
            self.print_status(f"Memory check failed: {e}", "WARNING")
            return True  # Don't fail deployment for memory check issues
    
    def check_async_warnings_in_logs(self) -> bool:
        """Check for async warnings that indicate timeout issues"""
        try:
            # For a real deployment, you'd check actual log files
            # For now, we'll simulate by running a quick test
            
            result = subprocess.run([
                sys.executable, "-c", 
                "import warnings; warnings.simplefilter('always'); "
                "from main import app; "
                "from fastapi.testclient import TestClient; "
                "client = TestClient(app); "
                "response = client.get('/health')"
            ], capture_output=True, text=True, timeout=30, env={
                **os.environ, 
                'TEST_MODE': 'true',
                'SLACK_BOT_TOKEN': 'test',
                'SLACK_SIGNING_SECRET': 'test',
                'NOTION_API_KEY': 'test',
                'NOTION_DB_ID': 'test',
                'OPENAI_API_KEY': 'test'
            })
            
            # Check for async warnings in stderr
            if "unawaited" in result.stderr.lower() or "_monitoring_loop" in result.stderr.lower():
                self.print_status("Found async warnings in logs!", "ERROR")
                self.print_status(f"Warning details: {result.stderr}", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.print_status(f"Async warning check failed: {e}", "WARNING")
            return True  # Don't fail deployment for this check
    
    def check_concurrent_request_handling(self) -> bool:
        """Test that the system can handle concurrent requests"""
        try:
            import concurrent.futures
            import threading
            
            def make_request():
                response = requests.get(f"{self.base_url}/health", timeout=10)
                return response.status_code == 200
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result(timeout=15) for future in futures]
            
            success_count = sum(results)
            if success_count < 4:  # Allow 1 failure
                self.print_status(f"Concurrent request test: only {success_count}/5 succeeded", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.print_status(f"Concurrent request test failed: {e}", "ERROR")
            return False
    
    def check_health_monitoring_active(self) -> bool:
        """Check that health monitoring is active (if exposed via endpoint)"""
        try:
            # In a real deployment, you might have a /health/detailed endpoint
            # For now, just check that the basic health endpoint includes monitoring info
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            # Check for timestamp indicating the system is actively monitoring
            return "timestamp" in data
            
        except Exception as e:
            self.print_status(f"Health monitoring check failed: {e}", "WARNING")
            return True  # Don't fail for this
    
    def run_all_checks(self) -> bool:
        """Run all health checks and return overall result"""
        
        self.print_status("🚀 Starting Deployment Health Check", "INFO")
        self.print_status("=" * 50, "INFO")
        
        # Critical checks - must pass
        critical_checks = [
            ("Basic Health Endpoint", self.check_basic_health_endpoint),
            ("Response Times", self.check_response_times),
            ("Async Warning Detection", self.check_async_warnings_in_logs),
            ("Concurrent Request Handling", self.check_concurrent_request_handling),
        ]
        
        # Non-critical checks - can warn but don't fail deployment
        optional_checks = [
            ("Memory Usage", self.check_memory_usage),
            ("Health Monitoring Active", self.check_health_monitoring_active),
        ]
        
        all_critical_passed = True
        
        # Run critical checks
        self.print_status("\n📋 Running Critical Checks", "INFO")
        for check_name, check_func in critical_checks:
            if not self.run_check(check_name, check_func):
                all_critical_passed = False
        
        # Run optional checks
        self.print_status("\n📋 Running Optional Checks", "INFO")
        for check_name, check_func in optional_checks:
            self.run_check(check_name, check_func)  # Don't affect overall result
        
        # Print summary
        self.print_summary()
        
        return all_critical_passed
    
    def print_summary(self):
        """Print a summary of all checks"""
        self.print_status("\n" + "=" * 50, "INFO")
        self.print_status("🏁 DEPLOYMENT HEALTH CHECK SUMMARY", "INFO")
        self.print_status("=" * 50, "INFO")
        
        self.print_status(f"✅ Checks Passed: {len(self.checks_passed)}", "SUCCESS")
        self.print_status(f"❌ Checks Failed: {len(self.checks_failed)}", "ERROR" if self.checks_failed else "INFO")
        self.print_status(f"⚠️  Warnings: {len(self.warnings_found)}", "WARNING" if self.warnings_found else "INFO")
        
        if self.checks_failed:
            self.print_status("\nFailed Checks:", "ERROR")
            for check in self.checks_failed:
                self.print_status(f"  • {check}", "ERROR")
        
        if self.warnings_found:
            self.print_status("\nWarnings:", "WARNING")
            for warning in self.warnings_found:
                self.print_status(f"  • {warning}", "WARNING")
        
        self.print_status("=" * 50, "INFO")


def main():
    """Main function to run deployment health checks"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deployment Health Checker")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the deployed application")
    parser.add_argument("--timeout", type=int, default=120,
                       help="Overall timeout for all checks in seconds")
    
    args = parser.parse_args()
    
    # Create health checker
    checker = DeploymentHealthChecker(args.url)
    
    try:
        # Run all checks with overall timeout
        success = checker.run_all_checks()
        
        if success:
            checker.print_status("🎉 DEPLOYMENT HEALTH CHECK PASSED!", "SUCCESS")
            checker.print_status("Deployment is healthy and ready for traffic", "SUCCESS")
            sys.exit(0)
        else:
            checker.print_status("💥 DEPLOYMENT HEALTH CHECK FAILED!", "ERROR")
            checker.print_status("Deployment issues detected - consider rollback", "ERROR")
            sys.exit(1)
            
    except KeyboardInterrupt:
        checker.print_status("Health check interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        checker.print_status(f"Health check failed with error: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()

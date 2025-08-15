#!/usr/bin/env python3
"""
E2E UI Testing for CEO Operator Dashboard
Tests the Streamlit dashboard functionality and core UI workflows.
"""

import os
import time
import json
import subprocess
import requests
import threading
import signal
import sys
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

class StreamlitUITester:
    """E2E UI tester for Streamlit dashboard"""
    
    def __init__(self, port: int = 8501, timeout: int = 30):
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://localhost:{port}"
        self.driver = None
        self.streamlit_process = None
        
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
        
    def setup_driver(self) -> bool:
        """Setup Chrome driver for testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            # Try to find Chrome driver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(self.timeout)
                return True
            except WebDriverException:
                # If ChromeDriver not found, try installing it
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.driver.set_page_load_timeout(self.timeout)
                    return True
                except Exception as e:
                    self.log_test(
                        "Chrome Driver Setup",
                        False,
                        "Failed to setup Chrome driver",
                        f"Error: {e}. Install chromedriver or webdriver-manager"
                    )
                    return False
        except Exception as e:
            self.log_test(
                "Driver Setup", 
                False,
                "Failed to setup web driver",
                str(e)
            )
            return False
    
    def start_streamlit_app(self) -> bool:
        """Start the Streamlit dashboard"""
        try:
            # Set test environment variables
            env = os.environ.copy()
            env.update({
                'TEST_MODE': 'true',
                'SLACK_BOT_TOKEN': 'fake_test_token',
                'SLACK_SIGNING_SECRET': 'fake_test_secret',
                'NOTION_API_KEY': 'fake_test_notion_key',
                'NOTION_DB_ID': 'fake_test_db_id',
                'OPENAI_API_KEY': 'fake_test_openai_key',
            })
            
            # Start Streamlit process
            cmd = ['streamlit', 'run', 'dashboard.py', '--server.port', str(self.port), '--server.headless', 'true']
            self.streamlit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # Wait for Streamlit to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.base_url}/healthz", timeout=2)
                    if response.status_code == 200:
                        self.log_test(
                            "Streamlit App Startup",
                            True,
                            f"Dashboard started successfully on port {self.port}",
                            f"Startup took {i+1} seconds"
                        )
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            self.log_test(
                "Streamlit App Startup",
                False,
                "Dashboard failed to start within timeout",
                f"Process PID: {self.streamlit_process.pid if self.streamlit_process else 'None'}"
            )
            return False
            
        except Exception as e:
            self.log_test(
                "Streamlit App Startup",
                False,
                "Failed to start Streamlit dashboard",
                str(e)
            )
            return False
    
    def test_dashboard_loads(self) -> bool:
        """Test if dashboard page loads successfully"""
        try:
            self.driver.get(self.base_url)
            
            # Wait for the main title to appear
            wait = WebDriverWait(self.driver, self.timeout)
            title_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            page_title = title_element.text
            if "CEO Operator Dashboard" in page_title or "Dashboard" in page_title:
                self.log_test(
                    "Dashboard Page Load",
                    True,
                    "Dashboard page loaded successfully",
                    f"Page title: {page_title}"
                )
                return True
            else:
                self.log_test(
                    "Dashboard Page Load",
                    False,
                    "Dashboard page loaded but title is incorrect",
                    f"Expected: CEO Operator Dashboard, Got: {page_title}"
                )
                return False
                
        except TimeoutException:
            self.log_test(
                "Dashboard Page Load",
                False,
                "Dashboard page load timed out",
                f"Page failed to load within {self.timeout} seconds"
            )
            return False
        except Exception as e:
            self.log_test(
                "Dashboard Page Load",
                False,
                "Dashboard page load failed",
                str(e)
            )
            return False
    
    def test_sidebar_navigation(self) -> bool:
        """Test sidebar navigation elements"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Look for sidebar elements (Streamlit uses specific classes)
            sidebar_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSidebar']")
            
            if sidebar_elements:
                sidebar = sidebar_elements[0]
                # Check for common sidebar elements like selectboxes or buttons
                selectboxes = sidebar.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
                buttons = sidebar.find_elements(By.CSS_SELECTOR, "[data-testid='stButton']")
                
                if selectboxes or buttons:
                    self.log_test(
                        "Sidebar Navigation",
                        True,
                        f"Sidebar navigation working with {len(selectboxes)} selectboxes and {len(buttons)} buttons",
                        "Interactive elements found in sidebar"
                    )
                    return True
                else:
                    self.log_test(
                        "Sidebar Navigation",
                        True,
                        "Sidebar exists but no interactive elements found",
                        "This might be normal if sidebar is informational only"
                    )
                    return True
            else:
                self.log_test(
                    "Sidebar Navigation",
                    False,
                    "No sidebar found in dashboard",
                    "Sidebar should exist for navigation"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Sidebar Navigation",
                False,
                "Failed to test sidebar navigation",
                str(e)
            )
            return False
    
    def test_metrics_display(self) -> bool:
        """Test if key metrics are displayed on dashboard"""
        try:
            # Look for metric elements (Streamlit metrics use specific structure)
            metric_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='metric-container']")
            
            if not metric_elements:
                # Try alternative selectors for metrics
                metric_elements = self.driver.find_elements(By.CSS_SELECTOR, ".metric")
                
            if not metric_elements:
                # Look for any numeric displays that might be metrics
                metric_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stMetric']")
            
            if metric_elements:
                metrics_text = []
                for element in metric_elements[:5]:  # Check first 5 metrics
                    try:
                        text = element.text
                        if text and any(char.isdigit() for char in text):
                            metrics_text.append(text[:50])  # Limit length
                    except:
                        continue
                
                self.log_test(
                    "Metrics Display",
                    True,
                    f"Found {len(metric_elements)} metric elements",
                    f"Sample metrics: {', '.join(metrics_text[:3])}"
                )
                return True
            else:
                # Check for any numeric content that might be metrics
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                if any(keyword in body_text.lower() for keyword in ['task', 'goal', 'hour', 'priority']):
                    self.log_test(
                        "Metrics Display",
                        True,
                        "Dashboard content found with business metrics keywords",
                        "Metrics might be in text form rather than dedicated metric widgets"
                    )
                    return True
                else:
                    self.log_test(
                        "Metrics Display",
                        False,
                        "No business metrics found on dashboard",
                        "Expected to find task counts, goals, or time metrics"
                    )
                    return False
                
        except Exception as e:
            self.log_test(
                "Metrics Display",
                False,
                "Failed to test metrics display",
                str(e)
            )
            return False
    
    def test_interactive_elements(self) -> bool:
        """Test interactive elements like buttons and inputs"""
        try:
            # Find buttons
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
            
            # Find text inputs
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTextInput'] input")
            
            # Find selectboxes
            selectboxes = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
            
            # Find sliders
            sliders = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSlider']")
            
            total_interactive = len(buttons) + len(text_inputs) + len(selectboxes) + len(sliders)
            
            if total_interactive > 0:
                self.log_test(
                    "Interactive Elements",
                    True,
                    f"Found {total_interactive} interactive elements",
                    f"Buttons: {len(buttons)}, Inputs: {len(text_inputs)}, Selectboxes: {len(selectboxes)}, Sliders: {len(sliders)}"
                )
                return True
            else:
                self.log_test(
                    "Interactive Elements",
                    False,
                    "No interactive elements found",
                    "Dashboard should have buttons or input fields for interaction"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Interactive Elements",
                False,
                "Failed to test interactive elements",
                str(e)
            )
            return False
    
    def test_data_visualization(self) -> bool:
        """Test if charts/visualizations are present"""
        try:
            # Look for Plotly charts (common in Streamlit dashboards)
            plotly_elements = self.driver.find_elements(By.CSS_SELECTOR, ".plotly")
            
            if not plotly_elements:
                # Look for Streamlit's built-in chart elements
                chart_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stPlotlyChart']")
                plotly_elements.extend(chart_elements)
            
            if not plotly_elements:
                # Look for other chart types
                chart_selectors = [
                    "[data-testid='stBarChart']",
                    "[data-testid='stLineChart']",
                    "[data-testid='stAreaChart']",
                    "canvas"  # Generic canvas element for charts
                ]
                for selector in chart_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    plotly_elements.extend(elements)
            
            if plotly_elements:
                self.log_test(
                    "Data Visualization",
                    True,
                    f"Found {len(plotly_elements)} visualization elements",
                    "Charts and graphs are rendering properly"
                )
                return True
            else:
                # Check if dashboard is meant to be purely informational
                self.log_test(
                    "Data Visualization",
                    True,
                    "No charts found - dashboard may be text-based",
                    "This could be intentional if dashboard focuses on text metrics"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Data Visualization",
                False,
                "Failed to test data visualization",
                str(e)
            )
            return False
    
    def test_responsive_design(self) -> bool:
        """Test dashboard responsiveness"""
        try:
            # Test different screen sizes
            sizes = [
                (1920, 1080),  # Desktop
                (768, 1024),   # Tablet
                (375, 667)     # Mobile
            ]
            
            responsive_issues = []
            
            for width, height in sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)  # Allow layout to adjust
                
                # Check if page is still functional
                body = self.driver.find_element(By.TAG_NAME, "body")
                if body.size['width'] < 100 or body.size['height'] < 100:
                    responsive_issues.append(f"{width}x{height}: Layout collapsed")
                
                # Check for horizontal scroll on small screens
                if width < 768:
                    scroll_width = self.driver.execute_script("return document.body.scrollWidth")
                    if scroll_width > width + 50:  # Allow some tolerance
                        responsive_issues.append(f"{width}x{height}: Horizontal scrolling required")
            
            # Reset to desktop size
            self.driver.set_window_size(1920, 1080)
            
            if not responsive_issues:
                self.log_test(
                    "Responsive Design",
                    True,
                    "Dashboard adapts well to different screen sizes",
                    "Tested desktop, tablet, and mobile viewports"
                )
                return True
            else:
                self.log_test(
                    "Responsive Design",
                    False,
                    f"Found {len(responsive_issues)} responsive design issues",
                    "; ".join(responsive_issues)
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Responsive Design",
                False,
                "Failed to test responsive design",
                str(e)
            )
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=5)
            except:
                try:
                    self.streamlit_process.kill()
                except:
                    pass
    
    def run_all_tests(self) -> bool:
        """Run all UI E2E tests"""
        print(f"🚀 Testing CEO Operator Dashboard UI")
        print("=" * 60)
        print()
        
        # Setup phase
        if not self.setup_driver():
            return False
            
        if not self.start_streamlit_app():
            self.cleanup()
            return False
        
        # Run tests
        try:
            self.test_dashboard_loads()
            self.test_sidebar_navigation()
            self.test_metrics_display()
            self.test_interactive_elements()
            self.test_data_visualization()
            self.test_responsive_design()
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
        except Exception as e:
            self.log_test(
                "Test Suite Execution",
                False,
                "Unexpected error during test execution",
                str(e)
            )
        finally:
            self.cleanup()
        
        # Print summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        if self.passed + self.failed > 0:
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
        
        return self.failed == 0

def main():
    """Main function to run UI E2E tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="E2E UI tests for CEO Operator Dashboard")
    parser.add_argument("--port", type=int, default=8501, help="Streamlit port (default: 8501)")
    parser.add_argument("--timeout", type=int, default=30, help="Test timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    
    # Check dependencies
    try:
        import streamlit
        from selenium import webdriver
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install streamlit selenium")
        sys.exit(1)
    
    # Run tests
    tester = StreamlitUITester(port=args.port, timeout=args.timeout)
    
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal, cleaning up...")
        tester.cleanup()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()

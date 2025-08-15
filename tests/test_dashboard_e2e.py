#!/usr/bin/env python3
"""
End-to-End Tests for OpsBrain Dashboard
Tests all dashboard functionality including UI interactions, API endpoints, and workflows
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the main app and dashboard components
# Add parent directory to sys.path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from src.web_dashboard import (
    get_dashboard_metrics, get_task_summary, get_comprehensive_analytics,
    integrate_dashboard_with_main_app
)
from src.config_manager import config_manager
from src.database import db_manager

class TestDashboardE2E:
    """End-to-end tests for dashboard functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
        # Ensure dashboard is integrated
        integrate_dashboard_with_main_app(app)
    
    def test_dashboard_homepage_renders(self):
        """Test that dashboard homepage renders successfully."""
        response = self.client.get("/dashboard/")
        
        assert response.status_code == 200
        assert "CEO Operator Dashboard" in response.text
        assert "Total Active Tasks" in response.text
        assert "High Priority Tasks" in response.text
        assert "Weekly Hours" in response.text
        assert "Revenue Pipeline" in response.text
    
    def test_dashboard_metrics_api(self):
        """Test dashboard metrics API endpoint."""
        response = self.client.get("/dashboard/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        required_fields = [
            "total_tasks", "high_priority_tasks", "completed_this_week",
            "revenue_pipeline", "weekly_hours_available", "tasks_per_hour"
        ]
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))
    
    def test_dashboard_tasks_api(self):
        """Test dashboard tasks API endpoint."""
        response = self.client.get("/dashboard/api/tasks")
        
        assert response.status_code == 200
        tasks = response.json()
        
        assert isinstance(tasks, list)
        if tasks:
            task = tasks[0]
            required_fields = ["id", "title", "priority", "status", "area", "impact"]
            for field in required_fields:
                assert field in task
    
    def test_dashboard_goals_api(self):
        """Test dashboard goals API endpoint."""
        response = self.client.get("/dashboard/api/goals")
        
        assert response.status_code == 200
        goals = response.json()
        assert isinstance(goals, list)
    
    def test_dashboard_analytics_api(self):
        """Test dashboard analytics API endpoint."""
        response = self.client.get("/dashboard/api/analytics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "overview" in data
        assert "priority_breakdown" in data
        assert "status_breakdown" in data
        assert "impact_analysis" in data
        assert "area_breakdown" in data
        
        # Verify overview structure
        overview = data["overview"]
        assert "total_tasks" in overview
        assert "completion_rate" in overview
        
        # Verify breakdown structures
        for breakdown in ["priority_breakdown", "status_breakdown", "impact_analysis"]:
            assert isinstance(data[breakdown], dict)
    
    @patch('main.load_business_brain')
    @patch('main.generate_ceo_weekly_plan')
    def test_weekly_plan_generation(self, mock_generate, mock_load_brain):
        """Test weekly plan generation functionality."""
        # Mock the business brain loading to return valid data
        mock_load_brain.return_value = {
            "vision": "Test vision",
            "current_priorities": ["Priority 1", "Priority 2"]
        }
        mock_generate.return_value = "Test weekly plan content"
        
        response = self.client.post("/dashboard/api/generate/weekly-plan")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return success true with mocked business brain
        assert data["success"] is True
        assert "plan" in data
        assert data["plan"] == "Test weekly plan content"
        assert "generated_at" in data
    
    @patch('main.generate_midweek_nudge')
    def test_midweek_nudge_generation(self, mock_generate):
        """Test midweek nudge generation functionality."""
        mock_generate.return_value = "Test midweek nudge content"
        
        response = self.client.post("/dashboard/api/generate/midweek-nudge")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "nudge" in data
        assert data["nudge"] == "Test midweek nudge content"
        assert "generated_at" in data
    
    @patch('main.generate_friday_retro')
    def test_friday_retro_generation(self, mock_generate):
        """Test Friday retrospective generation functionality."""
        mock_generate.return_value = "Test Friday retrospective content"
        
        response = self.client.post("/dashboard/api/generate/friday-retro")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "retrospective" in data
        assert data["retrospective"] == "Test Friday retrospective content"
        assert "generated_at" in data
    
    def test_dashboard_settings_page(self):
        """Test dashboard settings page renders."""
        response = self.client.get("/dashboard/settings")
        
        assert response.status_code == 200
        assert "Dashboard Settings" in response.text
        assert "Configuration Statistics" in response.text
    
    def test_dashboard_docs_page(self):
        """Test dashboard documentation page renders."""
        response = self.client.get("/dashboard/docs")
        
        assert response.status_code == 200
        assert "OpsBrain Documentation" in response.text
        assert "Getting Started" in response.text
        assert "Dashboard Guide" in response.text
        assert "Slack Integration" in response.text
        assert "Configuration" in response.text
        assert "API Reference" in response.text
    
    def test_dashboard_health_check(self):
        """Test dashboard health check endpoint."""
        response = self.client.get("/dashboard/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "config" in data
    
    def test_config_export_endpoint(self):
        """Test configuration export functionality."""
        response = self.client.get("/dashboard/api/config/export")
        
        assert response.status_code == 200
        configs = response.json()
        assert isinstance(configs, dict)
    
    def test_config_update_endpoint(self):
        """Test configuration update functionality."""
        update_data = {
            "key": "test_config",
            "value": "test_value",
            "category": "test",
            "description": "Test configuration"
        }
        
        response = self.client.post(
            "/dashboard/api/config/update",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
    
    def test_config_import_endpoint(self):
        """Test configuration import functionality."""
        import_data = {
            "test_category": {
                "test_key": "test_value"
            }
        }
        
        response = self.client.post(
            "/dashboard/api/config/import",
            json=import_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "imported_count" in data

class TestDashboardNavigation:
    """Test dashboard navigation and user workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_navigation_links_accessibility(self):
        """Test that all navigation links are accessible."""
        # Test main dashboard
        response = self.client.get("/dashboard/")
        assert response.status_code == 200
        
        # Test settings page
        response = self.client.get("/dashboard/settings")
        assert response.status_code == 200
        
        # Test docs page
        response = self.client.get("/dashboard/docs")
        assert response.status_code == 200
        
        # Test health endpoint
        response = self.client.get("/dashboard/health")
        assert response.status_code == 200
    
    def test_dashboard_ui_components_present(self):
        """Test that all UI components are present in the dashboard."""
        response = self.client.get("/dashboard/")
        html_content = response.text
        
        # Check for metric cards
        assert "Total Active Tasks" in html_content
        assert "High Priority Tasks" in html_content
        assert "Weekly Hours" in html_content
        assert "Revenue Pipeline" in html_content
        
        # Check for action buttons
        assert "Generate Weekly Plan" in html_content
        assert "Midweek Check-in" in html_content
        assert "Friday Retrospective" in html_content
        assert "View Analytics" in html_content
        
        # Check for JavaScript functions
        assert "generateWeeklyPlan()" in html_content
        assert "generateMidweekNudge()" in html_content
        assert "generateFridayRetro()" in html_content
        assert "showTaskAnalytics()" in html_content
        
        # Check for loading and modal functions
        assert "showLoading" in html_content
        assert "hideLoading" in html_content
        assert "showModal" in html_content
        assert "closeModal" in html_content

class TestDashboardDataIntegrity:
    """Test data integrity and error handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_metrics_data_consistency(self):
        """Test that metrics data is consistent."""
        # Get metrics multiple times and ensure consistency
        response1 = self.client.get("/dashboard/api/metrics")
        response2 = self.client.get("/dashboard/api/metrics")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Verify consistent data structure
        assert data1.keys() == data2.keys()
    
    def test_task_data_structure(self):
        """Test task data structure consistency."""
        response = self.client.get("/dashboard/api/tasks")
        assert response.status_code == 200
        
        tasks = response.json()
        for task in tasks:
            # Verify required fields
            assert "id" in task
            assert "title" in task
            assert "priority" in task
            assert "status" in task
            assert "area" in task
            assert "impact" in task
            
            # Verify data types
            assert isinstance(task["id"], str)
            assert isinstance(task["title"], str)
            assert task["priority"] in ["High", "Medium", "Low"]
            assert task["impact"] in ["High", "Medium", "Low", "Unknown"]
    
    @patch('src.web_dashboard.logger')
    def test_error_handling_on_api_failures(self, mock_logger):
        """Test proper error handling when APIs fail."""
        # Test what happens when database is unavailable
        with patch('src.database.db_manager.get_business_goals', side_effect=Exception("Database error")):
            response = self.client.get("/dashboard/api/goals")
            assert response.status_code == 200
            assert response.json() == []  # Should return empty list on error
    
    def test_analytics_calculation_accuracy(self):
        """Test analytics calculations are accurate."""
        # Get both tasks and analytics
        tasks_response = self.client.get("/dashboard/api/tasks")
        analytics_response = self.client.get("/dashboard/api/analytics")
        
        assert tasks_response.status_code == 200
        assert analytics_response.status_code == 200
        
        tasks = tasks_response.json()
        analytics = analytics_response.json()
        
        # Verify analytics match task data
        total_tasks = len(tasks)
        high_priority_count = len([t for t in tasks if t["priority"] == "High"])
        
        assert analytics["overview"]["total_tasks"] == total_tasks
        assert analytics["priority_breakdown"]["high"] == high_priority_count

class TestDashboardPerformance:
    """Test dashboard performance and responsiveness."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_api_response_times(self):
        """Test that API endpoints respond within reasonable time."""
        import time
        
        endpoints = [
            "/dashboard/api/metrics",
            "/dashboard/api/tasks", 
            "/dashboard/api/goals",
            "/dashboard/api/analytics",
            "/dashboard/health"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds
    
    def test_concurrent_requests_handling(self):
        """Test dashboard handles concurrent requests properly."""
        import concurrent.futures
        
        def make_request():
            return self.client.get("/dashboard/api/metrics")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_large_task_list_performance(self):
        """Test performance with large task datasets."""
        # This would be implemented when integrating with real data sources
        response = self.client.get("/dashboard/api/tasks")
        assert response.status_code == 200
        
        # Verify response is still fast even with current mock data
        import time
        start_time = time.time()
        self.client.get("/dashboard/api/tasks")
        response_time = time.time() - start_time
        
        assert response_time < 1.0

class TestDashboardSecurity:
    """Test dashboard security and validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_config_update_validation(self):
        """Test configuration update input validation."""
        # Test invalid data
        invalid_data = {
            "key": "",  # Empty key should fail
            "value": "test",
            "category": "test"
        }
        
        response = self.client.post(
            "/dashboard/api/config/update",
            json=invalid_data
        )
        
        # Should handle validation appropriately
        assert response.status_code in [200, 400, 422]
    
    def test_config_import_validation(self):
        """Test configuration import validation."""
        # Test malformed import data
        invalid_data = "not a dictionary"
        
        response = self.client.post(
            "/dashboard/api/config/import",
            json=invalid_data
        )
        
        # Should handle malformed data gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attempts."""
        # Test malicious input in config update
        malicious_data = {
            "key": "'; DROP TABLE configs; --",
            "value": "malicious",
            "category": "test"
        }
        
        response = self.client.post(
            "/dashboard/api/config/update",
            json=malicious_data
        )
        
        # Should not cause server error
        assert response.status_code in [200, 400, 422]
    
    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        # Test script injection in config values
        xss_data = {
            "key": "test_key",
            "value": "<script>alert('xss')</script>",
            "category": "test"
        }
        
        response = self.client.post(
            "/dashboard/api/config/update", 
            json=xss_data
        )
        
        # Should handle safely
        assert response.status_code in [200, 400, 422]

class TestDashboardIntegration:
    """Test dashboard integration with other system components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    @patch('src.config_manager.config_manager.get_config')
    def test_config_manager_integration(self, mock_get_config):
        """Test dashboard integration with config manager."""
        mock_get_config.return_value = 10
        
        response = self.client.get("/dashboard/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["weekly_hours_available"] == 10
        mock_get_config.assert_called()
    
    @patch('src.database.db_manager.get_business_goals')
    def test_database_integration(self, mock_get_goals):
        """Test dashboard integration with database manager."""
        mock_goals = [
            {"title": "Test Goal", "area": "sales", "progress": 50}
        ]
        mock_get_goals.return_value = mock_goals
        
        response = self.client.get("/dashboard/api/goals")
        assert response.status_code == 200
        
        data = response.json()
        assert data == mock_goals
        mock_get_goals.assert_called()
    
    def test_ceo_operator_integration(self):
        """Test dashboard integration with CEO operator functions."""
        # Test that endpoints exist and can be called
        response = self.client.post("/dashboard/api/generate/weekly-plan")
        assert response.status_code == 200
        
        response = self.client.post("/dashboard/api/generate/midweek-nudge")
        assert response.status_code == 200
        
        response = self.client.post("/dashboard/api/generate/friday-retro")
        assert response.status_code == 200

@pytest.mark.asyncio
class TestDashboardAsync:
    """Test asynchronous dashboard functionality."""
    
    async def test_async_metrics_function(self):
        """Test async metrics retrieval function."""
        metrics = await get_dashboard_metrics()
        
        assert hasattr(metrics, 'total_tasks')
        assert hasattr(metrics, 'high_priority_tasks')
        assert hasattr(metrics, 'revenue_pipeline')
        assert isinstance(metrics.total_tasks, int)
        assert isinstance(metrics.revenue_pipeline, float)
    
    async def test_async_task_summary_function(self):
        """Test async task summary function."""
        tasks = await get_task_summary()
        
        assert isinstance(tasks, list)
        if tasks:
            task = tasks[0]
            assert hasattr(task, 'id')
            assert hasattr(task, 'title')
            assert hasattr(task, 'priority')
    
    async def test_async_analytics_function(self):
        """Test async analytics function."""
        analytics = await get_comprehensive_analytics()
        
        assert isinstance(analytics, dict)
        assert analytics["success"] is True
        assert "overview" in analytics
        assert "priority_breakdown" in analytics

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])

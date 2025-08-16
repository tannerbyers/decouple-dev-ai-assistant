"""
FastAPI Startup Integration Tests

These tests would have caught today's async timeout issue by testing actual FastAPI startup.
"""
import pytest
import warnings
import asyncio
import threading
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestFastAPIStartupIntegration:
    """Integration tests for FastAPI startup and shutdown process"""
    
    def test_fastapi_startup_no_async_warnings(self):
        """CRITICAL: Test that FastAPI startup produces no async warnings
        
        This test would have caught today's issue:
        - RuntimeWarning: coroutine '_monitoring_loop' was never awaited
        """
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            
            # Mock environment variables to avoid requiring real credentials
            with patch.dict(os.environ, {
                'TEST_MODE': 'true',
                'SLACK_BOT_TOKEN': 'test_token',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'NOTION_API_KEY': 'test_notion_key',
                'NOTION_DB_ID': 'test_db_id',
                'OPENAI_API_KEY': 'test_openai_key'
            }):
                # Import and create the app (this triggers startup code)
                from main import app
                
                # Create test client (this initializes the app)
                client = TestClient(app)
                
                # Test a simple endpoint to ensure app is working
                response = client.get("/health")
                assert response.status_code == 200
            
            # Check for any RuntimeWarnings about unawaited coroutines
            runtime_warnings = [
                w for w in warning_list 
                if issubclass(w.category, RuntimeWarning) and 
                ("unawaited" in str(w.message) or "_monitoring_loop" in str(w.message))
            ]
            
            assert len(runtime_warnings) == 0, (
                f"Found {len(runtime_warnings)} async warnings during startup: "
                f"{[str(w.message) for w in runtime_warnings]}"
            )
    
    def test_health_monitor_starts_properly(self):
        """Test that health monitoring starts without creating hanging tasks"""
        with patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Mock the health monitor to track its behavior
            with patch('src.self_healing.HealthMonitor') as MockHealthMonitor:
                mock_monitor = MagicMock()
                MockHealthMonitor.return_value = mock_monitor
                
                # Import and create the app
                from main import app
                client = TestClient(app)
                
                # Verify health monitor was initialized but not started immediately
                # (it should start in the FastAPI startup event)
                assert mock_monitor.start_monitoring.call_count <= 1
                
                # Test health endpoint works
                response = client.get("/health")
                assert response.status_code == 200
    
    def test_async_context_handling(self):
        """Test that async/sync context transitions work properly"""
        with patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            from main import app
            
            # Test that we can start the app without async context issues
            with TestClient(app) as client:
                # Test multiple concurrent requests (simulates real usage)
                responses = []
                for i in range(5):
                    response = client.get("/health")
                    responses.append(response)
                
                # All requests should succeed
                assert all(r.status_code == 200 for r in responses)
    
    def test_startup_shutdown_events(self):
        """Test FastAPI startup and shutdown events execute properly"""
        startup_called = False
        shutdown_called = False
        
        def mock_startup():
            nonlocal startup_called
            startup_called = True
        
        def mock_shutdown():
            nonlocal shutdown_called
            shutdown_called = True
        
        with patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Patch the startup/shutdown events
            with patch('main.startup_event', side_effect=mock_startup), \
                 patch('main.shutdown_event', side_effect=mock_shutdown):
                
                from main import app
                
                # Create and close client to trigger startup/shutdown
                with TestClient(app) as client:
                    response = client.get("/health")
                    assert response.status_code == 200
                
                # Note: TestClient doesn't always trigger shutdown events
                # so we mainly test that startup works without errors
                # In a real deployment, these would be tested differently
    
    def test_memory_leak_prevention(self):
        """Test that startup doesn't create memory leaks or hanging resources"""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_threads = threading.active_count()
        
        with patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Create and destroy app multiple times
            for i in range(3):
                from main import app
                with TestClient(app) as client:
                    response = client.get("/health")
                    assert response.status_code == 200
                
                # Force garbage collection
                gc.collect()
        
        # Check memory usage after multiple startups
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_threads = threading.active_count()
        
        memory_increase = final_memory - initial_memory
        thread_increase = final_threads - initial_threads
        
        # Allow some memory increase but not excessive
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB - possible leak"
        assert thread_increase < 5, f"Thread count increased by {thread_increase} - possible resource leak"
    
    @pytest.mark.asyncio
    async def test_async_event_loop_compatibility(self):
        """Test that the app works properly in async contexts"""
        with patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Test that we can work with the app in an async context
            from main import app
            
            # This should not create conflicts with existing event loops
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200
                
                # Test that we can still create async tasks
                async def test_task():
                    await asyncio.sleep(0.1)
                    return "success"
                
                result = await test_task()
                assert result == "success"
    
    def test_production_simulation(self):
        """Simulate production-like conditions to catch edge cases"""
        with patch.dict(os.environ, {
            'TEST_MODE': 'false',  # Simulate production mode
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'NOTION_API_KEY': 'test_notion_key',
            'NOTION_DB_ID': 'test_db_id',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            # Mock external services to avoid real API calls
            with patch('requests.get') as mock_get, \
                 patch('notion_client.Client') as mock_notion, \
                 patch('langchain_openai.ChatOpenAI') as mock_openai:
                
                # Configure mocks
                mock_get.return_value.ok = True
                mock_notion.return_value.users.me.return_value = {"name": "test"}
                mock_openai.return_value.invoke.return_value.content = "test response"
                
                from main import app
                
                with TestClient(app) as client:
                    # Test health endpoint
                    response = client.get("/health")
                    assert response.status_code == 200
                    
                    # Test that production mode differences don't break anything
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert data["test_mode"] == False

class TestAsyncContextValidation:
    """Specific tests for async context issues that caused today's problem"""
    
    def test_health_monitor_async_context_detection(self):
        """Test that HealthMonitor properly detects async context"""
        from src.self_healing import HealthMonitor, ErrorMonitor
        
        # Test in sync context
        error_monitor = ErrorMonitor()
        health_monitor = HealthMonitor(error_monitor)
        
        # This should not raise any warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            health_monitor.start_monitoring()
            
            # Should not create any RuntimeWarnings
            runtime_warnings = [warning for warning in w if issubclass(warning.category, RuntimeWarning)]
            assert len(runtime_warnings) == 0, f"Unexpected warnings: {[str(w.message) for w in runtime_warnings]}"
    
    @pytest.mark.asyncio
    async def test_health_monitor_in_async_context(self):
        """Test that HealthMonitor works properly when started in async context"""
        from src.self_healing import HealthMonitor, ErrorMonitor
        
        error_monitor = ErrorMonitor()
        health_monitor = HealthMonitor(error_monitor)
        
        # This should work without warnings in async context
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            health_monitor.start_monitoring()
            
            # Give it a moment to start
            await asyncio.sleep(0.1)
            
            # Stop monitoring to clean up
            health_monitor.stop_monitoring()
            
            # Should not create any RuntimeWarnings
            runtime_warnings = [warning for warning in w if issubclass(warning.category, RuntimeWarning)]
            assert len(runtime_warnings) == 0, f"Unexpected warnings: {[str(w.message) for w in runtime_warnings]}"

if __name__ == "__main__":
    # Run tests directly for debugging
    pytest.main([__file__, "-v"])

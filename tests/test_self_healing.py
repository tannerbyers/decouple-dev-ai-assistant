import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from src.self_healing import (
    ErrorMonitor, HealthMonitor, SystemRecoveryCoordinator,
    self_healing, with_circuit_breaker, error_recovery_context,
    SystemComponent, ErrorSeverity, check_system_resources,
    initialize_self_healing_system, get_self_healing_system
)


class TestErrorMonitor:
    """Test cases for the ErrorMonitor component."""
    
    def test_error_monitor_initialization(self):
        """Test that ErrorMonitor initializes correctly."""
        monitor = ErrorMonitor()
        assert len(monitor.error_history) == 0
        assert len(monitor.component_health) == 0
        assert len(monitor.circuit_breakers) == 3  # SLACK, NOTION, OPENAI APIs
        assert len(monitor.recovery_strategies) == 0
    
    def test_register_error(self):
        """Test error registration functionality."""
        monitor = ErrorMonitor()
        
        # Register a simple error
        error = Exception("Test error")
        error_event = monitor.register_error(
            SystemComponent.SLACK_API, 
            error, 
            {"context": "test"}
        )
        
        assert len(monitor.error_history) == 1
        
        # Check the returned error event
        assert error_event.error_type == "Exception"
        assert error_event.message == "Test error"
        assert error_event.component == SystemComponent.SLACK_API
        assert error_event.context == {"context": "test"}
        assert error_event.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
    
    def test_register_recovery_strategy(self):
        """Test recovery strategy registration."""
        monitor = ErrorMonitor()
        
        def test_strategy(error_event):
            return True
        
        monitor.register_recovery_strategy(
            SystemComponent.SLACK_API, 
            "ConnectionError", 
            test_strategy
        )
        
        strategy_key = f"{SystemComponent.SLACK_API.value}_ConnectionError"
        assert strategy_key in monitor.recovery_strategies
        assert monitor.recovery_strategies[strategy_key] == test_strategy
    
    def test_get_health_summary(self):
        """Test health summary generation."""
        monitor = ErrorMonitor()
        
        # Register errors of different severities
        monitor.register_error(SystemComponent.SLACK_API, Exception("Low error"))
        monitor.register_error(SystemComponent.NOTION_API, ValueError("High error"))
        monitor.register_error(SystemComponent.OPENAI_API, ConnectionError("Critical error"))
        
        summary = monitor.get_health_summary()
        
        assert "overall_health" in summary
        assert "recent_errors" in summary
        assert "critical_errors" in summary
        assert "high_errors" in summary
        assert "component_health" in summary
        assert "circuit_breakers" in summary


class TestHealthMonitor:
    """Test cases for the HealthMonitor component."""
    
    def test_health_monitor_initialization(self):
        """Test that HealthMonitor initializes correctly."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        assert len(monitor.health_checks) == 0
        assert monitor.monitoring_active == False
        assert monitor.check_interval == 300  # 5 minutes
        assert monitor.error_monitor == error_monitor
    
    def test_register_health_check(self):
        """Test health check registration."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        
        async def test_check():
            return True
        
        monitor.register_health_check(SystemComponent.SLACK_API, test_check)
        
        assert SystemComponent.SLACK_API in monitor.health_checks
        assert monitor.health_checks[SystemComponent.SLACK_API] == test_check
    
    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        """Test running health checks."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        
        # Register a healthy check
        async def healthy_check():
            return True
        
        # Register an unhealthy check
        async def unhealthy_check():
            return False
        
        monitor.register_health_check(SystemComponent.SLACK_API, healthy_check)
        monitor.register_health_check(SystemComponent.NOTION_API, unhealthy_check)
        
        # Run health checks
        results = await monitor.run_health_checks()
        
        assert SystemComponent.SLACK_API in results
        assert SystemComponent.NOTION_API in results
        assert results[SystemComponent.SLACK_API].healthy is True
        assert results[SystemComponent.NOTION_API].healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_error_handling(self):
        """Test health check error handling."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        
        # Register a check that raises an exception
        async def failing_check():
            raise Exception("Health check failed")
        
        monitor.register_health_check(SystemComponent.SLACK_API, failing_check)
        
        # Run health checks - should handle error gracefully
        results = await monitor.run_health_checks()
        
        assert SystemComponent.SLACK_API in results
        assert results[SystemComponent.SLACK_API].healthy is False
        assert "error" in results[SystemComponent.SLACK_API].details
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        
        # Initially not monitoring
        assert monitor.monitoring_active is False
        
        # Test setting monitoring state directly (since start_monitoring creates async task)
        monitor.monitoring_active = True
        assert monitor.monitoring_active is True
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert monitor.monitoring_active is False


class TestSystemRecoveryCoordinator:
    """Test cases for the SystemRecoveryCoordinator component."""
    
    def test_recovery_coordinator_initialization(self):
        """Test that SystemRecoveryCoordinator initializes correctly."""
        error_monitor = ErrorMonitor()
        coordinator = SystemRecoveryCoordinator(error_monitor)
        assert coordinator.error_monitor == error_monitor
        assert coordinator.notion_client is None
        assert coordinator.recovery_in_progress is False
    
    def test_recovery_coordinator_with_notion(self):
        """Test SystemRecoveryCoordinator initialization with Notion client."""
        error_monitor = ErrorMonitor()
        mock_notion = Mock()
        coordinator = SystemRecoveryCoordinator(error_monitor, mock_notion)
        assert coordinator.error_monitor == error_monitor
        assert coordinator.notion_client == mock_notion
        assert coordinator.recovery_in_progress is False
    
    @patch('src.self_healing.ErrorEvent')
    def test_initiate_system_recovery(self, mock_error_event):
        """Test system recovery initiation."""
        error_monitor = ErrorMonitor()
        coordinator = SystemRecoveryCoordinator(error_monitor)
        
        # Create a mock error event
        mock_event = Mock()
        mock_event.component = SystemComponent.SLACK_API
        mock_event.severity = ErrorSeverity.CRITICAL
        
        # Mock health summary
        with patch.object(error_monitor, 'get_health_summary') as mock_summary:
            mock_summary.return_value = {
                "overall_health": "degraded",
                "recent_errors": 5,
                "critical_errors": 1
            }
            
            # Test recovery initiation
            coordinator.initiate_system_recovery(mock_event)
            
            # Should have called health summary
            mock_summary.assert_called_once()
    
    def test_recovery_in_progress_protection(self):
        """Test that recovery doesn't run if already in progress."""
        error_monitor = ErrorMonitor()
        coordinator = SystemRecoveryCoordinator(error_monitor)
        
        # Set recovery in progress
        coordinator.recovery_in_progress = True
        
        mock_event = Mock()
        mock_event.component = SystemComponent.SLACK_API
        
        # Should return early without doing anything
        coordinator.initiate_system_recovery(mock_event)
        
        # Recovery should still be in progress
        assert coordinator.recovery_in_progress is True


class TestSelfHealingDecorator:
    """Test cases for the self_healing decorator."""
    
    def test_self_healing_decorator_success(self):
        """Test self_healing decorator with successful function."""
        error_monitor = ErrorMonitor()
        
        @self_healing(SystemComponent.SLACK_API, error_monitor)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_self_healing_decorator_with_error(self):
        """Test self_healing decorator with function that raises error."""
        error_monitor = ErrorMonitor()
        
        @self_healing(SystemComponent.SLACK_API, error_monitor)
        def failing_function():
            raise ConnectionError("Connection failed")
        
        # Should register error and re-raise
        with pytest.raises(ConnectionError):
            failing_function()
        
        # Error should be recorded
        assert len(error_monitor.error_history) == 1
        assert error_monitor.error_history[0].error_type == "ConnectionError"
    
    @pytest.mark.asyncio
    async def test_self_healing_decorator_async(self):
        """Test self_healing decorator with async function."""
        error_monitor = ErrorMonitor()
        
        @self_healing(SystemComponent.SLACK_API, error_monitor)
        async def async_function():
            return "async success"
        
        result = await async_function()
        assert result == "async success"


class TestCircuitBreakerDecorator:
    """Test cases for the with_circuit_breaker decorator."""
    
    def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal operation."""
        error_monitor = ErrorMonitor()
        
        @with_circuit_breaker(SystemComponent.SLACK_API, error_monitor)
        def normal_function():
            return "success"
        
        result = normal_function()
        assert result == "success"
    
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        error_monitor = ErrorMonitor()
        
        @with_circuit_breaker(SystemComponent.SLACK_API, error_monitor)
        def failing_function():
            raise ConnectionError("Service unavailable")
        
        # First few calls should fail normally
        for i in range(6):  # Should trigger circuit breaker after 5 failures
            with pytest.raises(Exception):  # Could be ConnectionError or circuit breaker exception
                failing_function()
        
        # Circuit breaker should now be open
        circuit_breaker = error_monitor.circuit_breakers[SystemComponent.SLACK_API]
        assert circuit_breaker.state in ["OPEN", "HALF_OPEN"]


class TestErrorRecoveryContext:
    """Test cases for the error_recovery_context context manager."""
    
    def test_error_recovery_context_success(self):
        """Test error recovery context with successful operation."""
        error_monitor = ErrorMonitor()
        
        with error_recovery_context(SystemComponent.SLACK_API, error_monitor):
            result = "success"
        
        assert result == "success"
        # No errors should be registered for successful operation
        assert len(error_monitor.error_history) == 0
    
    def test_error_recovery_context_with_error(self):
        """Test error recovery context with error."""
        error_monitor = ErrorMonitor()
        
        with pytest.raises(ValueError):
            with error_recovery_context(SystemComponent.SLACK_API, error_monitor):
                raise ValueError("Test error")
        
        # Error should be registered
        assert len(error_monitor.error_history) == 1
        assert error_monitor.error_history[0].error_type == "ValueError"


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_check_system_resources(self):
        """Test system resource checking."""
        resources = check_system_resources()
        
        assert "cpu_percent" in resources
        assert "memory_percent" in resources
        assert "disk_percent" in resources
        
        # Values should be reasonable percentages
        assert 0 <= resources["cpu_percent"] <= 100
        assert 0 <= resources["memory_percent"] <= 100
        assert 0 <= resources["disk_percent"] <= 100
    
    def test_initialize_self_healing_system(self):
        """Test self-healing system initialization."""
        mock_notion = Mock()
        
        error_monitor, health_monitor, coordinator = initialize_self_healing_system(mock_notion)
        
        assert isinstance(error_monitor, ErrorMonitor)
        assert isinstance(health_monitor, HealthMonitor)
        assert isinstance(coordinator, SystemRecoveryCoordinator)
    
    def test_get_self_healing_system(self):
        """Test getting self-healing system components."""
        mock_notion = Mock()
        
        # Initialize first
        initialize_self_healing_system(mock_notion)
        
        # Then get
        error_monitor, health_monitor, coordinator = get_self_healing_system()
        
        assert isinstance(error_monitor, ErrorMonitor)
        assert isinstance(health_monitor, HealthMonitor)
        assert isinstance(coordinator, SystemRecoveryCoordinator)


class TestIntegration:
    """Integration tests for the complete self-healing system."""
    
    @pytest.mark.asyncio
    async def test_full_self_healing_workflow(self):
        """Test complete self-healing workflow."""
        mock_notion = Mock()
        
        # Initialize system
        error_monitor, health_monitor, coordinator = initialize_self_healing_system(mock_notion)
        
        # Register a health check
        async def test_api_health():
            return True
        
        health_monitor.register_health_check(SystemComponent.SLACK_API, test_api_health)
        
        # Register a recovery strategy
        def test_recovery(error_event):
            return True
        
        error_monitor.register_recovery_strategy(
            SystemComponent.SLACK_API, 
            "ConnectionError", 
            test_recovery
        )
        
        # Test the workflow with decorators
        @self_healing(SystemComponent.SLACK_API, error_monitor)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # Check health
        health_results = await health_monitor.run_health_checks()
        assert health_results[SystemComponent.SLACK_API].healthy is True


# Fixtures for testing
@pytest.fixture
def error_monitor():
    """Provide a fresh ErrorMonitor instance for tests."""
    return ErrorMonitor()


@pytest.fixture
def health_monitor(error_monitor):
    """Provide a fresh HealthMonitor instance for tests."""
    return HealthMonitor(error_monitor)


@pytest.fixture
def recovery_coordinator(error_monitor):
    """Provide a fresh SystemRecoveryCoordinator instance for tests."""
    return SystemRecoveryCoordinator(error_monitor)


@pytest.fixture
def mock_notion_client():
    """Provide a mock Notion client for tests."""
    mock_client = Mock()
    mock_client.pages.create.return_value = {"id": "test-page-id"}
    return mock_client


# Performance tests
class TestPerformance:
    """Performance tests for the self-healing system."""
    
    def test_error_monitoring_performance(self):
        """Test that error monitoring doesn't significantly impact performance."""
        monitor = ErrorMonitor()
        
        start_time = time.time()
        
        # Register many errors quickly
        for i in range(1000):
            error = Exception(f"Test error {i}")
            monitor.register_error(SystemComponent.SLACK_API, error)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        assert elapsed < 1.0
        assert len(monitor.error_history) == 1000
    
    @pytest.mark.asyncio
    async def test_health_monitoring_performance(self):
        """Test that health monitoring is efficient."""
        error_monitor = ErrorMonitor()
        monitor = HealthMonitor(error_monitor)
        
        # Register multiple health checks
        async def fast_check():
            return True
        
        for component in SystemComponent:
            monitor.register_health_check(component, fast_check)
        
        start_time = time.time()
        
        # Run health checks
        await monitor.run_health_checks()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly (less than 1 second for all components)
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__])

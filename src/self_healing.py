"""
OpsBrain Self-Healing System

A comprehensive self-healing architecture that monitors, diagnoses, and automatically
recovers from system failures across all components.
"""

import asyncio
import logging
import time
import traceback
import functools
import json
import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import requests
from contextlib import contextmanager
import psutil
import os

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemComponent(Enum):
    SLACK_API = "slack_api"
    NOTION_API = "notion_api"
    OPENAI_API = "openai_api"
    DATABASE = "database"
    WEBHOOK = "webhook"
    AUTHENTICATION = "authentication"
    TASK_PROCESSING = "task_processing"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

class RecoveryAction(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    ESCALATE = "escalate"
    ISOLATE = "isolate"
    NOTIFY = "notify"

@dataclass
class ErrorEvent:
    """Represents an error event in the system"""
    timestamp: str
    component: SystemComponent
    severity: ErrorSeverity
    error_type: str
    message: str
    stack_trace: Optional[str]
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_actions: List[str] = None
    
    def __post_init__(self):
        if self.recovery_actions is None:
            self.recovery_actions = []

@dataclass
class HealthCheck:
    """Represents a health check result"""
    component: SystemComponent
    healthy: bool
    latency_ms: Optional[float]
    last_check: str
    error_count: int
    details: Dict[str, Any]

class CircuitBreaker:
    """Circuit breaker implementation for external services"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker OPEN - service unavailable")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED - service recovered")
                return result
            
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit breaker OPEN - too many failures: {self.failure_count}")
                
                raise e

class ErrorMonitor:
    """Centralized error monitoring and tracking"""
    
    def __init__(self):
        self.error_history: List[ErrorEvent] = []
        self.component_health: Dict[SystemComponent, HealthCheck] = {}
        self.circuit_breakers: Dict[SystemComponent, CircuitBreaker] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.max_history = 1000
        self.lock = threading.Lock()
        
        # Initialize circuit breakers for external services
        for component in [SystemComponent.SLACK_API, SystemComponent.NOTION_API, 
                         SystemComponent.OPENAI_API]:
            self.circuit_breakers[component] = CircuitBreaker()
    
    def register_error(self, component: SystemComponent, error: Exception, 
                      context: Dict[str, Any] = None) -> ErrorEvent:
        """Register an error event"""
        if context is None:
            context = {}
            
        severity = self._assess_severity(component, error, context)
        
        error_event = ErrorEvent(
            timestamp=datetime.datetime.now().isoformat(),
            component=component,
            severity=severity,
            error_type=type(error).__name__,
            message=str(error),
            stack_trace=traceback.format_exc(),
            context=context
        )
        
        with self.lock:
            self.error_history.append(error_event)
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
        
        logger.error(f"Error registered: {component.value} - {error}")
        
        # Trigger recovery if appropriate
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._trigger_recovery(error_event)
        
        return error_event
    
    def _assess_severity(self, component: SystemComponent, error: Exception, 
                        context: Dict[str, Any]) -> ErrorSeverity:
        """Assess the severity of an error"""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Critical errors
        if component in [SystemComponent.DATABASE, SystemComponent.AUTHENTICATION]:
            return ErrorSeverity.CRITICAL
        
        if "timeout" in error_msg or "connection" in error_msg:
            return ErrorSeverity.HIGH
        
        if "rate limit" in error_msg or "quota" in error_msg:
            return ErrorSeverity.MEDIUM
        
        if error_type in ["ValidationError", "ValueError"]:
            return ErrorSeverity.LOW
        
        # Default to medium for unknown errors
        return ErrorSeverity.MEDIUM
    
    def _trigger_recovery(self, error_event: ErrorEvent):
        """Trigger automatic recovery for an error"""
        recovery_strategy = self._get_recovery_strategy(error_event)
        
        try:
            success = recovery_strategy(error_event)
            error_event.recovery_attempted = True
            error_event.recovery_successful = success
            
            if success:
                logger.info(f"Recovery successful for {error_event.component.value}")
            else:
                logger.warning(f"Recovery failed for {error_event.component.value}")
                
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            error_event.recovery_attempted = True
            error_event.recovery_successful = False
    
    def _get_recovery_strategy(self, error_event: ErrorEvent) -> Callable:
        """Get the appropriate recovery strategy for an error"""
        component = error_event.component
        error_type = error_event.error_type
        
        # Return registered strategy or default
        strategy_key = f"{component.value}_{error_type}"
        return self.recovery_strategies.get(strategy_key, self._default_recovery)
    
    def _default_recovery(self, error_event: ErrorEvent) -> bool:
        """Default recovery strategy"""
        logger.info(f"Applying default recovery for {error_event.component.value}")
        
        # For API errors, wait and retry
        if error_event.component in [SystemComponent.SLACK_API, SystemComponent.NOTION_API, 
                                    SystemComponent.OPENAI_API]:
            time.sleep(2)  # Brief wait before retry
            return True
        
        return False
    
    def register_recovery_strategy(self, component: SystemComponent, error_type: str, 
                                 strategy: Callable):
        """Register a custom recovery strategy"""
        key = f"{component.value}_{error_type}"
        self.recovery_strategies[key] = strategy
        logger.info(f"Registered recovery strategy: {key}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        recent_errors = [e for e in self.error_history 
                        if (datetime.datetime.now() - 
                           datetime.datetime.fromisoformat(e.timestamp)).seconds < 3600]
        
        critical_count = len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        high_count = len([e for e in recent_errors if e.severity == ErrorSeverity.HIGH])
        
        overall_health = "healthy"
        if critical_count > 0:
            overall_health = "critical"
        elif high_count > 3:
            overall_health = "degraded"
        elif len(recent_errors) > 10:
            overall_health = "unstable"
        
        return {
            "overall_health": overall_health,
            "recent_errors": len(recent_errors),
            "critical_errors": critical_count,
            "high_errors": high_count,
            "component_health": {c.value: h.healthy for c, h in self.component_health.items()},
            "circuit_breakers": {c.value: cb.state for c, cb in self.circuit_breakers.items()}
        }

class HealthMonitor:
    """Proactive health monitoring for system components"""
    
    def __init__(self, error_monitor: ErrorMonitor):
        self.error_monitor = error_monitor
        self.health_checks: Dict[SystemComponent, Callable] = {}
        self.monitoring_active = False
        self.check_interval = 300  # 5 minutes
        
    def register_health_check(self, component: SystemComponent, check_func: Callable):
        """Register a health check function for a component"""
        self.health_checks[component] = check_func
        logger.info(f"Registered health check for {component.value}")
    
    async def run_health_checks(self):
        """Run all registered health checks"""
        results = {}
        
        for component, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                healthy = await self._run_check(check_func)
                latency = (time.time() - start_time) * 1000
                
                health_check = HealthCheck(
                    component=component,
                    healthy=healthy,
                    latency_ms=latency,
                    last_check=datetime.datetime.now().isoformat(),
                    error_count=0,
                    details={}
                )
                
                self.error_monitor.component_health[component] = health_check
                results[component] = health_check
                
            except Exception as e:
                # Health check itself failed
                self.error_monitor.register_error(component, e, {"health_check": True})
                results[component] = HealthCheck(
                    component=component,
                    healthy=False,
                    latency_ms=None,
                    last_check=datetime.datetime.now().isoformat(),
                    error_count=1,
                    details={"error": str(e)}
                )
        
        return results
    
    async def _run_check(self, check_func: Callable) -> bool:
        """Run a single health check with timeout"""
        try:
            if asyncio.iscoroutinefunction(check_func):
                return await asyncio.wait_for(check_func(), timeout=30)
            else:
                return await asyncio.wait_for(
                    asyncio.to_thread(check_func), timeout=30
                )
        except asyncio.TimeoutError:
            return False
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Handle both sync and async contexts
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we have a running loop, create the task
            loop.create_task(self._monitoring_loop())
            logger.info("Health monitoring started in async context")
        except RuntimeError:
            # No event loop running, defer the start until an async context is available
            logger.info("Health monitoring deferred - no async context available")
            # We'll start monitoring when the first async health check is called
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                await self.run_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(60)  # Brief pause before retry

class SystemRecoveryCoordinator:
    """Coordinates system-wide recovery efforts"""
    
    def __init__(self, error_monitor: ErrorMonitor, notion_client=None):
        self.error_monitor = error_monitor
        self.notion_client = notion_client
        self.notion_db_id = os.getenv("NOTION_DB_ID")
        self.recovery_in_progress = False
        
    def initiate_system_recovery(self, trigger_event: ErrorEvent):
        """Initiate comprehensive system recovery"""
        if self.recovery_in_progress:
            logger.info("Recovery already in progress, skipping")
            return
        
        self.recovery_in_progress = True
        
        try:
            logger.info("Initiating system-wide recovery process")
            
            # 1. Assess system state
            health_summary = self.error_monitor.get_health_summary()
            
            # 2. Create recovery task in Notion
            if self.notion_client and self.notion_db_id:
                self._create_recovery_task(trigger_event, health_summary)
            
            # 3. Apply recovery strategies based on severity
            if health_summary["overall_health"] == "critical":
                self._apply_critical_recovery()
            elif health_summary["overall_health"] == "degraded":
                self._apply_degraded_recovery()
            
            # 4. Reset circuit breakers if appropriate
            self._reset_circuit_breakers()
            
            logger.info("System recovery process completed")
            
        except Exception as e:
            logger.error(f"System recovery failed: {e}")
        finally:
            self.recovery_in_progress = False
    
    def _create_recovery_task(self, trigger_event: ErrorEvent, health_summary: Dict):
        """Create a recovery task in Notion"""
        try:
            task_title = f"System Recovery Required - {trigger_event.component.value}"
            
            recovery_notes = f"""AUTOMATIC SYSTEM RECOVERY INITIATED
            
Trigger Event:
- Component: {trigger_event.component.value}
- Error: {trigger_event.error_type} - {trigger_event.message}
- Severity: {trigger_event.severity.value}
- Timestamp: {trigger_event.timestamp}

System Health Summary:
- Overall Health: {health_summary['overall_health']}
- Recent Errors: {health_summary['recent_errors']}
- Critical Errors: {health_summary['critical_errors']}

RECOVERY STEPS:
1. Investigate root cause of {trigger_event.component.value} failure
2. Verify system health checks are passing
3. Review error logs and patterns
4. Test component functionality
5. Update monitoring thresholds if needed

DELIVERABLE: System restored to healthy state with improved resilience"""
            
            properties = {
                "title": {
                    "title": [{"text": {"content": task_title}}]
                }
            }
            
            # Try to add notes if the database supports it
            try:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": recovery_notes}}]
                }
            except:
                pass
                
            # Try to set priority if supported
            try:
                properties["Priority"] = {
                    "select": {"name": "Critical"}
                }
            except:
                pass
            
            self.notion_client.pages.create(
                parent={"database_id": self.notion_db_id},
                properties=properties
            )
            
            logger.info("Created system recovery task in Notion")
            
        except Exception as e:
            logger.error(f"Failed to create recovery task: {e}")
    
    def _apply_critical_recovery(self):
        """Apply critical system recovery measures"""
        logger.info("Applying critical recovery measures")
        
        # Reset all circuit breakers
        for cb in self.error_monitor.circuit_breakers.values():
            with cb.lock:
                cb.state = "CLOSED"
                cb.failure_count = 0
        
        # Clear error history to prevent cascading issues
        with self.error_monitor.lock:
            self.error_monitor.error_history = []
    
    def _apply_degraded_recovery(self):
        """Apply recovery for degraded system state"""
        logger.info("Applying degraded state recovery")
        
        # Reset circuit breakers for recovered services
        current_time = time.time()
        for component, cb in self.error_monitor.circuit_breakers.items():
            if cb.state == "OPEN" and cb.last_failure_time:
                if current_time - cb.last_failure_time > cb.recovery_timeout:
                    with cb.lock:
                        cb.state = "HALF_OPEN"
                        logger.info(f"Circuit breaker for {component.value} set to HALF_OPEN")
    
    def _reset_circuit_breakers(self):
        """Reset circuit breakers based on current health"""
        for component, health in self.error_monitor.component_health.items():
            if health.healthy and component in self.error_monitor.circuit_breakers:
                cb = self.error_monitor.circuit_breakers[component]
                with cb.lock:
                    if cb.state != "CLOSED":
                        cb.state = "CLOSED"
                        cb.failure_count = 0
                        logger.info(f"Circuit breaker for {component.value} reset to CLOSED")

# Decorators for automatic error handling and recovery

def self_healing(component: SystemComponent, error_monitor: ErrorMonitor):
    """Decorator to add self-healing capabilities to functions"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_monitor.register_error(component, e, {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                })
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_monitor.register_error(component, e, {
                    "function": func.__name__,
                    "args": str(args)[:100], 
                    "kwargs": str(kwargs)[:100]
                })
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def with_circuit_breaker(component: SystemComponent, error_monitor: ErrorMonitor):
    """Decorator to add circuit breaker protection"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cb = error_monitor.circuit_breakers.get(component)
            if cb:
                return cb.call(func, *args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

@contextmanager
def error_recovery_context(component: SystemComponent, error_monitor: ErrorMonitor):
    """Context manager for error recovery"""
    try:
        yield
    except Exception as e:
        error_monitor.register_error(component, e)
        raise

# System resource monitoring
def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "healthy": cpu_percent < 80 and memory.percent < 85 and disk.percent < 90
        }
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        return {"healthy": False, "error": str(e)}

# Global self-healing system instance
_global_error_monitor = None
_global_health_monitor = None
_global_recovery_coordinator = None

def initialize_self_healing_system(notion_client=None):
    """Initialize the global self-healing system"""
    global _global_error_monitor, _global_health_monitor, _global_recovery_coordinator
    
    _global_error_monitor = ErrorMonitor()
    _global_health_monitor = HealthMonitor(_global_error_monitor)
    _global_recovery_coordinator = SystemRecoveryCoordinator(_global_error_monitor, notion_client)
    
    # Register default health checks
    _global_health_monitor.register_health_check(
        SystemComponent.MEMORY, 
        lambda: check_system_resources()["healthy"]
    )
    
    logger.info("Self-healing system initialized")
    return _global_error_monitor, _global_health_monitor, _global_recovery_coordinator

def get_self_healing_system():
    """Get the global self-healing system components"""
    return _global_error_monitor, _global_health_monitor, _global_recovery_coordinator

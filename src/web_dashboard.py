"""
FastAPI-based Web Dashboard for OpsBrain AI Assistant
Production-ready dashboard that works with Render.com deployment
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .config_manager import config_manager
from .database import db_manager

logger = logging.getLogger(__name__)

# Create router for dashboard routes
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Templates for HTML responses
templates = Jinja2Templates(directory="templates")

# Data Models
class DashboardMetrics(BaseModel):
    total_tasks: int
    high_priority_tasks: int
    completed_this_week: int
    revenue_pipeline: float
    weekly_hours_available: int
    tasks_per_hour: float

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any
    category: str = "general"
    description: str = ""

class TaskSummary(BaseModel):
    id: str
    title: str
    priority: str
    status: str
    area: str
    impact: str = "Unknown"

# Dashboard Data Functions
async def get_dashboard_metrics() -> DashboardMetrics:
    """Get dashboard metrics from various sources."""
    try:
        # Get task counts (mock data for now - integrate with actual Notion data)
        total_tasks = 38  # This would come from your Notion integration
        high_priority_tasks = 12  # This would be filtered from Notion data
        completed_this_week = 8  # This would be calculated from Notion data
        
        # Get configuration values
        weekly_hours = config_manager.get_config("dashboard_weekly_hours", 5)
        
        # Calculate revenue pipeline from business goals
        business_goals = db_manager.get_business_goals(area="sales")
        revenue_pipeline = sum(goal.get("progress", 0) * 1000 for goal in business_goals)  # Mock calculation
        
        tasks_per_hour = high_priority_tasks / max(weekly_hours, 1)
        
        return DashboardMetrics(
            total_tasks=total_tasks,
            high_priority_tasks=high_priority_tasks,
            completed_this_week=completed_this_week,
            revenue_pipeline=revenue_pipeline,
            weekly_hours_available=weekly_hours,
            tasks_per_hour=tasks_per_hour
        )
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return DashboardMetrics(
            total_tasks=0, high_priority_tasks=0, completed_this_week=0,
            revenue_pipeline=0.0, weekly_hours_available=5, tasks_per_hour=0.0
        )

async def get_task_summary() -> List[TaskSummary]:
    """Get task summary for dashboard."""
    # Mock data - replace with actual Notion integration
    mock_tasks = [
        TaskSummary(id="1", title="Implement lead generation system", priority="High", status="To Do", area="Sales", impact="High"),
        TaskSummary(id="2", title="Optimize client onboarding process", priority="High", status="In Progress", area="Delivery", impact="Medium"),
        TaskSummary(id="3", title="Create pricing strategy document", priority="Medium", status="To Do", area="Financial", impact="High"),
        TaskSummary(id="4", title="Set up performance monitoring", priority="Medium", status="To Do", area="Process", impact="Medium"),
        TaskSummary(id="5", title="Review team productivity metrics", priority="Low", status="To Do", area="Team", impact="Low"),
    ]
    return mock_tasks

# HTML Templates (embedded for now, can be moved to separate files)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CEO Operator Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .metric-card {
            @apply bg-white rounded-lg shadow-md p-6 border-l-4;
        }
        .metric-high { @apply border-red-500; }
        .metric-medium { @apply border-yellow-500; }
        .metric-low { @apply border-green-500; }
        .metric-info { @apply border-blue-500; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-4">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-gray-900">🎯 CEO Operator Dashboard</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button onclick="refreshDashboard()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            Refresh
                        </button>
                        <a href="/dashboard/settings" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">
                            Settings
                        </a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Metrics Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="metric-card metric-info">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-600">Total Active Tasks</p>
                            <p class="text-3xl font-bold text-gray-900" id="total-tasks">{{ metrics.total_tasks }}</p>
                            <p class="text-sm text-green-600">+{{ metrics.completed_this_week }} this week</p>
                        </div>
                        <div class="text-blue-500">
                            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path>
                                <path fill-rule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                    </div>
                </div>

                <div class="metric-card metric-high">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-600">High Priority Tasks</p>
                            <p class="text-3xl font-bold text-gray-900" id="high-priority">{{ metrics.high_priority_tasks }}</p>
                            <p class="text-sm text-gray-600">{{ "%.1f"|format(metrics.tasks_per_hour) }} tasks/hour available</p>
                        </div>
                        <div class="text-red-500">
                            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                    </div>
                </div>

                <div class="metric-card metric-medium">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-600">Weekly Hours</p>
                            <p class="text-3xl font-bold text-gray-900" id="weekly-hours">{{ metrics.weekly_hours_available }}h</p>
                            <p class="text-sm text-gray-600">Available for high-priority tasks</p>
                        </div>
                        <div class="text-yellow-500">
                            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                    </div>
                </div>

                <div class="metric-card metric-low">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-600">Revenue Pipeline</p>
                            <p class="text-3xl font-bold text-gray-900" id="revenue">${{ "{:,.0f}".format(metrics.revenue_pipeline) }}</p>
                            <p class="text-sm text-green-600">Active goals tracking</p>
                        </div>
                        <div class="text-green-500">
                            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-13a1 1 0 112 0v.092a4.535 4.535 0 013.5 1.676 1 1 0 11-1.5 1.32A2.535 2.535 0 0010 7c-.681 0-1.3.35-1.643.886a1 1 0 01-1.714-1.028A4.535 4.535 0 019 5.092V5zm-1 8v.092a4.535 4.535 0 003.5 1.676 1 1 0 001.5-1.32A2.535 2.535 0 0010 13c-.681 0-1.3-.35-1.643-.886a1 1 0 11-1.714 1.028A4.535 4.535 0 009 13.908V14a1 1 0 112 0z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Task Management Section -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- High Priority Tasks -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4">🔥 High Priority Tasks</h2>
                    <div id="high-priority-tasks" class="space-y-3">
                        <!-- Tasks will be loaded here -->
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4">⚡ Quick Actions</h2>
                    <div class="space-y-3">
                        <button onclick="generateWeeklyPlan()" class="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg text-left">
                            🎯 Generate Weekly Plan
                        </button>
                        <button onclick="generateMidweekNudge()" class="w-full bg-yellow-500 hover:bg-yellow-600 text-white py-2 px-4 rounded-lg text-left">
                            💡 Midweek Check-in
                        </button>
                        <button onclick="generateFridayRetro()" class="w-full bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg text-left">
                            🎉 Friday Retrospective
                        </button>
                        <button onclick="showTaskAnalytics()" class="w-full bg-purple-500 hover:bg-purple-600 text-white py-2 px-4 rounded-lg text-left">
                            📊 View Analytics
                        </button>
                    </div>
                </div>
            </div>

            <!-- Business Goals Section -->
            <div class="mt-8 bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">🎯 Active Business Goals</h2>
                <div id="business-goals" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <!-- Goals will be loaded here -->
                </div>
            </div>
        </main>
    </div>

    <script>
        // Dashboard JavaScript functionality
        async function refreshDashboard() {
            try {
                const response = await fetch('/dashboard/api/metrics');
                const data = await response.json();
                updateMetrics(data);
            } catch (error) {
                console.error('Error refreshing dashboard:', error);
            }
        }

        function updateMetrics(metrics) {
            document.getElementById('total-tasks').textContent = metrics.total_tasks;
            document.getElementById('high-priority').textContent = metrics.high_priority_tasks;
            document.getElementById('weekly-hours').textContent = metrics.weekly_hours_available + 'h';
            document.getElementById('revenue').textContent = '$' + metrics.revenue_pipeline.toLocaleString();
        }

        async function loadTasks() {
            try {
                const response = await fetch('/dashboard/api/tasks');
                const tasks = await response.json();
                displayTasks(tasks);
            } catch (error) {
                console.error('Error loading tasks:', error);
            }
        }

        function displayTasks(tasks) {
            const highPriorityContainer = document.getElementById('high-priority-tasks');
            const highPriorityTasks = tasks.filter(t => t.priority === 'High');
            
            highPriorityContainer.innerHTML = highPriorityTasks.map(task => `
                <div class="border-l-4 border-red-500 pl-4 py-2">
                    <h4 class="font-medium text-gray-900">${task.title}</h4>
                    <div class="flex justify-between items-center mt-1">
                        <span class="text-sm text-gray-600">${task.area} • ${task.impact} Impact</span>
                        <span class="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">${task.status}</span>
                    </div>
                </div>
            `).join('');
        }

        async function loadBusinessGoals() {
            try {
                const response = await fetch('/dashboard/api/goals');
                const goals = await response.json();
                displayGoals(goals);
            } catch (error) {
                console.error('Error loading goals:', error);
            }
        }

        function displayGoals(goals) {
            const goalsContainer = document.getElementById('business-goals');
            goalsContainer.innerHTML = goals.map(goal => `
                <div class="border border-gray-200 rounded-lg p-4">
                    <h4 class="font-medium text-gray-900">${goal.title}</h4>
                    <p class="text-sm text-gray-600 mt-1">${goal.area}</p>
                    <div class="mt-3">
                        <div class="flex justify-between text-sm">
                            <span>Progress</span>
                            <span>${goal.progress}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div class="bg-blue-500 h-2 rounded-full" style="width: ${goal.progress}%"></div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function generateWeeklyPlan() {
            alert('Generating weekly plan... (Feature will be connected to backend)');
        }

        async function generateMidweekNudge() {
            alert('Generating midweek nudge... (Feature will be connected to backend)');
        }

        async function generateFridayRetro() {
            alert('Generating Friday retrospective... (Feature will be connected to backend)');
        }

        function showTaskAnalytics() {
            // Placeholder for analytics view
            alert('Task analytics view coming soon!');
        }

        // Load initial data
        document.addEventListener('DOMContentLoaded', function() {
            loadTasks();
            loadBusinessGoals();
        });

        // Auto-refresh every 5 minutes
        setInterval(refreshDashboard, 300000);
    </script>
</body>
</html>
"""

# Dashboard Routes
@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    try:
        metrics = await get_dashboard_metrics()
        # Render HTML with metrics data
        from jinja2 import Template
        template = Template(DASHBOARD_HTML)
        html_content = template.render(metrics=metrics)
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        raise HTTPException(status_code=500, detail="Dashboard error")

@dashboard_router.get("/api/metrics")
async def get_metrics():
    """Get dashboard metrics as JSON."""
    metrics = await get_dashboard_metrics()
    return metrics.dict()

@dashboard_router.get("/api/tasks")
async def get_tasks():
    """Get tasks summary as JSON."""
    tasks = await get_task_summary()
    return [task.dict() for task in tasks]

@dashboard_router.get("/api/goals")
async def get_goals():
    """Get business goals as JSON."""
    try:
        goals = db_manager.get_business_goals()
        return goals
    except Exception as e:
        logger.error(f"Error getting goals: {e}")
        return []

@dashboard_router.get("/settings", response_class=HTMLResponse)
async def dashboard_settings(request: Request):
    """Dashboard settings page."""
    try:
        config_info = config_manager.get_config_info()
        all_configs = config_manager.export_configs()
        
        settings_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard Settings</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div class="min-h-screen py-8">
                <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between items-center mb-8">
                        <h1 class="text-3xl font-bold text-gray-900">⚙️ Dashboard Settings</h1>
                        <a href="/dashboard" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            Back to Dashboard
                        </a>
                    </div>
                    
                    <!-- Configuration Categories -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {generate_config_cards(all_configs)}
                    </div>
                    
                    <!-- Configuration Stats -->
                    <div class="mt-8 bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-xl font-semibold text-gray-900 mb-4">Configuration Statistics</h2>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div class="text-center">
                                <p class="text-2xl font-bold text-blue-600">{config_info['total_configs']}</p>
                                <p class="text-sm text-gray-600">Total Configs</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-green-600">{len(all_configs)}</p>
                                <p class="text-sm text-gray-600">Categories</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-purple-600">{config_info['cache_size']}</p>
                                <p class="text-sm text-gray-600">Cached Items</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-red-600">{len(all_configs.get('prompts', {}))}</p>
                                <p class="text-sm text-gray-600">AI Prompts</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=settings_html)
    except Exception as e:
        logger.error(f"Error rendering settings: {e}")
        raise HTTPException(status_code=500, detail="Settings error")

def generate_config_cards(all_configs: Dict[str, Any]) -> str:
    """Generate HTML cards for configuration categories."""
    cards_html = ""
    
    category_colors = {
        "general": "blue",
        "api": "green", 
        "slack": "purple",
        "notion": "indigo",
        "openai": "red",
        "dashboard": "yellow",
        "features": "pink",
        "prompts": "gray",
        "scheduling": "orange"
    }
    
    for category, configs in all_configs.items():
        color = category_colors.get(category, "blue")
        config_count = len(configs)
        
        cards_html += f"""
        <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-{color}-500">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-900">{category.title()}</h3>
                <span class="bg-{color}-100 text-{color}-800 text-xs px-2 py-1 rounded-full">
                    {config_count} items
                </span>
            </div>
            <div class="space-y-2">
        """
        
        # Show first 3 config keys
        config_keys = list(configs.keys())[:3]
        for key in config_keys:
            cards_html += f"""
                <div class="text-sm text-gray-600">• {key}</div>
            """
        
        if len(configs) > 3:
            cards_html += f"""
                <div class="text-sm text-gray-500">... and {len(configs) - 3} more</div>
            """
        
        cards_html += """
            </div>
            <button onclick="editCategory('{}', {})" 
                    class="mt-4 w-full bg-{}-500 hover:bg-{}-600 text-white py-2 px-4 rounded-lg text-sm">
                Edit Settings
            </button>
        </div>
        """.format(category, json.dumps(configs), color, color)
    
    return cards_html

@dashboard_router.post("/api/config/update")
async def update_config(config_request: ConfigUpdateRequest):
    """Update configuration value."""
    try:
        is_valid, error_msg = config_manager.validate_config(config_request.key, config_request.value)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        config_manager.set_config(
            config_request.key,
            config_request.value,
            config_request.category,
            config_request.description
        )
        
        return {"success": True, "message": f"Configuration {config_request.key} updated successfully"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/api/config/export")
async def export_config(category: Optional[str] = None):
    """Export configuration as JSON."""
    try:
        configs = config_manager.export_configs(category)
        return JSONResponse(content=configs)
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.post("/api/config/import")
async def import_config(request: Request):
    """Import configuration from JSON."""
    try:
        data = await request.json()
        imported_count = config_manager.import_configs(data, overwrite=True)
        return {"success": True, "imported_count": imported_count}
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check for dashboard
@dashboard_router.get("/health")
async def dashboard_health():
    """Dashboard health check."""
    try:
        # Test database connection
        db_info = db_manager.get_database_info()
        
        # Test config manager
        config_info = config_manager.get_config_info()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": True,
                "tables": db_info.get("tables", {}),
                "total_records": db_info.get("total_records", 0)
            },
            "config": {
                "total_configs": config_info.get("total_configs", 0),
                "categories": len(config_info) - 2  # Exclude total_configs and cache_size
            }
        }
    except Exception as e:
        logger.error(f"Dashboard health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Integration Functions for Main App
def integrate_dashboard_with_main_app(app):
    """Integrate dashboard routes with main FastAPI app."""
    app.include_router(dashboard_router)
    logger.info("Dashboard routes integrated with main app")

def get_dashboard_url() -> str:
    """Get the dashboard URL for the current deployment."""
    return "/dashboard"

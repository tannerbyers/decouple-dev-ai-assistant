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

async def get_comprehensive_analytics() -> Dict[str, Any]:
    """Get comprehensive analytics data for dashboard."""
    try:
        # Get task data
        tasks = await get_task_summary()
        
        # Calculate analytics
        total_tasks = len(tasks)
        high_priority_count = len([t for t in tasks if t.priority == "High"])
        medium_priority_count = len([t for t in tasks if t.priority == "Medium"]) 
        low_priority_count = len([t for t in tasks if t.priority == "Low"])
        
        in_progress_count = len([t for t in tasks if t.status == "In Progress"])
        todo_count = len([t for t in tasks if t.status == "To Do"])
        done_count = len([t for t in tasks if t.status == "Done"])
        
        # Area breakdown
        areas = {}
        for task in tasks:
            if task.area not in areas:
                areas[task.area] = {"count": 0, "high_priority": 0}
            areas[task.area]["count"] += 1
            if task.priority == "High":
                areas[task.area]["high_priority"] += 1
        
        # Impact analysis
        high_impact_count = len([t for t in tasks if t.impact == "High"])
        medium_impact_count = len([t for t in tasks if t.impact == "Medium"])
        low_impact_count = len([t for t in tasks if t.impact == "Low"])
        
        return {
            "success": True,
            "overview": {
                "total_tasks": total_tasks,
                "completion_rate": (done_count / max(total_tasks, 1)) * 100
            },
            "priority_breakdown": {
                "high": high_priority_count,
                "medium": medium_priority_count,
                "low": low_priority_count
            },
            "status_breakdown": {
                "todo": todo_count,
                "in_progress": in_progress_count,
                "done": done_count
            },
            "impact_analysis": {
                "high": high_impact_count,
                "medium": medium_impact_count,
                "low": low_impact_count
            },
            "area_breakdown": areas,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return {"success": False, "error": str(e)}

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
                        <a href="/dashboard/docs" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg">
                            Docs
                        </a>
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
            try {
                showLoading('Generating weekly plan...');
                const response = await fetch('/dashboard/api/generate/weekly-plan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showModal('📋 Weekly Plan Generated', data.plan);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                hideLoading();
                console.error('Error generating weekly plan:', error);
                alert('Error generating weekly plan. Please try again.');
            }
        }

        async function generateMidweekNudge() {
            try {
                showLoading('Generating midweek check-in...');
                const response = await fetch('/dashboard/api/generate/midweek-nudge', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showModal('💡 Midweek Check-in', data.nudge);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                hideLoading();
                console.error('Error generating midweek nudge:', error);
                alert('Error generating midweek nudge. Please try again.');
            }
        }

        async function generateFridayRetro() {
            try {
                showLoading('Generating Friday retrospective...');
                const response = await fetch('/dashboard/api/generate/friday-retro', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showModal('🎉 Friday Retrospective', data.retrospective);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                hideLoading();
                console.error('Error generating Friday retro:', error);
                alert('Error generating Friday retrospective. Please try again.');
            }
        }

        async function showTaskAnalytics() {
            try {
                showLoading('Loading analytics...');
                const response = await fetch('/dashboard/api/analytics');
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    displayAnalytics(data);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                hideLoading();
                console.error('Error loading analytics:', error);
                alert('Error loading analytics. Please try again.');
            }
        }
        
        function displayAnalytics(analytics) {
            const modalContent = `
                <div class="space-y-6">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center p-4 bg-blue-50 rounded-lg">
                            <p class="text-2xl font-bold text-blue-600">${analytics.overview.total_tasks}</p>
                            <p class="text-sm text-gray-600">Total Tasks</p>
                        </div>
                        <div class="text-center p-4 bg-green-50 rounded-lg">
                            <p class="text-2xl font-bold text-green-600">${analytics.overview.completion_rate.toFixed(1)}%</p>
                            <p class="text-sm text-gray-600">Completion Rate</p>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-semibold mb-2">Priority Breakdown</h4>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>High Priority:</span>
                                <span class="font-semibold text-red-600">${analytics.priority_breakdown.high}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Medium Priority:</span>
                                <span class="font-semibold text-yellow-600">${analytics.priority_breakdown.medium}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Low Priority:</span>
                                <span class="font-semibold text-green-600">${analytics.priority_breakdown.low}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-semibold mb-2">Area Breakdown</h4>
                        <div class="space-y-1">
                            ${Object.entries(analytics.area_breakdown).map(([area, data]) => `
                                <div class="flex justify-between text-sm">
                                    <span>${area}:</span>
                                    <span>${data.count} tasks (${data.high_priority} high priority)</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            showModal('📊 Task Analytics', modalContent);
        }
        
        function showLoading(message) {
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'loading-overlay';
            loadingDiv.innerHTML = `
                <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div class="bg-white rounded-lg p-6 max-w-sm mx-auto">
                        <div class="text-center">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p class="text-gray-700">${message}</p>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(loadingDiv);
        }
        
        function hideLoading() {
            const loadingDiv = document.getElementById('loading-overlay');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }
        
        function showModal(title, content) {
            const modalDiv = document.createElement('div');
            modalDiv.id = 'modal-overlay';
            modalDiv.innerHTML = `
                <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onclick="closeModal()">
                    <div class="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-auto" onclick="event.stopPropagation()">
                        <div class="p-6">
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-xl font-bold text-gray-900">${title}</h3>
                                <button onclick="closeModal()" class="text-gray-500 hover:text-gray-700">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>
                            </div>
                            <div class="prose max-w-none">
                                ${content}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modalDiv);
        }
        
        function closeModal() {
            const modalDiv = document.getElementById('modal-overlay');
            if (modalDiv) {
                modalDiv.remove();
            }
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

@dashboard_router.post("/api/generate/weekly-plan")
async def generate_weekly_plan():
    """Generate CEO weekly plan."""
    try:
        # Import CEO operator functions from main
        import main
        generate_ceo_weekly_plan = main.generate_ceo_weekly_plan
        load_business_brain = main.load_business_brain
        
        business_brain = load_business_brain()
        if not business_brain:
            return {"error": "Business brain configuration not loaded"}
        
        weekly_plan = generate_ceo_weekly_plan()
        return {
            "success": True,
            "plan": weekly_plan,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating weekly plan: {e}")
        return {"success": False, "error": str(e)}

@dashboard_router.post("/api/generate/midweek-nudge")
async def generate_midweek_nudge():
    """Generate midweek check-in nudge."""
    try:
        import main
        generate_midweek_nudge = main.generate_midweek_nudge
        
        nudge = generate_midweek_nudge()
        return {
            "success": True,
            "nudge": nudge,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating midweek nudge: {e}")
        return {"success": False, "error": str(e)}

@dashboard_router.post("/api/generate/friday-retro")
async def generate_friday_retro():
    """Generate Friday retrospective."""
    try:
        import main
        generate_friday_retro = main.generate_friday_retro
        
        retro = generate_friday_retro()
        return {
            "success": True,
            "retrospective": retro,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating Friday retro: {e}")
        return {"success": False, "error": str(e)}

@dashboard_router.get("/api/analytics")
async def get_task_analytics():
    """Get task analytics and insights."""
    try:
        # Get task analytics data
        analytics = await get_comprehensive_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {"success": False, "error": str(e)}

@dashboard_router.get("/api/metrics")
async def get_metrics():
    """Get dashboard metrics as JSON."""
    metrics = await get_dashboard_metrics()
    return metrics.model_dump()

@dashboard_router.get("/api/tasks")
async def get_tasks():
    """Get tasks summary as JSON."""
    tasks = await get_task_summary()
    return [task.model_dump() for task in tasks]

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
        
        # Validate that data is a dictionary
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Import data must be a dictionary")
        
        imported_count = config_manager.import_configs(data, overwrite=True)
        return {"success": True, "imported_count": imported_count}
    except ValueError as e:
        # Handle JSON parsing errors
        logger.error(f"Invalid JSON format: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_router.get("/docs", response_class=HTMLResponse)
async def dashboard_docs(request: Request):
    """Comprehensive documentation page."""
    docs_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpsBrain AI Assistant - Documentation</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="min-h-screen">
            <!-- Header -->
            <header class="bg-white shadow-sm border-b border-gray-200">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between items-center py-4">
                        <div class="flex items-center">
                            <h1 class="text-2xl font-bold text-gray-900">📚 OpsBrain Documentation</h1>
                        </div>
                        <div class="flex items-center space-x-4">
                            <a href="/dashboard" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                                Dashboard
                            </a>
                            <a href="/dashboard/settings" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">
                                Settings
                            </a>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <!-- Navigation -->
                <div class="flex flex-wrap gap-4 mb-8">
                    <button onclick="scrollToSection('getting-started')" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                        Getting Started
                    </button>
                    <button onclick="scrollToSection('dashboard')" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg">
                        Dashboard
                    </button>
                    <button onclick="scrollToSection('slack-integration')" class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg">
                        Slack Integration
                    </button>
                    <button onclick="scrollToSection('configuration')" class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg">
                        Configuration
                    </button>
                    <button onclick="scrollToSection('api-reference')" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg">
                        API Reference
                    </button>
                </div>

                <!-- Getting Started -->
                <section id="getting-started" class="mb-12">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-3xl font-bold text-gray-900 mb-6">🚀 Getting Started</h2>
                        
                        <div class="space-y-6">
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">What is OpsBrain?</h3>
                                <p class="text-gray-600 mb-4">OpsBrain is your AI-powered CEO operator assistant that helps streamline business operations, manage tasks, track goals, and provide strategic insights. It integrates with Slack, Notion, and other tools to provide a comprehensive business management solution.</p>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">🎯 Key Features</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div class="border border-gray-200 rounded-lg p-4">
                                        <h4 class="font-semibold text-blue-600 mb-2">📊 CEO Dashboard</h4>
                                        <p class="text-sm text-gray-600">Real-time metrics, task management, and business goal tracking in one central location.</p>
                                    </div>
                                    <div class="border border-gray-200 rounded-lg p-4">
                                        <h4 class="font-semibold text-green-600 mb-2">🤖 AI Assistant</h4>
                                        <p class="text-sm text-gray-600">Intelligent responses, strategic advice, and automated task generation via Slack integration.</p>
                                    </div>
                                    <div class="border border-gray-200 rounded-lg p-4">
                                        <h4 class="font-semibold text-purple-600 mb-2">📋 Task Management</h4>
                                        <p class="text-sm text-gray-600">Notion integration for seamless task creation, tracking, and completion workflows.</p>
                                    </div>
                                    <div class="border border-gray-200 rounded-lg p-4">
                                        <h4 class="font-semibold text-red-600 mb-2">⚙️ Configuration</h4>
                                        <p class="text-sm text-gray-600">Database-backed configuration system with categories, validation, and import/export capabilities.</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">🏁 Quick Setup</h3>
                                <div class="bg-gray-50 rounded-lg p-4">
                                    <ol class="list-decimal list-inside space-y-2 text-gray-700">
                                        <li><strong>Access the Dashboard:</strong> Navigate to <code class="bg-gray-200 px-1 rounded">/dashboard</code> to view your CEO operator dashboard</li>
                                        <li><strong>Configure Settings:</strong> Go to <code class="bg-gray-200 px-1 rounded">/dashboard/settings</code> to set up your API keys and preferences</li>
                                        <li><strong>Set Up Slack:</strong> Add your Slack Bot Token and Signing Secret in the Slack configuration category</li>
                                        <li><strong>Configure Notion:</strong> Add your Notion API Key and Database ID for task management</li>
                                        <li><strong>Start Using:</strong> Begin interacting with your AI assistant via Slack commands like <code class="bg-gray-200 px-1 rounded">/ai help</code></li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Dashboard Section -->
                <section id="dashboard" class="mb-12">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-3xl font-bold text-gray-900 mb-6">📊 Dashboard Guide</h2>
                        
                        <div class="space-y-6">
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Dashboard Overview</h3>
                                <p class="text-gray-600 mb-4">The CEO Operator Dashboard provides a comprehensive view of your business operations with real-time metrics and quick action buttons.</p>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">📈 Metrics Cards</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div class="border-l-4 border-blue-500 pl-4 py-2">
                                        <h4 class="font-semibold text-blue-600">Total Active Tasks</h4>
                                        <p class="text-sm text-gray-600">Shows the total number of active tasks across all business areas with weekly completion count.</p>
                                    </div>
                                    <div class="border-l-4 border-red-500 pl-4 py-2">
                                        <h4 class="font-semibold text-red-600">High Priority Tasks</h4>
                                        <p class="text-sm text-gray-600">Critical tasks requiring immediate attention with calculated tasks per hour capacity.</p>
                                    </div>
                                    <div class="border-l-4 border-yellow-500 pl-4 py-2">
                                        <h4 class="font-semibold text-yellow-600">Weekly Hours</h4>
                                        <p class="text-sm text-gray-600">Configured available hours per week for high-priority task execution.</p>
                                    </div>
                                    <div class="border-l-4 border-green-500 pl-4 py-2">
                                        <h4 class="font-semibold text-green-600">Revenue Pipeline</h4>
                                        <p class="text-sm text-gray-600">Calculated revenue potential based on active sales goals and progress.</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">⚡ Quick Actions</h3>
                                <div class="space-y-3">
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                                        <div>
                                            <h4 class="font-semibold">Generate Weekly Plan</h4>
                                            <p class="text-sm text-gray-600">Creates a strategic weekly plan based on your business goals and current priorities</p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                        <div>
                                            <h4 class="font-semibold">Midweek Check-in</h4>
                                            <p class="text-sm text-gray-600">Generates a midweek progress review with actionable recommendations</p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                        <div>
                                            <h4 class="font-semibold">Friday Retrospective</h4>
                                            <p class="text-sm text-gray-600">Creates a comprehensive weekly retrospective with insights and next steps</p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
                                        <div>
                                            <h4 class="font-semibold">View Analytics</h4>
                                            <p class="text-sm text-gray-600">Displays detailed task analytics with priority, status, and area breakdowns</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Slack Integration -->
                <section id="slack-integration" class="mb-12">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-3xl font-bold text-gray-900 mb-6">💬 Slack Integration</h2>
                        
                        <div class="space-y-6">
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Available Commands</h3>
                                <div class="bg-gray-50 rounded-lg p-4">
                                    <div class="space-y-3">
                                        <div>
                                            <code class="bg-gray-200 px-2 py-1 rounded">/ai help</code>
                                            <span class="ml-2 text-gray-600">- Show available commands and features</span>
                                        </div>
                                        <div>
                                            <code class="bg-gray-200 px-2 py-1 rounded">/ai dashboard</code>
                                            <span class="ml-2 text-gray-600">- Get dashboard summary and metrics</span>
                                        </div>
                                        <div>
                                            <code class="bg-gray-200 px-2 py-1 rounded">/ai [your question]</code>
                                            <span class="ml-2 text-gray-600">- Ask any business or strategic question</span>
                                        </div>
                                        <div>
                                            <code class="bg-gray-200 px-2 py-1 rounded">/ai create task: [task description]</code>
                                            <span class="ml-2 text-gray-600">- Create a new task in Notion</span>
                                        </div>
                                        <div>
                                            <code class="bg-gray-200 px-2 py-1 rounded">/ai create goal: [goal description]</code>
                                            <span class="ml-2 text-gray-600">- Create a new business goal</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">🎯 CEO Functions</h3>
                                <div class="space-y-3">
                                    <div>
                                        <h4 class="font-semibold text-blue-600">Weekly Planning</h4>
                                        <p class="text-sm text-gray-600">Automatically generates strategic weekly plans based on your business goals and current task priorities.</p>
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-yellow-600">Progress Tracking</h4>
                                        <p class="text-sm text-gray-600">Provides midweek check-ins and Friday retrospectives to keep you on track with your objectives.</p>
                                    </div>
                                    <div>
                                        <h4 class="font-semibold text-green-600">Strategic Insights</h4>
                                        <p class="text-sm text-gray-600">Offers AI-powered insights and recommendations based on your business data and goals.</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">⚙️ Setup Instructions</h3>
                                <div class="bg-blue-50 rounded-lg p-4">
                                    <ol class="list-decimal list-inside space-y-2 text-gray-700">
                                        <li>Create a Slack App in your workspace</li>
                                        <li>Configure OAuth & Permissions with required scopes</li>
                                        <li>Add your Bot User OAuth Token to the configuration</li>
                                        <li>Set up Event Subscriptions pointing to your deployment URL</li>
                                        <li>Configure Slash Commands with your app's webhook URL</li>
                                        <li>Install the app to your workspace</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Configuration -->
                <section id="configuration" class="mb-12">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-3xl font-bold text-gray-900 mb-6">⚙️ Configuration</h2>
                        
                        <div class="space-y-6">
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Configuration Categories</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div class="border-l-4 border-blue-500 pl-4">
                                        <h4 class="font-semibold text-blue-600">General</h4>
                                        <p class="text-sm text-gray-600">Basic application settings and preferences</p>
                                    </div>
                                    <div class="border-l-4 border-green-500 pl-4">
                                        <h4 class="font-semibold text-green-600">API</h4>
                                        <p class="text-sm text-gray-600">API keys and external service configurations</p>
                                    </div>
                                    <div class="border-l-4 border-purple-500 pl-4">
                                        <h4 class="font-semibold text-purple-600">Slack</h4>
                                        <p class="text-sm text-gray-600">Slack integration settings and tokens</p>
                                    </div>
                                    <div class="border-l-4 border-indigo-500 pl-4">
                                        <h4 class="font-semibold text-indigo-600">Notion</h4>
                                        <p class="text-sm text-gray-600">Notion API configuration and database IDs</p>
                                    </div>
                                    <div class="border-l-4 border-red-500 pl-4">
                                        <h4 class="font-semibold text-red-600">OpenAI</h4>
                                        <p class="text-sm text-gray-600">AI model settings and API configurations</p>
                                    </div>
                                    <div class="border-l-4 border-yellow-500 pl-4">
                                        <h4 class="font-semibold text-yellow-600">Dashboard</h4>
                                        <p class="text-sm text-gray-600">Dashboard display preferences and metrics</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">🔧 Configuration Features</h3>
                                <div class="space-y-3">
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                        <span>Validation: Automatic validation of configuration values</span>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                                        <span>Caching: In-memory caching for improved performance</span>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
                                        <span>Import/Export: JSON-based configuration backup and restore</span>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                                        <span>Categories: Organized configuration management</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- API Reference -->
                <section id="api-reference" class="mb-12">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-3xl font-bold text-gray-900 mb-6">🔌 API Reference</h2>
                        
                        <div class="space-y-6">
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Dashboard Endpoints</h3>
                                <div class="space-y-4">
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-green-500 text-white px-2 py-1 rounded text-xs">GET</span>
                                            <code class="font-mono">/dashboard/api/metrics</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Returns dashboard metrics including task counts, revenue pipeline, and weekly hours.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-green-500 text-white px-2 py-1 rounded text-xs">GET</span>
                                            <code class="font-mono">/dashboard/api/tasks</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Returns task summary with priority, status, area, and impact information.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-green-500 text-white px-2 py-1 rounded text-xs">GET</span>
                                            <code class="font-mono">/dashboard/api/goals</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Returns business goals from the database with progress tracking.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-green-500 text-white px-2 py-1 rounded text-xs">GET</span>
                                            <code class="font-mono">/dashboard/api/analytics</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Returns comprehensive task analytics with priority, status, and area breakdowns.</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Generation Endpoints</h3>
                                <div class="space-y-4">
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">POST</span>
                                            <code class="font-mono">/dashboard/api/generate/weekly-plan</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Generates a CEO weekly plan based on business brain configuration and current priorities.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">POST</span>
                                            <code class="font-mono">/dashboard/api/generate/midweek-nudge</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Creates a midweek check-in with progress review and recommendations.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">POST</span>
                                            <code class="font-mono">/dashboard/api/generate/friday-retro</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Generates a comprehensive Friday retrospective with weekly insights.</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-3">Configuration Endpoints</h3>
                                <div class="space-y-4">
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-green-500 text-white px-2 py-1 rounded text-xs">GET</span>
                                            <code class="font-mono">/dashboard/api/config/export</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Exports all or category-specific configurations as JSON.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">POST</span>
                                            <code class="font-mono">/dashboard/api/config/import</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Imports configuration from JSON with validation and overwrite options.</p>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center space-x-2 mb-2">
                                            <span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">POST</span>
                                            <code class="font-mono">/dashboard/api/config/update</code>
                                        </div>
                                        <p class="text-sm text-gray-600">Updates individual configuration values with validation.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>

        <script>
            function scrollToSection(sectionId) {
                document.getElementById(sectionId).scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=docs_html)

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

#!/usr/bin/env python3
"""
CEO Operator Dashboard
A comprehensive dashboard for monitoring tasks, weekly updates, and system performance.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import our existing modules
from main import (
    fetch_open_tasks,
    business_goals,
    create_notion_task,
    load_business_brain,
    generate_ceo_weekly_plan,
    generate_midweek_nudge,
    generate_friday_retro
)
from ceo_scheduler import CEOScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """Configuration for dashboard settings"""
    weekly_hours: int = 5
    max_weekly_hours: int = 20
    auto_weekly_plan: bool = True
    auto_midweek_nudge: bool = True
    auto_friday_retro: bool = True
    slack_channel: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DashboardConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

class ConfigManager:
    """Manages dashboard configuration persistence"""
    
    def __init__(self, config_file: str = "dashboard_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> DashboardConfig:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return DashboardConfig.from_dict(data)
            else:
                # Create default config file
                default_config = DashboardConfig()
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading dashboard config: {e}")
            return DashboardConfig()
    
    def save_config(self, config: DashboardConfig) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            logger.info(f"Dashboard configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving dashboard config: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Update specific configuration values"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            return self.save_config(self.config)
        except Exception as e:
            logger.error(f"Error updating dashboard config: {e}")
            return False

@dataclass
class DashboardMetrics:
    """Metrics for dashboard display"""
    total_tasks: int
    high_priority_tasks: int
    completed_this_week: int
    revenue_pipeline: float
    weekly_hours_available: int
    tasks_per_hour: float

@dataclass
class WeeklyUpdate:
    """Weekly update data structure"""
    week_start: str
    update_type: str  # 'plan', 'nudge', 'retro'
    content: str
    tasks_assigned: List[str]
    priority_focus: str
    created_at: str

class CEOOperatorDashboard:
    """Main dashboard class for CEO Operator system"""
    
    def __init__(self):
        self.business_brain = load_business_brain()
        self.config_manager = ConfigManager()
        self.weekly_hours = self.config_manager.config.weekly_hours
        self.max_weekly_hours = self.config_manager.config.max_weekly_hours
        self.scheduler = CEOScheduler()
        
        # Sync scheduler config with dashboard config
        self.scheduler.update_schedule_config(
            weekly_hours_available=self.weekly_hours,
            monday_plan=self.config_manager.config.auto_weekly_plan,
            wednesday_nudge=self.config_manager.config.auto_midweek_nudge,
            friday_retro=self.config_manager.config.auto_friday_retro,
            slack_channel=self.config_manager.config.slack_channel
        )
        
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="CEO Operator Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .priority-high {
            border-left: 4px solid #ff4444;
            padding-left: 1rem;
        }
        .priority-medium {
            border-left: 4px solid #ffaa00;
            padding-left: 1rem;
        }
        .priority-low {
            border-left: 4px solid #00aa44;
            padding-left: 1rem;
        }
        .weekly-update-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

    async def fetch_dashboard_data(self) -> Dict[str, Any]:
        """Fetch all data needed for dashboard"""
        try:
            # Fetch tasks and goals
            tasks = await fetch_open_tasks()
            goals = list(business_goals.values())
            
            # Process tasks data
            if isinstance(tasks, str):
                tasks_data = json.loads(tasks) if tasks else []
            else:
                tasks_data = tasks or []
            
            # Calculate metrics
            total_tasks = len(tasks_data)
            high_priority_tasks = sum(1 for task in tasks_data 
                                    if task.get('properties', {}).get('Priority', {}).get('select', {}).get('name') == 'High')
            
            # Estimate completed this week (mock data for now)
            completed_this_week = max(0, total_tasks // 4)  # Rough estimate
            
            # Calculate revenue pipeline from goals
            revenue_pipeline = sum(
                goal.get('target_value', 0) 
                for goal in goals 
                if goal.get('area') in ['Sales', 'Revenue']
            )
            
            metrics = DashboardMetrics(
                total_tasks=total_tasks,
                high_priority_tasks=high_priority_tasks,
                completed_this_week=completed_this_week,
                revenue_pipeline=revenue_pipeline,
                weekly_hours_available=self.weekly_hours,
                tasks_per_hour=high_priority_tasks / max(self.weekly_hours, 1)
            )
            
            return {
                'metrics': metrics,
                'tasks': tasks_data,
                'goals': goals,
                'weekly_updates': self.get_recent_weekly_updates()
            }
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return {
                'metrics': DashboardMetrics(0, 0, 0, 0.0, self.weekly_hours, 0.0),
                'tasks': [],
                'goals': [],
                'weekly_updates': []
            }

    def get_recent_weekly_updates(self) -> List[WeeklyUpdate]:
        """Get recent weekly updates (mock data for now)"""
        # In production, this would fetch from a database or file system
        mock_updates = [
            WeeklyUpdate(
                week_start=(datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d'),
                update_type='plan',
                content="Focus on lead generation and client delivery optimization this week.",
                tasks_assigned=['Setup lead magnet', 'Optimize client onboarding', 'Create sales pipeline'],
                priority_focus='Revenue Generation',
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M')
            ),
            WeeklyUpdate(
                week_start=(datetime.now() - timedelta(days=datetime.now().weekday() + 7)).strftime('%Y-%m-%d'),
                update_type='retro',
                content="Completed 8/12 high priority tasks. Strong progress on sales pipeline development.",
                tasks_assigned=['Lead magnet completed', 'Client onboarding improved', 'Sales pipeline 70% done'],
                priority_focus='Execution Excellence',
                created_at=(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
            )
        ]
        return mock_updates

    def render_metrics_overview(self, metrics: DashboardMetrics):
        """Render the main metrics overview"""
        st.header("📊 CEO Operator Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Active Tasks",
                value=metrics.total_tasks,
                delta=f"+{metrics.completed_this_week} this week"
            )
        
        with col2:
            st.metric(
                label="High Priority Tasks",
                value=metrics.high_priority_tasks,
                delta=f"{metrics.tasks_per_hour:.1f} tasks/hour available"
            )
        
        with col3:
            st.metric(
                label="Weekly Hours Available",
                value=f"{metrics.weekly_hours_available}h",
                delta=f"Max {self.max_weekly_hours}h"
            )
        
        with col4:
            st.metric(
                label="Revenue Pipeline",
                value=f"${metrics.revenue_pipeline:,.0f}",
                delta="Active goals tracking"
            )

    def render_tasks_section(self, tasks: List[Dict]):
        """Render the tasks monitoring section"""
        st.header("📋 Task Management")
        
        if not tasks:
            st.warning("No tasks found. Run the task generation script to populate your task list.")
            if st.button("Generate Comprehensive Tasks"):
                st.info("Run: `python create_tasks_fixed.py` to generate your task backlog")
            return
        
        # Filter tasks by priority
        high_priority = [t for t in tasks if t.get('properties', {}).get('Priority', {}).get('select', {}).get('name') == 'High']
        medium_priority = [t for t in tasks if t.get('properties', {}).get('Priority', {}).get('select', {}).get('name') == 'Medium']
        low_priority = [t for t in tasks if t.get('properties', {}).get('Priority', {}).get('select', {}).get('name') == 'Low']
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🔥 High Priority", "⚡ Medium Priority", "📝 Low Priority", "📊 Analytics"])
        
        with tab1:
            st.subheader(f"High Priority Tasks ({len(high_priority)})")
            self.render_priority_tasks(high_priority, "high", self.weekly_hours)
        
        with tab2:
            st.subheader(f"Medium Priority Tasks ({len(medium_priority)})")
            self.render_priority_tasks(medium_priority, "medium")
        
        with tab3:
            st.subheader(f"Low Priority Tasks ({len(low_priority)})")
            self.render_priority_tasks(low_priority, "low")
        
        with tab4:
            self.render_task_analytics(tasks)

    def render_priority_tasks(self, tasks: List[Dict], priority_level: str, weekly_hours: int = None):
        """Render tasks for a specific priority level"""
        if not tasks:
            st.info(f"No {priority_level} priority tasks found.")
            return
        
        # Show weekly capacity for high priority tasks
        if priority_level == "high" and weekly_hours:
            estimated_hours_needed = len(tasks) * 0.5  # Assume 30min per task
            st.info(f"📅 **Weekly Capacity**: {weekly_hours}h available | ~{estimated_hours_needed:.1f}h needed for {len(tasks)} tasks")
            
            if estimated_hours_needed > weekly_hours:
                st.warning(f"⚠️ You have {estimated_hours_needed - weekly_hours:.1f}h more tasks than time available. Consider deferring some tasks.")
        
        for i, task in enumerate(tasks):
            with st.expander(f"{task.get('properties', {}).get('Task', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled Task')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Task details
                    area = task.get('properties', {}).get('Area', {}).get('select', {}).get('name', 'General')
                    impact = task.get('properties', {}).get('Impact', {}).get('select', {}).get('name', 'Unknown')
                    
                    st.write(f"**Area**: {area}")
                    st.write(f"**Impact**: {impact}")
                    
                    # Description if available
                    description = task.get('properties', {}).get('Description', {})
                    if description and description.get('rich_text'):
                        desc_text = description['rich_text'][0].get('text', {}).get('content', '')
                        if desc_text:
                            st.write(f"**Description**: {desc_text}")
                
                with col2:
                    if st.button(f"Mark Complete", key=f"complete_{i}_{priority_level}"):
                        st.success("Task marked as complete!")
                        # TODO: Implement task completion logic
                    
                    if st.button(f"Defer", key=f"defer_{i}_{priority_level}"):
                        st.info("Task deferred to next week")
                        # TODO: Implement task deferral logic

    def render_task_analytics(self, tasks: List[Dict]):
        """Render task analytics and visualizations"""
        if not tasks:
            return
        
        # Prepare data for visualization
        priority_counts = {}
        area_counts = {}
        
        for task in tasks:
            # Priority distribution
            priority = task.get('properties', {}).get('Priority', {}).get('select', {}).get('name', 'Unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Area distribution
            area = task.get('properties', {}).get('Area', {}).get('select', {}).get('name', 'Unknown')
            area_counts[area] = area_counts.get(area, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Priority distribution pie chart
            fig_priority = px.pie(
                values=list(priority_counts.values()),
                names=list(priority_counts.keys()),
                title="Tasks by Priority",
                color_discrete_map={
                    'High': '#ff4444',
                    'Medium': '#ffaa00',
                    'Low': '#00aa44'
                }
            )
            st.plotly_chart(fig_priority, use_container_width=True)
        
        with col2:
            # Area distribution bar chart
            fig_area = px.bar(
                x=list(area_counts.keys()),
                y=list(area_counts.values()),
                title="Tasks by Business Area",
                labels={'x': 'Business Area', 'y': 'Number of Tasks'}
            )
            st.plotly_chart(fig_area, use_container_width=True)

    def render_weekly_updates_section(self, weekly_updates: List[WeeklyUpdate]):
        """Render the weekly updates section"""
        st.header("📅 Weekly Updates & Planning")
        
        # Scheduled updates overview
        self.render_scheduled_updates_overview()
        
        st.markdown("---")
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Generate Weekly Plan"):
                with st.spinner("Generating weekly plan..."):
                    try:
                        update = self.scheduler.manual_trigger_update('weekly_plan')
                        if update.status == 'completed':
                            st.success("Weekly plan generated!")
                            st.text_area("Weekly Plan", update.content, height=200)
                        else:
                            st.error(f"Error: {update.content}")
                    except Exception as e:
                        st.error(f"Error generating weekly plan: {e}")
        
        with col2:
            if st.button("💡 Midweek Check-in"):
                with st.spinner("Generating midweek nudge..."):
                    try:
                        update = self.scheduler.manual_trigger_update('midweek_nudge')
                        if update.status == 'completed':
                            st.success("Midweek check-in generated!")
                            st.text_area("Midweek Nudge", update.content, height=200)
                        else:
                            st.error(f"Error: {update.content}")
                    except Exception as e:
                        st.error(f"Error generating midweek nudge: {e}")
        
        with col3:
            if st.button("🎉 Friday Retrospective"):
                with st.spinner("Generating weekly retrospective..."):
                    try:
                        update = self.scheduler.manual_trigger_update('friday_retro')
                        if update.status == 'completed':
                            st.success("Weekly retrospective generated!")
                            st.text_area("Friday Retro", update.content, height=200)
                        else:
                            st.error(f"Error: {update.content}")
                    except Exception as e:
                        st.error(f"Error generating retrospective: {e}")
        
        # Show recent updates
        st.subheader("Recent Weekly Updates")
        
        # Get recent updates from scheduler
        recent_scheduler_updates = self.scheduler.get_recent_updates(5)
        
        if recent_scheduler_updates:
            for update in recent_scheduler_updates:
                status_color = {
                    'completed': '🟢',
                    'pending': '🟡', 
                    'failed': '🔴'
                }.get(update.status, '⚪')
                
                with st.expander(f"{status_color} {update.update_type.replace('_', ' ').title()} - {update.update_id}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if update.content:
                            st.text_area("Content", update.content, height=150, disabled=True)
                        else:
                            st.info("No content available")
                    
                    with col2:
                        st.write(f"**Status**: {update.status}")
                        st.write(f"**Created**: {update.created_at}")
                        if update.completed_at:
                            st.write(f"**Completed**: {update.completed_at}")
        
        # Fallback to mock data if no scheduler updates
        if not recent_scheduler_updates:
            for update in weekly_updates:
                with st.container():
                    st.markdown(f"""
                    <div class="weekly-update-card">
                        <h4>📋 {update.update_type.title()} - Week of {update.week_start}</h4>
                        <p><strong>Focus:</strong> {update.priority_focus}</p>
                        <p>{update.content}</p>
                        <small>Created: {update.created_at}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_scheduled_updates_overview(self):
        """Render overview of scheduled updates"""
        st.subheader("⏰ Scheduled Updates")
        
        # Get upcoming scheduled updates
        upcoming_updates = self.scheduler.get_next_scheduled_updates()
        
        if upcoming_updates:
            col1, col2, col3 = st.columns(3)
            
            for i, update in enumerate(upcoming_updates[:3]):
                col = [col1, col2, col3][i]
                
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h5>{update['type']}</h5>
                        <p><strong>{update['day']} @ {update['time']}</strong></p>
                        <small>{update['description']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No scheduled updates configured. Enable them in Settings.")

    def render_system_settings(self):
        """Render system settings and configuration"""
        st.header("⚙️ System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Time Management")
            
            # Weekly hours configuration
            new_weekly_hours = st.slider(
                "Weekly Hours Available",
                min_value=2,
                max_value=20,
                value=self.weekly_hours,
                help="How many hours per week do you have for high-priority tasks?"
            )
            
            # Scheduling preferences
            st.subheader("Scheduling")
            schedule_weekly_plan = st.checkbox(
                "Auto-generate weekly plans", 
                value=self.config_manager.config.auto_weekly_plan
            )
            schedule_midweek_nudge = st.checkbox(
                "Send midweek check-ins", 
                value=self.config_manager.config.auto_midweek_nudge
            )
            schedule_friday_retro = st.checkbox(
                "Generate Friday retrospectives", 
                value=self.config_manager.config.auto_friday_retro
            )
            
            # Slack channel configuration
            slack_channel = st.text_input(
                "Slack Channel (optional)",
                value=self.config_manager.config.slack_channel or "",
                help="Channel ID where automated updates will be posted"
            )
            
            # Save configuration button
            if st.button("💾 Save Configuration"):
                success = self.config_manager.update_config(
                    weekly_hours=new_weekly_hours,
                    auto_weekly_plan=schedule_weekly_plan,
                    auto_midweek_nudge=schedule_midweek_nudge,
                    auto_friday_retro=schedule_friday_retro,
                    slack_channel=slack_channel if slack_channel else None
                )
                
                if success:
                    self.weekly_hours = new_weekly_hours
                    
                    # Sync with scheduler
                    self.scheduler.update_schedule_config(
                        weekly_hours_available=new_weekly_hours,
                        monday_plan=schedule_weekly_plan,
                        wednesday_nudge=schedule_midweek_nudge,
                        friday_retro=schedule_friday_retro,
                        slack_channel=slack_channel if slack_channel else None
                    )
                    
                    st.success("✅ Configuration saved successfully!")
                    st.info(f"📊 Weekly hours: {new_weekly_hours}h")
                    st.info(f"⏰ Automated updates: {'Enabled' if any([schedule_weekly_plan, schedule_midweek_nudge, schedule_friday_retro]) else 'Disabled'}")
                else:
                    st.error("❌ Failed to save configuration")
        
        with col2:
            st.subheader("Business Brain Status")
            
            if self.business_brain:
                st.success("✅ Business brain loaded successfully")
                st.write(f"**Company**: {self.business_brain.get('company_name', 'Unknown')}")
                st.write(f"**Stage**: {self.business_brain.get('company_stage', 'Unknown')}")
                st.write(f"**North Star**: {self.business_brain.get('north_star_goal', 'Not set')}")
            else:
                st.error("❌ Business brain not loaded")
                if st.button("Reload Business Brain"):
                    self.business_brain = load_business_brain()
                    st.rerun()
            
            st.subheader("Database Connections")
            
            # Check environment variables
            notion_token = os.getenv('NOTION_TOKEN')
            notion_db = os.getenv('NOTION_DATABASE_ID')
            
            if notion_token and notion_db:
                st.success("✅ Notion integration configured")
            else:
                st.warning("⚠️ Notion integration not fully configured")
            
            slack_token = os.getenv('SLACK_BOT_TOKEN')
            if slack_token:
                st.success("✅ Slack integration configured")
            else:
                st.warning("⚠️ Slack integration not configured")

    def render_sidebar(self):
        """Render the sidebar navigation"""
        st.sidebar.title("🎯 CEO Operator")
        st.sidebar.markdown("---")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["Dashboard", "Tasks", "Weekly Updates", "Settings"],
            index=0
        )
        
        st.sidebar.markdown("---")
        
        # Quick stats in sidebar
        st.sidebar.subheader("Quick Stats")
        try:
            # Get basic metrics
            tasks_data = asyncio.run(fetch_open_tasks())
            if isinstance(tasks_data, str):
                tasks_data = json.loads(tasks_data) if tasks_data else []
            
            total_tasks = len(tasks_data) if tasks_data else 0
            st.sidebar.metric("Active Tasks", total_tasks)
            st.sidebar.metric("Weekly Hours", f"{self.weekly_hours}h")
            
        except Exception as e:
            st.sidebar.error("Unable to fetch stats")
        
        return page

    async def run_dashboard(self):
        """Main dashboard application"""
        self.setup_page_config()
        
        # Render sidebar and get current page
        current_page = self.render_sidebar()
        
        # Fetch dashboard data
        data = await self.fetch_dashboard_data()
        
        # Render the appropriate page
        if current_page == "Dashboard":
            self.render_metrics_overview(data['metrics'])
            st.markdown("---")
            
            # Recent activity summary
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔥 Priority Focus")
                high_priority_count = data['metrics'].high_priority_tasks
                if high_priority_count > 0:
                    st.success(f"You have {high_priority_count} high-priority tasks that fit in your {self.weekly_hours}h weekly schedule.")
                    if st.button("View High Priority Tasks"):
                        st.rerun()  # Will switch to tasks view
                else:
                    st.info("No high-priority tasks found. Great job staying on top of things!")
            
            with col2:
                st.subheader("📈 This Week's Progress")
                completed = data['metrics'].completed_this_week
                if completed > 0:
                    st.success(f"Completed {completed} tasks this week!")
                else:
                    st.info("Track your progress by marking tasks complete")
        
        elif current_page == "Tasks":
            self.render_tasks_section(data['tasks'])
        
        elif current_page == "Weekly Updates":
            self.render_weekly_updates_section(data['weekly_updates'])
        
        elif current_page == "Settings":
            self.render_system_settings()

def main():
    """Main entry point for the dashboard"""
    dashboard = CEOOperatorDashboard()
    asyncio.run(dashboard.run_dashboard())

if __name__ == "__main__":
    main()

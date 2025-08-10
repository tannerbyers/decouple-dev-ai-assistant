#!/usr/bin/env python3
"""
CEO Operator Scheduler
Handles automated weekly updates, task generation, and scheduled operations for the CEO Operator system.
"""

import os
import json
import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

# Import our existing modules
from main import (
    fetch_open_tasks,
    business_goals,
    create_notion_task,
    load_business_brain,
    generate_weekly_candidates,
    generate_ceo_weekly_plan,
    generate_midweek_nudge,
    generate_friday_retro,
    load_task_matrix
)

# Simple slack message posting function
async def post_slack_message(channel: str, message: str) -> bool:
    """Post a message to Slack channel - placeholder implementation"""
    try:
        # This would need proper Slack client setup
        # For now, just log the message
        logger.info(f"Would post to Slack #{channel}: {message[:100]}...")
        return True
    except Exception as e:
        logger.error(f"Error posting to Slack: {e}")
        return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ceo_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScheduledUpdate:
    """Data structure for scheduled updates"""
    update_id: str
    update_type: str  # 'weekly_plan', 'midweek_nudge', 'friday_retro'
    scheduled_time: str
    status: str  # 'pending', 'completed', 'failed'
    content: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class WeeklySchedule:
    """Weekly schedule configuration"""
    monday_plan: bool = True
    wednesday_nudge: bool = True
    friday_retro: bool = True
    weekly_hours_available: int = 5
    auto_generate_tasks: bool = False
    slack_channel: Optional[str] = None

class CEOScheduler:
    """Main scheduler class for CEO Operator automated operations"""
    
    def __init__(self, config_file: str = "scheduler_config.json"):
        self.config_file = config_file
        self.schedule_config = self.load_schedule_config()
        self.business_brain = load_business_brain()
        self.task_matrix = load_task_matrix()
        self.updates_history: List[ScheduledUpdate] = []
        self.running = False
        
        # Ensure log directory exists
        Path("logs").mkdir(exist_ok=True)
        
    def load_schedule_config(self) -> WeeklySchedule:
        """Load scheduling configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    return WeeklySchedule(**config_data)
            else:
                # Create default config
                default_config = WeeklySchedule()
                self.save_schedule_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading schedule config: {e}")
            return WeeklySchedule()
    
    def save_schedule_config(self, config: WeeklySchedule):
        """Save scheduling configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            logger.info(f"Schedule configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving schedule config: {e}")
    
    def update_schedule_config(self, **kwargs):
        """Update schedule configuration"""
        for key, value in kwargs.items():
            if hasattr(self.schedule_config, key):
                setattr(self.schedule_config, key, value)
        self.save_schedule_config(self.schedule_config)
        logger.info(f"Schedule config updated: {kwargs}")
    
    async def generate_weekly_plan(self) -> ScheduledUpdate:
        """Generate and post weekly plan"""
        update_id = f"weekly_plan_{datetime.now().strftime('%Y%m%d')}"
        update = ScheduledUpdate(
            update_id=update_id,
            update_type='weekly_plan',
            scheduled_time=datetime.now().isoformat(),
            status='pending',
            created_at=datetime.now().isoformat()
        )
        
        try:
            logger.info("Generating weekly plan...")
            
            # Generate the weekly plan
            plan_content = generate_ceo_weekly_plan(
                business_brain=self.business_brain,
                available_hours=self.schedule_config.weekly_hours_available
            )
            
            # Create comprehensive update message
            weekly_summary = await self.get_weekly_summary()
            
            full_message = f"""🎯 **CEO WEEKLY PLAN** - Week of {datetime.now().strftime('%B %d, %Y')}
            
**Available Time**: {self.schedule_config.weekly_hours_available} hours this week

**Weekly Summary**:
{weekly_summary}

**Strategic Plan**:
{plan_content}

---
Generated by CEO Operator at {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            # Post to Slack if configured
            if self.schedule_config.slack_channel:
                await post_slack_message(self.schedule_config.slack_channel, full_message)
            
            # Save update
            update.content = full_message
            update.status = 'completed'
            update.completed_at = datetime.now().isoformat()
            
            logger.info("Weekly plan generated and posted successfully")
            
        except Exception as e:
            logger.error(f"Error generating weekly plan: {e}")
            update.status = 'failed'
            update.content = f"Error: {str(e)}"
        
        self.updates_history.append(update)
        return update
    
    async def generate_midweek_nudge(self) -> ScheduledUpdate:
        """Generate and post midweek check-in"""
        update_id = f"midweek_nudge_{datetime.now().strftime('%Y%m%d')}"
        update = ScheduledUpdate(
            update_id=update_id,
            update_type='midweek_nudge',
            scheduled_time=datetime.now().isoformat(),
            status='pending',
            created_at=datetime.now().isoformat()
        )
        
        try:
            logger.info("Generating midweek nudge...")
            
            # Generate the midweek nudge
            nudge_content = generate_midweek_nudge(business_brain=self.business_brain)
            
            # Add progress tracking
            progress_update = await self.get_midweek_progress()
            
            full_message = f"""💡 **MIDWEEK CHECK-IN** - {datetime.now().strftime('%A, %B %d')}
            
**Progress Update**:
{progress_update}

**Midweek Guidance**:
{nudge_content}

---
Stay focused on your high-priority tasks! 🚀
            """
            
            # Post to Slack if configured
            if self.schedule_config.slack_channel:
                await post_slack_message(self.schedule_config.slack_channel, full_message)
            
            # Save update
            update.content = full_message
            update.status = 'completed'
            update.completed_at = datetime.now().isoformat()
            
            logger.info("Midweek nudge generated and posted successfully")
            
        except Exception as e:
            logger.error(f"Error generating midweek nudge: {e}")
            update.status = 'failed'
            update.content = f"Error: {str(e)}"
        
        self.updates_history.append(update)
        return update
    
    async def generate_friday_retro(self) -> ScheduledUpdate:
        """Generate and post Friday retrospective"""
        update_id = f"friday_retro_{datetime.now().strftime('%Y%m%d')}"
        update = ScheduledUpdate(
            update_id=update_id,
            update_type='friday_retro',
            scheduled_time=datetime.now().isoformat(),
            status='pending',
            created_at=datetime.now().isoformat()
        )
        
        try:
            logger.info("Generating Friday retrospective...")
            
            # Generate the retrospective
            retro_content = generate_friday_retro(business_brain=self.business_brain)
            
            # Add weekly accomplishments
            weekly_accomplishments = await self.get_weekly_accomplishments()
            
            full_message = f"""🎉 **FRIDAY RETROSPECTIVE** - Week Ending {datetime.now().strftime('%B %d, %Y')}
            
**This Week's Accomplishments**:
{weekly_accomplishments}

**Weekly Reflection**:
{retro_content}

**Preparation for Next Week**:
✅ Review completed tasks
✅ Plan Monday's priorities  
✅ Set weekly goals

---
Great work this week! Time to recharge for the next one. 💪
            """
            
            # Post to Slack if configured
            if self.schedule_config.slack_channel:
                await post_slack_message(self.schedule_config.slack_channel, full_message)
            
            # Save update
            update.content = full_message
            update.status = 'completed'
            update.completed_at = datetime.now().isoformat()
            
            logger.info("Friday retrospective generated and posted successfully")
            
        except Exception as e:
            logger.error(f"Error generating Friday retrospective: {e}")
            update.status = 'failed'
            update.content = f"Error: {str(e)}"
        
        self.updates_history.append(update)
        return update
    
    async def get_weekly_summary(self) -> str:
        """Get weekly summary of tasks and goals"""
        try:
            tasks = await fetch_open_tasks()
            if isinstance(tasks, str):
                tasks_data = json.loads(tasks) if tasks else []
            else:
                tasks_data = tasks or []
            
            total_tasks = len(tasks_data)
            high_priority = sum(1 for t in tasks_data 
                              if t.get('properties', {}).get('Priority', {}).get('select', {}).get('name') == 'High')
            
            goals = business_goals
            active_goals = len([g for g in goals if g.get('status') == 'active'])
            
            return f"""• {total_tasks} active tasks ({high_priority} high priority)
• {active_goals} active business goals
• {self.schedule_config.weekly_hours_available}h available this week"""
            
        except Exception as e:
            logger.error(f"Error getting weekly summary: {e}")
            return "Unable to fetch weekly summary"
    
    async def get_midweek_progress(self) -> str:
        """Get midweek progress update"""
        try:
            # This would ideally track actual completion status
            # For now, provide motivational progress update
            day_of_week = datetime.now().strftime('%A')
            week_progress = (datetime.now().weekday() + 1) / 7 * 100
            
            return f"""• It's {day_of_week} - you're {week_progress:.0f}% through the week
• Stay focused on your high-priority tasks
• Remember your weekly goal of {self.schedule_config.weekly_hours_available} productive hours"""
            
        except Exception as e:
            logger.error(f"Error getting midweek progress: {e}")
            return "Midweek progress tracking unavailable"
    
    async def get_weekly_accomplishments(self) -> str:
        """Get weekly accomplishments summary"""
        try:
            # This would ideally track completed tasks
            # For now, provide encouragement and weekly wrap-up
            return f"""• Maintained focus on strategic priorities
• Made progress on revenue-generating activities  
• Completed key tasks within {self.schedule_config.weekly_hours_available}h weekly time budget
• Stayed aligned with business goals and north star"""
            
        except Exception as e:
            logger.error(f"Error getting weekly accomplishments: {e}")
            return "Weekly accomplishments summary unavailable"
    
    def setup_schedule(self):
        """Setup the weekly schedule"""
        schedule.clear()  # Clear any existing schedules
        
        # Monday: Weekly Plan (9:00 AM)
        if self.schedule_config.monday_plan:
            schedule.every().monday.at("09:00").do(self.run_async_job, self.generate_weekly_plan)
            logger.info("Scheduled: Monday weekly plan at 9:00 AM")
        
        # Wednesday: Midweek Nudge (2:00 PM)
        if self.schedule_config.wednesday_nudge:
            schedule.every().wednesday.at("14:00").do(self.run_async_job, self.generate_midweek_nudge)
            logger.info("Scheduled: Wednesday midweek nudge at 2:00 PM")
        
        # Friday: Retrospective (5:00 PM)
        if self.schedule_config.friday_retro:
            schedule.every().friday.at("17:00").do(self.run_async_job, self.generate_friday_retro)
            logger.info("Scheduled: Friday retrospective at 5:00 PM")
        
        logger.info("Weekly schedule configured successfully")
    
    def run_async_job(self, job_func):
        """Run async job in scheduler context"""
        try:
            asyncio.run(job_func())
        except Exception as e:
            logger.error(f"Error running scheduled job: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.setup_schedule()
        self.running = True
        
        def run_scheduler():
            logger.info("CEO Scheduler started")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("CEO Scheduler stopped")
    
    def get_next_scheduled_updates(self) -> List[Dict[str, str]]:
        """Get list of next scheduled updates"""
        try:
            upcoming = []
            
            if self.schedule_config.monday_plan:
                upcoming.append({
                    'type': 'Weekly Plan',
                    'day': 'Monday',
                    'time': '9:00 AM',
                    'description': 'Strategic weekly planning and task prioritization'
                })
            
            if self.schedule_config.wednesday_nudge:
                upcoming.append({
                    'type': 'Midweek Check-in', 
                    'day': 'Wednesday',
                    'time': '2:00 PM',
                    'description': 'Progress review and motivation boost'
                })
            
            if self.schedule_config.friday_retro:
                upcoming.append({
                    'type': 'Friday Retrospective',
                    'day': 'Friday', 
                    'time': '5:00 PM',
                    'description': 'Weekly accomplishments and next week preparation'
                })
            
            return upcoming
            
        except Exception as e:
            logger.error(f"Error getting scheduled updates: {e}")
            return []
    
    def get_recent_updates(self, limit: int = 10) -> List[ScheduledUpdate]:
        """Get recent scheduled updates"""
        return sorted(
            self.updates_history, 
            key=lambda x: x.created_at or '', 
            reverse=True
        )[:limit]
    
    def manual_trigger_update(self, update_type: str) -> ScheduledUpdate:
        """Manually trigger a scheduled update"""
        if update_type == 'weekly_plan':
            return asyncio.run(self.generate_weekly_plan())
        elif update_type == 'midweek_nudge':
            return asyncio.run(self.generate_midweek_nudge())
        elif update_type == 'friday_retro':
            return asyncio.run(self.generate_friday_retro())
        else:
            raise ValueError(f"Unknown update type: {update_type}")

def main():
    """Main entry point for the scheduler"""
    scheduler = CEOScheduler()
    
    try:
        scheduler.start_scheduler()
        
        # Keep the main thread alive
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()

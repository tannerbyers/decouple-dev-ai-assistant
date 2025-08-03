#!/usr/bin/env python3
"""
Business Goal Management System
Integrates with OpsBrain to track SMART goals and CEO activities
"""

import os
import json
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class GoalStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Goal:
    id: str
    title: str
    description: str
    category: str  # SALES, DELIVERY, PRODUCT, FINANCIAL, TEAM, PROCESS
    status: GoalStatus
    priority: Priority
    target_date: str
    progress_percentage: int
    weekly_actions: List[str]
    daily_actions: List[str]
    success_metrics: Dict[str, str]
    created_date: str
    last_updated: str
    notes: str = ""

class GoalManager:
    def __init__(self, data_file: str = "business_goals.json"):
        self.data_file = data_file
        self.goals: Dict[str, Goal] = {}
        self.load_goals()
    
    def load_goals(self):
        """Load goals from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for goal_id, goal_data in data.items():
                        goal_data['status'] = GoalStatus(goal_data['status'])
                        goal_data['priority'] = Priority(goal_data['priority'])
                        self.goals[goal_id] = Goal(**goal_data)
            except Exception as e:
                print(f"Error loading goals: {e}")
                self.goals = {}
    
    def save_goals(self):
        """Save goals to JSON file"""
        data = {}
        for goal_id, goal in self.goals.items():
            goal_dict = asdict(goal)
            goal_dict['status'] = goal.status.value
            goal_dict['priority'] = goal.priority.value
            data[goal_id] = goal_dict
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_goal(self, title: str, description: str, category: str, 
                   target_date: str, weekly_actions: List[str] = None,
                   daily_actions: List[str] = None, 
                   success_metrics: Dict[str, str] = None) -> str:
        """Create a new SMART goal"""
        goal_id = f"{category.lower()}_{len([g for g in self.goals.values() if g.category == category]) + 1}"
        
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            category=category,
            status=GoalStatus.NOT_STARTED,
            priority=Priority.MEDIUM,
            target_date=target_date,
            progress_percentage=0,
            weekly_actions=weekly_actions or [],
            daily_actions=daily_actions or [],
            success_metrics=success_metrics or {},
            created_date=datetime.datetime.now().isoformat(),
            last_updated=datetime.datetime.now().isoformat()
        )
        
        self.goals[goal_id] = goal
        self.save_goals()
        return goal_id
    
    def update_goal_progress(self, goal_id: str, progress: int, 
                           status: GoalStatus = None, notes: str = None):
        """Update goal progress and status"""
        if goal_id not in self.goals:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = self.goals[goal_id]
        goal.progress_percentage = min(100, max(0, progress))
        
        if status:
            goal.status = status
        elif progress == 100:
            goal.status = GoalStatus.COMPLETED
        elif progress > 0:
            goal.status = GoalStatus.IN_PROGRESS
        
        if notes:
            goal.notes += f"\n{datetime.datetime.now().strftime('%Y-%m-%d')}: {notes}"
        
        goal.last_updated = datetime.datetime.now().isoformat()
        self.save_goals()
    
    def get_weekly_actions(self, category: str = None) -> List[Dict]:
        """Get all weekly actions, optionally filtered by category"""
        actions = []
        for goal in self.goals.values():
            if category and goal.category.upper() != category.upper():
                continue
            if goal.status not in [GoalStatus.COMPLETED, GoalStatus.DEFERRED]:
                for action in goal.weekly_actions:
                    actions.append({
                        'goal_id': goal.id,
                        'goal_title': goal.title,
                        'category': goal.category,
                        'action': action,
                        'priority': goal.priority.value
                    })
        return sorted(actions, key=lambda x: x['priority'], reverse=True)
    
    def get_daily_actions(self, category: str = None) -> List[Dict]:
        """Get all daily actions, optionally filtered by category"""
        actions = []
        for goal in self.goals.values():
            if category and goal.category.upper() != category.upper():
                continue
            if goal.status not in [GoalStatus.COMPLETED, GoalStatus.DEFERRED]:
                for action in goal.daily_actions:
                    actions.append({
                        'goal_id': goal.id,
                        'goal_title': goal.title,
                        'category': goal.category,
                        'action': action,
                        'priority': goal.priority.value
                    })
        return sorted(actions, key=lambda x: x['priority'], reverse=True)
    
    def get_ceo_dashboard(self) -> Dict:
        """Generate CEO dashboard with key metrics"""
        total_goals = len(self.goals)
        completed_goals = len([g for g in self.goals.values() if g.status == GoalStatus.COMPLETED])
        in_progress_goals = len([g for g in self.goals.values() if g.status == GoalStatus.IN_PROGRESS])
        blocked_goals = len([g for g in self.goals.values() if g.status == GoalStatus.BLOCKED])
        
        # Calculate average progress by category
        category_progress = {}
        for category in ["SALES", "DELIVERY", "PRODUCT", "FINANCIAL", "TEAM", "PROCESS"]:
            category_goals = [g for g in self.goals.values() if g.category == category]
            if category_goals:
                avg_progress = sum(g.progress_percentage for g in category_goals) / len(category_goals)
                category_progress[category] = round(avg_progress, 1)
            else:
                category_progress[category] = 0
        
        # Get high priority actions for this week
        high_priority_actions = [
            action for action in self.get_weekly_actions() 
            if action['priority'] >= Priority.HIGH.value
        ]
        
        return {
            'overview': {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'in_progress_goals': in_progress_goals,
                'blocked_goals': blocked_goals,
                'completion_rate': round(completed_goals / total_goals * 100, 1) if total_goals > 0 else 0
            },
            'category_progress': category_progress,
            'high_priority_actions': high_priority_actions[:10],  # Top 10
            'generated_at': datetime.datetime.now().isoformat()
        }
    
    def research_goal_opportunities(self, category: str) -> List[str]:
        """Research and suggest new goal opportunities based on category"""
        research_prompts = {
            'SALES': [
                "Analyze current sales funnel conversion rates",
                "Research competitor pricing strategies",
                "Identify new lead generation channels",
                "Explore partnership opportunities with complementary services",
                "Review client feedback for upselling opportunities"
            ],
            'DELIVERY': [
                "Audit current project delivery times vs. estimates",
                "Identify most time-consuming manual processes",
                "Research automation tools for common tasks",
                "Analyze client satisfaction scores by project type",
                "Document knowledge gaps in team capabilities"
            ],
            'PRODUCT': [
                "Analyze OpsBrain usage patterns and pain points",
                "Research feature requests from existing users",
                "Competitive analysis of similar AI assistant tools",
                "Identify integration opportunities with popular business tools",
                "Evaluate technical debt impact on development speed"
            ],
            'FINANCIAL': [
                "Analyze profit margins by client and project type",
                "Research pricing optimization opportunities",
                "Identify cost reduction opportunities in operations",
                "Evaluate ROI on marketing and sales activities",
                "Plan cash flow scenarios for next 6 months"
            ],
            'TEAM': [
                "Assess current team capacity vs. demand",
                "Research contractor vs. employee cost-benefit analysis",
                "Identify skill gaps that limit business growth",
                "Evaluate remote work productivity metrics",
                "Plan succession strategies for key responsibilities"
            ],
            'PROCESS': [
                "Map current business processes and identify bottlenecks",
                "Research business automation opportunities",
                "Analyze time allocation across different business functions",
                "Evaluate tool stack efficiency and integration gaps",
                "Document standard operating procedures gaps"
            ]
        }
        
        return research_prompts.get(category.upper(), [])

def initialize_default_goals():
    """Initialize the goal manager with default Q1 2025 goals"""
    gm = GoalManager()
    
    # Sales & Marketing Goals
    gm.create_goal(
        title="Lead Generation Pipeline",
        description="Generate 50 qualified leads per month through content marketing",
        category="SALES",
        target_date="2025-03-31",
        weekly_actions=[
            "Plan 2 blog topics based on client conversations",
            "Write and publish first blog post",
            "Write and publish second blog post",
            "Review lead quality and engagement metrics"
        ],
        daily_actions=[
            "Share content on LinkedIn",
            "Respond to comments and engage with prospects",
            "Update CRM with new lead information"
        ],
        success_metrics={
            "monthly_leads": "50",
            "leads_per_blog_post": "15",
            "content_frequency": "2 posts/week"
        }
    )
    
    gm.create_goal(
        title="Client Acquisition",
        description="Close 3 new agency clients at $5k+/month retainer",
        category="SALES",
        target_date="2025-03-31",
        weekly_actions=[
            "Identify 5 new prospects via LinkedIn/referrals",
            "Send personalized outreach to 5 prospects",
            "Follow up with previous week's prospects",
            "Conduct 2 discovery calls with interested prospects",
            "Send proposals to qualified prospects"
        ],
        success_metrics={
            "new_clients": "3",
            "monthly_recurring_revenue": "$15000",
            "average_deal_size": "$5000"
        }
    )
    
    # Delivery & Operations Goals
    gm.create_goal(
        title="Service Standardization",
        description="Create standardized delivery process for 80% of common client requests",
        category="DELIVERY",
        target_date="2025-02-28",
        weekly_actions=[
            "Document one delivery process (2 hours)",
            "Test documented process with current client",
            "Refine process based on testing feedback"
        ],
        success_metrics={
            "processes_documented": "5",
            "time_reduction": "40%",
            "standardization_coverage": "80%"
        }
    )
    
    # Product Development Goals
    gm.create_goal(
        title="OpsBrain Enhancement",
        description="Complete 8 high-impact features from TODO.md",
        category="PRODUCT",
        target_date="2025-03-31",
        weekly_actions=[
            "Development and testing (Week 1)",
            "Deployment and documentation (Week 2)",
            "Client feedback collection and iteration planning"
        ],
        success_metrics={
            "features_completed": "8",
            "features_per_month": "2",
            "deployment_frequency": "bi-weekly"
        }
    )
    
    print("Default goals initialized successfully!")
    return gm

if __name__ == "__main__":
    # Command line interface for goal management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python goal_manager.py [init|dashboard|actions|research]")
        sys.exit(1)
    
    command = sys.argv[1]
    gm = GoalManager()
    
    if command == "init":
        gm = initialize_default_goals()
    
    elif command == "dashboard":
        dashboard = gm.get_ceo_dashboard()
        print("\n🎯 CEO DASHBOARD")
        print("=" * 50)
        print(f"Goals: {dashboard['overview']['total_goals']} total, {dashboard['overview']['completed_goals']} completed ({dashboard['overview']['completion_rate']}%)")
        print(f"In Progress: {dashboard['overview']['in_progress_goals']}, Blocked: {dashboard['overview']['blocked_goals']}")
        
        print("\n📊 CATEGORY PROGRESS")
        for category, progress in dashboard['category_progress'].items():
            print(f"{category}: {progress}%")
        
        print("\n🔥 HIGH PRIORITY ACTIONS THIS WEEK")
        for i, action in enumerate(dashboard['high_priority_actions'][:5], 1):
            print(f"{i}. [{action['category']}] {action['action']}")
    
    elif command == "actions":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        actions = gm.get_weekly_actions(category)
        
        print(f"\n📋 WEEKLY ACTIONS{' - ' + category if category else ''}")
        print("=" * 50)
        for i, action in enumerate(actions[:10], 1):
            print(f"{i}. [{action['category']}] {action['action']}")
    
    elif command == "research":
        category = sys.argv[2] if len(sys.argv) > 2 else "SALES"
        opportunities = gm.research_goal_opportunities(category)
        
        print(f"\n🔍 RESEARCH OPPORTUNITIES - {category}")
        print("=" * 50)
        for i, opportunity in enumerate(opportunities, 1):
            print(f"{i}. {opportunity}")
    
    else:
        print("Unknown command. Use: init, dashboard, actions, or research")

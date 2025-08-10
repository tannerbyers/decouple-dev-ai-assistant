from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from notion_client import Client as NotionClient
from src.trello_client import trello_client
import os, requests, json, hmac, hashlib, time, logging, datetime, subprocess
from typing import Optional, Dict, List, Tuple, Any
from notion_client.errors import APIResponseError
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import yaml
from concurrent.futures import ThreadPoolExecutor

# Initialize FastAPI application
app = FastAPI()

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")  # Main tasks database
NOTION_GOALS_DB_ID = os.getenv("NOTION_GOALS_DB_ID", NOTION_DB_ID)  # Business goals database
NOTION_CLIENTS_DB_ID = os.getenv("NOTION_CLIENTS_DB_ID")  # Client management database
NOTION_PROJECTS_DB_ID = os.getenv("NOTION_PROJECTS_DB_ID")  # Project tracking database
NOTION_METRICS_DB_ID = os.getenv("NOTION_METRICS_DB_ID")  # Business metrics database
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Setup logging with more explicit configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure logs go to stdout
    ]
)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_vars = {
    "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
    "SLACK_SIGNING_SECRET": SLACK_SIGNING_SECRET,
    "NOTION_API_KEY": NOTION_API_KEY,
    "NOTION_DB_ID": NOTION_DB_ID,
    "OPENAI_API_KEY": OPENAI_API_KEY
}

# Optional database IDs for enhanced features
optional_dbs = {
    "NOTION_GOALS_DB_ID": NOTION_GOALS_DB_ID,
    "NOTION_CLIENTS_DB_ID": NOTION_CLIENTS_DB_ID,
    "NOTION_PROJECTS_DB_ID": NOTION_PROJECTS_DB_ID,
    "NOTION_METRICS_DB_ID": NOTION_METRICS_DB_ID
}

missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars and not TEST_MODE:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Log startup info  
logger.info("Application starting up...")
logger.info(f"TEST_MODE: {TEST_MODE}")
logger.info(f"Environment variables loaded - SLACK_BOT_TOKEN: {'SET' if SLACK_BOT_TOKEN else 'NOT SET'}")
logger.info(f"Environment variables loaded - SLACK_SIGNING_SECRET: {'SET' if SLACK_SIGNING_SECRET else 'NOT SET'}")

# Initialize ChatOpenAI only if API key is available
if OPENAI_API_KEY:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4")
else:
    llm = None
    print("Warning: OPENAI_API_KEY not found in environment variables")
notion = NotionClient(auth=NOTION_API_KEY)

# Business goal management classes
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

class BusinessArea(Enum):
    SALES = "sales"
    DELIVERY = "delivery"
    PRODUCT = "product"
    FINANCIAL = "financial"
    TEAM = "team"
    PROCESS = "process"

@dataclass
class BusinessGoal:
    id: str
    title: str
    description: str
    area: BusinessArea
    status: GoalStatus
    priority: Priority
    target_date: str
    progress: int
    weekly_actions: List[str]
    daily_actions: List[str]
    success_metrics: Dict[str, str]
    created_date: str
    last_updated: str
    notes: str = ""

# In-memory goal storage (in production, use database)
business_goals: Dict[str, BusinessGoal] = {}

# Thread context management for conversation continuity
thread_contexts: Dict[str, Dict] = {}  # {"channel:thread_ts": {"messages": [...], "created_at": timestamp}}

def get_thread_context(thread_ts: Optional[str], channel: str, user_text: str) -> Dict:
    """Retrieve or create conversation context for a thread."""
    # Clean up old threads first (cleanup threads older than 24 hours)
    cleanup_old_threads()
    
    # Create thread key - use channel for non-threaded messages
    thread_key = f"{channel}:{thread_ts}" if thread_ts else channel
    
    # Get existing context or create new one
    if thread_key in thread_contexts:
        context = thread_contexts[thread_key]
        # Add new user message to existing context
        context['messages'].append(f"User: {user_text}")
        
        # Keep only last 10 messages to prevent memory bloat
        if len(context['messages']) > 10:
            context['messages'] = context['messages'][-10:]
            
        logger.info(f"Retrieved existing thread context with {len(context['messages'])} messages")
    else:
        # Create new context
        context = {
            'messages': [f"User: {user_text}"],
            'created_at': time.time()
        }
        thread_contexts[thread_key] = context
        logger.info(f"Created new thread context for key: {thread_key}")
    
    return context

def update_thread_context(thread_ts: Optional[str], channel: str, ai_response: str) -> None:
    """Update thread context with AI response and manage message history."""
    thread_key = f"{channel}:{thread_ts}" if thread_ts else channel
    
    if thread_key in thread_contexts:
        context = thread_contexts[thread_key]
        context['messages'].append(f"OpsBrain: {ai_response}")
        
        # Keep only last 10 messages to prevent memory bloat
        if len(context['messages']) > 10:
            context['messages'] = context['messages'][-10:]
            
        logger.info(f"Updated thread context with AI response. Total messages: {len(context['messages'])}")
    else:
        logger.warning(f"Attempted to update non-existent thread context: {thread_key}")

def cleanup_old_threads() -> None:
    """Remove thread conversations older than 24 hours to manage memory usage."""
    current_time = time.time()
    twenty_four_hours = 24 * 60 * 60  # 24 hours in seconds
    
    threads_to_remove = []
    for thread_key, context in thread_contexts.items():
        if current_time - context['created_at'] > twenty_four_hours:
            threads_to_remove.append(thread_key)
    
    for thread_key in threads_to_remove:
        del thread_contexts[thread_key]
        
    if threads_to_remove:
        logger.info(f"Cleaned up {len(threads_to_remove)} old thread contexts")

def load_business_goals_from_json(filename: str = "business_goals.json") -> None:
    """Load business goals from JSON file into memory."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                for goal_id, goal_data in data.items():
                    # Handle both 'area' and 'category' field names
                    area_value = goal_data.get('area') or goal_data.get('category', 'sales')
                    if isinstance(area_value, str):
                        area_value = area_value.lower()
                    
                    # Convert string enums back to enum objects
                    goal_data['area'] = BusinessArea(area_value)
                    goal_data['status'] = GoalStatus(goal_data['status'])
                    goal_data['priority'] = Priority(goal_data['priority'])
                    
                    # Map legacy field names to new field names if needed
                    goal_data['progress'] = goal_data.get('progress', goal_data.get('progress_percentage', 0))
                    
                    # Remove legacy fields that aren't in the dataclass
                    legacy_fields = ['category', 'progress_percentage']
                    for field in legacy_fields:
                        goal_data.pop(field, None)
                    
                    business_goals[goal_id] = BusinessGoal(**goal_data)
                
                logger.info(f"Loaded {len(business_goals)} business goals from {filename}")
        else:
            logger.warning(f"Business goals file {filename} not found. Starting with empty goals.")
    except Exception as e:
        logger.error(f"Error loading business goals from {filename}: {e}")
        logger.info("Starting with empty business goals.")

# Load business goals from JSON file at startup
load_business_goals_from_json()

# CEO Operator System Components
business_brain: Dict[str, Any] = {}
task_matrix: Dict[str, List[str]] = {}

def load_business_brain() -> Dict[str, Any]:
    """Load business brain configuration from YAML file."""
    global business_brain
    try:
        if os.path.exists('business_brain.yaml'):
            with open('business_brain.yaml', 'r') as f:
                business_brain = yaml.safe_load(f)
                logger.info(f"Loaded business brain configuration: {business_brain.get('company', {}).get('name', 'Unknown')}")
        else:
            logger.warning("Business brain YAML not found. Using default configuration.")
            business_brain = {
                'company': {'name': 'Decouple Dev', 'positioning': 'Async dev agency'},
                'goals': {'north_star': 'Hit $30k/mo revenue'},
                'policy': {'priority_order': ['RevenueNow', 'Retention', 'Systems', 'Brand']}
            }
    except Exception as e:
        logger.error(f"Error loading business brain: {e}")
        business_brain = {}
    return business_brain

def load_task_matrix() -> Dict[str, List[str]]:
    """Load task matrix from YAML file."""
    global task_matrix
    try:
        if os.path.exists('task_matrix.yaml'):
            with open('task_matrix.yaml', 'r') as f:
                task_matrix = yaml.safe_load(f)
                total_tasks = sum(len(tasks) for tasks in task_matrix.values())
                logger.info(f"Loaded task matrix with {total_tasks} total tasks across {len(task_matrix)} areas")
        else:
            logger.warning("Task matrix YAML not found. Using default task matrix.")
            task_matrix = {
                'marketing': ['Define ICP/pain bullets', 'Content creation'],
                'sales': ['Outbound outreach', 'Discovery calls'],
                'delivery': ['Process documentation', 'Quality assurance'],
                'ops': ['Weekly reviews', 'System maintenance']
            }
    except Exception as e:
        logger.error(f"Error loading task matrix: {e}")
        task_matrix = {}
    return task_matrix

@dataclass
class TaskCandidate:
    """Represents a potential task for priority scoring."""
    title: str
    description: str
    area: str
    role: str  # CMO, CSO, COO, CTO
    revenue_impact: int  # 0-5
    time_to_impact: int  # 0-5 (days=5, weeks=3, months=1)
    effort: int  # 0-5 (lower effort = higher score)
    strategic_compounding: int  # 0-3
    fit_to_constraints: int  # 0-2
    due_date: str
    owner: str
    estimate: str  # S, M, L
    acceptance_criteria: str
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score using the Priority Engine formula."""
        effort_inverse = 5 - self.effort if self.effort > 0 else 5
        return (
            (2 * self.revenue_impact) + 
            (1.5 * self.time_to_impact) + 
            (1 * effort_inverse) + 
            (1 * self.strategic_compounding) + 
            (1 * self.fit_to_constraints)
        )

def perform_gap_check() -> List[str]:
    """Check what tasks are missing vs Task Matrix."""
    current_tasks = fetch_open_tasks()
    current_task_titles = [task.lower() for task in current_tasks if isinstance(task, str)]
    
    gaps = []
    
    for area, required_tasks in task_matrix.items():
        for required_task in required_tasks:
            # Simple keyword matching to see if required task exists
            task_keywords = required_task.lower().split()[:3]  # First 3 words
            if not any(all(keyword in current_title for keyword in task_keywords) 
                      for current_title in current_task_titles):
                gaps.append(f"[{area.title()}] {required_task}")
    
    return gaps

def generate_weekly_candidates() -> List[TaskCandidate]:
    """Generate candidate tasks based on Business Brain and Task Matrix."""
    candidates = []
    
    # CMO Pass - Marketing tasks
    marketing_tasks = task_matrix.get('marketing', [])
    for task in marketing_tasks[:3]:  # Limit to top 3 to avoid flooding
        candidates.append(TaskCandidate(
            title=f"[Marketing] {task[:50]}...",
            description=task,
            area="Marketing",
            role="CMO",
            revenue_impact=4,  # Marketing usually high revenue impact
            time_to_impact=4,  # Usually quick wins
            effort=3,  # Moderate effort
            strategic_compounding=2,  # Good for brand building
            fit_to_constraints=2,  # Fits constraints
            due_date=(datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            owner="Me",
            estimate="M",
            acceptance_criteria=f"Complete: {task}"
        ))
    
    # CSO Pass - Sales tasks 
    sales_tasks = task_matrix.get('sales', [])
    for task in sales_tasks[:3]:
        candidates.append(TaskCandidate(
            title=f"[Sales] {task[:50]}...",
            description=task,
            area="Sales",
            role="CSO",
            revenue_impact=5,  # Sales = direct revenue
            time_to_impact=5,  # Immediate impact
            effort=2,  # Usually not too complex
            strategic_compounding=1,  # Less compounding than systems
            fit_to_constraints=2,
            due_date=(datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            owner="Me",
            estimate="S",
            acceptance_criteria=f"Complete: {task}"
        ))
    
    # COO Pass - Operations tasks
    ops_tasks = task_matrix.get('ops', [])
    for task in ops_tasks[:2]:
        candidates.append(TaskCandidate(
            title=f"[Ops] {task[:50]}...",
            description=task,
            area="Ops",
            role="COO",
            revenue_impact=2,  # Indirect revenue impact
            time_to_impact=3,  # Medium-term
            effort=4,  # Usually higher effort
            strategic_compounding=3,  # High compounding for systems
            fit_to_constraints=1,  # May not fit time constraints
            due_date=(datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
            owner="Me",
            estimate="L",
            acceptance_criteria=f"Complete: {task}"
        ))
    
    return candidates

def generate_ceo_weekly_plan(user_text: str = "") -> str:
    """Generate CEO weekly plan following the Weekly Runbook."""
    logger.info("Starting CEO Weekly Plan generation...")
    
    # 1) Pull: Business Brain + Task Matrix + current tasks
    current_tasks = fetch_open_tasks()
    
    # 2) Gap Check
    gaps = perform_gap_check()
    
    # 3) Generate candidates and score via Priority Engine
    candidates = generate_weekly_candidates()
    
    # Sort by priority score (highest first)
    candidates.sort(key=lambda x: x.priority_score, reverse=True)
    
    # 4) Select top 6-8 tasks for "This Week"
    this_week_tasks = candidates[:6]  # Limit to 6 tasks
    
    # 5) Generate Slack summary
    focus_theme = "Revenue pipeline + process foundations"
    
    if business_brain.get('goals', {}).get('north_star'):
        focus_theme = f"Working toward: {business_brain['goals']['north_star']}"
    
    plan_response = f"""*Decouple Dev — Weekly Plan*
• Focus: {focus_theme}
• Top tasks (ranked by priority):
"""
    
    for i, task in enumerate(this_week_tasks, 1):
        plan_response += f"  {i}) {task.title} — due {task.due_date} — Owner: {task.owner} (Score: {task.priority_score:.1f})\n"
    
    if gaps:
        plan_response += f"\n• Identified gaps: {len(gaps)} missing tasks from matrix\n"
        plan_response += f"  Top gaps: {', '.join(gaps[:3])}\n"
    
    plan_response += "\n• CTA: Approve Trello changes? (Y/N). If N, reply with edits."
    
    return plan_response

def generate_midweek_nudge() -> str:
    """Generate Wednesday pipeline push message."""
    current_tasks = fetch_open_tasks()
    sales_tasks = [task for task in current_tasks if 'sales' in task.lower() or 'client' in task.lower() or 'proposal' in task.lower()]
    
    response = "*Pipeline Push*\n"
    response += f"• Current sales tasks: {len(sales_tasks)} active\n"
    response += "• Reminder: Record 1 proof asset today (before/after screenshot)\n"
    response += "• CTA: Reply with any warm intros I should chase this week."
    
    return response

def generate_friday_retro() -> str:
    """Generate Friday retrospective message."""
    current_tasks = fetch_open_tasks()
    
    response = "*Weekly Retro*\n"
    response += f"• This week: Completed X tasks, {len(current_tasks)} still pending\n"
    response += "• Metrics: discovery calls 0, proposals 0, content pieces 0\n"
    response += "• Proof assets captured: [List any screenshots/metrics]\n"
    response += "• Next Up (tentative): Focus on pipeline + content creation\n"
    response += "• CTA: Approve 'Next Up' to schedule for Monday?"
    
    return response

def create_trello_card_json(task: TaskCandidate) -> Dict[str, Any]:
    """Create Trello card JSON payload for a task."""
    labels = []
    
    # Add priority label
    priority_label = business_brain.get('policy', {}).get('priority_order', ['RevenueNow'])[0]
    labels.append(priority_label)
    
    # Add area label
    labels.append(task.area)
    
    return {
        "name": task.title,
        "desc": f"""Goal: {task.description}
Acceptance Criteria: {task.acceptance_criteria}
Subtasks:
- [Task breakdown here]
Owner: {task.owner}
Estimate: {task.estimate}
Priority Score: {task.priority_score:.1f}
Links:
""",
        "due": task.due_date,
        "idList": "<ThisWeekListID>",  # Would be replaced with actual Trello list ID
        "idMembers": ["<member_id_owner>"],
        "labels": labels
    }

def get_discovery_call_script() -> str:
    """Return the discovery call script for sales tasks."""
    return """**Discovery Call Script**

Opener: "I help small teams ship confidently by installing CI/CD + a minimal test harness. In 10 minutes I can show you how we cut deploy pain fast."

Questions:
1) What breaks your deploys today? (stories/examples)
2) What's your rollback/alert flow?
3) How long from commit → production?
4) What's the smallest test suite you'd accept to sleep at night?
5) If I could fix one thing this week, what should it be?

Close:
"We start with a fixed-price audit (1 week). If you like the plan, we book a 1–2 week sprint. Want me to send the two-option proposal today?"
"""

# Load configurations at startup
load_business_brain()
load_task_matrix()

def get_app_version() -> str:
    """Get the current app version from git or fallback to timestamp."""
    try:
        # Try to get git commit hash
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    # Fallback to timestamp
    return datetime.datetime.now().strftime('%Y%m%d-%H%M')

def add_version_timestamp(response: str) -> str:
    """Add version and timestamp information to response."""
    version = get_app_version()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    return f"{response}\n\n---\n_OpsBrain v{version} • Updated: {timestamp}_"

def get_user_name(user_id: str) -> str:
    """Get user's display name from Slack API"""
    try:
        response = requests.get(
            "https://slack.com/api/users.info",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            params={"user": user_id},
            timeout=5
        )
        
        if response.ok:
            data = response.json()
            if data.get("ok"):
                user = data.get("user", {})
                return user.get("display_name") or user.get("real_name") or user.get("name") or f"User {user_id}"
        
        logger.warning(f"Failed to get user name for {user_id}: {response.text}")
        return f"User {user_id}"
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return f"User {user_id}"

def create_business_goal(title: str, description: str, area: str, target_date: str, 
                        weekly_actions: List[str] = None, daily_actions: List[str] = None,
                        success_metrics: Dict[str, str] = None) -> str:
    """Create a new SMART business goal."""
    goal_id = f"{area.lower()}_{len([g for g in business_goals.values() if g.area.value == area.lower()]) + 1}"
    
    goal = BusinessGoal(
        id=goal_id,
        title=title,
        description=description,
        area=BusinessArea(area.lower()),
        status=GoalStatus.NOT_STARTED,
        priority=Priority.MEDIUM,
        target_date=target_date,
        progress=0,
        weekly_actions=weekly_actions or [],
        daily_actions=daily_actions or [],
        success_metrics=success_metrics or {},
        created_date=datetime.datetime.now().isoformat(),
        last_updated=datetime.datetime.now().isoformat()
    )
    
    business_goals[goal_id] = goal
    return goal_id

def get_ceo_dashboard() -> Dict:
    """Generate CEO dashboard with business metrics and priorities."""
    total_goals = len(business_goals)
    completed = len([g for g in business_goals.values() if g.status == GoalStatus.COMPLETED])
    in_progress = len([g for g in business_goals.values() if g.status == GoalStatus.IN_PROGRESS])
    blocked = len([g for g in business_goals.values() if g.status == GoalStatus.BLOCKED])
    
    # Calculate progress by business area
    area_progress = {}
    for area in BusinessArea:
        area_goals = [g for g in business_goals.values() if g.area == area]
        if area_goals:
            avg_progress = sum(g.progress for g in area_goals) / len(area_goals)
            area_progress[area.value] = round(avg_progress, 1)
        else:
            area_progress[area.value] = 0
    
    # Get high priority actions
    high_priority_actions = []
    for goal in business_goals.values():
        if goal.status not in [GoalStatus.COMPLETED, GoalStatus.DEFERRED] and goal.priority.value >= Priority.HIGH.value:
            for action in goal.weekly_actions[:2]:  # Top 2 actions per high-priority goal
                high_priority_actions.append({
                    'area': goal.area.value,
                    'goal': goal.title,
                    'action': action,
                    'priority': goal.priority.value
                })
    
    return {
        'overview': {
            'total_goals': total_goals,
            'completed': completed,
            'in_progress': in_progress,
            'blocked': blocked,
            'completion_rate': round(completed / total_goals * 100, 1) if total_goals > 0 else 0
        },
        'area_progress': area_progress,
        'high_priority_actions': sorted(high_priority_actions, key=lambda x: x['priority'], reverse=True)[:10]
    }
def analyze_business_request(user_text: str) -> Dict:
    """Analyze user request and determine business context and recommendations."""
    user_lower = user_text.lower()

    if "help" in user_lower:
        return {
            'request_type': 'help',
            'detected_areas': [],
            'is_ceo_focused': False
        }
    
    # Detect business area focus
    area_keywords = {
        'sales': ['sales', 'lead', 'client', 'prospect', 'revenue', 'close', 'pipeline', 'acquisition', 'customer'],
        'delivery': ['delivery', 'project', 'deliver', 'quality', 'process', 'client work', 'standardize', 'efficiency'],
        'product': ['product', 'feature', 'development', 'opsbrain', 'build', 'code', 'technical', 'integration'],
        'financial': ['financial', 'profit', 'margin', 'pricing', 'cost', 'budget', 'roi', 'cash flow'],
        'team': ['team', 'hire', 'contractor', 'employee', 'capacity', 'skills', 'onboard'],
        'process': ['process', 'automate', 'system', 'workflow', 'optimize', 'metrics', 'kpi']
    }
    
    detected_areas = []
    for area, keywords in area_keywords.items():
        if any(keyword in user_lower for keyword in keywords):
            detected_areas.append(area)
    
    # Detect request type - more specific patterns first
    request_types = {
        'task_backlog': ['create all tasks', 'task backlog', 'generate tasks', 'missing tasks', 'all the tasks', 'first customer', 'review all tasks', 'missing items'],
        'goal_creation': ['goal', 'create', 'add', 'new objective', 'target'],
        'progress_update': ['progress', 'update', 'status', 'completed', 'done'],
        'dashboard': ['dashboard', 'overview', 'summary'],
        'planning': ['plan', 'strategy', 'next', 'priorities', 'focus'],
        'research': ['research', 'analyze', 'opportunities', 'market', 'competitor']
    }
    
    detected_request_type = 'general'
    for req_type, keywords in request_types.items():
        if any(keyword in user_lower for keyword in keywords):
            detected_request_type = req_type
            break
    
    return {
        'detected_areas': detected_areas,
        'request_type': detected_request_type,
        'is_ceo_focused': any(word in user_lower for word in ['ceo', 'business', 'strategy', 'growth', 'revenue', 'grow'])
    }

def generate_ceo_insights(user_text: str, tasks: List[str], analysis: Dict) -> str:
    """Generate CEO-focused insights and actionable recommendations."""
    dashboard = get_ceo_dashboard()
    
    # Build context-aware prompt based on analysis
    business_context = ""
    if analysis['detected_areas']:
        areas_text = ", ".join(analysis['detected_areas'])
        business_context += f"Focus areas detected: {areas_text}\n"
    
    if dashboard['overview']['total_goals'] > 0:
        business_context += f"""Current business status:
- Goals: {dashboard['overview']['total_goals']} total, {dashboard['overview']['completion_rate']}% complete
- In progress: {dashboard['overview']['in_progress']}, Blocked: {dashboard['overview']['blocked']}
- Area progress: {', '.join([f"{k}: {v}%" for k, v in dashboard['area_progress'].items() if v > 0])}
"""
    
    # Get relevant goals for detected areas
    relevant_goals = []
    if analysis['detected_areas']:
        for goal in business_goals.values():
            if goal.area.value in analysis['detected_areas'] and goal.status != GoalStatus.COMPLETED:
                relevant_goals.append(f"- {goal.title}: {goal.progress}% complete")
    
    if relevant_goals:
        business_context += f"\nRelevant active goals:\n" + "\n".join(relevant_goals[:3])
    
    # Generate specialized response based on request type
    if analysis['request_type'] == 'dashboard':
        return generate_dashboard_response(dashboard)
    elif analysis['request_type'] == 'goal_creation':
        return generate_goal_suggestions(analysis['detected_areas'], user_text)
    elif analysis['request_type'] == 'planning':
        return generate_planning_response(dashboard, analysis['detected_areas'])
    elif analysis['request_type'] == 'help':
        return generate_help_response()
    else:
        # General CEO-focused response
        task_list = "\n".join(f"- {t}" for t in tasks[:5])  # Top 5 tasks
        
        prompt = f"""You are OpsBrain, a CEO-level AI assistant. Respond like a strategic executive - concise, action-oriented, results-focused.

{business_context}

Current tasks: {len(tasks)} pending
User request: "{user_text}"

RESPONSE STYLE:
- If task completed successfully: "Task completed" or "Done"
- If there's an issue: "Issue: [specific problem]"
- For questions: Give 1-2 sentence strategic answer
- For requests: Confirm action taken or identify blocking issue
- No bullet points, no detailed explanations unless specifically asked
- Focus on what's blocking revenue or efficiency
- Maximum 2 sentences unless complex strategic question

Respond now:"""
        
        return prompt

def generate_dashboard_response(dashboard: Dict) -> str:
    """Generate a CEO dashboard summary."""
    overview = dashboard['overview']
    
    response = f"📊 **CEO Dashboard Summary**\n\n"
    response += f"**Goals:** {overview['total_goals']} total • {overview['completion_rate']}% complete\n"
    response += f"**Status:** {overview['in_progress']} in progress • {overview['blocked']} blocked\n\n"
    
    if dashboard['area_progress']:
        response += "**Business Area Progress:**\n"
        for area, progress in dashboard['area_progress'].items():
            if progress > 0:
                response += f"• {area.title()}: {progress}%\n"
    
    if dashboard['high_priority_actions']:
        response += "\n**Top Priority Actions This Week:**\n"
        for i, action in enumerate(dashboard['high_priority_actions'][:3], 1):
            response += f"{i}. [{action['area'].title()}] {action['action']}\n"
    
    response += "\n💡 Focus on revenue-generating activities and blocked items first."
    return response

def generate_help_response() -> str:
    """Generate a help response with available commands."""
    help_text = """
    **OpsBrain - Help Guide**

    Here are some of the things you can ask me to do:

    **Task Management:**
    - Create, update, or complete tasks.
    - Example: "Create task: Design new landing page."

    **Goal Setting & Management:**
    - Create or view business goals.
    - Example: "Create goal: Increase sales by 20% in Q3."

    **Client Management:**
    - Add or update client information.
    - Example: "Add client: Acme Corporation."

    **Metrics Tracking:**
    - Log and review business metrics.
    - Example: "Log metric: $10k revenue in July."

    **Strategic Insights:**
    - Get personalized advice and next steps.
    - Keywords: sales, delivery, product, financial, team, process.

    **General Questions:**
    - Ask for help or guidance on using OpsBrain.
    - Example: "How can I improve my team's productivity?"
    
    Type "help" anytime to see this guide again.
    """
    return help_text


def generate_goal_suggestions(areas: List[str], user_text: str) -> str:
    """Generate SMART goal suggestions based on detected business areas."""
    area = areas[0] if areas else 'sales'  # Default to sales
    
    goal_templates = {
        'sales': [
            "Generate 50 qualified leads per month through content marketing by [date]",
            "Close 3 new clients at $5K+ monthly retainer by [date]",
            "Achieve $15K monthly recurring revenue by [date]"
        ],
        'delivery': [
            "Reduce project delivery time by 40% through process standardization by [date]",
            "Achieve 95% client satisfaction score by [date]",
            "Document 5 core delivery processes by [date]"
        ],
        'product': [
            "Complete 8 high-impact OpsBrain features by [date]",
            "Integrate OpsBrain with 3 popular business tools by [date]",
            "Deploy automated testing for all core features by [date]"
        ],
        'financial': [
            "Increase profit margin to 70% through pricing optimization by [date]",
            "Reduce operational costs by 20% while maintaining quality by [date]",
            "Establish 6-month cash flow buffer by [date]"
        ],
        'team': [
            "Hire first contractor (VA or developer) by [date]",
            "Create comprehensive onboarding process by [date]",
            "Establish team productivity metrics and tracking by [date]"
        ],
        'process': [
            "Automate 80% of routine administrative tasks by [date]",
            "Create CEO dashboard with key business metrics by [date]",
            "Implement weekly business review process by [date]"
        ]
    }
    
    suggestions = goal_templates.get(area, goal_templates['sales'])
    
    response = f"🎯 **SMART Goal Suggestions for {area.title()}:**\n\n"
    for i, suggestion in enumerate(suggestions, 1):
        response += f"{i}. {suggestion}\n"
    
    response += f"\n💡 Choose one goal that directly impacts revenue or efficiency. Would you like me to help create a specific goal with weekly actions?"
    return response

def generate_planning_response(dashboard: Dict, areas: List[str]) -> str:
    """Generate strategic planning recommendations."""
    response = "📋 **Strategic Planning Recommendations:**\n\n"
    
    # Priority areas based on progress
    low_progress_areas = [area for area, progress in dashboard['area_progress'].items() if progress < 50]
    
    if low_progress_areas:
        response += f"**Focus Areas (Low Progress):** {', '.join(low_progress_areas)}\n\n"
    
    response += "**This Week's CEO Priorities:**\n"
    response += "1. **Revenue Focus:** Spend 60% of time on sales and client delivery\n"
    response += "2. **Process Improvement:** Document one key workflow\n"
    response += "3. **Strategic Planning:** Block 2 hours for business planning\n\n"
    
    response += "**Key Metrics to Track:**\n"
    response += "• Monthly Recurring Revenue (MRR)\n"
    response += "• Client acquisition cost vs. lifetime value\n"
    response += "• Weekly time allocation across business areas\n\n"
    
    response += "💡 Remember: Focus on activities that move the revenue needle first."
    return response

async def handle_task_backlog_request(user_text: str, business_goals: Dict, channel: str):
    """Handle the asynchronous task backlog generation and posting to Notion."""
    logger.info("Starting task backlog generation...")
    db_info = await get_notion_db_info(NOTION_DB_ID)
    if not db_info.properties:
        logger.error("Could not retrieve Notion DB info. Aborting task backlog generation.")
        return

    tasks = await generate_task_backlog(user_text, business_goals, db_info)
    if tasks:
        await bulk_create_notion_tasks(tasks, channel)
    else:
        logger.warning("No tasks were generated by the LLM.")

# Intelligent Task Management System
@dataclass
class NotionDBInfo:
    properties: Dict[str, str]

async def get_notion_db_info(database_id: str) -> NotionDBInfo:
    """Get the structure of the Notion database."""
    try:
        db = await asyncio.to_thread(notion.databases.retrieve, database_id=database_id)
        properties = {prop_name: prop_data['type'] for prop_name, prop_data in db['properties'].items()}
        return NotionDBInfo(properties=properties)
    except APIResponseError as e:
        logger.error(f"Notion API error while fetching DB info: {e}")
        return NotionDBInfo(properties={})

async def generate_task_backlog(user_text: str, business_goals: Dict, db_info: NotionDBInfo) -> List[Dict]:
    """Generate a detailed task backlog based on business goals and user request."""
    goal_summary = "\n".join([f"- {g.title}: {g.description}" for g in business_goals.values()])
    
    prompt = f"""You are OpsBrain, a CEO-level AI assistant specializing in comprehensive task planning.

    Business Goals:
    {goal_summary}

    User Request: "{user_text}"

    Notion Database Properties: {json.dumps(db_info.properties)}

    CRITICAL: Generate a COMPLETE task backlog covering ALL areas of the business. Don't create partial lists.
    
    For business success, identify missing tasks in:
    - Sales & Marketing (lead gen, content, outreach, proposals)
    - Client Delivery (project setup, quality assurance, documentation)
    - Operations (processes, systems, automation)
    - Financial (pricing, invoicing, metrics tracking)
    - Product Development (features, testing, deployment)
    - Team & Hiring (recruitment, onboarding, management)
    
    Each task must have: title, status, priority (High/Medium/Low), project, notes
    Include SOPs in notes where needed.
    
    Output as JSON array with complete task coverage - no partial lists.
    """
    
    try:
        ai_message = await llm.ainvoke(prompt)
        task_list_json = ai_message.content
        tasks = json.loads(task_list_json)
        return tasks
    except Exception as e:
        logger.error(f"Error generating task backlog: {e}")
        return []

async def bulk_create_notion_tasks(tasks: List[Dict], channel: str):
    """Create a list of tasks in Notion with rate limiting."""
    total_tasks = len(tasks)
    if total_tasks == 0:
        return

    success_count = 0
    failed_tasks = []

    # Notify user that task creation is starting
    initial_message = f"🤖 Understood! Generating and adding {total_tasks} tasks to your Notion database. This might take a moment..."
    requests.post("https://slack.com/api/chat.postMessage", headers={
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json"
    }, json={
        "channel": channel,
        "text": initial_message
    })

    async def create_task_with_retry(task):
        nonlocal success_count
        try:
            await asyncio.to_thread(create_notion_task, **task)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to create task '{task.get('title')}': {e}")
            failed_tasks.append(task.get('title'))
        await asyncio.sleep(0.5)  # Rate limiting

    # Create tasks concurrently with proper async handling
    tasks_to_create = [create_task_with_retry(task) for task in tasks]
    await asyncio.gather(*tasks_to_create)

    # Final report
    final_message = f"✅ Successfully created {success_count}/{total_tasks} tasks in Notion."
    if failed_tasks:
        final_message += f"\n❌ Failed to create: {", ".join(failed_tasks)}"
    
    requests.post("https://slack.com/api/chat.postMessage", headers={
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json"
    }, json={
        "channel": channel,
        "text": final_message
    })
def create_notion_task(title: str, status: str = "To Do", priority: str = "Medium", 
                      project: str = None, due_date: str = None, notes: str = None) -> bool:
    """Create a new task in the Notion tasks database."""
    try:
        properties = {
            "Task": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}}
        }
        
        if priority:
            properties["Priority"] = {"select": {"name": priority}}
        if project:
            properties["Project"] = {"rich_text": [{"text": {"content": project}}]}
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=properties
        )
        logger.info(f"Created task in Notion: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Notion task: {e}")
        return False

def update_notion_task(task_id: str, status: str = None, priority: str = None, 
                      notes: str = None, progress: int = None) -> bool:
    """Update an existing task in Notion."""
    try:
        properties = {}
        
        if status:
            properties["Status"] = {"select": {"name": status}}
        if priority:
            properties["Priority"] = {"select": {"name": priority}}
        if progress is not None:
            properties["Progress"] = {"number": progress}
        if notes:
            # Append to existing notes
            current_notes = get_task_notes(task_id)
            updated_notes = f"{current_notes}\n\n{datetime.datetime.now().strftime('%Y-%m-%d')}: {notes}" if current_notes else notes
            properties["Notes"] = {"rich_text": [{"text": {"content": updated_notes}}]}
        
        notion.pages.update(page_id=task_id, properties=properties)
        logger.info(f"Updated task {task_id} in Notion")
        return True
    except Exception as e:
        logger.error(f"Failed to update Notion task: {e}")
        return False

def create_business_goal_in_notion(title: str, area: str, target_date: str, 
                                  description: str = None, success_metrics: str = None) -> bool:
    """Create a business goal in Notion goals database."""
    if not NOTION_GOALS_DB_ID:
        return False
    
    try:
        properties = {
            "Goal": {"title": [{"text": {"content": title}}]},
            "Area": {"select": {"name": area.title()}},
            "Target Date": {"date": {"start": target_date}},
            "Status": {"select": {"name": "Not Started"}},
            "Progress": {"number": 0}
        }
        
        if description:
            properties["Description"] = {"rich_text": [{"text": {"content": description}}]}
        if success_metrics:
            properties["Success Metrics"] = {"rich_text": [{"text": {"content": success_metrics}}]}
        
        notion.pages.create(
            parent={"database_id": NOTION_GOALS_DB_ID},
            properties=properties
        )
        logger.info(f"Created business goal in Notion: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Notion goal: {e}")
        return False

def create_client_record(name: str, status: str = "Prospect", deal_value: float = None, 
                        contact_email: str = None, notes: str = None) -> bool:
    """Create a client record in Notion clients database."""
    if not NOTION_CLIENTS_DB_ID:
        return False
    
    try:
        properties = {
            "Client Name": {"title": [{"text": {"content": name}}]},
            "Status": {"select": {"name": status}}
        }
        
        if deal_value:
            properties["Deal Value"] = {"number": deal_value}
        if contact_email:
            properties["Contact Email"] = {"email": contact_email}
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        notion.pages.create(
            parent={"database_id": NOTION_CLIENTS_DB_ID},
            properties=properties
        )
        logger.info(f"Created client record in Notion: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Notion client record: {e}")
        return False

def log_business_metric(metric_name: str, value: float, date: str = None, 
                       category: str = "General", notes: str = None) -> bool:
    """Log a business metric in Notion metrics database."""
    if not NOTION_METRICS_DB_ID:
        return False
    
    try:
        properties = {
            "Metric": {"title": [{"text": {"content": metric_name}}]},
            "Value": {"number": value},
            "Date": {"date": {"start": date or datetime.datetime.now().strftime('%Y-%m-%d')}},
            "Category": {"select": {"name": category}}
        }
        
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        notion.pages.create(
            parent={"database_id": NOTION_METRICS_DB_ID},
            properties=properties
        )
        logger.info(f"Logged business metric: {metric_name} = {value}")
        return True
    except Exception as e:
        logger.error(f"Failed to log business metric: {e}")
        return False

def get_task_notes(task_id: str) -> str:
    """Get existing notes from a Notion task."""
    try:
        page = notion.pages.retrieve(page_id=task_id)
        notes_property = page.get('properties', {}).get('Notes', {})
        if notes_property.get('rich_text'):
            return notes_property['rich_text'][0].get('text', {}).get('content', '')
        return ''
    except Exception as e:
        logger.error(f"Failed to get task notes: {e}")
        return ''

def search_notion_database(database_id: str, query: str, property_name: str = None) -> List[Dict]:
    """Search for records in a Notion database."""
    try:
        filter_conditions = []
        
        if property_name:
            filter_conditions.append({
                "property": property_name,
                "rich_text": {"contains": query}
            })
        else:
            # Search common text properties
            common_props = ["Task", "Goal", "Client Name", "Metric", "Name", "Title"]
            for prop in common_props:
                filter_conditions.append({
                    "property": prop,
                    "rich_text": {"contains": query}
                })
        
        search_filter = {"or": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]
        
        results = notion.databases.query(
            database_id=database_id,
            filter=search_filter
        )
        
        return results.get('results', [])
    except Exception as e:
        logger.error(f"Failed to search Notion database: {e}")
        return []

def execute_database_action(action_type: str, **kwargs) -> Dict:
    """Execute database actions based on AI analysis."""
    result = {"success": False, "message": "", "action": action_type}
    
    try:
        # Handle Trello actions with CEO-style responses
        if action_type == "trello_done":
            task_name = kwargs.get('task_name', 'task')
            if trello_client.is_configured():
                success = trello_client.move_task_to_done(task_name)
                result["success"] = success
                result["message"] = "Task completed" if success else f"Issue: Could not find or move task '{task_name}'"
            else:
                result["message"] = "Issue: Trello not configured"
        
        elif action_type == "trello_status":
            task_name = kwargs.get('task_name', 'task')
            if trello_client.is_configured():
                status = trello_client.get_task_status(task_name)
                result["success"] = status is not None
                result["message"] = f"Status: {status}" if status else f"Issue: Task '{task_name}' not found"
            else:
                result["message"] = "Issue: Trello not configured"
        
        elif action_type == "add_business_tasks":
            areas = kwargs.get('areas', [])
            if trello_client.is_configured():
                count = trello_client.add_missing_business_tasks(areas)
                result["success"] = count > 0
                result["message"] = f"Added {count} business tasks" if count > 0 else "Issue: No tasks created"
            else:
                result["message"] = "Issue: Trello not configured"
        
        elif action_type == "create_task":
            success = create_notion_task(
                title=kwargs.get('title', ''),
                status=kwargs.get('status', 'To Do'),
                priority=kwargs.get('priority', 'Medium'),
                project=kwargs.get('project'),
                due_date=kwargs.get('due_date'),
                notes=kwargs.get('notes')
            )
            result["success"] = success
            result["message"] = f"Task '{kwargs.get('title')}' created successfully" if success else "Failed to create task"
        
        elif action_type == "create_goal":
            success = create_business_goal_in_notion(
                title=kwargs.get('title', ''),
                area=kwargs.get('area', 'sales'),
                target_date=kwargs.get('target_date', ''),
                description=kwargs.get('description'),
                success_metrics=kwargs.get('success_metrics')
            )
            result["success"] = success
            result["message"] = f"Goal '{kwargs.get('title')}' created successfully" if success else "Failed to create goal"
        
        elif action_type == "create_client":
            success = create_client_record(
                name=kwargs.get('name', ''),
                status=kwargs.get('status', 'Prospect'),
                deal_value=kwargs.get('deal_value'),
                contact_email=kwargs.get('contact_email'),
                notes=kwargs.get('notes')
            )
            result["success"] = success
            result["message"] = f"Client '{kwargs.get('name')}' created successfully" if success else "Failed to create client record"
        
        elif action_type == "log_metric":
            success = log_business_metric(
                metric_name=kwargs.get('metric_name', ''),
                value=kwargs.get('value', 0),
                date=kwargs.get('date'),
                category=kwargs.get('category', 'General'),
                notes=kwargs.get('notes')
            )
            result["success"] = success
            result["message"] = f"Metric '{kwargs.get('metric_name')}' logged successfully" if success else "Failed to log metric"
        
        else:
            result["message"] = f"Unknown action type: {action_type}"
        
    except Exception as e:
        logger.error(f"Database action failed: {e}")
        result["message"] = f"Error executing {action_type}: {str(e)}"
    
    return result

def parse_database_request(user_text: str) -> Dict:
    """Parse user request to determine if database action is needed."""
    user_lower = user_text.lower()
    
    # Detect action types
    action_keywords = {
        'create_task': ['create task', 'add task', 'new task', 'task:', 'todo:'],
        'create_goal': ['create goal', 'add goal', 'new goal', 'goal:', 'objective:'],
        'create_client': ['add client', 'new client', 'create client', 'client:', 'prospect:'],
        'log_metric': ['log metric', 'record metric', 'track metric', 'metric:', 'kpi:'],
        'update_task': ['update task', 'complete task', 'finish task', 'mark done'],
        'trello_done': ['status to done', 'status done', 'mark as done', 'mark done', 'task done', 'set to done', 'as done', 'to done'],
        'trello_status': ['task status', 'check status', 'status of'],
        'add_business_tasks': ['add missing tasks', 'create all tasks', 'missing business tasks'],
        'search': ['find', 'search', 'look for', 'show me']
    }
    
    detected_action = None
    for action, keywords in action_keywords.items():
        if any(keyword in user_lower for keyword in keywords):
            detected_action = action
            break
    
    # Extract parameters based on action type
    params = {}
    if detected_action == 'create_task':
        # Extract task title (look for patterns like "task: title" or "create task title")
        if ':' in user_text:
            params['title'] = user_text.split(':', 1)[1].strip()
        else:
            # Remove command words and use the rest as title
            title = user_text
            for keyword in action_keywords['create_task']:
                title = title.replace(keyword, '', 1).strip()
            params['title'] = title
    
    elif detected_action == 'create_goal':
        if ':' in user_text:
            params['title'] = user_text.split(':', 1)[1].strip()
        else:
            title = user_text
            for keyword in action_keywords['create_goal']:
                title = title.replace(keyword, '', 1).strip()
            params['title'] = title
        
        # Detect area from keywords
        area_keywords = {
            'sales': ['sales', 'lead', 'client', 'revenue', 'acquisition'],
            'delivery': ['delivery', 'project', 'quality', 'process'],
            'product': ['product', 'feature', 'development', 'technical'],
            'financial': ['financial', 'profit', 'cost', 'budget'],
            'team': ['team', 'hire', 'contractor', 'employee'],
            'process': ['process', 'workflow', 'automation', 'system']
        }
        
        for area, keywords in area_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                params['area'] = area
                break
        
        if 'area' not in params:
            params['area'] = 'sales'  # Default area
    
    elif detected_action == 'create_client':
        if ':' in user_text:
            params['name'] = user_text.split(':', 1)[1].strip()
        else:
            name = user_text
            for keyword in action_keywords['create_client']:
                name = name.replace(keyword, '', 1).strip()
            params['name'] = name
    
    # Handle Trello-specific actions
    if detected_action == 'trello_done':
        # Extract task name from text like "Set AI agent status to done"
        task_keywords = ['ai agent', 'task', 'item']
        for keyword in task_keywords:
            if keyword in user_lower:
                # Find the task name around the keyword
                words = user_text.lower().split()
                if keyword.replace(' ', '') in ' '.join(words):
                    params['task_name'] = keyword
                    break
        if 'task_name' not in params:
            params['task_name'] = 'ai agent'  # Default based on your example
    
    elif detected_action == 'add_business_tasks':
        params['areas'] = ['sales', 'delivery', 'financial', 'operations', 'team']
    
    return {
        'action': detected_action,
        'params': params,
        'requires_db_action': detected_action is not None
    }

class SlackMessage(BaseModel):
    type: str
    event: dict
    user_id: Optional[str] = None
    user_name: Optional[str] = None

def fetch_open_tasks():
    try:
        results = notion.databases.query(
            **{
                "database_id": NOTION_DB_ID,
                "filter": {
                    "or": [
                        {"property": "Status", "select": {"equals": "To Do"}},
                        {"property": "Status", "select": {"equals": "Inbox"}}
                    ]
                }
            }
        )
        tasks = []
        logger.info(f"Found {len(results['results'])} rows in Notion database")
        
        for i, row in enumerate(results["results"]):
            try:
                # Debug logging for first few rows (only in TEST_MODE)
                if TEST_MODE and i < 3:  # Only log first 3 rows to avoid spam
                    logger.info(f"Row {i} properties keys: {list(row.get('properties', {}).keys())}")
                    task_prop = row.get("properties", {}).get("Task", {})
                    logger.info(f"Row {i} Task property: {task_prop}")
                
                # More robust task parsing
                task_property = row.get("properties", {}).get("Task", {})
                title_array = task_property.get("title", [])
                
                if title_array and len(title_array) > 0:
                    text_content = title_array[0].get("text", {})
                    title = text_content.get("content", "Untitled Task")
                else:
                    title = "Untitled Task"
                    
                if title.strip():  # Only add non-empty titles
                    tasks.append(title)
                    if TEST_MODE:
                        logger.info(f"Successfully parsed task: '{title}'")
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Failed to parse task {i}: {e}")
                if TEST_MODE and i < 3:  # Only log full row data for first few to avoid spam
                    logger.warning(f"Row {i} full data: {json.dumps(row, indent=2)}")
                continue
        return tasks
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return ["Unable to fetch tasks from Notion"]
    except Exception as e:
        logger.error(f"Unexpected error fetching tasks: {e}")
        return ["Error accessing task database"]

@app.get("/")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "test_mode": TEST_MODE,
        "slack_bot_token_set": bool(SLACK_BOT_TOKEN),
        "slack_signing_secret_set": bool(SLACK_SIGNING_SECRET),
        "notion_api_key_set": bool(NOTION_API_KEY),
        "openai_api_key_set": bool(OPENAI_API_KEY)
    }

@app.get("/health")
async def health_check_alt():
    """Alternative health check endpoint for compatibility."""
    return await health_check()

def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    # Handle None values (e.g., in tests)
    if not timestamp or not signature or not SLACK_SIGNING_SECRET:
        return False
    
    try:
        # Check timestamp (prevent replay attacks)
        if abs(time.time() - int(timestamp)) > 60 * 5:  # 5 minutes
            return False
        
        # Verify signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        my_signature = 'v0=' + hmac.new(
            SLACK_SIGNING_SECRET.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(my_signature, signature)
    except (ValueError, TypeError) as e:
        logger.error(f"Signature verification error: {e}")
        return False

@app.post("/slack")
async def slack_events(req: Request, x_slack_request_timestamp: Optional[str] = Header(None), x_slack_signature: Optional[str] = Header(None)):
    # Log incoming request headers (only in TEST_MODE to reduce noise)
    if TEST_MODE:
        logger.info(f"Incoming Slack request - Headers: {dict(req.headers)}")
        logger.info(f"Timestamp header: {x_slack_request_timestamp}")
        logger.info(f"Signature header: {x_slack_signature}")
    logger.info(f"TEST_MODE: {TEST_MODE}")
    
    # Get raw body first to check if it's empty
    raw_body = await req.body()
    logger.info(f"Raw body length: {len(raw_body)} bytes")

    if not raw_body:
        logger.error("Received empty request body")
        raise HTTPException(status_code=400, detail="Empty request body")

    # Check content type to determine how to parse the body
    content_type = req.headers.get("content-type", "")
    logger.info(f"Content-Type: {content_type}")
    
    # Parse body based on content type
    if "application/x-www-form-urlencoded" in content_type:
        # Slash command format
        from urllib.parse import parse_qs
        try:
            form_data = parse_qs(raw_body.decode('utf-8'))
            # Convert form data to a more usable format
            body = {key: value[0] if len(value) == 1 else value for key, value in form_data.items()}
            logger.info(f"Parsed form data keys: {list(body.keys())}")
            logger.info(f"Command: {body.get('command', 'unknown')}")
        except Exception as e:
            logger.error(f"Form decode error: {str(e)} - Raw body: {raw_body[:500]}")
            raise HTTPException(status_code=400, detail=f"Invalid form data: {str(e)}")
    else:
        # JSON format (event subscriptions)
        try:
            body = json.loads(raw_body)
            logger.info(f"Parsed JSON body keys: {list(body.keys())}")
            logger.info(f"Body type: {body.get('type', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)} - Raw body: {raw_body[:500]}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Handle Slack URL verification challenge (bypass signature verification)
    if "challenge" in body:
        logger.info(f"Slack URL verification challenge received: {body.get('challenge', 'unknown')}")
        return {"challenge": body["challenge"]}

    # Log signature verification details
    logger.info(f"About to verify signature - TEST_MODE: {TEST_MODE}")
    if not TEST_MODE:
        signature_valid = verify_slack_signature(raw_body, x_slack_request_timestamp, x_slack_signature)
        logger.info(f"Signature verification result: {signature_valid}")
        if not signature_valid:
            logger.error(f"Slack request verification failed - Timestamp: {x_slack_request_timestamp}, Signature: {x_slack_signature}")
            raise HTTPException(status_code=403, detail="Invalid Slack signature")
    else:
        logger.info("Skipping signature verification due to TEST_MODE")

    # Handle different types of Slack requests
    try:
        # Check if this is a slash command
        if "command" in body:
            logger.info("Processing slash command")
            user_text = body.get("text", "")
            channel = body.get("channel_id")
            command = body.get("command")
            user_id = body.get("user_id")
            trigger_id = body.get("trigger_id")
            
            logger.info(f"Slash command: {command}, text: {user_text}, channel: {channel}")
            
            # Return immediate acknowledgment FIRST - must be under 3 seconds for Slack
            immediate_response = {
                "text": "🤔 Let me analyze your tasks and get back to you...",
                "response_type": "ephemeral"  # Only visible to user who ran command
            }
            
            # Start background task to send the actual response
            import threading
            
            def send_delayed_response():
                try:
                    # Get or create thread context for this conversation
                    context = get_thread_context(None, channel, user_text)
                    
                    # First, post the original command to make it visible in the channel
                    if user_text.strip():  # Only post if there's actual text
                        try:
                            original_message_response = requests.post("https://slack.com/api/chat.postMessage", headers={
                                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                                "Content-type": "application/json"
                            }, json={
                "channel": channel,
                "text": f"*{get_user_name(user_id)}* used `{command}`: {user_text}"
                            }, timeout=10)
                            
                            if not original_message_response.ok:
                                logger.error(f"Failed to post original command: {original_message_response.status_code} - {original_message_response.text}")
                            else:
                                logger.info("Successfully posted original slash command to channel")
                                # Original message posted successfully
                        except requests.RequestException as e:
                            logger.error(f"Failed to post original message to Slack: {e}")
                    
                    # Get tasks and generate AI response in background
                    tasks = fetch_open_tasks()
                    task_list = "\n".join(f"- {t}" for t in tasks)
                    
                    if not llm:
                        ai_response = "Sorry, OpenAI API key is not configured."
                    else:
                        try:
                            # Include conversation context in prompt if available
                            conversation_context = "\n".join(context['messages'][-6:]) if len(context['messages']) > 1 else ""
                            context_prompt = f"\n\nConversation context:\n{conversation_context}" if conversation_context else ""
                            
                            # Analyze the business context of the request
                            analysis = analyze_business_request(user_text)
                            
                            # Check if this requires database action
                            db_request = parse_database_request(user_text)
                            
                            # Execute database action if needed
                            db_result = None
                            if db_request['requires_db_action']:
                                db_result = execute_database_action(db_request['action'], **db_request['params'])
                                logger.info(f"Database action result: {db_result}")
                            
                            if analysis['request_type'] == 'help':
                                # Direct help response - no LLM needed
                                ai_response = generate_help_response()
                            elif analysis['request_type'] == 'task_backlog':
                                # Trigger async task backlog generation
                                ai_response = "🤖 I understand you want me to generate a task backlog. Let me analyze your business goals and create comprehensive tasks for you. This process will run in the background, and I'll update you with progress."
                                # Start the async task generation process safely
                                try:
                                    import asyncio
                                    # Check if there's already an event loop running
                                    try:
                                        loop = asyncio.get_event_loop()
                                        if loop.is_running():
                                            # Create task in existing loop
                                            asyncio.create_task(handle_task_backlog_request(user_text, business_goals, channel))
                                        else:
                                            # Run in existing loop
                                            loop.run_until_complete(handle_task_backlog_request(user_text, business_goals, channel))
                                    except RuntimeError:
                                        # No loop exists, create new one
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            loop.run_until_complete(handle_task_backlog_request(user_text, business_goals, channel))
                                        finally:
                                            loop.close()
                                except Exception as e:
                                    logger.error(f"Error in task backlog generation: {e}")
                                    ai_response += "\n\n⚠️ There was an issue starting the task backlog generation. Please try again later."
                            elif analysis['is_ceo_focused'] or analysis['request_type'] in ['dashboard', 'goal_creation', 'planning']:
                                # Use CEO-focused response generation
                                if analysis['request_type'] in ['dashboard', 'goal_creation', 'planning']:
                                    ai_response = generate_ceo_insights(user_text, tasks, analysis)
                                    if not ai_response.startswith('📊') and not ai_response.startswith('🎯') and not ai_response.startswith('📋'):
                                        # It's a prompt, not a direct response
                                        ai_message = llm.invoke(ai_response)
                                        ai_response = ai_message.content
                                else:
                                    prompt = generate_ceo_insights(user_text, tasks, analysis)
                                    ai_message = llm.invoke(prompt)
                                    ai_response = ai_message.content
                            else:
                                # Standard OpsBrain response - CEO style
                                prompt = f"""You are OpsBrain, a CEO-level AI assistant. Respond like a strategic executive.

Current tasks: {len(tasks)} pending
User request: '{user_text}'{context_prompt}

RESPONSE RULES:
- Task completed: "Task completed" or "Done"
- Issue found: "Issue: [specific problem]"
- Questions: 1-2 sentence strategic answer
- Requests: Confirm action or identify blocker
- No bullet points or long explanations
- Maximum 2 sentences unless complex strategy question
- Focus on revenue/efficiency blockers only

Respond:"""
                                ai_message = llm.invoke(prompt)
                                ai_response = ai_message.content
                            
                            # If database action was executed, prepend the result to the AI response
                            if db_result:
                                if db_result['success']:
                                    ai_response = f"✅ {db_result['message']}\n\n{ai_response}"
                                else:
                                    ai_response = f"❌ {db_result['message']}\n\n{ai_response}"
                        except Exception as e:
                            logger.error(f"OpenAI API error: {e}")
                            ai_response = "Sorry, I'm having trouble generating a response right now."
                    
                    # Update thread context with AI response
                    update_thread_context(None, channel, ai_response)
                    
                    # Post response directly in the channel
                    try:
                        slack_response = requests.post("https://slack.com/api/chat.postMessage", headers={
                            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                            "Content-type": "application/json"
                        }, json={
                            "channel": channel,
                            "text": add_version_timestamp(ai_response)
                        }, timeout=10)
                        
                        if not slack_response.ok:
                            logger.error(f"Slack API error: {slack_response.status_code} - {slack_response.text}")
                        else:
                            logger.info("Successfully sent slash command response")
                    except requests.RequestException as e:
                        logger.error(f"Failed to send message to Slack: {e}")
                        
                except Exception as e:
                    logger.error(f"Error in delayed response: {e}")
            
            # Start background thread with proper cleanup
            thread = threading.Thread(
                target=send_delayed_response, 
                name=f"slack-response-{int(time.time())}",
                daemon=True  # Dies when main process dies
            )
            thread.start()
            
            # Return immediate acknowledgment using the prepared response
            return immediate_response
        elif "event" in body:
            logger.info("Processing event subscription")
            slack_msg = SlackMessage(**body)
            event = slack_msg.event

            if event.get("subtype") == "bot_message":
                return {"ok": True}

            user_text = event["text"]
            channel = event["channel"]
            thread_ts = event.get("thread_ts")  # Get thread timestamp if message is in a thread
            
            # For events, get tasks and generate response directly (no timeout concern)
            tasks = fetch_open_tasks()
            task_list = "\n".join(f"- {t}" for t in tasks)
            
            # Get or create thread context for this conversation
            context = get_thread_context(thread_ts, channel, user_text)

            if not llm:
                response = "Sorry, OpenAI API key is not configured."
            else:
                try:
                    # Include conversation context in prompt if available
                    conversation_context = "\n".join(context['messages'][-6:]) if len(context['messages']) > 1 else ""
                    context_prompt = f"\n\nConversation context:\n{conversation_context}" if conversation_context else ""
                    
                    # Analyze the business context of the request
                    analysis = analyze_business_request(user_text)
                    
                    # Check if this requires database action
                    db_request = parse_database_request(user_text)
                    
                    # Execute database action if needed
                    db_result = None
                    if db_request['requires_db_action']:
                        db_result = execute_database_action(db_request['action'], **db_request['params'])
                        logger.info(f"Database action result: {db_result}")
                    
                    if analysis['request_type'] == 'help':
                        # Direct help response - no LLM needed
                        response = generate_help_response()
                    elif analysis['request_type'] == 'task_backlog':
                        # Trigger async task backlog generation for events
                        response = "🤖 I understand you want me to generate a task backlog. Let me analyze your business goals and create comprehensive tasks for you. This process will run in the background, and I'll update you with progress."
                        # Start the async task generation process safely
                        try:
                            import asyncio
                            # Check if there's already an event loop running
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Create task in existing loop
                                    asyncio.create_task(handle_task_backlog_request(user_text, business_goals, channel))
                                else:
                                    # Run in existing loop
                                    loop.run_until_complete(handle_task_backlog_request(user_text, business_goals, channel))
                            except RuntimeError:
                                # No loop exists, create new one
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    loop.run_until_complete(handle_task_backlog_request(user_text, business_goals, channel))
                                finally:
                                    loop.close()
                        except Exception as e:
                            logger.error(f"Error in task backlog generation: {e}")
                            response += "\n\n⚠️ There was an issue starting the task backlog generation. Please try again later."
                    elif analysis['is_ceo_focused'] or analysis['request_type'] in ['dashboard', 'goal_creation', 'planning']:
                        # Use CEO-focused response generation
                        if analysis['request_type'] in ['dashboard', 'goal_creation', 'planning']:
                            response = generate_ceo_insights(user_text, tasks, analysis)
                            if not response.startswith('📊') and not response.startswith('🎯') and not response.startswith('📋'):
                                # It's a prompt, not a direct response
                                ai_message = llm.invoke(response)
                                response = ai_message.content
                        else:
                            prompt = generate_ceo_insights(user_text, tasks, analysis)
                            ai_message = llm.invoke(prompt)
                            response = ai_message.content
                    else:
                        # Standard OpsBrain response - CEO style
                        prompt = f"""You are OpsBrain, a CEO-level AI assistant. Respond like a strategic executive.

Current tasks: {len(tasks)} pending
User request: '{user_text}'{context_prompt}

RESPONSE RULES:
- Task completed: "Task completed" or "Done"
- Issue found: "Issue: [specific problem]"
- Questions: 1-2 sentence strategic answer
- Requests: Confirm action or identify blocker
- No bullet points or long explanations
- Maximum 2 sentences unless complex strategy question
- Focus on revenue/efficiency blockers only

Respond:"""
                        ai_message = llm.invoke(prompt)
                        response = ai_message.content
                    
                    # If database action was executed, prepend the result to the response
                    if db_result:
                        if db_result['success']:
                            response = f"✅ {db_result['message']}\n\n{response}"
                        else:
                            response = f"❌ {db_result['message']}\n\n{response}"
                except Exception as e:
                    logger.error(f"OpenAI API error: {e}")
                    response = "Sorry, I'm having trouble generating a response right now."
            
            # Post the message via API (include thread_ts if this is a thread reply)
            message_data = {
                "channel": channel,
                "text": add_version_timestamp(response)
            }
            if thread_ts:
                message_data["thread_ts"] = thread_ts
            
            try:
                slack_response = requests.post("https://slack.com/api/chat.postMessage", headers={
                    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                    "Content-type": "application/json"
                }, json=message_data, timeout=10)
                
                if not slack_response.ok:
                    logger.error(f"Slack API error: {slack_response.status_code} - {slack_response.text}")
                else:
                    # Update thread context with AI response
                    update_thread_context(thread_ts, channel, response)
            except requests.RequestException as e:
                logger.error(f"Failed to send message to Slack: {e}")
            
        else:
            logger.error(f"Unknown Slack request format: {list(body.keys())}")
            return {"ok": True}
                
    except Exception as e:
        logger.error(f"Unexpected error in slack_events: {e}")
        # Still return ok to prevent Slack from retrying
        return {"ok": True}

    return {"ok": True}

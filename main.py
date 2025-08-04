from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from notion_client import Client as NotionClient
import os, requests, json, hmac, hashlib, time, logging, datetime
from typing import Optional, Dict, List
from notion_client.errors import APIResponseError
from dataclasses import dataclass, asdict
from enum import Enum

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

def load_business_goals_from_json(filename: str = "business_goals.json") -> None:
    """Load business goals from JSON file into memory."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                for goal_id, goal_data in data.items():
                    # Convert string enums back to enum objects
                    goal_data['area'] = BusinessArea(goal_data['area'].lower())
                    goal_data['status'] = GoalStatus(goal_data['status'])
                    goal_data['priority'] = Priority(goal_data['priority'])
                    
                    business_goals[goal_id] = BusinessGoal(**goal_data)
                
                logger.info(f"Loaded {len(business_goals)} business goals from {filename}")
        else:
            logger.warning(f"Business goals file {filename} not found. Starting with empty goals.")
    except Exception as e:
        logger.error(f"Error loading business goals from {filename}: {e}")
        logger.info("Starting with empty business goals.")

# Load business goals from JSON file at startup
load_business_goals_from_json()

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
    
    # Detect request type
    request_types = {
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
        'is_ceo_focused': any(word in user_lower for word in ['ceo', 'business', 'strategy', 'growth', 'revenue'])
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
        
        prompt = f"""You are OpsBrain, a strategic AI assistant for a solo dev founder building a $10K/month agency in under 30 hrs/week.

{business_context}

Current task backlog (top 5):
{task_list}

User request: "{user_text}"

As a CEO advisor, provide:
1. One strategic insight relevant to their request
2. Two specific, actionable next steps they can take today
3. One metric they should track to measure progress

Keep response under 200 words, focused on revenue growth and efficiency. Use bullet points for clarity."""
        
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

# Notion Database Management Functions
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
        if action_type == "create_task":
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
            
            # Start background task to send the actual response
            import threading
            
            def send_delayed_response():
                try:
                    # Simple context for this request (no thread detection)
                    context = {'messages': [f"User: {user_text}"], 'created_at': time.time()}
                    
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
                                # Standard OpsBrain response
                                prompt = f"""You are OpsBrain, a strategic assistant for a solo dev founder building a $10K/month agency in under 30 hrs/week. 

Current task backlog:
{task_list}

User request: '{user_text}'.{context_prompt}

Provide 1-2 focused actions or strategic insights that help grow the business. Focus on revenue, efficiency, and CEO-level priorities. Use bullet points for clarity."""
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
                    
                    # No thread context to update since we're posting directly in channel
                    
                    # Post response directly in the channel
                    try:
                        slack_response = requests.post("https://slack.com/api/chat.postMessage", headers={
                            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                            "Content-type": "application/json"
                        }, json={
                            "channel": channel,
                            "text": ai_response
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
            
            # Return immediate acknowledgment (this will be ephemeral and disappear)
            return {
                "text": "🤔 Let me analyze your tasks and get back to you...",
                "response_type": "ephemeral"  # Only visible to user who ran command
            }
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
            
            # Simple context for event messages
            context = {'messages': [f"User: {user_text}"], 'created_at': time.time()}

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
                        # Standard OpsBrain response
                        prompt = f"""You are OpsBrain, a strategic assistant for a solo dev founder building a $10K/month agency in under 30 hrs/week. 

Current task backlog:
{task_list}

User request: '{user_text}'.{context_prompt}

Provide 1-2 focused actions or strategic insights that help grow the business. Focus on revenue, efficiency, and CEO-level priorities. Use bullet points for clarity."""
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
                "text": response
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

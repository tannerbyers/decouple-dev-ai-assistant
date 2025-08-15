"""
AI Persona-based Prompt System

This module provides different AI personas and prompts based on request type.
It enables flexible response handling for various task management scenarios.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    """AI Persona types for different request handling."""
    TASK_MANAGER = "task_manager"        # Practical task operations
    CEO_STRATEGIST = "ceo_strategist"    # High-level strategic planning  
    ASSISTANT = "assistant"              # General helpful responses
    ANALYST = "analyst"                  # Data analysis and insights
    EXECUTOR = "executor"                # Direct action execution


class RequestType(Enum):
    """Request types that determine persona selection."""
    # Task Management (Practical)
    TASK_REVIEW = "task_review"          # Review/analyze existing tasks
    TASK_CLEANUP = "task_cleanup"        # Remove/clean tasks
    TASK_UPDATE = "task_update"          # Update task status/details
    TASK_CREATION = "task_creation"      # Create new tasks
    BULK_OPERATIONS = "bulk_operations"  # Mass task operations
    
    # Strategic Planning (CEO-level)
    STRATEGIC_PLANNING = "strategic_planning"  # High-level planning
    PRIORITY_SETTING = "priority_setting"     # Set priorities/focus
    BUSINESS_ANALYSIS = "business_analysis"   # Business insights
    GOAL_PLANNING = "goal_planning"           # Goal creation/planning
    
    # General
    HELP = "help"                        # Help requests
    GENERAL = "general"                  # General questions
    

@dataclass
class PromptContext:
    """Context information for prompt generation."""
    user_text: str
    tasks: List[str]
    business_goals: Dict
    dashboard_data: Dict
    conversation_context: List[str]
    detected_areas: List[str]
    task_count: int


class PersonaPrompts:
    """AI persona-specific prompts for different request types."""
    
    @staticmethod
    def task_manager_review(context: PromptContext) -> str:
        """Task Manager persona for reviewing/analyzing tasks."""
        return f"""You are a Task Manager AI - practical, direct, and focused on task efficiency.

Current Tasks: {context.task_count} tasks in system
User Request: "{context.user_text}"

Your job: Analyze tasks practically and provide actionable feedback.

TASK MANAGER STYLE:
- Be specific about what needs to change
- Focus on actionability and clarity
- Identify duplicates, outdated items, unclear tasks
- No high-level strategy unless asked
- Give direct recommendations: "Remove X because Y", "Update Z to include W"

Task List (showing first 20):
{chr(10).join(f"- {task}" for task in context.tasks[:20])}

Analyze these tasks and give practical recommendations:"""

    @staticmethod
    def task_manager_cleanup(context: PromptContext) -> str:
        """Task Manager persona for cleaning up tasks."""
        return f"""You are a Task Manager AI. The user wants to clean up their task list.

User Request: "{context.user_text}"
Total Tasks: {context.task_count}

TASK CLEANUP ANALYSIS:
Be aggressive in identifying tasks that should be removed:
1. Duplicates or near-duplicates  
2. Vague or unclear tasks
3. Outdated or irrelevant items
4. Tasks that don't contribute to business goals
5. Authentication errors or technical debt that's not blocking

RESPONSE FORMAT:
List specific task titles or patterns that should be removed.
For each, give a brief reason (duplicate, outdated, unclear, etc.).

Don't give strategic advice - just practical cleanup recommendations.

Tasks to analyze:
{chr(10).join(f"- {task}" for task in context.tasks[:30])}

Tasks to remove:"""

    @staticmethod
    def task_manager_bulk_update(context: PromptContext) -> str:
        """Task Manager persona for bulk task updates."""
        return f"""You are a Task Manager AI handling bulk task operations.

User Request: "{context.user_text}"
Current Tasks: {context.task_count}

BULK OPERATION HANDLER:
- Focus on efficient mass changes
- Understand patterns in user request
- Apply consistent updates across similar tasks
- Confirm what will be changed before executing

Available bulk operations:
- Update status (To Do → In Progress → Done)
- Change priority (High/Medium/Low)
- Add tags or categories  
- Update due dates
- Bulk deletion

Tell me exactly what bulk operation you want to perform and I'll execute it.

Current task sample:
{chr(10).join(f"- {task}" for task in context.tasks[:15])}

What bulk operation should I execute?"""

    @staticmethod
    def ceo_strategist_planning(context: PromptContext) -> str:
        """CEO Strategist persona for high-level planning."""
        business_context = ""
        if context.detected_areas:
            business_context += f"Focus areas: {', '.join(context.detected_areas)}\n"
        
        goal_summary = ""
        if context.business_goals:
            goal_summary = "\n".join([f"- {g.title}" for g in context.business_goals.values()][:3])
            business_context += f"Active goals:\n{goal_summary}\n"
        
        return f"""You are a CEO Strategist AI - think big picture, revenue-focused, strategic.

{business_context}
Current Tasks: {context.task_count} in system
User Request: "{context.user_text}"

CEO STRATEGIST MINDSET:
- What moves the revenue needle most?
- What are the highest-leverage activities?  
- What's missing from a business perspective?
- Focus on priorities and resource allocation
- Think in terms of business outcomes, not just task completion

STRATEGIC RECOMMENDATIONS:
1. **This Week's Priorities** - Top 3 revenue-impacting focuses
2. **Missing Elements** - What business areas need attention  
3. **Resource Allocation** - Where to spend time/energy
4. **Next Quarter Focus** - Strategic direction

Provide CEO-level strategic guidance for the request:"""

    @staticmethod
    def ceo_strategist_priorities(context: PromptContext) -> str:
        """CEO Strategist persona for priority setting."""
        return f"""You are a CEO Strategist AI focused on priority optimization.

User Request: "{context.user_text}"
Current Tasks: {context.task_count}
Business Areas Detected: {', '.join(context.detected_areas) if context.detected_areas else 'General'}

PRIORITY FRAMEWORK:
1. **Revenue Impact** - Direct revenue generation (sales, delivery)
2. **Revenue Enablers** - Systems that scale revenue (processes, product) 
3. **Risk Mitigation** - Preventing business disruption
4. **Growth Infrastructure** - Team, tools, processes for scale

PRIORITY ASSESSMENT:
Based on current business state, rank your top priorities this week.

High Priority (Do First):
Medium Priority (Do After):  
Low Priority (Do Later):
Eliminate (Don't Do):

Current task sample:
{chr(10).join(f"- {task}" for task in context.tasks[:10])}

What should be the focus priorities?"""

    @staticmethod
    def assistant_general(context: PromptContext) -> str:
        """General Assistant persona for flexible responses."""
        context_info = ""
        if context.conversation_context:
            recent_context = "\n".join(context.conversation_context[-4:])
            context_info = f"Recent conversation:\n{recent_context}\n\n"
            
        return f"""You are OpsBrain, a helpful AI assistant for business task management.

{context_info}User Request: "{context.user_text}"
Current Tasks: {context.task_count} in system

ASSISTANT APPROACH:
- Be directly helpful with whatever they're asking
- Don't assume they want strategic advice unless requested
- If they ask for specific information, provide it
- If they want task help, help with tasks
- Match the tone and complexity they're looking for
- Be practical and actionable

Respond helpfully to their specific request:"""

    @staticmethod
    def analyst_insights(context: PromptContext) -> str:
        """Analyst persona for data analysis and insights."""
        return f"""You are a Business Analyst AI focused on data-driven insights.

User Request: "{context.user_text}"
Total Tasks: {context.task_count}

ANALYST PERSPECTIVE:
- Look for patterns and trends  
- Identify data-driven insights
- Quantify problems and opportunities
- Provide evidence-based recommendations
- Focus on metrics and measurable outcomes

ANALYSIS AREAS:
- Task completion patterns
- Resource allocation efficiency  
- Bottleneck identification
- Performance metrics
- ROI optimization

Provide analytical insights based on available data:"""


class PersonaClassifier:
    """Classifies requests and determines appropriate AI persona."""
    
    def __init__(self):
        self.request_patterns = {
            # Task Management Patterns (Task Manager Persona)
            RequestType.TASK_REVIEW: [
                'review all tasks', 'analyze tasks', 'look at tasks', 'check tasks',
                'task analysis', 'evaluate tasks', 'assess tasks', 'audit tasks',
                'analyze my tasks', 'review my tasks', 'look at my tasks'
            ],
            RequestType.TASK_CLEANUP: [
                'clean up tasks', 'remove tasks', 'delete tasks', 'cleanup tasks',
                'remove irrelevant', 'doesnt make sense', "doesn't make sense", 
                'get rid of', 'eliminate tasks', 'prune tasks', 'remove duplicates',
                'clean up my tasks', 'cleanup my tasks'
            ],
            RequestType.TASK_UPDATE: [
                'update task', 'change task', 'modify task', 'edit task',
                'mark done', 'complete task', 'finish task', 'status update'
            ],
            RequestType.TASK_CREATION: [
                'create task', 'add task', 'new task', 'task:', 'todo:',
                'make task', 'generate task'
            ],
            RequestType.BULK_OPERATIONS: [
                'update all', 'change all', 'bulk update', 'mass update',
                'all tasks', 'everything', 'batch', 'multiple tasks',
                'mark all', 'set all', 'update all tasks', 'change all tasks'
            ],
            
            # Strategic Planning Patterns (CEO Strategist Persona)
            RequestType.STRATEGIC_PLANNING: [
                'strategy', 'strategic', 'business plan', 'roadmap', 'vision',
                'long term', 'big picture', 'growth', 'scale', 'expand'
            ],
            RequestType.PRIORITY_SETTING: [
                'priorities', 'focus', 'important', 'urgent', 'what should i',
                'where to spend', 'time allocation', 'resource allocation',
                'what should i focus', 'show me priorities', 'business priorities'
            ],
            RequestType.BUSINESS_ANALYSIS: [
                'business', 'revenue', 'growth', 'opportunities', 'market',
                'competitive', 'performance', 'metrics', 'kpi'
            ],
            RequestType.GOAL_PLANNING: [
                'goal', 'objective', 'target', 'milestone', 'achieve',
                'accomplish', 'aim', 'outcome'
            ],
            
            # General Patterns
            RequestType.HELP: ['help', 'how to', 'guide', 'tutorial', 'explain', 'how do i use'],
            RequestType.GENERAL: []  # Catch-all
        }
        
        self.persona_mapping = {
            RequestType.TASK_REVIEW: PersonaType.TASK_MANAGER,
            RequestType.TASK_CLEANUP: PersonaType.TASK_MANAGER,
            RequestType.TASK_UPDATE: PersonaType.TASK_MANAGER,
            RequestType.TASK_CREATION: PersonaType.TASK_MANAGER,
            RequestType.BULK_OPERATIONS: PersonaType.TASK_MANAGER,
            
            RequestType.STRATEGIC_PLANNING: PersonaType.CEO_STRATEGIST,
            RequestType.PRIORITY_SETTING: PersonaType.CEO_STRATEGIST,
            RequestType.BUSINESS_ANALYSIS: PersonaType.CEO_STRATEGIST,
            RequestType.GOAL_PLANNING: PersonaType.CEO_STRATEGIST,
            
            RequestType.HELP: PersonaType.ASSISTANT,
            RequestType.GENERAL: PersonaType.ASSISTANT
        }

    def classify_request(self, user_text: str, detected_areas: List[str] = None) -> tuple[RequestType, PersonaType]:
        """Classify user request and return request type and appropriate persona."""
        user_lower = user_text.lower()
        
        # Check for explicit strategic keywords that force CEO persona
        strategic_keywords = ['ceo', 'strategic', 'business strategy', 'revenue focus', 
                             'growth strategy', 'business priorities', 'what should i focus']
        if any(keyword in user_lower for keyword in strategic_keywords):
            return RequestType.STRATEGIC_PLANNING, PersonaType.CEO_STRATEGIST
        
        # Check patterns in order of specificity - most specific first
        priority_checks = [
            RequestType.TASK_CLEANUP,
            RequestType.TASK_REVIEW, 
            RequestType.BULK_OPERATIONS,
            RequestType.TASK_UPDATE,
            RequestType.TASK_CREATION,
            RequestType.PRIORITY_SETTING,
            RequestType.BUSINESS_ANALYSIS,
            RequestType.GOAL_PLANNING,
            RequestType.STRATEGIC_PLANNING,
            RequestType.HELP
        ]
        
        for request_type in priority_checks:
            patterns = self.request_patterns.get(request_type, [])
            if any(pattern in user_lower for pattern in patterns):
                persona = self.persona_mapping[request_type]
                logger.info(f"Classified request as {request_type.value} → {persona.value}")
                return request_type, persona
        
        # Default to general assistant
        return RequestType.GENERAL, PersonaType.ASSISTANT


class PersonaPromptManager:
    """Main manager for persona-based prompt generation."""
    
    def __init__(self):
        self.classifier = PersonaClassifier()
        self.prompts = PersonaPrompts()

    def generate_prompt(self, context: PromptContext) -> str:
        """Generate appropriate prompt based on request classification."""
        request_type, persona = self.classifier.classify_request(
            context.user_text, 
            context.detected_areas
        )
        
        logger.info(f"Using {persona.value} persona for {request_type.value} request")
        
        # Route to appropriate prompt based on request type and persona
        if persona == PersonaType.TASK_MANAGER:
            if request_type == RequestType.TASK_REVIEW:
                return self.prompts.task_manager_review(context)
            elif request_type == RequestType.TASK_CLEANUP:
                return self.prompts.task_manager_cleanup(context)
            elif request_type == RequestType.BULK_OPERATIONS:
                return self.prompts.task_manager_bulk_update(context)
            else:
                return self.prompts.task_manager_review(context)  # Default task manager
                
        elif persona == PersonaType.CEO_STRATEGIST:
            if request_type == RequestType.PRIORITY_SETTING:
                return self.prompts.ceo_strategist_priorities(context)
            else:
                return self.prompts.ceo_strategist_planning(context)  # Default CEO
                
        elif persona == PersonaType.ANALYST:
            return self.prompts.analyst_insights(context)
            
        else:  # ASSISTANT or fallback
            return self.prompts.assistant_general(context)

    def get_request_classification(self, user_text: str, detected_areas: List[str] = None) -> Dict[str, str]:
        """Get request classification info for debugging/logging."""
        request_type, persona = self.classifier.classify_request(user_text, detected_areas)
        return {
            'request_type': request_type.value,
            'persona': persona.value,
            'user_text': user_text,
            'detected_areas': detected_areas or []
        }

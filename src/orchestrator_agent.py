"""
Orchestrator Agent - Routes requests to appropriate specialized agents
Uses Strands SDK for deterministic agent orchestration
"""
import os
import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from strands import Strand, StrandConfig

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests the orchestrator can handle"""
    TASK_CREATE = "task_create"
    TASK_UPDATE = "task_update"
    TASK_COMPLETE = "task_complete"
    TASK_REMOVE = "task_remove"
    TASK_DISCOVERY = "task_discovery"
    PRIORITY_RANKING = "priority_ranking"
    DAILY_PRIORITY = "daily_priority"
    CHAT_TASK_ADD = "chat_task_add"
    GENERAL_QUERY = "general_query"


@dataclass
class AgentRequest:
    """Standard request format for agent communication"""
    request_type: RequestType
    user_input: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class AgentResponse:
    """Standard response format from agents"""
    success: bool
    data: Any
    message: str
    error: Optional[str] = None
    agent_used: Optional[str] = None


class OrchestratorAgent:
    """Main orchestrator that routes requests to specialized agents"""
    
    def __init__(self, config_path: str = "config/agents.yaml"):
        self.config_path = config_path
        self.agents = {}
        self.routing_rules = {}
        self.load_configuration()
        self.initialize_agents()
        
        logger.info("Orchestrator Agent initialized with routing capabilities")
    
    def load_configuration(self):
        """Load agent configuration and routing rules"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.routing_rules = config.get('routing_rules', {})
                    self.agent_configs = config.get('agents', {})
            else:
                logger.warning(f"Agent config file {self.config_path} not found, using defaults")
                self.setup_default_config()
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {e}")
            self.setup_default_config()
    
    def setup_default_config(self):
        """Set up default configuration if config file is missing"""
        self.routing_rules = {
            "task_create": "task_manager",
            "task_update": "task_manager", 
            "task_complete": "task_manager",
            "task_remove": "task_manager",
            "task_discovery": "task_discovery",
            "priority_ranking": "priority_engine",
            "daily_priority": "priority_engine",
            "chat_task_add": "chat_handler"
        }
        
        self.agent_configs = {
            "task_manager": {
                "name": "Task Manager",
                "capabilities": ["create", "update", "delete", "complete"],
                "prompt_template": "task_manager_prompt.yaml"
            },
            "task_discovery": {
                "name": "Task Discovery Agent",
                "capabilities": ["analyze_gaps", "suggest_tasks", "business_analysis"],
                "prompt_template": "task_discovery_prompt.yaml"
            },
            "priority_engine": {
                "name": "Priority Engine",
                "capabilities": ["score_tasks", "rank_priorities", "daily_selection"],
                "prompt_template": "priority_engine_prompt.yaml"
            },
            "chat_handler": {
                "name": "Chat Interface Handler",
                "capabilities": ["parse_chat", "extract_tasks", "natural_language"],
                "prompt_template": "chat_handler_prompt.yaml"
            }
        }
    
    def initialize_agents(self):
        """Initialize Strands SDK agents based on configuration"""
        try:
            # Configure Strands SDK
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            # Initialize each agent with Strands
            for agent_name, config in self.agent_configs.items():
                strand_config = StrandConfig(
                    name=config["name"],
                    model="gpt-4",
                    openai_api_key=openai_api_key,
                    temperature=0.1,  # Low temperature for deterministic responses
                    max_tokens=2000
                )
                
                # Load agent-specific prompt if available
                prompt_path = f"config/{config.get('prompt_template', 'default_prompt.yaml')}"
                agent_prompt = self.load_agent_prompt(prompt_path, agent_name)
                
                self.agents[agent_name] = Strand(
                    config=strand_config,
                    system_prompt=agent_prompt
                )
                
            logger.info(f"Initialized {len(self.agents)} Strands agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def load_agent_prompt(self, prompt_path: str, agent_name: str) -> str:
        """Load agent-specific prompt template"""
        try:
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    prompt_config = yaml.safe_load(f)
                    return prompt_config.get('system_prompt', self.get_default_prompt(agent_name))
            else:
                return self.get_default_prompt(agent_name)
        except Exception as e:
            logger.warning(f"Failed to load prompt for {agent_name}: {e}")
            return self.get_default_prompt(agent_name)
    
    def get_default_prompt(self, agent_name: str) -> str:
        """Get default prompt for an agent"""
        default_prompts = {
            "task_manager": """You are a Task Manager agent focused on CRUD operations for tasks.
Your role is to create, update, complete, and remove tasks efficiently.
Always provide clear confirmation of actions taken and maintain task data integrity.
Respond with structured data that can be processed programmatically.""",
            
            "task_discovery": """You are a Task Discovery agent specialized in identifying missing tasks.
Analyze business contexts, goals, and current task matrices to find gaps.
Suggest new tasks that align with business objectives and revenue generation.
Focus on actionable, specific tasks that move the business forward.""",
            
            "priority_engine": """You are a Priority Engine agent that scores and ranks tasks deterministically.
Use consistent scoring criteria: revenue impact, time to impact, effort, strategic value.
Provide numerical scores and clear ranking rationale.
Select daily priorities based on objective business criteria.""",
            
            "chat_handler": """You are a Chat Interface Handler that parses natural language requests.
Extract task information from conversational input and structure it for other agents.
Identify intent, extract task details, and format requests appropriately.
Handle ambiguous requests by asking clarifying questions."""
        }
        
        return default_prompts.get(agent_name, "You are a helpful AI agent.")
    
    def analyze_request(self, user_input: str, context: Dict[str, Any] = None) -> AgentRequest:
        """Analyze user input and determine request type and routing"""
        context = context or {}
        
        # Simple pattern matching for request type detection
        # In production, this could be more sophisticated
        user_lower = user_input.lower()
        
        if any(phrase in user_lower for phrase in ["create task", "add task", "new task"]):
            request_type = RequestType.TASK_CREATE
        elif any(phrase in user_lower for phrase in ["update task", "modify task", "change task"]):
            request_type = RequestType.TASK_UPDATE
        elif any(phrase in user_lower for phrase in ["complete task", "finish task", "done task"]):
            request_type = RequestType.TASK_COMPLETE
        elif any(phrase in user_lower for phrase in ["remove task", "delete task", "cancel task"]):
            request_type = RequestType.TASK_REMOVE
        elif any(phrase in user_lower for phrase in ["find tasks", "missing tasks", "discover tasks", "gap analysis"]):
            request_type = RequestType.TASK_DISCOVERY
        elif any(phrase in user_lower for phrase in ["prioritize", "rank tasks", "priority score"]):
            request_type = RequestType.PRIORITY_RANKING
        elif any(phrase in user_lower for phrase in ["daily priority", "today's task", "what should i work on"]):
            request_type = RequestType.DAILY_PRIORITY
        elif "task:" in user_lower or user_lower.startswith(("i need to", "i should", "i want to")):
            request_type = RequestType.CHAT_TASK_ADD
        else:
            request_type = RequestType.GENERAL_QUERY
        
        return AgentRequest(
            request_type=request_type,
            user_input=user_input,
            context=context,
            metadata={"analyzed_at": "now", "confidence": "high"}
        )
    
    def route_request(self, request: AgentRequest) -> str:
        """Determine which agent should handle the request"""
        request_type_str = request.request_type.value
        agent_name = self.routing_rules.get(request_type_str, "task_manager")
        
        # Fallback routing logic
        if agent_name not in self.agents:
            logger.warning(f"Agent {agent_name} not found, using task_manager as fallback")
            agent_name = "task_manager"
        
        return agent_name
    
    async def process_request(self, user_input: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Main method to process user requests through the agent system"""
        try:
            # Analyze the request
            request = self.analyze_request(user_input, context)
            
            # Route to appropriate agent
            agent_name = self.route_request(request)
            agent = self.agents[agent_name]
            
            logger.info(f"Routing request to {agent_name} for {request.request_type.value}")
            
            # Prepare the prompt for the agent
            agent_prompt = self.build_agent_prompt(request, agent_name)
            
            # Get response from the agent
            response = await agent.run(agent_prompt)
            
            return AgentResponse(
                success=True,
                data=response,
                message=f"Request processed by {agent_name}",
                agent_used=agent_name
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to process request",
                error=str(e)
            )
    
    def build_agent_prompt(self, request: AgentRequest, agent_name: str) -> str:
        """Build a structured prompt for the agent"""
        context_str = json.dumps(request.context, indent=2) if request.context else "No additional context"
        
        prompt = f"""
REQUEST TYPE: {request.request_type.value}
USER INPUT: {request.user_input}
CONTEXT: {context_str}

Please process this request according to your role as {agent_name}.
Provide a clear, actionable response that can be processed programmatically.
"""
        return prompt
    
    def get_daily_priority_task(self, context: Dict[str, Any] = None) -> AgentResponse:
        """Get the highest priority task for today - deterministic selection"""
        try:
            priority_request = AgentRequest(
                request_type=RequestType.DAILY_PRIORITY,
                user_input="What is the highest priority task for today?",
                context=context or {},
                metadata={"request_time": "now", "deterministic": True}
            )
            
            agent_name = self.route_request(priority_request)
            agent = self.agents[agent_name]
            
            # Build deterministic prompt
            prompt = f"""
You are tasked with selecting the single highest priority task for today.
Use these criteria in order of importance:
1. Revenue impact (0-5 scale)
2. Time to completion vs impact ratio
3. Strategic alignment with business goals
4. Urgency based on deadlines

CONTEXT: {json.dumps(priority_request.context, indent=2)}

Return the single highest priority task with:
- Task ID
- Title
- Reasoning for selection
- Expected completion time
- Revenue/business impact

Be deterministic - same inputs should always produce the same output.
"""
            
            # This would be synchronous in a real implementation
            # For now, we'll create a mock response
            return AgentResponse(
                success=True,
                data={
                    "task_id": "daily_priority_001",
                    "title": "Complete high-impact revenue task",
                    "reasoning": "Highest revenue impact with manageable time investment",
                    "completion_time": "2-3 hours",
                    "business_impact": "Direct revenue generation"
                },
                message="Daily priority task selected",
                agent_used=agent_name
            )
            
        except Exception as e:
            logger.error(f"Error getting daily priority: {e}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to get daily priority task",
                error=str(e)
            )
    
    def add_task_via_chat(self, chat_input: str) -> AgentResponse:
        """Add a task through natural language chat interface"""
        try:
            request = AgentRequest(
                request_type=RequestType.CHAT_TASK_ADD,
                user_input=chat_input,
                context={},
                metadata={"source": "chat", "parsed": True}
            )
            
            # Route to chat handler
            agent_name = self.route_request(request)
            
            # Mock response for now - in real implementation, this would call the agent
            return AgentResponse(
                success=True,
                data={
                    "task_title": f"Task extracted from: {chat_input[:50]}...",
                    "task_description": "Parsed from chat input",
                    "priority": "Medium",
                    "estimated_effort": "2-3 hours"
                },
                message="Task added via chat interface",
                agent_used=agent_name
            )
            
        except Exception as e:
            logger.error(f"Error adding task via chat: {e}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to add task via chat",
                error=str(e)
            )


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


def initialize_orchestrator(config_path: str = None) -> OrchestratorAgent:
    """Initialize the orchestrator with optional config path"""
    global _orchestrator
    config_path = config_path or "config/agents.yaml"
    _orchestrator = OrchestratorAgent(config_path)
    return _orchestrator

"""
Agent Integration Layer - Connects orchestrator system with existing main.py
Provides backward compatibility while enabling new agent-based functionality
Optimized for Slack's 3-second timeout constraints with background processing
"""
import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from notion_client import Client as NotionClient

# Import the new agent system
try:
    from .orchestrator_agent import OrchestratorAgent, initialize_orchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    # Fallback for missing Strands SDK or orchestrator
    logging.warning(f"Orchestrator not available (missing dependencies): {e}")
    OrchestratorAgent = None
    ORCHESTRATOR_AVAILABLE = False
    
    # Create mock initialize_orchestrator function
    def initialize_orchestrator(config_path: str = None):
        logging.warning("Using mock orchestrator initializer")
        return None

# Import agent modules with fallbacks to mock implementations
try:
    from .task_manager_agent import TaskManager
except ImportError:
    try:
        from .mock_task_manager import TaskManager
    except ImportError:
        try:
            from mock_task_manager import TaskManager
        except ImportError:
            TaskManager = None
    
try:
    from .task_discovery_agent import TaskDiscoveryAgent
except ImportError:
    try:
        from .mock_discovery_agent import DiscoveryAgent as TaskDiscoveryAgent
    except ImportError:
        try:
            from mock_discovery_agent import DiscoveryAgent as TaskDiscoveryAgent
        except ImportError:
            TaskDiscoveryAgent = None
    
try:
    from .priority_engine_agent import PriorityEngineAgent, PriorityContext
except ImportError:
    try:
        from .mock_priority_engine import PriorityEngine as PriorityEngineAgent
        # Create a simple PriorityContext class for mock compatibility
        class PriorityContext:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
    except ImportError:
        try:
            from mock_priority_engine import PriorityEngine as PriorityEngineAgent
            # Create a simple PriorityContext class for mock compatibility
            class PriorityContext:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
        except ImportError:
            PriorityEngineAgent = None
            PriorityContext = None
    
try:
    from .chat_handler_agent import ChatHandlerAgent
except ImportError:
    try:
        from .mock_chat_handler import ChatHandler as ChatHandlerAgent
    except ImportError:
        try:
            from mock_chat_handler import ChatHandler as ChatHandlerAgent
        except ImportError:
            ChatHandlerAgent = None

logger = logging.getLogger(__name__)


class AgentIntegration:
    """Integration layer for the agent system"""
    
    def __init__(self, notion_client: NotionClient, database_id: str):
        self.notion = notion_client
        self.database_id = database_id
        
        # Initialize individual agents (fallback for direct access)
        if TaskManager:
            self.task_manager = TaskManager(notion_client, database_id)
        else:
            logger.warning("TaskManager not available")
            self.task_manager = None
            
        if TaskDiscoveryAgent:
            self.task_discovery = TaskDiscoveryAgent()
        else:
            logger.warning("TaskDiscoveryAgent not available")
            self.task_discovery = None
            
        if PriorityEngineAgent:
            self.priority_engine = PriorityEngineAgent()
        else:
            logger.warning("PriorityEngineAgent not available")
            self.priority_engine = None
            
        if ChatHandlerAgent:
            self.chat_handler = ChatHandlerAgent()
        else:
            logger.warning("ChatHandlerAgent not available")
            self.chat_handler = None
        
        # Initialize orchestrator
        try:
            self.orchestrator = initialize_orchestrator()
            logger.info("Agent system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.orchestrator = None
    
    async def process_user_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for processing user requests through the agent system"""
        try:
            if not self.orchestrator:
                logger.warning("Orchestrator not available, using fallback processing")
                return await self._fallback_processing(user_input, context)
            
            # Use orchestrator to process request
            response = await self.orchestrator.process_request(user_input, context)
            
            if response.success:
                logger.info(f"Request processed successfully by {response.agent_used}")
                return {
                    "success": True,
                    "response": response.data,
                    "agent_used": response.agent_used,
                    "message": response.message
                }
            else:
                logger.error(f"Request processing failed: {response.error}")
                return {
                    "success": False,
                    "error": response.error,
                    "fallback_used": False
                }
        
        except Exception as e:
            logger.error(f"Error in agent processing: {e}")
            return await self._fallback_processing(user_input, context)
    
    async def get_daily_priority_task(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get the highest priority task for today"""
        try:
            if not self.task_manager:
                return {
                    "success": False,
                    "error": "Task manager not available",
                    "daily_priority": None
                }
                
            if not self.priority_engine:
                return {
                    "success": False,
                    "error": "Priority engine not available",
                    "daily_priority": None
                }
            
            # Get current tasks
            tasks_result = self.task_manager.list_tasks(limit=50)
            if not tasks_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve tasks",
                    "daily_priority": None
                }
            
            tasks = tasks_result["tasks"]
            
            # Create priority context if available
            priority_context = None
            if PriorityContext:
                priority_context = PriorityContext(
                    current_business_goals=[],  # Would load from business goals
                    available_time_hours=context.get("available_hours", 8) if context else 8,
                    current_revenue=context.get("current_revenue", 0) if context else 0,
                    target_revenue=context.get("target_revenue", 30000) if context else 30000,
                    business_stage=context.get("business_stage", "early_stage") if context else "early_stage",
                    constraints=context.get("constraints", {}) if context else {}
                )
            
            # Use priority engine to select daily priority
            result = self.priority_engine.get_daily_priority(tasks, priority_context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting daily priority: {e}")
            return {
                "success": False,
                "error": str(e),
                "daily_priority": None
            }
    
    async def add_task_via_chat(self, chat_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a task through natural language chat interface"""
        try:
            if not self.chat_handler:
                return {
                    "success": False,
                    "error": "Chat handler not available",
                    "task_id": None
                }
                
            if not self.task_manager:
                return {
                    "success": False,
                    "error": "Task manager not available",
                    "task_id": None
                }
            
            # Parse chat input
            parsed_result = self.chat_handler.create_task_from_chat(chat_input, context)
            
            if not parsed_result["success"]:
                return parsed_result
            
            # Create the task using task manager
            task_data = parsed_result["task_data"]
            creation_result = self.task_manager.create_task(task_data)
            
            if creation_result["success"]:
                return {
                    "success": True,
                    "task_id": creation_result["task_id"],
                    "message": f"Created task from chat: {task_data['title']}",
                    "parsed_request": parsed_result.get("parsed_request"),
                    "warnings": parsed_result.get("warnings", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create task: {creation_result['error']}",
                    "parsed_request": parsed_result.get("parsed_request")
                }
                
        except Exception as e:
            logger.error(f"Error adding task via chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": None
            }
    
    async def discover_missing_tasks(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Discover tasks that are missing from the current task matrix"""
        try:
            # Get current tasks
            tasks_result = self.task_manager.list_tasks(limit=100)
            if not tasks_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve current tasks for gap analysis"
                }
            
            current_tasks = tasks_result["tasks"]
            
            # Perform gap analysis
            gap_analysis = self.task_discovery.analyze_business_gaps(current_tasks)
            
            if gap_analysis["success"]:
                # Also get foundational task suggestions
                foundational_tasks = self.task_discovery.discover_missing_foundations()
                
                return {
                    "success": True,
                    "gap_analysis": gap_analysis,
                    "foundational_suggestions": foundational_tasks,
                    "total_gaps": sum(len(gaps) for gaps in gap_analysis.get("gaps_by_area", {}).values()),
                    "overall_coverage": gap_analysis.get("overall_coverage", 0)
                }
            else:
                return gap_analysis
                
        except Exception as e:
            logger.error(f"Error discovering missing tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_weekly_plan(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a weekly task plan based on business priorities"""
        try:
            # Generate weekly candidates
            weekly_plan = self.task_discovery.generate_weekly_task_candidates(context)
            
            if not weekly_plan["success"]:
                return weekly_plan
            
            # Score and rank the candidates
            candidates = weekly_plan["weekly_candidates"]
            
            # Convert to task format for priority engine
            candidate_tasks = []
            for candidate in candidates:
                candidate_tasks.append({
                    "id": f"candidate_{len(candidate_tasks)}",
                    "title": candidate["title"],
                    "description": candidate["description"],
                    "project": candidate["area"],
                    "priority": candidate["priority"],
                    "estimated_effort": candidate["estimated_effort"],
                    "due_date": candidate.get("due_date_suggestion")
                })
            
            # Create priority context
            priority_context = PriorityContext(
                current_business_goals=context.get("business_goals", []),
                available_time_hours=context.get("available_hours", 40),
                current_revenue=context.get("current_revenue", 0),
                target_revenue=context.get("target_revenue", 30000),
                business_stage=context.get("business_stage", "early_stage"),
                constraints=context.get("constraints", {})
            )
            
            # Score and rank
            scoring_result = self.priority_engine.score_tasks(candidate_tasks, priority_context)
            
            return {
                "success": True,
                "weekly_plan": weekly_plan,
                "scored_tasks": scoring_result.get("scored_tasks", []),
                "plan_summary": {
                    "total_candidates": len(candidates),
                    "estimated_time": weekly_plan.get("total_estimated_time", 0),
                    "time_available": weekly_plan.get("time_available", 40),
                    "priority_distribution": weekly_plan.get("priority_distribution", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task using the task manager"""
        if not self.task_manager:
            return {"success": False, "error": "Task manager not available"}
        return self.task_manager.create_task(task_data)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task using the task manager"""
        if not self.task_manager:
            return {"success": False, "error": "Task manager not available"}
        return self.task_manager.update_task(task_id, updates)
    
    def complete_task(self, task_id: str, completion_notes: str = None) -> Dict[str, Any]:
        """Complete a task using the task manager"""
        if not self.task_manager:
            return {"success": False, "error": "Task manager not available"}
        return self.task_manager.complete_task(task_id, completion_notes)
    
    def remove_task(self, task_id: str, reason: str = None) -> Dict[str, Any]:
        """Remove a task using the task manager"""
        if not self.task_manager:
            return {"success": False, "error": "Task manager not available"}
        return self.task_manager.remove_task(task_id, reason)
    
    def list_tasks(self, filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """List tasks using the task manager"""
        if not self.task_manager:
            return {"success": False, "error": "Task manager not available", "tasks": []}
        return self.task_manager.list_tasks(filters, limit)
    
    async def _fallback_processing(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback processing when orchestrator is not available"""
        try:
            user_lower = user_input.lower()
            
            # Simple pattern matching for fallback
            if any(phrase in user_lower for phrase in ["create task", "add task", "new task"]):
                # Try to create task via chat handler
                return await self.add_task_via_chat(user_input, context)
            
            elif any(phrase in user_lower for phrase in ["daily priority", "today's task", "what should i work on"]):
                # Get daily priority
                return await self.get_daily_priority_task(context)
            
            elif any(phrase in user_lower for phrase in ["missing tasks", "gap analysis", "discover tasks"]):
                # Discover missing tasks
                return await self.discover_missing_tasks(context)
            
            elif any(phrase in user_lower for phrase in ["weekly plan", "plan week", "generate plan"]):
                # Generate weekly plan
                return await self.generate_weekly_plan(context)
            
            else:
                # Default response
                return {
                    "success": False,
                    "error": "Could not process request - orchestrator unavailable and no fallback pattern matched",
                    "fallback_used": True,
                    "suggestion": "Try being more specific with your request (e.g., 'create task', 'daily priority', 'weekly plan')"
                }
                
        except Exception as e:
            logger.error(f"Error in fallback processing: {e}")
            return {
                "success": False,
                "error": f"Fallback processing failed: {str(e)}",
                "fallback_used": True
            }


# Global agent integration instance
_agent_integration = None


def get_agent_integration(notion_client: NotionClient = None, database_id: str = None) -> AgentIntegration:
    """Get or create the global agent integration instance"""
    global _agent_integration
    
    if _agent_integration is None:
        if not notion_client or not database_id:
            raise ValueError("notion_client and database_id are required for first initialization")
        _agent_integration = AgentIntegration(notion_client, database_id)
    
    return _agent_integration


def initialize_agent_integration(notion_client: NotionClient, database_id: str) -> AgentIntegration:
    """Initialize the agent integration system"""
    global _agent_integration
    _agent_integration = AgentIntegration(notion_client, database_id)
    return _agent_integration


# Convenience functions for backward compatibility with existing main.py code

async def agent_process_request(user_input: str, context: Dict[str, Any] = None) -> str:
    """Process user request and return formatted response string"""
    try:
        integration = get_agent_integration()
        result = await integration.process_user_request(user_input, context)
        
        if result["success"]:
            response = str(result.get("response", "Request processed successfully"))
            if result.get("agent_used"):
                response += f"\n\n_Processed by: {result['agent_used']}_"
            return response
        else:
            error_msg = result.get("error", "Unknown error occurred")
            if result.get("fallback_used"):
                error_msg += " (fallback processing attempted)"
            return f"❌ Error: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error in agent_process_request: {e}")
        return f"❌ System error: {str(e)}"


async def agent_process_request_with_timeout(user_input: str, context: Dict[str, Any] = None, 
                                          timeout_seconds: float = 2.5, 
                                          callback_function: Callable = None) -> Dict[str, Any]:
    """Process user request with timeout handling for Slack (3 second limit)
    
    Args:
        user_input: The user's request text
        context: Context dictionary for the request
        timeout_seconds: Timeout in seconds (default 2.5s for Slack's 3s limit)
        callback_function: Optional function to call with the result when processing completes
        
    Returns:
        Dict with immediate response for Slack and background task info
    """
    # Create immediate response for Slack
    immediate_response = {
        "response_type": "in_channel",
        "immediate_response": True,
        "text": "🤔 Processing your request...",
        "completed": False
    }
    
    # Start a background task to process the request
    async def background_task():
        try:
            # Get real response
            integration = get_agent_integration()
            start_time = time.time()
            result = await integration.process_user_request(user_input, context)
            processing_time = time.time() - start_time
            
            # Format the response
            if result["success"]:
                response_text = str(result.get("response", "Request processed successfully"))
                if result.get("agent_used"):
                    response_text += f"\n\n_Processed by: {result['agent_used']} in {processing_time:.2f}s_"
            else:
                error_msg = result.get("error", "Unknown error occurred")
                if result.get("fallback_used"):
                    error_msg += " (fallback processing attempted)"
                response_text = f"❌ Error: {error_msg}"
            
            # Call the callback with the complete response if provided
            if callback_function:
                # Add timing information
                result["processing_time"] = processing_time
                result["response_text"] = response_text
                await callback_function(result)
                
            logger.info(f"Background processing completed in {processing_time:.2f}s")
            return response_text
            
        except Exception as e:
            error_text = f"❌ Error in background processing: {str(e)}"
            logger.error(error_text)
            
            # Call callback with error if provided
            if callback_function:
                await callback_function({
                    "success": False,
                    "error": str(e),
                    "response_text": error_text
                })
            
            return error_text
    
    # Start the background task without waiting for it
    task = asyncio.create_task(background_task())
    
    # Add task to the response for tracking
    immediate_response["background_task"] = task
    
    return immediate_response


async def agent_get_daily_priority() -> str:
    """Get daily priority task as formatted string"""
    try:
        integration = get_agent_integration()
        result = await integration.get_daily_priority_task()
        
        if result["success"] and result.get("daily_priority"):
            priority_task = result["daily_priority"]
            response = f"🎯 **Today's Priority Task:**\n"
            response += f"**{priority_task['task_title']}** (Score: {priority_task['total_score']:.1f})\n\n"
            
            if result.get("reasoning"):
                response += f"**Why this task:**\n{result['reasoning']}\n"
            
            return response
        else:
            return "❌ No suitable priority task found for today"
            
    except Exception as e:
        logger.error(f"Error in agent_get_daily_priority: {e}")
        return f"❌ Error getting daily priority: {str(e)}"


async def agent_add_task_from_chat(chat_input: str) -> str:
    """Add task from chat and return formatted response"""
    try:
        integration = get_agent_integration()
        result = await integration.add_task_via_chat(chat_input)
        
        if result["success"]:
            response = f"✅ Task created: **{result.get('message', 'Task created successfully')}**"
            
            if result.get("warnings"):
                response += f"\n\n⚠️ **Warnings:**\n"
                for warning in result["warnings"]:
                    response += f"- {warning}\n"
            
            return response
        else:
            return f"❌ Failed to create task: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in agent_add_task_from_chat: {e}")
        return f"❌ Error creating task: {str(e)}"

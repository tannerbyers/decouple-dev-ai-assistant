"""
Mock Chat Handler - Simple implementation for testing
This provides basic conversational AI functionality without external dependencies
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChatHandler:
    """Mock chat handler for conversational AI interactions"""
    
    def __init__(self):
        logger.info("Mock ChatHandler initialized")
        
        # Pre-defined responses for common queries
        self.responses = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Greetings! I'm here to assist you."
            ],
            "task_help": [
                "I can help you create, update, or manage your tasks. What would you like to do?",
                "For task management, I can create new tasks, update existing ones, or help you prioritize your work.",
                "Let me help you with your tasks. Would you like to create a new task or manage existing ones?"
            ],
            "search_help": [
                "I can help you search for users, projects, or resources in your organization.",
                "What would you like to search for? I can find users, projects, documents, or other resources.",
                "I can discover information about people, projects, and resources. What are you looking for?"
            ],
            "priority_help": [
                "I can help you prioritize your tasks based on urgency, impact, and other factors.",
                "Let me analyze your tasks and provide priority recommendations.",
                "I can rank your tasks to help you focus on what matters most."
            ],
            "unknown": [
                "I'm not sure I understand that. Can you please rephrase your question?",
                "Could you provide more details about what you're looking for?",
                "I'm here to help with tasks, searches, and priorities. What would you like to do?"
            ]
        }
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a conversational message and return a response"""
        try:
            logger.info(f"Mock: Processing message: {message[:50]}...")
            
            message_lower = message.lower()
            response_type = self._classify_message(message_lower)
            
            # Get response based on classification
            response_options = self.responses.get(response_type, self.responses["unknown"])
            response_text = response_options[0]  # Use first response for consistency in testing
            
            # Add context-aware enhancements
            enhanced_response = self._enhance_response(response_text, message_lower, context)
            
            return {
                "success": True,
                "response": enhanced_response,
                "message_type": response_type,
                "confidence": 0.85,
                "context": context or {}
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm sorry, I encountered an error processing your message."
            }
    
    def generate_task_suggestion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a task suggestion based on context"""
        try:
            logger.info("Mock: Generating task suggestion")
            
            # Mock task suggestion based on context
            suggestions = [
                {
                    "title": "Follow up on high-priority customer inquiry",
                    "description": "Check status of customer issue and provide update",
                    "priority": "High",
                    "estimated_effort": "30 minutes"
                },
                {
                    "title": "Review and update project timeline",
                    "description": "Assess current project progress and adjust deadlines",
                    "priority": "Medium", 
                    "estimated_effort": "1 hour"
                },
                {
                    "title": "Prepare for upcoming team meeting",
                    "description": "Review agenda items and prepare status updates",
                    "priority": "Medium",
                    "estimated_effort": "20 minutes"
                }
            ]
            
            # Select suggestion based on context or default to first
            selected_suggestion = suggestions[0]
            
            return {
                "success": True,
                "suggestion": selected_suggestion,
                "reasoning": "Based on your recent activity and priorities, this task would have high impact.",
                "context": context or {}
            }
            
        except Exception as e:
            logger.error(f"Error generating task suggestion: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestion": None
            }
    
    def provide_context_summary(self, items: List[Dict[str, Any]], item_type: str) -> Dict[str, Any]:
        """Provide a conversational summary of items (tasks, users, projects, etc.)"""
        try:
            logger.info(f"Mock: Providing summary for {len(items)} {item_type} items")
            
            if not items:
                return {
                    "success": True,
                    "summary": f"No {item_type} items found matching your criteria.",
                    "count": 0
                }
            
            count = len(items)
            
            if item_type == "tasks":
                summary = self._summarize_tasks(items)
            elif item_type == "users":
                summary = self._summarize_users(items)
            elif item_type == "projects":
                summary = self._summarize_projects(items)
            else:
                summary = f"Found {count} {item_type} items."
            
            return {
                "success": True,
                "summary": summary,
                "count": count,
                "item_type": item_type
            }
            
        except Exception as e:
            logger.error(f"Error providing context summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": "Unable to provide summary."
            }
    
    def _classify_message(self, message: str) -> str:
        """Classify the type of message to determine appropriate response"""
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon"]
        task_keywords = ["task", "todo", "create", "add", "update", "complete", "finish"]
        search_keywords = ["find", "search", "look for", "who is", "what is", "show me"]
        priority_keywords = ["priority", "urgent", "important", "rank", "order"]
        
        if any(keyword in message for keyword in greeting_keywords):
            return "greeting"
        elif any(keyword in message for keyword in task_keywords):
            return "task_help"
        elif any(keyword in message for keyword in search_keywords):
            return "search_help"
        elif any(keyword in message for keyword in priority_keywords):
            return "priority_help"
        else:
            return "unknown"
    
    def _enhance_response(self, base_response: str, message: str, context: Dict[str, Any]) -> str:
        """Enhance the base response with context-specific information"""
        # Add user name if available in context
        if context and context.get("user_name"):
            base_response = base_response.replace("Hello!", f"Hello {context['user_name']}!")
            base_response = base_response.replace("Hi there!", f"Hi {context['user_name']}!")
        
        # Add specific suggestions based on message content
        if "create" in message and "task" in message:
            base_response += " Would you like me to help you create a specific task?"
        elif "search" in message:
            base_response += " What would you like to search for specifically?"
        elif "priority" in message:
            base_response += " I can analyze your current tasks and suggest priorities."
        
        return base_response
    
    def _summarize_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """Create a conversational summary of tasks"""
        count = len(tasks)
        
        # Count by priority if available
        high_priority = sum(1 for task in tasks if task.get("priority") == "High")
        medium_priority = sum(1 for task in tasks if task.get("priority") == "Medium")
        low_priority = sum(1 for task in tasks if task.get("priority") == "Low")
        
        summary = f"Found {count} tasks. "
        
        if high_priority > 0:
            summary += f"{high_priority} are high priority. "
        if medium_priority > 0:
            summary += f"{medium_priority} are medium priority. "
        if low_priority > 0:
            summary += f"{low_priority} are low priority."
        
        return summary.strip()
    
    def create_task_from_chat(self, chat_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse chat input and extract task creation data"""
        try:
            logger.info(f"Mock: Creating task from chat input: {chat_input[:50]}...")
            
            # Simple parsing logic for common task creation patterns
            chat_lower = chat_input.lower()
            
            # Extract task title
            title = chat_input.strip()
            if "create task" in chat_lower:
                # Remove "create task" prefix
                title = chat_input[chat_lower.find("create task") + len("create task"):].strip()
            elif "add task" in chat_lower:
                title = chat_input[chat_lower.find("add task") + len("add task"):].strip()
            elif "new task" in chat_lower:
                title = chat_input[chat_lower.find("new task") + len("new task"):].strip()
            
            # Clean up title
            if title.startswith(":"):
                title = title[1:].strip()
            if not title:
                title = "Task from chat: " + chat_input[:50]
            
            # Determine priority from keywords
            priority = "Medium"  # default
            if any(word in chat_lower for word in ["urgent", "asap", "immediately", "critical"]):
                priority = "High"
            elif any(word in chat_lower for word in ["when possible", "later", "low priority"]):
                priority = "Low"
            
            # Extract due date hints (simplified)
            due_date = None
            if "today" in chat_lower:
                due_date = datetime.now().strftime("%Y-%m-%d")
            elif "tomorrow" in chat_lower:
                due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            task_data = {
                "title": title,
                "description": f"Created from chat: {chat_input}",
                "priority": priority,
                "status": "To Do",
                "project": context.get("project", "General") if context else "General"
            }
            
            if due_date:
                task_data["due_date"] = due_date
            
            warnings = []
            if len(title) < 5:
                warnings.append("Task title is very short - consider adding more details")
            
            return {
                "success": True,
                "task_data": task_data,
                "parsed_request": {
                    "original_input": chat_input,
                    "detected_title": title,
                    "detected_priority": priority,
                    "detected_due_date": due_date
                },
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error creating task from chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_data": None
            }
    
    def _summarize_users(self, users: List[Dict[str, Any]]) -> str:
        """Create a conversational summary of users"""
        count = len(users)
        
        # Extract roles if available
        roles = [user.get("role", "Unknown") for user in users]
        unique_roles = list(set(roles))
        
        summary = f"Found {count} users"
        if unique_roles and "Unknown" not in unique_roles:
            summary += f" across {len(unique_roles)} different roles: {', '.join(unique_roles[:3])}"
            if len(unique_roles) > 3:
                summary += " and others"
        
        return summary + "."
    
    def _summarize_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Create a conversational summary of projects"""
        count = len(projects)
        
        # Count by status if available
        active = sum(1 for project in projects if project.get("status") == "active")
        planning = sum(1 for project in projects if project.get("status") == "planning")
        
        summary = f"Found {count} projects. "
        
        if active > 0:
            summary += f"{active} are currently active. "
        if planning > 0:
            summary += f"{planning} are in planning phase."
        
        return summary.strip()

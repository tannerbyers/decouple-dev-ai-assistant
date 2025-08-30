"""
Mock Task Manager Agent - Simple implementation for testing
This provides basic task management functionality without full dependencies
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from notion_client import Client as NotionClient

logger = logging.getLogger(__name__)


class TaskManager:
    """Mock task manager for basic CRUD operations"""
    
    def __init__(self, notion_client: NotionClient, database_id: str):
        self.notion = notion_client
        self.database_id = database_id
        logger.info(f"Mock TaskManager initialized for database {database_id}")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Mock task creation - in production this would create in Notion
            task_id = str(uuid.uuid4())
            title = task_data.get("title", "Untitled Task")
            
            logger.info(f"Mock: Creating task '{title}'")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task '{title}' created successfully",
                "data": {
                    "id": task_id,
                    "title": title,
                    "status": task_data.get("status", "To Do"),
                    "priority": task_data.get("priority", "Medium"),
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": None
            }
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            logger.info(f"Mock: Updating task {task_id} with {updates}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task updated successfully",
                "updates_applied": updates
            }
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_task(self, task_id: str, completion_notes: str = None) -> Dict[str, Any]:
        """Mark a task as completed"""
        try:
            logger.info(f"Mock: Completing task {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task marked as completed",
                "completion_notes": completion_notes
            }
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def remove_task(self, task_id: str, reason: str = None) -> Dict[str, Any]:
        """Remove/delete a task"""
        try:
            logger.info(f"Mock: Removing task {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task removed successfully",
                "reason": reason
            }
        except Exception as e:
            logger.error(f"Error removing task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_tasks(self, filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """List tasks with optional filtering"""
        try:
            # Mock task list - in production this would query Notion
            mock_tasks = [
                {
                    "id": "task-1",
                    "title": "High priority sales task",
                    "status": "To Do",
                    "priority": "High",
                    "project": "Sales",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "task-2", 
                    "title": "Medium priority marketing task",
                    "status": "In Progress",
                    "priority": "Medium",
                    "project": "Marketing",
                    "created_at": "2024-01-01T01:00:00Z"
                },
                {
                    "id": "task-3",
                    "title": "Low priority operations task",
                    "status": "To Do",
                    "priority": "Low",
                    "project": "Operations",
                    "created_at": "2024-01-01T02:00:00Z"
                }
            ]
            
            # Apply filters if provided
            filtered_tasks = mock_tasks
            if filters:
                if filters.get("status"):
                    filtered_tasks = [t for t in filtered_tasks if t["status"] == filters["status"]]
                if filters.get("priority"):
                    filtered_tasks = [t for t in filtered_tasks if t["priority"] == filters["priority"]]
            
            # Apply limit
            limited_tasks = filtered_tasks[:limit]
            
            logger.info(f"Mock: Listed {len(limited_tasks)} tasks")
            
            return {
                "success": True,
                "tasks": limited_tasks,
                "total_count": len(limited_tasks),
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }

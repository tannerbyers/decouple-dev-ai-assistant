"""
Task Manager Agent - Handles CRUD operations for tasks
Integrates with Notion API for persistent task storage
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from notion_client import Client as NotionClient

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Task data structure"""
    id: Optional[str]
    title: str
    description: str
    status: str
    priority: str
    project: Optional[str]
    due_date: Optional[str]
    created_date: str
    estimated_effort: Optional[str]
    tags: List[str]
    notes: Optional[str] = None


class TaskManager:
    """Agent responsible for task CRUD operations"""
    
    def __init__(self, notion_client: NotionClient, database_id: str):
        self.notion = notion_client
        self.database_id = database_id
        self.valid_statuses = ["To Do", "In Progress", "Blocked", "Done", "Cancelled"]
        self.valid_priorities = ["Low", "Medium", "High", "Critical"]
        
        logger.info("Task Manager initialized with Notion integration")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in the system"""
        try:
            # Validate required fields
            if not task_data.get("title"):
                return {
                    "success": False,
                    "error": "Task title is required",
                    "task_id": None
                }
            
            # Build task object with defaults
            task = Task(
                id=None,  # Will be set by Notion
                title=task_data["title"],
                description=task_data.get("description", ""),
                status=task_data.get("status", "To Do"),
                priority=task_data.get("priority", "Medium"),
                project=task_data.get("project"),
                due_date=task_data.get("due_date"),
                created_date=datetime.now().isoformat(),
                estimated_effort=task_data.get("estimated_effort", "Medium"),
                tags=task_data.get("tags", []),
                notes=task_data.get("notes")
            )
            
            # Validate status and priority
            if task.status not in self.valid_statuses:
                task.status = "To Do"
            if task.priority not in self.valid_priorities:
                task.priority = "Medium"
            
            # Create in Notion
            notion_task = self._create_notion_task(task)
            if notion_task:
                logger.info(f"Successfully created task: {task.title}")
                return {
                    "success": True,
                    "task_id": notion_task["id"],
                    "message": f"Created task: {task.title}",
                    "task_data": asdict(task)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create task in Notion",
                    "task_id": None
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
            # Get current task data
            current_task = self.get_task(task_id)
            if not current_task or not current_task.get("success"):
                return {
                    "success": False,
                    "error": f"Task {task_id} not found",
                    "task_id": task_id
                }
            
            # Apply updates
            task_data = current_task["task_data"]
            for key, value in updates.items():
                if key in task_data:
                    task_data[key] = value
            
            # Validate updated values
            if task_data.get("status") not in self.valid_statuses:
                task_data["status"] = "To Do"
            if task_data.get("priority") not in self.valid_priorities:
                task_data["priority"] = "Medium"
            
            # Update in Notion
            success = self._update_notion_task(task_id, updates)
            if success:
                logger.info(f"Successfully updated task: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": f"Updated task {task_id}",
                    "updated_fields": list(updates.keys())
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update task in Notion",
                    "task_id": task_id
                }
                
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    def complete_task(self, task_id: str, completion_notes: str = None) -> Dict[str, Any]:
        """Mark a task as completed"""
        try:
            updates = {
                "status": "Done",
                "completed_date": datetime.now().isoformat()
            }
            
            if completion_notes:
                current_task = self.get_task(task_id)
                if current_task and current_task.get("success"):
                    existing_notes = current_task["task_data"].get("notes", "")
                    completion_note = f"Completed on {datetime.now().strftime('%Y-%m-%d')}: {completion_notes}"
                    updates["notes"] = f"{existing_notes}\n\n{completion_note}" if existing_notes else completion_note
            
            result = self.update_task(task_id, updates)
            if result["success"]:
                result["message"] = f"Task {task_id} marked as completed"
                logger.info(f"Task completed: {task_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    def remove_task(self, task_id: str, reason: str = None) -> Dict[str, Any]:
        """Remove (archive) a task from the system"""
        try:
            # Add removal note if reason provided
            if reason:
                removal_note = f"Task removed on {datetime.now().strftime('%Y-%m-%d')}: {reason}"
                self.update_task(task_id, {"notes": removal_note})
            
            # Archive in Notion (soft delete)
            success = self._archive_notion_task(task_id)
            if success:
                logger.info(f"Task archived: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": f"Task {task_id} archived successfully",
                    "reason": reason
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to archive task in Notion",
                    "task_id": task_id
                }
                
        except Exception as e:
            logger.error(f"Error removing task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a single task by ID"""
        try:
            notion_page = self.notion.pages.retrieve(page_id=task_id)
            task_data = self._parse_notion_task(notion_page)
            
            if task_data:
                return {
                    "success": True,
                    "task_id": task_id,
                    "task_data": task_data
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to parse task data",
                    "task_id": task_id
                }
                
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    def list_tasks(self, filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """List tasks with optional filters"""
        try:
            # Build Notion query filters
            notion_filter = self._build_notion_filters(filters or {})
            
            # Query Notion database
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter=notion_filter,
                page_size=min(limit, 100)
            )
            
            tasks = []
            for page in response["results"]:
                task_data = self._parse_notion_task(page)
                if task_data:
                    tasks.append(task_data)
            
            logger.info(f"Retrieved {len(tasks)} tasks")
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks),
                "has_more": response.get("has_more", False)
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }
    
    def get_tasks_by_priority(self, priority: str = "High") -> Dict[str, Any]:
        """Get tasks filtered by priority level"""
        return self.list_tasks(filters={"priority": priority})
    
    def get_overdue_tasks(self) -> Dict[str, Any]:
        """Get tasks that are past their due date"""
        today = datetime.now().date().isoformat()
        return self.list_tasks(filters={"due_date_before": today, "status_not": "Done"})
    
    def get_tasks_by_project(self, project: str) -> Dict[str, Any]:
        """Get tasks filtered by project"""
        return self.list_tasks(filters={"project": project})
    
    def bulk_update_tasks(self, task_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update multiple tasks in batch"""
        try:
            results = []
            successful = 0
            failed = 0
            
            for update in task_updates:
                task_id = update.get("task_id")
                updates = update.get("updates", {})
                
                if not task_id:
                    results.append({
                        "task_id": None,
                        "success": False,
                        "error": "task_id is required"
                    })
                    failed += 1
                    continue
                
                result = self.update_task(task_id, updates)
                results.append(result)
                
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
            
            logger.info(f"Bulk update completed: {successful} successful, {failed} failed")
            return {
                "success": True,
                "results": results,
                "summary": {
                    "total": len(task_updates),
                    "successful": successful,
                    "failed": failed
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _create_notion_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Create task in Notion database"""
        try:
            # Get database schema to check available properties
            db_info = self.notion.databases.retrieve(database_id=self.database_id)
            available_props = set(db_info['properties'].keys())
            
            # Build properties based on available fields
            properties = {}
            
            # Title (required)
            title_prop = self._find_property_by_type(db_info['properties'], 'title')
            if title_prop:
                properties[title_prop] = {"title": [{"text": {"content": task.title}}]}
            
            # Status
            if "Status" in available_props and task.status:
                properties["Status"] = {"select": {"name": task.status}}
            
            # Priority
            if "Priority" in available_props and task.priority:
                properties["Priority"] = {"select": {"name": task.priority}}
            
            # Project/Category
            if task.project:
                for prop_name in ["Project", "Category", "Area"]:
                    if prop_name in available_props:
                        prop_type = db_info['properties'][prop_name]['type']
                        if prop_type == 'select':
                            properties[prop_name] = {"select": {"name": task.project}}
                        elif prop_type == 'rich_text':
                            properties[prop_name] = {"rich_text": [{"text": {"content": task.project}}]}
                        break
            
            # Description/Notes
            if task.description or task.notes:
                content = f"{task.description}\n\n{task.notes}" if task.notes else task.description
                for prop_name in ["Description", "Notes", "Details"]:
                    if prop_name in available_props:
                        properties[prop_name] = {"rich_text": [{"text": {"content": content}}]}
                        break
            
            # Due Date
            if task.due_date and "Due Date" in available_props:
                properties["Due Date"] = {"date": {"start": task.due_date}}
            
            # Create page
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create Notion task: {e}")
            return None
    
    def _update_notion_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task in Notion"""
        try:
            # Get database schema
            db_info = self.notion.databases.retrieve(database_id=self.database_id)
            available_props = set(db_info['properties'].keys())
            
            properties = {}
            
            # Map updates to Notion properties
            for key, value in updates.items():
                if key == "status" and "Status" in available_props:
                    properties["Status"] = {"select": {"name": value}}
                elif key == "priority" and "Priority" in available_props:
                    properties["Priority"] = {"select": {"name": value}}
                elif key == "notes" and value:
                    for prop_name in ["Notes", "Description", "Details"]:
                        if prop_name in available_props:
                            properties[prop_name] = {"rich_text": [{"text": {"content": value}}]}
                            break
                elif key == "due_date" and "Due Date" in available_props and value:
                    properties["Due Date"] = {"date": {"start": value}}
            
            if properties:
                self.notion.pages.update(page_id=task_id, properties=properties)
                return True
            else:
                logger.warning(f"No properties to update for task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update Notion task {task_id}: {e}")
            return False
    
    def _archive_notion_task(self, task_id: str) -> bool:
        """Archive task in Notion"""
        try:
            self.notion.pages.update(page_id=task_id, archived=True)
            return True
        except Exception as e:
            logger.error(f"Failed to archive Notion task {task_id}: {e}")
            return False
    
    def _parse_notion_task(self, notion_page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Notion page into task data"""
        try:
            props = notion_page["properties"]
            
            # Get title
            title = ""
            title_prop = self._find_property_by_type(props, 'title')
            if title_prop and props[title_prop]['title']:
                title = props[title_prop]['title'][0]['text']['content']
            
            # Get other properties
            status = self._get_select_value(props, "Status")
            priority = self._get_select_value(props, "Priority")
            project = self._get_text_value(props, ["Project", "Category", "Area"])
            description = self._get_text_value(props, ["Description", "Notes", "Details"])
            due_date = self._get_date_value(props, "Due Date")
            
            return {
                "id": notion_page["id"],
                "title": title,
                "description": description or "",
                "status": status or "To Do",
                "priority": priority or "Medium",
                "project": project,
                "due_date": due_date,
                "created_date": notion_page["created_time"],
                "last_edited": notion_page["last_edited_time"],
                "url": notion_page["url"]
            }
            
        except Exception as e:
            logger.error(f"Error parsing Notion task: {e}")
            return None
    
    def _find_property_by_type(self, properties: Dict[str, Any], prop_type: str) -> Optional[str]:
        """Find property name by type"""
        for name, prop in properties.items():
            if prop.get('type') == prop_type:
                return name
        return None
    
    def _get_select_value(self, props: Dict[str, Any], prop_name: str) -> Optional[str]:
        """Get select property value"""
        if prop_name in props and props[prop_name]['select']:
            return props[prop_name]['select']['name']
        return None
    
    def _get_text_value(self, props: Dict[str, Any], prop_names: List[str]) -> Optional[str]:
        """Get text/rich_text property value"""
        for prop_name in prop_names:
            if prop_name in props:
                if props[prop_name].get('rich_text'):
                    return props[prop_name]['rich_text'][0]['text']['content']
                elif props[prop_name].get('title'):
                    return props[prop_name]['title'][0]['text']['content']
        return None
    
    def _get_date_value(self, props: Dict[str, Any], prop_name: str) -> Optional[str]:
        """Get date property value"""
        if prop_name in props and props[prop_name]['date']:
            return props[prop_name]['date']['start']
        return None
    
    def _build_notion_filters(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build Notion API filters from simple filter dict"""
        if not filters:
            return None
        
        notion_filters = []
        
        for key, value in filters.items():
            if key == "status":
                notion_filters.append({
                    "property": "Status",
                    "select": {"equals": value}
                })
            elif key == "status_not":
                notion_filters.append({
                    "property": "Status", 
                    "select": {"does_not_equal": value}
                })
            elif key == "priority":
                notion_filters.append({
                    "property": "Priority",
                    "select": {"equals": value}
                })
            elif key == "project":
                notion_filters.append({
                    "property": "Project",
                    "rich_text": {"contains": value}
                })
            elif key == "due_date_before":
                notion_filters.append({
                    "property": "Due Date",
                    "date": {"before": value}
                })
        
        if len(notion_filters) == 1:
            return notion_filters[0]
        elif len(notion_filters) > 1:
            return {"and": notion_filters}
        else:
            return None

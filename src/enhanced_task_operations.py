"""
Enhanced Task Operations

This module provides comprehensive task management operations including
bulk updates, intelligent filtering, and advanced task analysis.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class BulkOperationType(Enum):
    """Types of bulk operations that can be performed on tasks."""
    STATUS_UPDATE = "status_update"
    PRIORITY_UPDATE = "priority_update"
    BULK_DELETE = "bulk_delete"
    TAG_UPDATE = "tag_update"
    DUE_DATE_UPDATE = "due_date_update"
    NOTES_APPEND = "notes_append"
    PROJECT_ASSIGNMENT = "project_assignment"


@dataclass
class TaskFilter:
    """Filter criteria for task operations."""
    status: Optional[str] = None
    priority: Optional[str] = None
    project: Optional[str] = None
    contains_text: Optional[str] = None
    created_before: Optional[str] = None
    created_after: Optional[str] = None
    has_due_date: Optional[bool] = None


@dataclass
class BulkOperation:
    """Represents a bulk operation to be performed on tasks."""
    operation_type: BulkOperationType
    filters: TaskFilter
    new_values: Dict[str, Any]
    confirmation_required: bool = True
    
    
@dataclass 
class TaskOperationResult:
    """Result of a task operation."""
    success: bool
    affected_count: int
    message: str
    affected_tasks: List[Dict] = None
    errors: List[str] = None


class EnhancedTaskOperations:
    """Enhanced task operations with bulk capabilities."""
    
    def __init__(self, notion_client, database_id: str):
        self.notion = notion_client
        self.db_id = database_id
        
    async def get_all_tasks_detailed(self) -> List[Dict[str, Any]]:
        """Get all tasks with complete details for analysis."""
        try:
            response = await asyncio.to_thread(
                self.notion.databases.query, 
                database_id=self.db_id
            )
            
            tasks = []
            for page in response['results']:
                try:
                    props = page['properties']
                    
                    # Extract task details safely
                    task_data = {
                        'id': page['id'],
                        'title': self._extract_title(props.get('Task', {})),
                        'status': self._extract_select(props.get('Status', {})),
                        'priority': self._extract_select(props.get('Priority', {})),
                        'project': self._extract_rich_text(props.get('Project', {})),
                        'notes': self._extract_rich_text(props.get('Notes', {})),
                        'due_date': self._extract_date(props.get('Due Date', {})),
                        'created_time': page.get('created_time'),
                        'last_edited_time': page.get('last_edited_time'),
                        'url': page.get('url', '')
                    }
                    
                    tasks.append(task_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing task {page.get('id', 'unknown')}: {e}")
                    continue
                    
            logger.info(f"Retrieved {len(tasks)} detailed tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching detailed tasks: {e}")
            return []
    
    def _extract_title(self, title_prop: Dict) -> str:
        """Extract title from Notion title property."""
        try:
            return title_prop.get('title', [{}])[0].get('text', {}).get('content', '')
        except (IndexError, KeyError):
            return ''
    
    def _extract_select(self, select_prop: Dict) -> str:
        """Extract value from Notion select property."""
        try:
            return select_prop.get('select', {}).get('name', '')
        except (KeyError, TypeError):
            return ''
    
    def _extract_rich_text(self, rich_text_prop: Dict) -> str:
        """Extract text from Notion rich text property."""
        try:
            rich_texts = rich_text_prop.get('rich_text', [])
            if rich_texts:
                return rich_texts[0].get('text', {}).get('content', '')
            return ''
        except (IndexError, KeyError, TypeError):
            return ''
    
    def _extract_date(self, date_prop: Dict) -> str:
        """Extract date from Notion date property."""
        try:
            date_obj = date_prop.get('date')
            if date_obj:
                return date_obj.get('start', '')
            return ''
        except (KeyError, TypeError):
            return ''
    
    def filter_tasks(self, tasks: List[Dict], task_filter: TaskFilter) -> List[Dict]:
        """Filter tasks based on criteria."""
        filtered = tasks
        
        if task_filter.status:
            filtered = [t for t in filtered if t['status'].lower() == task_filter.status.lower()]
            
        if task_filter.priority:
            filtered = [t for t in filtered if t['priority'].lower() == task_filter.priority.lower()]
            
        if task_filter.project:
            filtered = [t for t in filtered if task_filter.project.lower() in t['project'].lower()]
            
        if task_filter.contains_text:
            text = task_filter.contains_text.lower()
            filtered = [t for t in filtered 
                       if text in t['title'].lower() or text in t['notes'].lower()]
        
        if task_filter.has_due_date is not None:
            if task_filter.has_due_date:
                filtered = [t for t in filtered if t['due_date']]
            else:
                filtered = [t for t in filtered if not t['due_date']]
        
        return filtered
    
    async def execute_bulk_operation(self, operation: BulkOperation) -> TaskOperationResult:
        """Execute a bulk operation on filtered tasks."""
        try:
            # Get all tasks
            all_tasks = await self.get_all_tasks_detailed()
            
            # Filter tasks based on criteria  
            target_tasks = self.filter_tasks(all_tasks, operation.filters)
            
            if not target_tasks:
                return TaskOperationResult(
                    success=True,
                    affected_count=0,
                    message="No tasks matched the filter criteria.",
                    affected_tasks=[]
                )
            
            # Execute the operation based on type
            if operation.operation_type == BulkOperationType.STATUS_UPDATE:
                return await self._bulk_status_update(target_tasks, operation.new_values['status'])
            elif operation.operation_type == BulkOperationType.PRIORITY_UPDATE:
                return await self._bulk_priority_update(target_tasks, operation.new_values['priority'])
            elif operation.operation_type == BulkOperationType.BULK_DELETE:
                return await self._bulk_delete(target_tasks)
            elif operation.operation_type == BulkOperationType.PROJECT_ASSIGNMENT:
                return await self._bulk_project_assignment(target_tasks, operation.new_values['project'])
            elif operation.operation_type == BulkOperationType.NOTES_APPEND:
                return await self._bulk_notes_append(target_tasks, operation.new_values['note'])
            else:
                return TaskOperationResult(
                    success=False,
                    affected_count=0,
                    message=f"Unsupported operation type: {operation.operation_type.value}",
                    errors=["Operation not implemented"]
                )
                
        except Exception as e:
            logger.error(f"Error executing bulk operation: {e}")
            return TaskOperationResult(
                success=False,
                affected_count=0,
                message=f"Error executing bulk operation: {str(e)}",
                errors=[str(e)]
            )
    
    async def _bulk_status_update(self, tasks: List[Dict], new_status: str) -> TaskOperationResult:
        """Update status for multiple tasks."""
        success_count = 0
        errors = []
        
        for task in tasks:
            try:
                await asyncio.to_thread(
                    self.notion.pages.update,
                    page_id=task['id'],
                    properties={"Status": {"select": {"name": new_status}}}
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to update {task['title']}: {str(e)}")
        
        return TaskOperationResult(
            success=success_count > 0,
            affected_count=success_count,
            message=f"Updated status to '{new_status}' for {success_count}/{len(tasks)} tasks",
            affected_tasks=[{'id': t['id'], 'title': t['title']} for t in tasks[:success_count]],
            errors=errors
        )
    
    async def _bulk_priority_update(self, tasks: List[Dict], new_priority: str) -> TaskOperationResult:
        """Update priority for multiple tasks.""" 
        success_count = 0
        errors = []
        
        for task in tasks:
            try:
                await asyncio.to_thread(
                    self.notion.pages.update,
                    page_id=task['id'],
                    properties={"Priority": {"select": {"name": new_priority}}}
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to update {task['title']}: {str(e)}")
        
        return TaskOperationResult(
            success=success_count > 0,
            affected_count=success_count,
            message=f"Updated priority to '{new_priority}' for {success_count}/{len(tasks)} tasks",
            affected_tasks=[{'id': t['id'], 'title': t['title']} for t in tasks[:success_count]],
            errors=errors
        )
    
    async def _bulk_delete(self, tasks: List[Dict]) -> TaskOperationResult:
        """Archive/delete multiple tasks."""
        success_count = 0
        errors = []
        
        for task in tasks:
            try:
                await asyncio.to_thread(
                    self.notion.pages.update,
                    page_id=task['id'],
                    archived=True
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to delete {task['title']}: {str(e)}")
        
        return TaskOperationResult(
            success=success_count > 0,
            affected_count=success_count,
            message=f"Archived {success_count}/{len(tasks)} tasks",
            affected_tasks=[{'id': t['id'], 'title': t['title']} for t in tasks[:success_count]],
            errors=errors
        )
    
    async def _bulk_project_assignment(self, tasks: List[Dict], project: str) -> TaskOperationResult:
        """Assign project to multiple tasks."""
        success_count = 0
        errors = []
        
        for task in tasks:
            try:
                await asyncio.to_thread(
                    self.notion.pages.update,
                    page_id=task['id'],
                    properties={"Project": {"rich_text": [{"text": {"content": project}}]}}
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to update {task['title']}: {str(e)}")
        
        return TaskOperationResult(
            success=success_count > 0,
            affected_count=success_count,
            message=f"Assigned project '{project}' to {success_count}/{len(tasks)} tasks",
            affected_tasks=[{'id': t['id'], 'title': t['title']} for t in tasks[:success_count]],
            errors=errors
        )
    
    async def _bulk_notes_append(self, tasks: List[Dict], note: str) -> TaskOperationResult:
        """Append note to multiple tasks."""
        success_count = 0
        errors = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for task in tasks:
            try:
                existing_notes = task.get('notes', '')
                new_notes = f"{existing_notes}\n\n[{timestamp}] {note}".strip()
                
                await asyncio.to_thread(
                    self.notion.pages.update,
                    page_id=task['id'],
                    properties={"Notes": {"rich_text": [{"text": {"content": new_notes}}]}}
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                errors.append(f"Failed to update {task['title']}: {str(e)}")
        
        return TaskOperationResult(
            success=success_count > 0,
            affected_count=success_count,
            message=f"Added notes to {success_count}/{len(tasks)} tasks",
            affected_tasks=[{'id': t['id'], 'title': t['title']} for t in tasks[:success_count]],
            errors=errors
        )


class TaskAnalyzer:
    """Analyzes tasks for insights and recommendations."""
    
    @staticmethod
    def analyze_task_distribution(tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze distribution of tasks across different dimensions."""
        total = len(tasks)
        if total == 0:
            return {"total": 0, "message": "No tasks to analyze"}
        
        # Status distribution
        status_counts = {}
        for task in tasks:
            status = task.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for task in tasks:
            priority = task.get('priority', 'Unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Project distribution
        project_counts = {}
        for task in tasks:
            project = task.get('project') or 'No Project'
            project_counts[project] = project_counts.get(project, 0) + 1
        
        # Tasks with/without due dates
        with_due_dates = sum(1 for task in tasks if task.get('due_date'))
        without_due_dates = total - with_due_dates
        
        return {
            "total": total,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "project_distribution": project_counts,
            "due_date_status": {
                "with_due_dates": with_due_dates,
                "without_due_dates": without_due_dates
            }
        }
    
    @staticmethod
    def identify_cleanup_candidates(tasks: List[Dict]) -> List[Dict[str, Any]]:
        """Identify tasks that might need cleanup."""
        candidates = []
        
        # Track title similarities for duplicate detection
        title_groups = {}
        for task in tasks:
            title = task.get('title', '').lower().strip()
            if len(title) < 3:  # Too short titles
                candidates.append({
                    'task': task,
                    'reason': 'title_too_short',
                    'description': 'Task title is too short or empty'
                })
                continue
                
            # Group similar titles
            key = title[:20]  # First 20 chars as grouping key
            if key not in title_groups:
                title_groups[key] = []
            title_groups[key].append(task)
        
        # Find potential duplicates
        for group in title_groups.values():
            if len(group) > 1:
                for task in group[1:]:  # Keep first, flag others
                    candidates.append({
                        'task': task,
                        'reason': 'potential_duplicate',
                        'description': f'Similar to other task(s)'
                    })
        
        # Find vague or unclear tasks
        vague_keywords = ['fix', 'update', 'check', 'look at', 'review', 'handle']
        for task in tasks:
            title = task.get('title', '').lower()
            if any(keyword in title for keyword in vague_keywords) and len(title.split()) < 4:
                candidates.append({
                    'task': task,
                    'reason': 'vague_title',
                    'description': 'Task title is too vague or unclear'
                })
        
        # Find tasks without status or priority
        for task in tasks:
            if not task.get('status'):
                candidates.append({
                    'task': task,
                    'reason': 'missing_status',
                    'description': 'Task missing status'
                })
            if not task.get('priority'):
                candidates.append({
                    'task': task,
                    'reason': 'missing_priority', 
                    'description': 'Task missing priority'
                })
        
        return candidates


class BulkOperationParser:
    """Parses user requests into bulk operations."""
    
    @staticmethod
    def parse_bulk_request(user_text: str) -> Optional[BulkOperation]:
        """Parse user text into a BulkOperation object."""
        text = user_text.lower()
        
        # Status updates
        if 'mark all' in text or 'set all' in text or 'change all' in text:
            if 'done' in text or 'complete' in text:
                return BulkOperation(
                    operation_type=BulkOperationType.STATUS_UPDATE,
                    filters=TaskFilter(),  # All tasks
                    new_values={'status': 'Done'}
                )
            elif 'in progress' in text:
                return BulkOperation(
                    operation_type=BulkOperationType.STATUS_UPDATE,
                    filters=TaskFilter(),
                    new_values={'status': 'In Progress'}
                )
        
        # Priority updates
        if 'set priority' in text or 'change priority' in text:
            if 'high' in text:
                return BulkOperation(
                    operation_type=BulkOperationType.PRIORITY_UPDATE,
                    filters=TaskFilter(),
                    new_values={'priority': 'High'}
                )
        
        # Bulk deletion
        if 'delete all' in text or 'remove all' in text:
            return BulkOperation(
                operation_type=BulkOperationType.BULK_DELETE,
                filters=TaskFilter(),
                new_values={}
            )
        
        # Project assignment
        if 'assign to project' in text or 'move to project' in text:
            # Extract project name (simplified)
            words = user_text.split()
            try:
                project_idx = next(i for i, word in enumerate(words) if 'project' in word.lower())
                if project_idx + 1 < len(words):
                    project = words[project_idx + 1]
                    return BulkOperation(
                        operation_type=BulkOperationType.PROJECT_ASSIGNMENT,
                        filters=TaskFilter(),
                        new_values={'project': project}
                    )
            except StopIteration:
                pass
        
        return None

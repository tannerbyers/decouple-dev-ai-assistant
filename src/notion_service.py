"""Notion database integration."""
import logging
from typing import List
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError
from .config import config

logger = logging.getLogger(__name__)

class NotionService:
    """Service for interacting with Notion databases."""
    
    def __init__(self):
        self.client = NotionClient(auth=config.notion_api_key)
    
    def fetch_open_tasks(self) -> List[str]:
        """Fetch tasks with status 'To Do' or 'Inbox' from Notion database."""
        try:
            results = self.client.databases.query(
                **{
                    "database_id": config.notion_db_id,
                    "filter": {
                        "or": [
                            {"property": "Status", "select": {"equals": "To Do"}},
                            {"property": "Status", "select": {"equals": "Inbox"}}
                        ]
                    }
                }
            )
            
            tasks = []
            for row in results["results"]:
                try:
                    title = row["properties"]["Task"]["title"][0]["text"]["content"]
                    tasks.append(title)
                except (KeyError, IndexError, TypeError) as e:
                    logger.warning(f"Failed to parse task: {e}")
                    continue
            
            return tasks
            
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            return ["Unable to fetch tasks from Notion"]
        except Exception as e:
            logger.error(f"Unexpected error fetching tasks: {e}")
            return ["Error accessing task database"]
    
    def create_task(self, title: str, status: str = "Inbox") -> bool:
        """Create a new task in the Notion database."""
        try:
            self.client.pages.create(
                parent={"database_id": config.notion_db_id},
                properties={
                    "Task": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            logger.info(f"Created task: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to create task '{title}': {e}")
            return False
    
    def update_task_status(self, task_title: str, new_status: str) -> bool:
        """Update a task's status by searching for it by title."""
        # This is a placeholder for future implementation
        # Would need to search for the task first, then update it
        logger.info(f"TODO: Update task '{task_title}' to status '{new_status}'")
        return True

# Global service instance
notion_service = NotionService()

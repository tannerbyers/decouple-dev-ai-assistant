"""Trello integration for CEO-level task management."""
import os
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TrelloClient:
    """CEO-focused Trello integration."""
    
    def __init__(self):
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        self.board_id = os.getenv("TRELLO_BOARD_ID")  # Main board for CEO tasks
        self.base_url = "https://api.trello.com/1"
        
    def is_configured(self) -> bool:
        """Check if Trello is properly configured."""
        return bool(self.api_key and self.token and self.board_id)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Trello API."""
        if not self.is_configured():
            logger.error("Trello not configured")
            return None
            
        url = f"{self.base_url}/{endpoint}"
        params = {
            'key': self.api_key,
            'token': self.token
        }
        
        if data:
            params.update(data)
            
        try:
            if method.upper() == 'POST':
                response = requests.post(url, params=params)
            elif method.upper() == 'PUT':
                response = requests.put(url, params=params)
            else:
                response = requests.get(url, params=params)
                
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Trello API error: {e}")
            return None
    
    def move_task_to_done(self, task_name: str) -> bool:
        """Move a task to Done list - CEO style response."""
        if not self.is_configured():
            return False
            
        try:
            # Get board lists
            lists = self._make_request('GET', f'boards/{self.board_id}/lists')
            if not lists:
                return False
                
            # Find Done/Complete list
            done_list = None
            for lst in lists:
                if lst['name'].lower() in ['done', 'complete', 'completed', 'finished']:
                    done_list = lst
                    break
                    
            if not done_list:
                logger.error("No 'Done' list found on board")
                return False
                
            # Find the card by name
            cards = self._make_request('GET', f'boards/{self.board_id}/cards')
            if not cards:
                return False
                
            target_card = None
            for card in cards:
                if task_name.lower() in card['name'].lower():
                    target_card = card
                    break
                    
            if not target_card:
                logger.error(f"Task '{task_name}' not found")
                return False
                
            # Move card to Done list
            result = self._make_request('PUT', f"cards/{target_card['id']}", {
                'idList': done_list['id']
            })
            
            return result is not None
        except Exception as e:
            logger.error(f"Error moving task to done: {e}")
            return False
    
    def create_task(self, title: str, list_name: str = "To Do", description: str = "") -> bool:
        """Create a new task in specified list."""
        if not self.is_configured():
            return False
            
        # Get board lists
        lists = self._make_request('GET', f'boards/{self.board_id}/lists')
        if not lists:
            return False
            
        # Find target list
        target_list = None
        for lst in lists:
            if lst['name'].lower() == list_name.lower():
                target_list = lst
                break
                
        if not target_list:
            # Default to first list if not found
            target_list = lists[0]
            
        # Create card
        result = self._make_request('POST', 'cards', {
            'name': title,
            'desc': description,
            'idList': target_list['id']
        })
        
        return result is not None
    
    def get_task_status(self, task_name: str) -> Optional[str]:
        """Get current status/list of a task."""
        if not self.is_configured():
            return None
            
        # Get all cards
        cards = self._make_request('GET', f'boards/{self.board_id}/cards')
        if not cards:
            return None
            
        # Find the card
        for card in cards:
            if task_name.lower() in card['name'].lower():
                # Get list name
                list_info = self._make_request('GET', f"lists/{card['idList']}")
                return list_info['name'] if list_info else "Unknown"
                
        return None
    
    def add_missing_business_tasks(self, business_areas: List[str]) -> int:
        """Add comprehensive tasks for all business areas - CEO level."""
        if not self.is_configured():
            return 0
            
        task_templates = {
            'sales': [
                'Create weekly content calendar for lead generation',
                'Set up automated lead scoring system', 
                'Design client onboarding sequence',
                'Implement referral program strategy',
                'Create sales dashboard with KPIs'
            ],
            'delivery': [
                'Document standard project delivery process',
                'Create quality assurance checklist',
                'Set up client communication templates',
                'Implement project milestone tracking',
                'Design client feedback collection system'
            ],
            'financial': [
                'Set up automated invoicing system',
                'Create monthly financial reporting dashboard',
                'Implement expense tracking automation',
                'Design pricing strategy framework',
                'Set up cash flow forecasting'
            ],
            'operations': [
                'Automate routine administrative tasks',
                'Create CEO weekly review process',
                'Implement team productivity metrics',
                'Set up business intelligence dashboard',
                'Design workflow optimization system'
            ],
            'team': [
                'Create contractor hiring process',
                'Design team onboarding checklist',
                'Implement performance tracking system',
                'Set up knowledge management system',
                'Create team communication protocols'
            ]
        }
        
        created_count = 0
        
        for area in business_areas:
            if area in task_templates:
                for task in task_templates[area]:
                    if self.create_task(f"[{area.upper()}] {task}", "Backlog"):
                        created_count += 1
                        
        return created_count


# Global Trello client instance
trello_client = TrelloClient()

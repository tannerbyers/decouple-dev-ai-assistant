import os
import pytest
from unittest.mock import patch, MagicMock
import json

# Set environment variables before importing
os.environ['TRELLO_API_KEY'] = 'fake_trello_key'
os.environ['TRELLO_TOKEN'] = 'fake_trello_token'
os.environ['TRELLO_BOARD_ID'] = 'fake_board_id'

from src.trello_client import TrelloClient, trello_client


class TestTrelloClient:
    """Test CEO-level Trello integration functionality."""
    
    def test_is_configured_true(self):
        """Test that client recognizes proper configuration."""
        client = TrelloClient()
        assert client.is_configured() is True
    
    def test_is_configured_false_missing_key(self):
        """Test that client recognizes missing configuration."""
        with patch.dict(os.environ, {'TRELLO_API_KEY': ''}, clear=False):
            client = TrelloClient()
            assert client.is_configured() is False
    
    @patch('src.trello_client.requests.get')
    def test_move_task_to_done_success(self, mock_get):
        """Test successful task completion - CEO style."""
        client = TrelloClient()
        
        # Mock getting board lists
        mock_get.side_effect = [
            MagicMock(
                ok=True, 
                json=lambda: [
                    {'id': 'list1', 'name': 'To Do'},
                    {'id': 'done_list', 'name': 'Done'}
                ]
            ),
            MagicMock(
                ok=True,
                json=lambda: [
                    {'id': 'card1', 'name': 'AI Agent Setup', 'idList': 'list1'}
                ]
            )
        ]
        
        # Mock the PUT request for moving card
        with patch('src.trello_client.requests.put') as mock_put:
            mock_put.return_value = MagicMock(ok=True, json=lambda: {})
            
            result = client.move_task_to_done('AI Agent')
            
            assert result is True
            mock_put.assert_called_once()
            # Verify the card was moved to the Done list
            call_args = mock_put.call_args
            assert 'idList' in call_args.kwargs.get('params', {})
    
    @patch('src.trello_client.requests.get')
    def test_move_task_to_done_task_not_found(self, mock_get):
        """Test task completion when task doesn't exist."""
        client = TrelloClient()
        
        # Mock getting board lists and cards
        mock_get.side_effect = [
            MagicMock(
                ok=True, 
                json=lambda: [{'id': 'done_list', 'name': 'Done'}]
            ),
            MagicMock(
                ok=True,
                json=lambda: []  # No cards found
            )
        ]
        
        result = client.move_task_to_done('NonExistent Task')
        assert result is False
    
    @patch('src.trello_client.requests.get')
    def test_move_task_to_done_no_done_list(self, mock_get):
        """Test task completion when no Done list exists."""
        client = TrelloClient()
        
        # Mock getting board lists without Done list
        mock_get.return_value = MagicMock(
            ok=True, 
            json=lambda: [
                {'id': 'list1', 'name': 'To Do'},
                {'id': 'list2', 'name': 'In Progress'}
            ]
        )
        
        result = client.move_task_to_done('Any Task')
        assert result is False
    
    @patch('src.trello_client.requests.get')
    def test_create_task_success(self, mock_get):
        """Test creating a new task."""
        client = TrelloClient()
        
        # Mock getting board lists
        mock_get.return_value = MagicMock(
            ok=True, 
            json=lambda: [
                {'id': 'todo_list', 'name': 'To Do'},
                {'id': 'done_list', 'name': 'Done'}
            ]
        )
        
        with patch('src.trello_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {})
            
            result = client.create_task('New CEO Task', 'To Do')
            
            assert result is True
            mock_post.assert_called_once()
    
    @patch('src.trello_client.requests.get')
    def test_get_task_status_success(self, mock_get):
        """Test getting task status."""
        client = TrelloClient()
        
        # Mock getting cards and list info
        mock_get.side_effect = [
            MagicMock(
                ok=True,
                json=lambda: [
                    {'id': 'card1', 'name': 'AI Agent Setup', 'idList': 'list1'}
                ]
            ),
            MagicMock(
                ok=True,
                json=lambda: {'name': 'In Progress'}
            )
        ]
        
        status = client.get_task_status('AI Agent')
        assert status == 'In Progress'
    
    @patch('src.trello_client.requests.get')
    def test_get_task_status_not_found(self, mock_get):
        """Test getting status of non-existent task."""
        client = TrelloClient()
        
        mock_get.return_value = MagicMock(
            ok=True,
            json=lambda: []  # No cards found
        )
        
        status = client.get_task_status('NonExistent Task')
        assert status is None
    
    def test_add_missing_business_tasks_not_configured(self):
        """Test task creation when Trello not configured."""
        with patch.dict(os.environ, {'TRELLO_API_KEY': ''}, clear=False):
            client = TrelloClient()
            
            result = client.add_missing_business_tasks(['sales', 'delivery'])
            assert result == 0
    
    @patch('src.trello_client.requests.get')
    def test_add_missing_business_tasks_success(self, mock_get):
        """Test comprehensive business task creation."""
        client = TrelloClient()
        
        # Mock getting board lists
        mock_get.return_value = MagicMock(
            ok=True, 
            json=lambda: [
                {'id': 'backlog_list', 'name': 'Backlog'}
            ]
        )
        
        with patch('src.trello_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {})
            
            result = client.add_missing_business_tasks(['sales', 'delivery'])
            
            # Should create multiple tasks for each area
            assert result > 0
            assert mock_post.call_count > 5  # Should create multiple tasks
            
            # Verify sales and delivery tasks were created
            call_args_list = [call.kwargs['params']['name'] for call in mock_post.call_args_list]
            sales_tasks = [name for name in call_args_list if 'SALES' in name]
            delivery_tasks = [name for name in call_args_list if 'DELIVERY' in name]
            
            assert len(sales_tasks) > 0
            assert len(delivery_tasks) > 0
    
    def test_trello_not_configured_methods(self):
        """Test all methods handle unconfigured Trello gracefully."""
        with patch.dict(os.environ, {'TRELLO_API_KEY': ''}, clear=False):
            client = TrelloClient()
            
            assert client.move_task_to_done('task') is False
            assert client.create_task('task') is False  
            assert client.get_task_status('task') is None
            assert client.add_missing_business_tasks(['sales']) == 0
    
    @patch('src.trello_client.requests.get')
    def test_api_error_handling(self, mock_get):
        """Test handling of Trello API errors."""
        client = TrelloClient()
        
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        result = client.move_task_to_done('task')
        assert result is False
    
    def test_business_task_templates_coverage(self):
        """Test that all business areas have task templates."""
        client = TrelloClient()
        
        # This tests the internal task_templates dict
        expected_areas = ['sales', 'delivery', 'financial', 'operations', 'team']
        
        with patch('src.trello_client.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                ok=True, 
                json=lambda: [{'id': 'list1', 'name': 'Backlog'}]
            )
            
            with patch('src.trello_client.requests.post') as mock_post:
                mock_post.return_value = MagicMock(ok=True, json=lambda: {})
                
                result = client.add_missing_business_tasks(expected_areas)
                
                # Should create tasks for all areas
                assert result > 0
                
                # Verify all areas were covered
                call_args_list = [call.kwargs['params']['name'] for call in mock_post.call_args_list]
                
                for area in expected_areas:
                    area_tasks = [name for name in call_args_list if area.upper() in name]
                    assert len(area_tasks) > 0, f"No tasks created for {area}"


class TestGlobalTrelloClient:
    """Test the global trello_client instance."""
    
    def test_global_client_configured(self):
        """Test that global client uses environment variables."""
        assert trello_client.api_key == 'fake_trello_key'
        assert trello_client.token == 'fake_trello_token'
        assert trello_client.board_id == 'fake_board_id'
        assert trello_client.is_configured() is True


# Integration-style tests for CEO workflow
class TestCEOWorkflow:
    """Test CEO-level workflow scenarios."""
    
    @patch('src.trello_client.requests.get')
    def test_ceo_task_completion_workflow(self, mock_get):
        """Test complete CEO task completion workflow."""
        client = TrelloClient()
        
        # Scenario: CEO says "Set AI agent status to done"
        # 1. Find the task
        # 2. Move to Done list
        # 3. Return simple "Task completed" response
        
        mock_get.side_effect = [
            # Get lists
            MagicMock(
                ok=True, 
                json=lambda: [
                    {'id': 'todo', 'name': 'To Do'},
                    {'id': 'done', 'name': 'Done'}
                ]
            ),
            # Get cards
            MagicMock(
                ok=True,
                json=lambda: [
                    {'id': 'card1', 'name': 'Setup AI Agent for Notion Tasks', 'idList': 'todo'}
                ]
            )
        ]
        
        with patch('src.trello_client.requests.put') as mock_put:
            mock_put.return_value = MagicMock(ok=True, json=lambda: {})
            
            # This is what happens when CEO says "Set AI agent status to done"
            success = client.move_task_to_done('ai agent')
            
            assert success is True
            
            # Verify the workflow
            # 1. Got the lists
            # 2. Got the cards
            # 3. Moved card to Done list
            assert mock_get.call_count == 2
            mock_put.assert_called_once()
    
    @patch('src.trello_client.requests.get')
    def test_ceo_comprehensive_task_creation(self, mock_get):
        """Test CEO requesting comprehensive business task creation."""
        client = TrelloClient()
        
        # Scenario: CEO says "Create all missing business tasks"
        mock_get.return_value = MagicMock(
            ok=True, 
            json=lambda: [{'id': 'backlog', 'name': 'Backlog'}]
        )
        
        with patch('src.trello_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {})
            
            # Create tasks for all business areas
            areas = ['sales', 'delivery', 'financial', 'operations', 'team']
            count = client.add_missing_business_tasks(areas)
            
            # Should create comprehensive task coverage
            assert count >= 20  # At least 4 tasks per area
            assert mock_post.call_count >= 20
            
            # Verify comprehensive coverage - check that essential business tasks are included
            task_names = [call.kwargs['params']['name'] for call in mock_post.call_args_list]
            
            # Should have revenue-focused tasks
            revenue_tasks = [name for name in task_names if any(word in name.lower() 
                           for word in ['lead', 'sales', 'revenue', 'client', 'pricing'])]
            assert len(revenue_tasks) > 0
            
            # Should have operational efficiency tasks
            ops_tasks = [name for name in task_names if any(word in name.lower() 
                        for word in ['automate', 'process', 'system', 'workflow'])]
            assert len(ops_tasks) > 0

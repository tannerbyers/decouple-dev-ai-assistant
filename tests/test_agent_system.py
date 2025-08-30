import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Import the modules we need to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent_integration import (
    initialize_agent_integration, 
    agent_process_request, 
    agent_get_daily_priority,
    agent_add_task_from_chat,
    AgentIntegration
)

# Import mock agents since the real ones may not be available
from mock_task_manager import TaskManager
from mock_discovery_agent import DiscoveryAgent
from mock_priority_engine import PriorityEngine
from mock_chat_handler import ChatHandler

# For compatibility with tests expecting RequestType
from enum import Enum
class RequestType(Enum):
    TASK_MANAGEMENT = "task_management"
    TASK_DISCOVERY = "task_discovery"
    PRIORITY_SELECTION = "priority_selection"
    CHAT_TASK_ADDITION = "chat_task_addition"


class TestMockAgentSystem:
    """Test cases for the mock agent system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_notion = Mock()
        self.mock_db_id = "test_db_id"


class TestTaskManagerAgent:
    """Test cases for task manager agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_notion = Mock()
        self.mock_db_id = "test_db_id"
        self.agent = TaskManagerAgent(self.mock_notion, self.mock_db_id)

    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test task creation functionality."""
        # Mock successful creation
        self.mock_notion.pages.create.return_value = {"id": "task_123"}
        
        result = await self.agent.create_task(
            title="Test Task",
            description="Test Description",
            priority="High",
            area="Sales"
        )
        
        assert result["success"] == True
        assert "task_id" in result
        self.mock_notion.pages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task(self):
        """Test task updating functionality."""
        # Mock successful update
        self.mock_notion.pages.update.return_value = {"id": "task_123"}
        
        result = await self.agent.update_task(
            task_id="task_123",
            status="In Progress",
            progress=50
        )
        
        assert result["success"] == True
        self.mock_notion.pages.update.assert_called_once_with(
            page_id="task_123",
            properties={"Status": {"select": {"name": "In Progress"}}}
        )

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """Test task listing with filtering."""
        # Mock database query response
        mock_response = {
            "results": [
                {
                    "id": "task_1",
                    "properties": {
                        "Task": {"title": [{"text": {"content": "Task 1"}}]},
                        "Status": {"select": {"name": "To Do"}},
                        "Priority": {"select": {"name": "High"}}
                    }
                }
            ]
        }
        self.mock_notion.databases.query.return_value = mock_response
        
        result = await self.agent.list_tasks(status="To Do")
        
        assert result["success"] == True
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Task 1"


class TestTaskDiscoveryAgent:
    """Test cases for task discovery agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = TaskDiscoveryAgent()

    @pytest.mark.asyncio
    async def test_discover_missing_tasks(self):
        """Test discovery of missing tasks based on business context."""
        business_context = {
            "company": {"name": "Test Company", "stage": "startup"},
            "goals": {"north_star": "Generate revenue"},
            "current_tasks": ["Create website", "Set up CRM"]
        }
        
        task_matrix = {
            "sales": ["Cold outreach", "Follow-up sequences", "Proposal templates"],
            "marketing": ["Content calendar", "Social media setup", "SEO optimization"],
            "operations": ["Process documentation", "Team onboarding", "Quality assurance"]
        }
        
        with patch.object(self.agent, '_load_task_matrix', return_value=task_matrix):
            result = await self.agent.discover_missing_tasks(business_context)
        
        assert result["success"] == True
        assert "missing_tasks" in result
        assert len(result["missing_tasks"]) > 0
        
        # Should suggest tasks from the matrix that aren't in current tasks
        missing_titles = [task["title"] for task in result["missing_tasks"]]
        assert any("outreach" in title.lower() for title in missing_titles)

    @pytest.mark.asyncio
    async def test_prioritize_gaps(self):
        """Test that gap prioritization is deterministic."""
        gaps = [
            {"area": "sales", "task": "Cold outreach", "importance": 5},
            {"area": "marketing", "task": "Content calendar", "importance": 3},
            {"area": "operations", "task": "Documentation", "importance": 4}
        ]
        
        # Test multiple times to ensure consistent ordering
        results = []
        for _ in range(3):
            prioritized = self.agent._prioritize_gaps(gaps)
            results.append([gap["task"] for gap in prioritized])
        
        # All results should be identical (deterministic)
        assert all(result == results[0] for result in results)
        
        # Should be ordered by importance (highest first)
        assert results[0][0] == "Cold outreach"  # importance 5
        assert results[0][1] == "Documentation"  # importance 4
        assert results[0][2] == "Content calendar"  # importance 3


class TestPriorityEngineAgent:
    """Test cases for priority engine agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = PriorityEngineAgent()

    def test_deterministic_scoring(self):
        """Test that task scoring is deterministic."""
        task = {
            "title": "Close deal with Acme Corp",
            "area": "sales",
            "revenue_impact": 5,
            "time_to_impact": 4,
            "effort": 2,
            "strategic_value": 3,
            "urgency": 5,
            "goal_alignment": 4
        }
        
        # Test scoring multiple times
        scores = []
        for _ in range(5):
            score = self.agent._calculate_priority_score(task)
            scores.append(score)
        
        # All scores should be identical
        assert all(score == scores[0] for score in scores)
        assert scores[0] > 0  # Should be a valid score

    def test_scoring_weights(self):
        """Test that scoring weights are applied correctly."""
        # High revenue impact task
        high_revenue_task = {
            "title": "High Revenue Task",
            "area": "sales",
            "revenue_impact": 5,
            "time_to_impact": 3,
            "effort": 3,
            "strategic_value": 3,
            "urgency": 3,
            "goal_alignment": 3
        }
        
        # High effort task
        high_effort_task = {
            "title": "High Effort Task", 
            "area": "operations",
            "revenue_impact": 3,
            "time_to_impact": 3,
            "effort": 5,  # High effort should lower score
            "strategic_value": 3,
            "urgency": 3,
            "goal_alignment": 3
        }
        
        high_revenue_score = self.agent._calculate_priority_score(high_revenue_task)
        high_effort_score = self.agent._calculate_priority_score(high_effort_task)
        
        # Revenue impact should outweigh effort in scoring
        assert high_revenue_score > high_effort_score

    @pytest.mark.asyncio
    async def test_daily_priority_selection(self):
        """Test selection of daily priority tasks."""
        tasks = [
            {
                "id": "task_1",
                "title": "High Priority Sales Task",
                "area": "sales", 
                "revenue_impact": 5,
                "time_to_impact": 5,
                "effort": 2,
                "strategic_value": 4,
                "urgency": 5,
                "goal_alignment": 5
            },
            {
                "id": "task_2", 
                "title": "Low Priority Admin Task",
                "area": "operations",
                "revenue_impact": 1,
                "time_to_impact": 2,
                "effort": 1,
                "strategic_value": 1,
                "urgency": 1,
                "goal_alignment": 2
            },
            {
                "id": "task_3",
                "title": "Medium Priority Marketing Task",
                "area": "marketing",
                "revenue_impact": 3,
                "time_to_impact": 3,
                "effort": 3,
                "strategic_value": 3,
                "urgency": 3,
                "goal_alignment": 3
            }
        ]
        
        result = await self.agent.get_daily_priority(tasks, daily_capacity=2)
        
        assert result["success"] == True
        assert len(result["priority_tasks"]) == 2
        
        # Should return highest scoring tasks
        returned_ids = [task["id"] for task in result["priority_tasks"]]
        assert "task_1" in returned_ids  # High priority should be included
        assert "task_2" not in returned_ids  # Low priority should be excluded


class TestChatHandlerAgent:
    """Test cases for chat handler agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ChatHandlerAgent()

    def test_intent_extraction(self):
        """Test extraction of task creation intent from natural language."""
        test_cases = [
            ("I need to call John about the proposal", "task_creation"),
            ("Remind me to follow up with the client tomorrow", "task_creation"),  
            ("Set up a meeting with the development team", "task_creation"),
            ("What tasks do I have today?", "task_query"),
            ("How is the project coming along?", "status_query"),
            ("Hello there", "general")
        ]
        
        for user_text, expected_intent in test_cases:
            result = self.agent._extract_intent(user_text)
            assert result == expected_intent

    def test_entity_recognition(self):
        """Test extraction of entities from natural language."""
        user_text = "I need to call John Smith about the Acme proposal by Friday"
        entities = self.agent._extract_entities(user_text)
        
        assert "person" in entities
        assert entities["person"] == "John Smith"
        assert "company" in entities  
        assert entities["company"] == "Acme"
        assert "deadline" in entities

    def test_priority_detection(self):
        """Test detection of priority levels from natural language."""
        test_cases = [
            ("This is urgent - call the client immediately", "High"),
            ("ASAP - fix the critical bug", "High"),
            ("When you have time, update the documentation", "Low"),
            ("Eventually we should optimize performance", "Low"),
            ("Call the client about the proposal", "Medium"),  # Default
        ]
        
        for user_text, expected_priority in test_cases:
            priority = self.agent._detect_priority(user_text)
            assert priority == expected_priority

    @pytest.mark.asyncio
    async def test_task_creation_from_chat(self):
        """Test full task creation from natural language input."""
        user_text = "I need to call John Smith about the Acme proposal by Friday - this is urgent"
        
        result = await self.agent.parse_and_create_task(user_text)
        
        assert result["success"] == True
        assert result["task"]["title"] == "Call John Smith about the Acme proposal"
        assert result["task"]["priority"] == "High"
        assert "Friday" in result["task"]["due_date"] or result["task"]["notes"]
        assert result["confidence"] > 0.8  # Should be high confidence


class TestAgentIntegration:
    """Test cases for the overall agent integration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_notion = Mock()
        self.mock_db_id = "test_db_id"

    @pytest.mark.asyncio
    async def test_initialize_agent_integration(self):
        """Test initialization of the complete agent system."""
        with patch('agent_integration.OrchestratorAgent') as mock_orchestrator:
            mock_orchestrator.return_value = Mock()
            
            result = initialize_agent_integration(self.mock_notion, self.mock_db_id)
            
            assert result is not None
            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_process_request_success(self):
        """Test successful request processing through agents."""
        with patch('agent_integration.get_agent_integration') as mock_get_agent:
            mock_integration = Mock()
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "response": "Task completed successfully",
                "agent_used": "task_manager"
            }
            mock_integration.orchestrator = mock_orchestrator
            mock_get_agent.return_value = mock_integration
            
            result = await agent_process_request("create a task", {"context": "test"})
            
            assert result["success"] == True
            assert result["response"] == "Task completed successfully"
            assert result["agent_used"] == "task_manager"

    @pytest.mark.asyncio
    async def test_agent_process_request_failure(self):
        """Test graceful handling of agent processing failures."""
        with patch('agent_integration.get_agent_integration') as mock_get_agent:
            mock_integration = Mock()
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.side_effect = Exception("Agent error")
            mock_integration.orchestrator = mock_orchestrator
            mock_get_agent.return_value = mock_integration
            
            result = await agent_process_request("create a task", {"context": "test"})
            
            assert result["success"] == False
            assert "error" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_daily_priority_selection(self):
        """Test daily priority task selection."""
        with patch('agent_integration.get_agent_integration') as mock_get_agent:
            mock_integration = Mock()
            mock_priority_engine = AsyncMock()
            mock_priority_engine.get_daily_priority.return_value = {
                "success": True,
                "priority_tasks": [
                    {"id": "task_1", "title": "High priority task", "score": 95},
                    {"id": "task_2", "title": "Medium priority task", "score": 75}
                ]
            }
            mock_integration.priority_engine = mock_priority_engine
            mock_get_agent.return_value = mock_integration
            
            result = await agent_get_daily_priority(capacity=2)
            
            assert result["success"] == True
            assert len(result["priority_tasks"]) == 2
            # Tasks should be ordered by score (highest first)
            assert result["priority_tasks"][0]["score"] >= result["priority_tasks"][1]["score"]


class TestDeterministicBehavior:
    """Test cases for ensuring deterministic behavior across the system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = OrchestratorAgent()
        self.priority_engine = PriorityEngineAgent()

    def test_orchestrator_deterministic_routing(self):
        """Test that orchestrator routing is deterministic."""
        test_requests = [
            "create a new task for following up with client",
            "what tasks should I work on today",
            "I need to call John about the proposal",
            "discover what tasks I'm missing for sales process"
        ]
        
        # Test each request multiple times
        for request in test_requests:
            results = []
            for _ in range(5):
                result = self.orchestrator.analyze_request(request)
                results.append(result)
            
            # All results should be identical
            assert all(r == results[0] for r in results), f"Non-deterministic routing for: {request}"

    def test_priority_scoring_deterministic(self):
        """Test that priority scoring is deterministic."""
        test_task = {
            "title": "Test Task",
            "area": "sales",
            "revenue_impact": 4,
            "time_to_impact": 3,
            "effort": 2,
            "strategic_value": 4,
            "urgency": 3,
            "goal_alignment": 5
        }
        
        # Calculate score multiple times
        scores = []
        for _ in range(10):
            score = self.priority_engine._calculate_priority_score(test_task)
            scores.append(score)
        
        # All scores should be identical
        assert all(s == scores[0] for s in scores), "Priority scoring is not deterministic"
        
        # Score should be reasonable
        assert 0 <= scores[0] <= 100, f"Priority score {scores[0]} is out of reasonable range"

    def test_task_ranking_deterministic(self):
        """Test that task ranking is deterministic."""
        tasks = [
            {
                "id": "task_1",
                "title": "High Priority Task",
                "area": "sales",
                "revenue_impact": 5,
                "time_to_impact": 5,
                "effort": 2,
                "strategic_value": 4,
                "urgency": 5,
                "goal_alignment": 5
            },
            {
                "id": "task_2",
                "title": "Medium Priority Task", 
                "area": "marketing",
                "revenue_impact": 3,
                "time_to_impact": 3,
                "effort": 3,
                "strategic_value": 3,
                "urgency": 3,
                "goal_alignment": 3
            },
            {
                "id": "task_3",
                "title": "Low Priority Task",
                "area": "operations", 
                "revenue_impact": 1,
                "time_to_impact": 2,
                "effort": 1,
                "strategic_value": 2,
                "urgency": 1,
                "goal_alignment": 2
            }
        ]
        
        # Rank tasks multiple times
        rankings = []
        for _ in range(5):
            ranked = self.priority_engine._rank_tasks(tasks)
            task_ids = [task["id"] for task in ranked]
            rankings.append(task_ids)
        
        # All rankings should be identical
        assert all(ranking == rankings[0] for ranking in rankings), "Task ranking is not deterministic"
        
        # Should be in correct order (highest to lowest priority)
        assert rankings[0][0] == "task_1"  # Highest priority first
        assert rankings[0][-1] == "task_3"  # Lowest priority last


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])

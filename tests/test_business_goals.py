import os
import pytest
from unittest.mock import patch, MagicMock
import datetime
from fastapi.testclient import TestClient

# Set environment variables before importing main
os.environ['SLACK_BOT_TOKEN'] = 'fake_slack_token'
os.environ['SLACK_SIGNING_SECRET'] = 'fake_signing_secret'
os.environ['NOTION_API_KEY'] = 'fake_notion_key'
os.environ['NOTION_DB_ID'] = 'fake_db_id'
os.environ['NOTION_GOALS_DB_ID'] = 'fake_goals_db_id'
os.environ['NOTION_CLIENTS_DB_ID'] = 'fake_clients_db_id'
os.environ['NOTION_METRICS_DB_ID'] = 'fake_metrics_db_id'
os.environ['NOTION_PROJECTS_DB_ID'] = 'fake_projects_db_id'
os.environ['OPENAI_API_KEY'] = 'fake_openai_key'
os.environ['TEST_MODE'] = 'true'

from main import (
    app, 
    BusinessGoal, GoalStatus, Priority, BusinessArea,
    create_business_goal, get_ceo_dashboard, analyze_business_request,
    generate_ceo_insights, generate_dashboard_response, generate_goal_suggestions,
    generate_planning_response, generate_help_response,
    create_notion_task, create_business_goal_in_notion, create_client_record,
    log_business_metric, execute_database_action, parse_database_request,
    business_goals
)

client = TestClient(app)

@pytest.fixture
def clean_business_goals():
    """Clean business_goals dictionary before each test."""
    business_goals.clear()
    yield
    business_goals.clear()


class TestBusinessGoalManagement:
    """Test business goal creation and management."""
    
    def test_create_business_goal(self, clean_business_goals):
        """Test creating a new business goal."""
        goal_id = create_business_goal(
            title="Increase sales",
            description="Grow monthly revenue",
            area="sales",
            target_date="2025-03-31",
            weekly_actions=["Make 10 calls", "Send 5 proposals"],
            success_metrics={"revenue": "$10000", "clients": "3"}
        )
        
        assert goal_id == "sales_1"
        assert goal_id in business_goals
        
        goal = business_goals[goal_id]
        assert goal.title == "Increase sales"
        assert goal.area == BusinessArea.SALES
        assert goal.status == GoalStatus.NOT_STARTED
        assert goal.priority == Priority.MEDIUM
        assert goal.progress == 0
        assert len(goal.weekly_actions) == 2
        assert goal.success_metrics["revenue"] == "$10000"
    
    def test_create_multiple_goals_same_area(self, clean_business_goals):
        """Test creating multiple goals in the same business area."""
        goal1_id = create_business_goal("Goal 1", "Description 1", "sales", "2025-03-31")
        goal2_id = create_business_goal("Goal 2", "Description 2", "sales", "2025-03-31")
        
        assert goal1_id == "sales_1"
        assert goal2_id == "sales_2"
        assert len(business_goals) == 2
    
    def test_get_ceo_dashboard_empty(self, clean_business_goals):
        """Test CEO dashboard with no goals."""
        dashboard = get_ceo_dashboard()
        
        assert dashboard['overview']['total_goals'] == 0
        assert dashboard['overview']['completion_rate'] == 0
        assert all(progress == 0 for progress in dashboard['area_progress'].values())
        assert len(dashboard['high_priority_actions']) == 0
    
    def test_get_ceo_dashboard_with_goals(self, clean_business_goals):
        """Test CEO dashboard with active goals."""
        # Create goals in different areas with different progress
        goal1_id = create_business_goal("Sales Goal", "Description", "sales", "2025-03-31")
        goal2_id = create_business_goal("Product Goal", "Description", "product", "2025-03-31")
        
        # Manually update goal status and progress for testing
        business_goals[goal1_id].status = GoalStatus.IN_PROGRESS
        business_goals[goal1_id].progress = 50
        business_goals[goal1_id].priority = Priority.HIGH
        business_goals[goal1_id].weekly_actions = ["Action 1", "Action 2"]
        
        business_goals[goal2_id].status = GoalStatus.COMPLETED
        business_goals[goal2_id].progress = 100
        
        dashboard = get_ceo_dashboard()
        
        assert dashboard['overview']['total_goals'] == 2
        assert dashboard['overview']['completed'] == 1
        assert dashboard['overview']['in_progress'] == 1
        assert dashboard['overview']['completion_rate'] == 50.0
        assert dashboard['area_progress']['sales'] == 50.0
        assert dashboard['area_progress']['product'] == 100.0
        assert len(dashboard['high_priority_actions']) == 2  # 2 actions from high priority goal


class TestBusinessRequestAnalysis:
    """Test analysis of user business requests."""
    
    def test_analyze_help_request(self):
        """Test detection of help requests."""
        analysis = analyze_business_request("help me understand this")
        assert analysis['request_type'] == 'help'
        assert not analysis['is_ceo_focused']
    
    def test_analyze_dashboard_request(self):
        """Test detection of dashboard requests."""
        analysis = analyze_business_request("show me the dashboard overview")
        assert analysis['request_type'] == 'dashboard'
        assert 'process' not in analysis['detected_areas']  # 'overview' shouldn't trigger process area
    
    def test_analyze_goal_creation_request(self):
        """Test detection of goal creation requests."""
        analysis = analyze_business_request("create a new sales goal for Q1")
        assert analysis['request_type'] == 'goal_creation'
        assert 'sales' in analysis['detected_areas']
    
    def test_analyze_planning_request(self):
        """Test detection of planning requests."""
        analysis = analyze_business_request("what should my strategy be for next quarter")
        assert analysis['request_type'] == 'planning'
    
    def test_analyze_ceo_focused_request(self):
        """Test detection of CEO-focused requests."""
        analysis = analyze_business_request("what's my business growth strategy")
        assert analysis['is_ceo_focused'] == True
    
    def test_analyze_multiple_business_areas(self):
        """Test detection of multiple business areas."""
        analysis = analyze_business_request("improve sales and delivery processes")
        assert 'sales' in analysis['detected_areas']
        assert 'delivery' in analysis['detected_areas']
    
    def test_analyze_financial_keywords(self):
        """Test financial area keyword detection."""
        analysis = analyze_business_request("increase profit margins and ROI")
        assert 'financial' in analysis['detected_areas']
    
    def test_analyze_team_keywords(self):
        """Test team area keyword detection."""
        analysis = analyze_business_request("hire a new contractor for the team")
        assert 'team' in analysis['detected_areas']


class TestResponseGeneration:
    """Test various response generation functions."""
    
    def test_generate_help_response(self):
        """Test help response generation."""
        response = generate_help_response()
        
        assert "OpsBrain - Help Guide" in response
        assert "Task Management" in response
        assert "Goal Setting" in response
        assert "Client Management" in response
        assert "Metrics Tracking" in response
        assert "Create task:" in response
        assert "Add client:" in response
    
    def test_generate_dashboard_response(self, clean_business_goals):
        """Test dashboard response generation."""
        # Create test dashboard data
        dashboard = {
            'overview': {
                'total_goals': 5,
                'completed': 2,
                'in_progress': 2,
                'blocked': 1,
                'completion_rate': 40.0
            },
            'area_progress': {
                'sales': 75.0,
                'product': 50.0,
                'delivery': 0
            },
            'high_priority_actions': [
                {'area': 'sales', 'goal': 'Increase revenue', 'action': 'Make 10 calls', 'priority': 4},
                {'area': 'product', 'goal': 'Launch feature', 'action': 'Complete testing', 'priority': 3}
            ]
        }
        
        response = generate_dashboard_response(dashboard)
        
        assert "📊 **CEO Dashboard Summary**" in response
        assert "5 total • 40.0% complete" in response
        assert "2 in progress • 1 blocked" in response
        assert "Sales: 75.0%" in response
        assert "Product: 50.0%" in response
        assert "Make 10 calls" in response
        assert "💡 Focus on revenue-generating activities" in response
    
    def test_generate_goal_suggestions_sales(self):
        """Test goal suggestions for sales area."""
        response = generate_goal_suggestions(['sales'], "I need sales goals")
        
        assert "🎯 **SMART Goal Suggestions for Sales:**" in response
        assert "Generate 50 qualified leads" in response
        assert "Close 3 new clients" in response
        assert "Achieve $15K monthly recurring revenue" in response
        assert "💡 Choose one goal that directly impacts revenue" in response
    
    def test_generate_goal_suggestions_product(self):
        """Test goal suggestions for product area."""
        response = generate_goal_suggestions(['product'], "product development goals")
        
        assert "🎯 **SMART Goal Suggestions for Product:**" in response
        assert "Complete 8 high-impact OpsBrain features" in response
        assert "Integrate OpsBrain with 3 popular business tools" in response
    
    def test_generate_goal_suggestions_default(self):
        """Test goal suggestions with no area specified."""
        response = generate_goal_suggestions([], "I need goals")
        
        # Should default to sales
        assert "🎯 **SMART Goal Suggestions for Sales:**" in response
    
    def test_generate_planning_response(self, clean_business_goals):
        """Test planning response generation."""
        dashboard = {
            'area_progress': {
                'sales': 75.0,
                'delivery': 25.0,  # Low progress
                'product': 30.0    # Low progress
            }
        }
        
        response = generate_planning_response(dashboard, ['sales'])
        
        assert "📋 **Strategic Planning Recommendations:**" in response
        assert "**Focus Areas (Low Progress):** delivery, product" in response
        assert "This Week's CEO Priorities:" in response
        assert "**Revenue Focus:** Spend 60% of time" in response
        assert "Key Metrics to Track:" in response
        assert "Monthly Recurring Revenue (MRR)" in response
    
    @patch('main.llm')
    def test_generate_ceo_insights_with_llm(self, mock_llm, clean_business_goals):
        """Test CEO insights generation with LLM."""
        mock_llm.invoke.return_value = MagicMock(content="Strategic advice here")
        
        analysis = {'detected_areas': ['sales'], 'request_type': 'general', 'is_ceo_focused': True}
        tasks = ["Task 1", "Task 2"]
        
        # This should return a prompt for the LLM
        prompt = generate_ceo_insights("How do I grow sales?", tasks, analysis)
        
        assert "You are OpsBrain, a strategic AI assistant" in prompt
        assert "solo dev founder building a $10K/month agency" in prompt
        assert "How do I grow sales?" in prompt
        assert "Task 1" in prompt
        assert "As a CEO advisor, provide:" in prompt


class TestNotionDatabaseOperations:
    """Test Notion database operations."""
    
    @patch('main.notion')
    def test_create_notion_task_success(self, mock_notion):
        """Test successful task creation in Notion."""
        mock_notion.pages.create.return_value = {"id": "task_123"}
        
        result = create_notion_task(
            title="Test Task",
            status="To Do",
            priority="High",
            project="Test Project",
            due_date="2025-01-15",
            notes="Test notes"
        )
        
        assert result is True
        mock_notion.pages.create.assert_called_once()
        
        # Verify the properties passed to Notion
        call_args = mock_notion.pages.create.call_args
        properties = call_args[1]['properties']
        assert properties['Task']['title'][0]['text']['content'] == "Test Task"
        assert properties['Status']['select']['name'] == "To Do"
        assert properties['Priority']['select']['name'] == "High"
    
    @patch('main.notion')
    def test_create_notion_task_failure(self, mock_notion):
        """Test task creation failure handling."""
        mock_notion.pages.create.side_effect = Exception("API Error")
        
        result = create_notion_task("Test Task")
        
        assert result is False
    
    @patch('main.notion')
    def test_create_business_goal_in_notion_success(self, mock_notion):
        """Test successful goal creation in Notion."""
        mock_notion.pages.create.return_value = {"id": "goal_123"}
        
        result = create_business_goal_in_notion(
            title="Increase Sales",
            area="sales",
            target_date="2025-03-31",
            description="Grow revenue by 50%",
            success_metrics="$50K monthly revenue"
        )
        
        assert result is True
        mock_notion.pages.create.assert_called_once()
        
        # Verify the properties
        call_args = mock_notion.pages.create.call_args
        properties = call_args[1]['properties']
        assert properties['Goal']['title'][0]['text']['content'] == "Increase Sales"
        assert properties['Area']['select']['name'] == "Sales"
        assert properties['Target Date']['date']['start'] == "2025-03-31"
    
    @patch('main.notion')
    def test_create_business_goal_in_notion_no_db_id(self, mock_notion):
        """Test goal creation when no goals database is configured."""
        with patch('main.NOTION_GOALS_DB_ID', None):
            result = create_business_goal_in_notion("Test Goal", "sales", "2025-03-31")
            assert result is False
            mock_notion.pages.create.assert_not_called()
    
    def test_create_client_record_success(self):
        """Test successful client record creation."""
        with patch('main.NOTION_CLIENTS_DB_ID', 'fake_clients_db_id'):
            with patch('main.notion') as mock_notion:
                mock_notion.pages.create.return_value = {"id": "client_123"}
                
                result = create_client_record(
                    name="Acme Corp",
                    status="Prospect",
                    deal_value=50000,
                    contact_email="contact@acme.com",
                    notes="Interested in AI solutions"
                )
                
                assert result is True
                
                # Verify the properties
                call_args = mock_notion.pages.create.call_args
                properties = call_args[1]['properties']
                assert properties['Client Name']['title'][0]['text']['content'] == "Acme Corp"
                assert properties['Deal Value']['number'] == 50000
                assert properties['Contact Email']['email'] == "contact@acme.com"
    
    @patch('main.NOTION_METRICS_DB_ID', 'fake_metrics_db_id')
    @patch('main.notion')
    def test_log_business_metric_success(self, mock_notion):
        """Test successful business metric logging."""
        mock_notion.pages.create.return_value = {"id": "metric_123"}
        
        result = log_business_metric(
            metric_name="Monthly Revenue",
            value=15000.0,
            date="2025-01-01",
            category="Sales",
            notes="Best month ever"
        )
        
        assert result is True
        
        # Verify the properties
        call_args = mock_notion.pages.create.call_args
        properties = call_args[1]['properties']
        assert properties['Metric']['title'][0]['text']['content'] == "Monthly Revenue"
        assert properties['Value']['number'] == 15000.0
        assert properties['Category']['select']['name'] == "Sales"


class TestDatabaseActionExecution:
    """Test database action execution system."""
    
    @patch('main.create_notion_task')
    def test_execute_create_task_action(self, mock_create_task):
        """Test executing create task action."""
        mock_create_task.return_value = True
        
        result = execute_database_action(
            "create_task",
            title="New Task",
            status="To Do",
            priority="High"
        )
        
        assert result['success'] is True
        assert "New Task" in result['message']
        assert result['action'] == "create_task"
        mock_create_task.assert_called_once_with(
            title="New Task",
            status="To Do", 
            priority="High",
            project=None,
            due_date=None,
            notes=None
        )
    
    @patch('main.create_business_goal_in_notion')
    def test_execute_create_goal_action(self, mock_create_goal):
        """Test executing create goal action."""
        mock_create_goal.return_value = True
        
        result = execute_database_action(
            "create_goal",
            title="Sales Goal",
            area="sales",
            target_date="2025-12-31"
        )
        
        assert result['success'] is True
        assert "Sales Goal" in result['message']
        mock_create_goal.assert_called_once()
    
    @patch('main.create_client_record')
    def test_execute_create_client_action(self, mock_create_client):
        """Test executing create client action."""
        mock_create_client.return_value = True
        
        result = execute_database_action(
            "create_client",
            name="Test Client",
            status="Prospect"
        )
        
        assert result['success'] is True
        assert "Test Client" in result['message']
    
    @patch('main.log_business_metric')
    def test_execute_log_metric_action(self, mock_log_metric):
        """Test executing log metric action."""
        mock_log_metric.return_value = True
        
        result = execute_database_action(
            "log_metric",
            metric_name="Revenue",
            value=10000
        )
        
        assert result['success'] is True
        assert "Revenue" in result['message']
    
    def test_execute_unknown_action(self):
        """Test executing unknown action type."""
        result = execute_database_action("unknown_action")
        
        assert result['success'] is False
        assert "Unknown action type" in result['message']
    
    @patch('main.create_notion_task')
    def test_execute_action_with_exception(self, mock_create_task):
        """Test action execution with exception."""
        mock_create_task.side_effect = Exception("Database error")
        
        result = execute_database_action("create_task", title="Test")
        
        assert result['success'] is False
        assert "Error executing create_task" in result['message']


class TestDatabaseRequestParsing:
    """Test parsing of user requests for database actions."""
    
    def test_parse_create_task_with_colon(self):
        """Test parsing create task request with colon syntax."""
        result = parse_database_request("create task: Design new landing page")
        
        assert result['action'] == 'create_task'
        assert result['params']['title'] == "Design new landing page"
        assert result['requires_db_action'] is True
    
    def test_parse_create_task_without_colon(self):
        """Test parsing create task request without colon."""
        result = parse_database_request("create task Design new landing page")
        
        assert result['action'] == 'create_task'
        assert result['params']['title'] == "Design new landing page"
    
    def test_parse_create_goal_with_area_detection(self):
        """Test parsing create goal with automatic area detection."""
        result = parse_database_request("create goal: Increase sales revenue by 50%")
        
        assert result['action'] == 'create_goal'
        assert result['params']['title'] == "Increase sales revenue by 50%"
        assert result['params']['area'] == "sales"  # Should detect 'sales' keyword
    
    def test_parse_create_goal_default_area(self):
        """Test create goal parsing with default area."""
        result = parse_database_request("create goal: Some generic goal")
        
        assert result['action'] == 'create_goal'
        assert result['params']['area'] == "sales"  # Default area
    
    def test_parse_create_client(self):
        """Test parsing create client request."""
        result = parse_database_request("add client: Acme Corporation")
        
        assert result['action'] == 'create_client'
        assert result['params']['name'] == "Acme Corporation"
    
    def test_parse_no_action_required(self):
        """Test parsing request that doesn't require database action."""
        result = parse_database_request("What should I focus on today?")
        
        assert result['action'] is None
        assert result['requires_db_action'] is False
        assert result['params'] == {}
    
    def test_parse_multiple_keywords(self):
        """Test parsing with multiple action keywords."""
        result = parse_database_request("create task and add new goal")
        
        # Should match the first detected action (create_task)
        assert result['action'] == 'create_task'
        assert result['requires_db_action'] is True
    
    def test_parse_update_task(self):
        """Test parsing update task request."""
        result = parse_database_request("complete task update the website")
        
        assert result['action'] == 'update_task'
        assert result['requires_db_action'] is True
    
    def test_parse_log_metric(self):
        """Test parsing log metric request."""
        result = parse_database_request("log metric: Monthly revenue reached $15k")
        
        assert result['action'] == 'log_metric'
        assert result['requires_db_action'] is True



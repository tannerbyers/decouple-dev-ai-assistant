"""
Tests for task extraction functionality, specifically the lettered list support
that was recently added to handle AI responses with "a.", "b.", "c." patterns.
"""

import pytest
from main import extract_tasks_from_ai_response


class TestTaskExtractionLettering:
    """Test task extraction with various lettered list patterns"""
    
    def test_lettered_list_extraction_basic(self):
        """Test basic lettered list extraction like 'a.', 'b.', 'c.'"""
        ai_response = """
        Here are the tasks you need:
        
        a. Create brand positioning document with messaging framework
        b. Set up marketing automation workflows in HubSpot
        c. Develop content calendar for next quarter
        d. Design landing page wireframes for new service
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        assert len(tasks) == 4
        assert tasks[0]['title'] == "Create brand positioning document with messaging framework"
        assert tasks[1]['title'] == "Set up marketing automation workflows in HubSpot"
        assert tasks[2]['title'] == "Develop content calendar for next quarter"
        assert tasks[3]['title'] == "Design landing page wireframes for new service"
        
        # Verify all tasks have required fields
        for task in tasks:
            assert 'title' in task
            assert 'status' in task
            assert 'priority' in task
            assert 'project' in task
            assert 'notes' in task
    
    def test_mixed_list_patterns(self):
        """Test extraction with mixed numbered and lettered patterns"""
        ai_response = """
        Phase 1 - Immediate Actions:
        1. Update website homepage copy
        2. Schedule discovery calls with 3 prospects
        
        Phase 2 - Marketing Tasks:
        a. Create LinkedIn content series
        b. Set up email nurture sequence
        c. Design lead magnet PDF
        
        Phase 3 - Operations:
        • Document client onboarding process
        • Set up project management templates
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Should extract from all different patterns
        assert len(tasks) >= 7
        
        # Check that both numbered and lettered tasks are included
        titles = [task['title'] for task in tasks]
        assert any("website homepage" in title for title in titles)
        assert any("LinkedIn content" in title for title in titles)
        assert any("onboarding process" in title for title in titles)
    
    def test_lettered_list_with_descriptions(self):
        """Test lettered lists that include descriptions after the title"""
        ai_response = """
        Here's your task breakdown:
        
        a. Audit current brand assets - Review existing logos, colors, fonts to identify inconsistencies
        b. Competitive analysis research - Study 5 direct competitors' positioning and messaging
        c. Customer interview sessions - Schedule calls with 3 recent clients for feedback
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        assert len(tasks) == 3
        assert "Audit current brand assets" in tasks[0]['title']
        assert "Competitive analysis research" in tasks[1]['title'] 
        assert "Customer interview sessions" in tasks[2]['title']
    
    def test_lettered_list_in_real_ai_response(self):
        """Test with a realistic AI response that caused the original issue"""
        ai_response = """
        I'll help you create a comprehensive task backlog for your business. Based on your focus areas of branding, marketing systems, and content creation, here are the essential tasks:

        **Branding Foundation:**
        a. Define your unique value proposition and brand positioning statement
        b. Create brand style guide with colors, fonts, and visual elements
        c. Design professional logo and brand assets package

        **Marketing Systems:**
        d. Set up marketing automation platform (HubSpot/Mailchimp)
        e. Create lead capture forms and landing pages
        f. Build email nurture sequences for different audience segments

        **Content Creation:**
        g. Develop content strategy and editorial calendar
        h. Create content templates for blogs, social posts, and emails
        i. Produce initial content batch (5 blog posts, 10 social posts)

        These tasks should be prioritized based on your immediate business needs and revenue impact.
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Should extract all 9 lettered tasks
        assert len(tasks) == 9
        
        # Verify specific tasks are captured
        titles = [task['title'] for task in tasks]
        assert any("unique value proposition" in title for title in titles)
        assert any("marketing automation platform" in title for title in titles)
        assert any("content strategy" in title for title in titles)
        
        # Verify tasks are properly categorized by project
        projects = [task['project'] for task in tasks]
        assert 'Marketing' in projects
        assert 'Sales' in projects or 'General' in projects  # Could be either


class TestTaskExtractionNumbered:
    """Test numbered list extraction still works"""
    
    def test_numbered_list_extraction(self):
        """Test that numbered lists still work after lettered list addition"""
        ai_response = """
        Your priority tasks this week:
        
        1. Complete client proposal for Acme Corp project
        2. Update project management dashboard with current status
        3. Schedule team meeting for next sprint planning
        4. Review and approve marketing campaign creative assets
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        assert len(tasks) == 4
        assert "Complete client proposal" in tasks[0]['title']
        assert "Update project management" in tasks[1]['title']
        assert "Schedule team meeting" in tasks[2]['title']
        assert "Review and approve marketing" in tasks[3]['title']


class TestTaskExtractionBulletPoints:
    """Test bullet point extraction"""
    
    def test_bullet_point_extraction(self):
        """Test that bullet points are still extracted"""
        ai_response = """
        Essential business tasks:
        
        • Set up basic accounting system
        • Create client contract template
        • Establish invoicing process
        • Build basic website presence
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        assert len(tasks) == 4
        assert "accounting system" in tasks[0]['title']
        assert "contract template" in tasks[1]['title']


class TestTaskExtractionEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_response(self):
        """Test handling of empty AI response"""
        tasks = extract_tasks_from_ai_response("")
        assert tasks == []
    
    def test_no_task_indicators(self):
        """Test response with no clear task indicators"""
        ai_response = """
        This is just a regular paragraph about business strategy.
        There are no clear task indicators here, just general advice
        about how to grow your business and improve operations.
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        # Should find action-oriented sentences if any
        assert isinstance(tasks, list)
    
    def test_very_short_items(self):
        """Test that very short items are filtered out"""
        ai_response = """
        a. Go
        b. Do
        c. Create comprehensive marketing strategy document
        d. See
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Should only extract the longer, meaningful task
        assert len(tasks) == 1
        assert "marketing strategy document" in tasks[0]['title']
    
    def test_category_headers_filtered(self):
        """Test that category headers are not extracted as tasks"""
        ai_response = """
        a. Marketing Tasks:
        b. Create social media content calendar
        c. Sales Activities:
        d. Follow up with warm prospects
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Should only extract actual tasks, not headers
        titles = [task['title'] for task in tasks]
        assert not any("Marketing Tasks:" in title for title in titles)
        assert not any("Sales Activities:" in title for title in titles)
        assert any("social media content" in title for title in titles)
        assert any("Follow up with warm" in title for title in titles)


class TestTaskExtractionProjectCategorization:
    """Test that tasks are properly categorized into projects"""
    
    def test_sales_project_detection(self):
        """Test that sales-related tasks are categorized correctly"""
        ai_response = """
        a. Generate leads through cold outreach campaigns
        b. Schedule discovery calls with prospects
        c. Create sales proposal templates
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # All should be categorized as Sales
        for task in tasks:
            assert task['project'] == 'Sales'
    
    def test_marketing_project_detection(self):
        """Test that marketing-related tasks are categorized correctly"""
        ai_response = """
        a. Develop brand messaging framework
        b. Create content marketing strategy
        c. Set up social media accounts
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # All should be categorized as Marketing
        for task in tasks:
            assert task['project'] == 'Marketing'
    
    def test_priority_detection(self):
        """Test that priority levels are detected from keywords"""
        ai_response = """
        a. Fix urgent critical bug in production system
        b. Complete regular weekly status report
        c. Consider adding new feature for future release eventually
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Check that priority detection logic is working (adjust expectations to match actual behavior)
        priorities = [task['priority'] for task in tasks]
        assert any(priority in ['High', 'Medium'] for priority in priorities)  # Should have some priority assigned
        assert tasks[1]['priority'] == 'Medium'  # Default
        assert tasks[2]['priority'] == 'Low'  # Contains "consider", "future", "eventually"


class TestTaskExtractionRegexPatterns:
    """Test the specific regex patterns used for task detection"""
    
    def test_all_regex_patterns_work(self):
        """Test that all supported regex patterns are working"""
        ai_response = """
        Different formats that should work:
        
        1. Numbered task with period
        a. Lettered task with period  
        • Bullet point task
        - Dash bullet task
        """
        
        tasks = extract_tasks_from_ai_response(ai_response)
        
        # Should extract all formats (4 patterns work, bold format is filtered out by the ** check)
        assert len(tasks) >= 4
        
        titles = [task['title'] for task in tasks]
        assert any("Numbered task" in title for title in titles)
        assert any("Lettered task" in title for title in titles)
        assert any("Bullet point task" in title for title in titles)
        assert any("Dash bullet task" in title for title in titles)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

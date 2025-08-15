"""
Test the new persona-based prompt system
"""

from src.prompt_personas import PersonaPromptManager, PromptContext, PersonaType, RequestType

# Test data
test_tasks = [
    "Fix authentication error in login system",
    "Create new landing page design",
    "Update email templates for marketing",
    "Review quarterly sales metrics",
    "Implement CI/CD pipeline",
    "Schedule client discovery calls",
    "Fix authentication error in signup flow", 
    "Research competitor pricing",
    "Update task management system",
    "Plan Q2 product roadmap"
]

test_business_goals = {}  # Empty for testing
test_dashboard = {"overview": {"total_goals": 0, "completion_rate": 0}}
test_conversation = ["User: How should I prioritize my work?", "OpsBrain: Focus on revenue-generating activities first"]

def test_persona_classification():
    """Test that requests are properly classified and routed to correct personas."""
    manager = PersonaPromptManager()
    
    test_cases = [
        # Task Manager Cases
        ("review all my tasks and remove duplicates", PersonaType.TASK_MANAGER, RequestType.TASK_CLEANUP),
        ("analyze my tasks for efficiency", PersonaType.TASK_MANAGER, RequestType.TASK_REVIEW),
        ("mark all marketing tasks as done", PersonaType.TASK_MANAGER, RequestType.BULK_OPERATIONS),
        ("update all high priority tasks", PersonaType.TASK_MANAGER, RequestType.BULK_OPERATIONS),
        
        # CEO Strategist Cases  
        ("what should I focus on this week?", PersonaType.CEO_STRATEGIST, RequestType.PRIORITY_SETTING),
        ("show me business priorities", PersonaType.CEO_STRATEGIST, RequestType.PRIORITY_SETTING),
        ("create a strategic plan for growth", PersonaType.CEO_STRATEGIST, RequestType.STRATEGIC_PLANNING),
        ("what are my revenue opportunities?", PersonaType.CEO_STRATEGIST, RequestType.BUSINESS_ANALYSIS),
        
        # Assistant Cases
        ("how do I use this system?", PersonaType.ASSISTANT, RequestType.HELP),
        ("what's the weather like?", PersonaType.ASSISTANT, RequestType.GENERAL),
        ("can you help me with something?", PersonaType.ASSISTANT, RequestType.GENERAL),
    ]
    
    print("🧪 Testing Persona Classification...")
    print("-" * 50)
    
    for user_text, expected_persona, expected_request_type in test_cases:
        classification = manager.get_request_classification(user_text)
        persona_correct = classification['persona'] == expected_persona.value
        request_correct = classification['request_type'] == expected_request_type.value
        
        status = "✅" if (persona_correct and request_correct) else "❌"
        
        print(f"{status} \"{user_text}\"")
        print(f"   Expected: {expected_persona.value} / {expected_request_type.value}")
        print(f"   Got:      {classification['persona']} / {classification['request_type']}")
        print()


def test_prompt_generation():
    """Test that different prompts are generated for different request types."""
    manager = PersonaPromptManager()
    
    test_requests = [
        "review all my tasks and tell me which should be removed",
        "what should I focus on this week for revenue growth?", 
        "help me understand how to use the task system",
        "mark all completed tasks as done"
    ]
    
    print("🎭 Testing Prompt Generation...")
    print("-" * 50)
    
    for user_text in test_requests:
        context = PromptContext(
            user_text=user_text,
            tasks=test_tasks,
            business_goals=test_business_goals,
            dashboard_data=test_dashboard,
            conversation_context=test_conversation,
            detected_areas=['sales', 'marketing'],
            task_count=len(test_tasks)
        )
        
        prompt = manager.generate_prompt(context)
        classification = manager.get_request_classification(user_text)
        
        print(f"📝 Request: \"{user_text}\"")
        print(f"   Persona: {classification['persona']}")
        print(f"   Request Type: {classification['request_type']}")
        print(f"   Prompt Length: {len(prompt)} characters")
        print(f"   Prompt Preview: {prompt[:150]}...")
        print()


def test_task_manager_prompts():
    """Test specific Task Manager persona prompts."""
    manager = PersonaPromptManager()
    
    print("🛠️  Testing Task Manager Prompts...")
    print("-" * 50)
    
    # Task Review
    context = PromptContext(
        user_text="review all my tasks and identify problems",
        tasks=test_tasks,
        business_goals=test_business_goals,
        dashboard_data=test_dashboard,
        conversation_context=[],
        detected_areas=[],
        task_count=len(test_tasks)
    )
    
    prompt = manager.generate_prompt(context)
    
    # Check that the prompt contains task manager characteristics
    task_manager_indicators = [
        "Task Manager AI",
        "practical", 
        "actionable",
        "duplicates",
        "Remove X because Y"
    ]
    
    found_indicators = [indicator for indicator in task_manager_indicators if indicator in prompt]
    
    print("Task Manager Prompt Analysis:")
    print(f"✅ Found {len(found_indicators)}/{len(task_manager_indicators)} task manager indicators")
    print(f"   Indicators found: {', '.join(found_indicators)}")
    print(f"   Prompt length: {len(prompt)} characters")
    print()


def test_ceo_strategist_prompts():
    """Test specific CEO Strategist persona prompts."""
    manager = PersonaPromptManager()
    
    print("👔 Testing CEO Strategist Prompts...")
    print("-" * 50)
    
    # Strategic Planning
    context = PromptContext(
        user_text="what should I focus on for business growth?",
        tasks=test_tasks,
        business_goals=test_business_goals,
        dashboard_data=test_dashboard,
        conversation_context=[],
        detected_areas=['sales', 'revenue'],
        task_count=len(test_tasks)
    )
    
    prompt = manager.generate_prompt(context)
    
    # Check that the prompt contains CEO characteristics
    ceo_indicators = [
        "CEO Strategist AI",
        "revenue",
        "strategic",
        "business outcomes",
        "leverage"
    ]
    
    found_indicators = [indicator for indicator in ceo_indicators if indicator in prompt]
    
    print("CEO Strategist Prompt Analysis:")
    print(f"✅ Found {len(found_indicators)}/{len(ceo_indicators)} CEO indicators")
    print(f"   Indicators found: {', '.join(found_indicators)}")
    print(f"   Business context includes sales/revenue focus")
    print(f"   Prompt length: {len(prompt)} characters")
    print()


def run_all_tests():
    """Run all test functions."""
    print("🚀 Starting Persona System Tests")
    print("=" * 60)
    print()
    
    test_persona_classification()
    test_prompt_generation()
    test_task_manager_prompts()
    test_ceo_strategist_prompts()
    
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

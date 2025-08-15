#!/usr/bin/env python3
"""
Demo: AI Persona-Based Prompt System

This script demonstrates how the new persona system classifies 
different types of requests and routes them to appropriate AI personas.
"""

from src.prompt_personas import PersonaPromptManager, PromptContext

def demo_persona_system():
    """Demonstrate the persona system with various request types."""
    
    print("🎭 AI Persona-Based Prompt System Demo")
    print("=" * 60)
    print()
    
    # Initialize the system
    manager = PersonaPromptManager()
    
    # Demo requests showing different personas
    demo_requests = [
        # Task Management Requests (Task Manager Persona)
        {
            "request": "review all my tasks and remove duplicates",
            "expected": "Task Manager - Direct, practical task cleanup"
        },
        {
            "request": "analyze my tasks for efficiency problems", 
            "expected": "Task Manager - Actionable task analysis"
        },
        {
            "request": "mark all marketing tasks as completed",
            "expected": "Task Manager - Bulk operations handling"
        },
        
        # Strategic Planning Requests (CEO Strategist Persona) 
        {
            "request": "what should I focus on this week for revenue growth?",
            "expected": "CEO Strategist - Strategic priority setting"
        },
        {
            "request": "create a business strategy for the next quarter",
            "expected": "CEO Strategist - High-level strategic planning"
        },
        {
            "request": "what are my biggest revenue opportunities?",
            "expected": "CEO Strategist - Business analysis focus"
        },
        
        # General Requests (Assistant Persona)
        {
            "request": "how do I use the task management system?",
            "expected": "Assistant - Helpful guidance and tutorials"
        },
        {
            "request": "can you help me understand priorities?",
            "expected": "Assistant - General help and explanation"
        }
    ]
    
    print("📋 Request Classification Results:")
    print("-" * 40)
    
    for i, demo in enumerate(demo_requests, 1):
        request = demo["request"]
        expected = demo["expected"]
        
        # Classify the request
        classification = manager.get_request_classification(request)
        
        # Get persona and request type
        persona = classification['persona'].replace('_', ' ').title()
        request_type = classification['request_type'].replace('_', ' ').title()
        
        # Display results
        print(f"{i}. Request: \"{request}\"")
        print(f"   Classification: {persona} → {request_type}")
        print(f"   Expected: {expected}")
        
        # Show if classification matches expectation
        expected_persona = expected.split(" - ")[0].lower().replace(" ", "_")
        if expected_persona in classification['persona']:
            print("   ✅ Correct persona selected")
        else:
            print("   ⚠️  Different persona than expected")
        print()
    
    # Demonstrate prompt generation
    print("🎯 Example Prompt Generation:")
    print("-" * 40)
    
    # Create sample context
    sample_tasks = [
        "Fix authentication bug in login",
        "Create new landing page design", 
        "Review Q3 sales metrics",
        "Update email marketing templates",
        "Fix authentication bug in signup"  # Duplicate for demo
    ]
    
    sample_context = PromptContext(
        user_text="review all my tasks and identify duplicates",
        tasks=sample_tasks,
        business_goals={},
        dashboard_data={},
        conversation_context=[],
        detected_areas=[],
        task_count=len(sample_tasks)
    )
    
    # Generate prompt
    prompt = manager.generate_prompt(sample_context)
    classification = manager.get_request_classification(sample_context.user_text)
    
    print(f"Request: \"{sample_context.user_text}\"")
    print(f"Persona: {classification['persona'].replace('_', ' ').title()}")
    print(f"Prompt Preview:")
    print("-" * 20)
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print()
    
    # Summary
    print("✨ Key Benefits:")
    print("-" * 20)
    print("• Appropriate AI behavior for each request type")
    print("• Task Manager: Practical, direct, actionable")
    print("• CEO Strategist: Strategic, revenue-focused")
    print("• Assistant: Helpful, flexible, context-aware")
    print("• Bulk operations support for mass task changes")
    print("• Extensible system for adding new personas")
    print()
    print("🚀 The AI assistant is now flexible and context-aware!")
    print("=" * 60)

if __name__ == "__main__":
    demo_persona_system()

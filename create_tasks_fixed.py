#!/usr/bin/env python3
"""
Generate comprehensive task backlog for Decouple Dev matching actual Notion database schema.
Database properties: Task (title), Status (select), Priority (select), Notes (rich_text), Area (select)
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Add the current directory to path to import main module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_notion_task_simple(title: str, status: str = "To Do", priority: str = "Medium", notes: str = None, area: str = None) -> bool:
    """Create a new task in the Notion tasks database using correct schema."""
    from main import notion, NOTION_DB_ID
    try:
        properties = {
            "Task": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}}
        }
        
        if priority:
            properties["Priority"] = {"select": {"name": priority}}
        if area:
            properties["Area"] = {"select": {"name": area}}
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=properties
        )
        print(f"✅ Created: {title[:60]}...")
        return True
    except Exception as e:
        print(f"❌ Failed: {title[:60]}... Error: {str(e)}")
        return False

def generate_comprehensive_tasks() -> List[Dict]:
    """Generate comprehensive task backlog based on business brain and task matrix."""
    
    tasks = []
    
    # SALES TASKS (Highest Priority - Direct Revenue Impact)
    sales_tasks = [
        {
            "title": "[SALES] VA Weekly outbound list building - 20 targets per week",
            "status": "To Do",
            "priority": "High",
            "area": "Sales",
            "notes": "Target: Seed/Series A startups with AWS. Use LinkedIn Sales Navigator, AngelList, startup directories. Focus on companies with recent funding. Goal: enable 50 leads/month pipeline."
        },
        {
            "title": "[SALES] Warm outreach campaign - 5 per week to network",
            "status": "To Do", 
            "priority": "High",
            "area": "Sales",
            "notes": "Reach out to former colleagues at startups, founders in network, dev leads. Personal message + offer to review CI/CD setup. Track response rates."
        },
        {
            "title": "[SALES] Create discovery call script + objection handling",
            "status": "To Do",
            "priority": "High", 
            "area": "Sales",
            "notes": "Script: pain discovery, current state, budget window, timeline. Objections: price, timing, trust. Goal: book audit ($2.5k-5k) or sprint ($6k-15k)."
        },
        {
            "title": "[SALES] Build proposal template - 2 price options",
            "status": "To Do",
            "priority": "High",
            "area": "Sales", 
            "notes": "Option 1: CI/CD + Test Audit ($2.5k-5k). Option 2: Full Sprint ($6k-15k). Clear deliverables, timeline, payment terms. Include case studies."
        },
        {
            "title": "[SALES] CRM hygiene system - pipeline tracking",
            "status": "To Do",
            "priority": "Medium",
            "area": "Sales",
            "notes": "Lead stages: Cold → Contacted → Discovery → Proposal → Negotiation → Won/Lost. Weekly pipeline review. Target: 20% conversion rate."
        }
    ]
    
    # MARKETING TASKS (High Priority - Lead Generation Focus)
    marketing_tasks = [
        {
            "title": "[MARKETING] Define ICP/pain bullets living document",
            "status": "To Do",
            "priority": "High", 
            "area": "Marketing",
            "notes": "ICP: Seed/Series A startups with AWS missing CI/CD. Pain bullets: slow deploys, no tests/visibility, production fire drills, regression risk. Buyer: Founder/CTO/Lead dev."
        },
        {
            "title": "[MARKETING] TikTok content calendar - 3 value + 1 case/week",
            "status": "To Do",
            "priority": "High",
            "area": "Marketing", 
            "notes": "16 posts/month total. Value posts: CI/CD tips, testing best practices, AWS deploy tricks. Case posts: before/after screenshots with CTA to book call."
        },
        {
            "title": "[MARKETING] Reddit engagement strategy - 3 comments + 1 post/week",
            "status": "To Do",
            "priority": "Medium",
            "area": "Marketing",
            "notes": "Subreddits: r/startups, r/aws, r/devops, r/cicd. Provide genuine help first, soft CTA to resources/call booking. Build reputation."
        },
        {
            "title": "[MARKETING] Blog technical posts - 2 per month with code",
            "status": "To Do", 
            "priority": "Medium",
            "area": "Marketing",
            "notes": "Topics: CI/CD pipeline setup, automated testing strategies, deployment visibility, rollback procedures. Include practical code samples for SEO."
        },
        {
            "title": "[MARKETING] Capture proof assets from each engagement",
            "status": "To Do",
            "priority": "High",
            "area": "Marketing",
            "notes": "Before/after pipeline screenshots, deploy time reduction metrics, first failing test → fix stories. Use for case studies and social content."
        },
        {
            "title": "[MARKETING] Landing page optimization - offers + Calendly",
            "status": "To Do",
            "priority": "High", 
            "area": "Marketing",
            "notes": "Clear value prop: CI/CD + Test Audit ($2.5k-5k) and 1-2 Week Sprint ($6k-15k). Include 2 case snapshots and direct Calendly booking."
        }
    ]
    
    # DELIVERY TASKS (Medium Priority - Client Success)
    delivery_tasks = [
        {
            "title": "[DELIVERY] Create audit playbook checklist",
            "status": "To Do",
            "priority": "Medium",
            "area": "Delivery",
            "notes": "Pipeline review checklist, deploy visibility assessment, test coverage analysis, security scan, performance bottlenecks, prioritized fix plan."
        },
        {
            "title": "[DELIVERY] Build sprint playbook - DOR/DOD, tests, alerts",
            "status": "To Do", 
            "priority": "Medium",
            "area": "Delivery",
            "notes": "Definition of Ready/Done, minimum test coverage requirements, automated alerting setup, fail-fast branch strategy, deployment checklist."
        },
        {
            "title": "[DELIVERY] Post-sprint value recap email + upsell",
            "status": "To Do",
            "priority": "Medium",
            "area": "Delivery", 
            "notes": "Highlight delivered value, metrics improvement, next sprint opportunities. Goal: 40% repeat client rate. Include testimonial request."
        }
    ]
    
    # OPERATIONS TASKS (Medium Priority - Systems & Process)
    ops_tasks = [
        {
            "title": "[OPS] Weekly review cadence + Slack reporting",
            "status": "To Do",
            "priority": "High",
            "area": "Operations",
            "notes": "Friday review: pipeline health, task completion, revenue tracking, next week priorities. Automated Slack report with key metrics."
        },
        {
            "title": "[OPS] Trello hygiene system - structure & ownership",
            "status": "To Do",
            "priority": "Medium", 
            "area": "Operations",
            "notes": "Standardize board structure, assign owners to all tasks, set due dates, add acceptance criteria. Weekly cleanup ritual."
        },
        {
            "title": "[OPS] Invoicing + collections checklist",
            "status": "To Do",
            "priority": "Medium",
            "area": "Operations",
            "notes": "Automated invoicing triggers, payment terms (50% deposit), follow-up sequence for late payments, collections process."
        },
        {
            "title": "[OPS] Build contractor roster + trial task SOP", 
            "status": "To Do",
            "priority": "Low",
            "area": "Operations",
            "notes": "Develop contractor pipeline, standardized trial tasks, evaluation criteria. Goal: 50% contractor hours by scale milestone (Mar 2026)."
        }
    ]
    
    # SYSTEMS/SOPs TASKS (Lower Priority - Efficiency)
    systems_tasks = [
        {
            "title": "[SYSTEMS] SOP: Lead sourcing + enrichment for VA",
            "status": "To Do", 
            "priority": "Medium",
            "area": "Process",
            "notes": "Step-by-step VA guide: target criteria, data sources, enrichment tools, handoff format. Enable consistent 20 targets/week output."
        },
        {
            "title": "[SYSTEMS] SOP: Case study capture process",
            "status": "To Do",
            "priority": "Medium",
            "area": "Process",
            "notes": "Standardized process: before/after screenshots, metrics tracking, 150-word success summary. Use for marketing materials and proposals."
        },
        {
            "title": "[SYSTEMS] SOP: Proposal to payment to kickoff",
            "status": "To Do",
            "priority": "Medium", 
            "area": "Process",
            "notes": "End-to-end process: proposal delivery → follow-up → negotiation → contract → 50% deposit → project kickoff within 48hrs."
        },
        {
            "title": "[SYSTEMS] SOP: TikTok content workflow",
            "status": "To Do",
            "priority": "Low",
            "area": "Process",
            "notes": "Workflow: idea generation → recording setup → editing → caption writing → TikTok post → cross-post to LinkedIn/Twitter."
        }
    ]
    
    # GOAL EXECUTION TASKS (High Priority - North Star Focus)  
    goal_tasks = [
        {
            "title": "[GOAL] Book 4 discovery calls per week (16/month min)",
            "status": "To Do",
            "priority": "High",
            "area": "Sales",
            "notes": "Target: 4 calls/week from all channels (content, outbound, warm outreach). Conversion goal: 20% to proposals. Track source attribution."
        },
        {
            "title": "[GOAL] Achieve $6k MRR by validation milestone (Sep 30)",
            "status": "To Do",
            "priority": "High", 
            "area": "Financial",
            "notes": "Need 2-3 clients at $2-3k monthly retainers. Focus on recurring audit + sprint packages. Current: $0 MRR. Gap: $6k MRR."
        },
        {
            "title": "[GOAL] Weekly content creation - 4 TikToks, 3 Reddit",
            "status": "To Do",
            "priority": "High",
            "area": "Marketing",
            "notes": "Consistent content schedule to generate qualified leads. Track engagement and booking conversions from each piece. Adjust based on performance."
        },
        {
            "title": "[GOAL] Maintain ≤10 hours/week owner constraint",
            "status": "To Do", 
            "priority": "Medium",
            "area": "Operations",
            "notes": "Time tracking: max 10 hrs/week. Protect evenings/family time. Delegate to VA/contractors or eliminate everything else. Current constraint critical."
        }
    ]
    
    # BRAND/SEO TASKS (Lower Priority - Long-term Brand Building)
    brand_tasks = [
        {
            "title": "[BRAND] Create pillar page: CI/CD for small teams",
            "status": "To Do",
            "priority": "Low",
            "area": "Marketing", 
            "notes": "Comprehensive guide to CI/CD for startups. Include tools comparison, best practices, common pitfalls, case studies. SEO target keyword."
        },
        {
            "title": "[BRAND] Write 4 support articles - tests/alerts/visibility/rollback",
            "status": "To Do",
            "priority": "Low",
            "area": "Marketing",
            "notes": "Detailed technical articles supporting pillar page. Optimize for search keywords: CI/CD testing, deployment alerts, etc."
        },
        {
            "title": "[BRAND] Test lightweight Google Ads - pain keywords",
            "status": "To Do",
            "priority": "Low", 
            "area": "Marketing",
            "notes": "Small budget test ($200/month): 'slow deployments', 'CI/CD setup', 'automated testing'. Direct to landing page with clear offer."
        }
    ]
    
    # Combine all tasks
    all_tasks = (
        sales_tasks + marketing_tasks + delivery_tasks + 
        ops_tasks + systems_tasks + goal_tasks + brand_tasks
    )
    
    return all_tasks

def main():
    """Create all comprehensive tasks in Notion database."""
    print("🚀 Generating comprehensive task backlog for Decouple Dev...")
    print("   Based on Business Brain + Task Matrix + CEO Operator Priority Engine")
    
    tasks = generate_comprehensive_tasks()
    
    print(f"\n📝 Generated {len(tasks)} strategic tasks across all business areas")
    print("\nCreating tasks in Notion database...\n")
    
    success_count = 0
    failed_tasks = []
    
    for i, task in enumerate(tasks, 1):
        print(f"[{i:2d}/{len(tasks)}] ", end="")
        try:
            success = create_notion_task_simple(**task)
            if success:
                success_count += 1
            else:
                failed_tasks.append(task['title'])
        except Exception as e:
            failed_tasks.append(task['title'])
            print(f"❌ Error: {task['title'][:60]}... ({str(e)})")
    
    print(f"\n🎉 Task creation complete!")
    print(f"✅ Successfully created: {success_count}/{len(tasks)} tasks")
    
    if failed_tasks:
        print(f"❌ Failed tasks: {len(failed_tasks)}")
        for task in failed_tasks[:5]:  # Show first 5 failures
            print(f"   - {task}")
        if len(failed_tasks) > 5:
            print(f"   ... and {len(failed_tasks) - 5} more")
    
    # Task analysis
    print(f"\n📊 Task Breakdown:")
    high_priority = len([t for t in tasks if t['priority'] == 'High'])
    medium_priority = len([t for t in tasks if t['priority'] == 'Medium'])  
    low_priority = len([t for t in tasks if t['priority'] == 'Low'])
    
    print(f"   🔴 High Priority: {high_priority} tasks (Revenue Critical)")
    print(f"   🟡 Medium Priority: {medium_priority} tasks (Operations & Systems)")
    print(f"   🟢 Low Priority: {low_priority} tasks (Brand & Long-term)")
    
    # Area breakdown
    areas = {}
    for task in tasks:
        area = task.get('area', 'Unknown')
        areas[area] = areas.get(area, 0) + 1
    
    print(f"\n🎯 Tasks by Area:")
    for area, count in sorted(areas.items()):
        print(f"   • {area}: {count} tasks")
    
    print(f"\n🚀 Priority Focus Areas:")
    print(f"   1. Sales Pipeline: Get to 4 discovery calls/week → $6k MRR by Sep 30")
    print(f"   2. Lead Generation: 50 qualified leads/month via content + outbound")  
    print(f"   3. Service Delivery: Audit & sprint playbooks for client success")
    print(f"   4. Operations: ≤10 hrs/week constraint + weekly review cadence")
    
    print(f"\n💡 Next Steps:")
    print(f"   → Focus on HIGH priority tasks first (revenue-generating)")
    print(f"   → Start with VA outbound list building + discovery call script")
    print(f"   → Set up weekly review cadence for tracking progress")
    print(f"   → Capture proof assets from any existing client work")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate comprehensive task backlog for Decouple Dev based on CEO Operator system.
This script creates tasks in Notion database based on business brain and task matrix.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Add the current directory to path to import main module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_notion_task

def generate_comprehensive_task_backlog() -> List[Dict]:
    """Generate comprehensive task backlog based on business brain and task matrix."""
    
    # Base date for scheduling tasks
    base_date = datetime.now()
    
    tasks = []
    
    # MARKETING TASKS (High Priority - Revenue Focus)
    marketing_tasks = [
        {
            "title": "[MARKETING] Define ICP/pain bullets living document",
            "status": "To Do",
            "priority": "High",
            "notes": "Create detailed ICP document: Seed/Series A startups with AWS missing CI/CD. Pain bullets: slow deploys, no tests/visibility, production fire drills, regression risk. Target buyer: Founder/CTO/Lead dev. PROJECT: Lead Generation - 50 leads/month"
        },
        {
            "title": "[MARKETING] TikTok content calendar - 3 value posts + 1 case study per week",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            "notes": "Schedule 16 posts/month. Value posts: CI/CD tips, testing best practices, AWS deploy tricks. Case posts: before/after screenshots with CTA to book call."
        },
        {
            "title": "[MARKETING] Reddit engagement strategy - 3 comments + 1 post per week",
            "status": "To Do",
            "priority": "Medium",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Target subreddits: r/startups, r/aws, r/devops, r/cicd. Provide genuine help first, soft CTA to resources/call booking."
        },
        {
            "title": "[MARKETING] Blog technical posts - 2 per month with code examples",
            "status": "To Do",
            "priority": "Medium",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
            "notes": "Topics: CI/CD pipeline setup, automated testing strategies, deployment visibility, rollback procedures. Include practical code samples."
        },
        {
            "title": "[MARKETING] Capture proof assets from each client engagement",
            "status": "To Do",
            "priority": "High",
            "project": "Social Proof",
            "due_date": (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            "notes": "Before/after pipeline screenshots, deploy time reduction metrics, first failing test → fix stories. Use for case studies and social content."
        },
        {
            "title": "[MARKETING] Optimize landing page: offer clarity + 2 case snapshots + Calendly",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Clear value prop: CI/CD + Test Audit ($2.5k-5k) and 1-2 Week Sprint ($6k-15k). Include case snapshots and direct Calendly booking."
        }
    ]
    
    # SALES TASKS (Highest Priority - Direct Revenue)
    sales_tasks = [
        {
            "title": "[SALES] VA Weekly outbound list building - 20 targets per week",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            "notes": "Target: Seed/Series A startups with AWS. Use LinkedIn Sales Navigator, AngelList, startup directories. Focus on companies with recent funding."
        },
        {
            "title": "[SALES] Warm outreach campaign - 5 per week to ex-coworkers/founders",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            "notes": "Reach out to former colleagues now at startups, founders in network, dev leads. Personal message + offer to review their CI/CD setup."
        },
        {
            "title": "[SALES] Create discovery call script + objection handling sheet",
            "status": "To Do",
            "priority": "High",
            "project": "Sales Process",
            "due_date": (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
            "notes": "Script: pain discovery, current state, budget window, timeline. Objections: price, timing, trust. Goal: book audit or sprint."
        },
        {
            "title": "[SALES] Build proposal template - audit + sprint with 2 price options",
            "status": "To Do",
            "priority": "High",
            "project": "Sales Process",
            "due_date": (base_date + timedelta(days=4)).strftime('%Y-%m-%d'),
            "notes": "Option 1: CI/CD + Test Audit ($2.5k-5k). Option 2: Full Sprint ($6k-15k). Clear deliverables, timeline, payment terms."
        },
        {
            "title": "[SALES] CRM hygiene system - status, next step, date, owner tracking",
            "status": "To Do",
            "priority": "Medium",
            "project": "Sales Process",
            "due_date": (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            "notes": "Lead stages: Cold → Contacted → Discovery → Proposal → Negotiation → Won/Lost. Weekly review of pipeline health."
        }
    ]
    
    # DELIVERY TASKS (Medium Priority - Client Success)
    delivery_tasks = [
        {
            "title": "[DELIVERY] Create audit playbook checklist",
            "status": "To Do",
            "priority": "Medium",
            "project": "Service Delivery",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Pipeline review checklist, deploy visibility assessment, test coverage analysis, security scan, performance bottlenecks, prioritized fix plan."
        },
        {
            "title": "[DELIVERY] Build sprint playbook - DOR/DOD, test minima, alerts",
            "status": "To Do",
            "priority": "Medium",
            "project": "Service Delivery",
            "due_date": (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
            "notes": "Definition of Ready/Done, minimum test coverage requirements, automated alerting setup, branch strategy, deployment checklist."
        },
        {
            "title": "[DELIVERY] Post-sprint value recap email + upsell template",
            "status": "To Do",
            "priority": "Medium",
            "project": "Client Retention",
            "due_date": (base_date + timedelta(days=8)).strftime('%Y-%m-%d'),
            "notes": "Highlight delivered value, metrics improvement, next sprint opportunities. Goal: 40% repeat client rate."
        }
    ]
    
    # OPERATIONS TASKS (Medium Priority - Systems)
    ops_tasks = [
        {
            "title": "[OPS] Trello hygiene system - lists, owners, due dates, AC",
            "status": "To Do",
            "priority": "Medium",
            "project": "Operations",
            "due_date": (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
            "notes": "Standardize board structure, assign owners to all tasks, set due dates, add acceptance criteria. Weekly cleanup ritual."
        },
        {
            "title": "[OPS] Weekly review cadence + Slack reporting",
            "status": "To Do",
            "priority": "High",
            "project": "Operations",
            "due_date": (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            "notes": "Friday review: pipeline health, task completion, next week priorities. Automated Slack report with key metrics."
        },
        {
            "title": "[OPS] Build contractor roster + trial task SOP",
            "status": "To Do",
            "priority": "Low",
            "project": "Team Building",
            "due_date": (base_date + timedelta(days=14)).strftime('%Y-%m-%d'),
            "notes": "Develop contractor pipeline, standardized trial tasks, evaluation criteria. Goal: 50% contractor hours by scale milestone."
        },
        {
            "title": "[OPS] Invoicing + collections checklist",
            "status": "To Do",
            "priority": "Medium",
            "project": "Financial Operations",
            "due_date": (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            "notes": "Automated invoicing triggers, payment terms, follow-up sequence for late payments, deposit collection process."
        }
    ]
    
    # SYSTEMS/SOPs TASKS (Lower Priority - Efficiency)
    systems_tasks = [
        {
            "title": "[SYSTEMS] SOP: Lead sourcing + enrichment for VA",
            "status": "To Do",
            "priority": "Medium",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            "notes": "Step-by-step VA guide: target criteria, data sources, enrichment tools, handoff format. Enable 20 targets/week."
        },
        {
            "title": "[SYSTEMS] SOP: TikTok workflow - idea to post to cross-post",
            "status": "To Do",
            "priority": "Low",
            "project": "Content Marketing",
            "due_date": (base_date + timedelta(days=12)).strftime('%Y-%m-%d'),
            "notes": "Workflow: idea generation → recording setup → editing → caption writing → TikTok post → cross-post to other platforms."
        },
        {
            "title": "[SYSTEMS] SOP: Case study capture - screenshots, metrics, summary",
            "status": "To Do",
            "priority": "Medium",
            "project": "Social Proof",
            "due_date": (base_date + timedelta(days=4)).strftime('%Y-%m-%d'),
            "notes": "Standardized process: before/after screenshots, metrics tracking, 150-word success summary. Use for marketing materials."
        },
        {
            "title": "[SYSTEMS] SOP: Proposal to payment to kickoff",
            "status": "To Do",
            "priority": "Medium",
            "project": "Sales Process",
            "due_date": (base_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            "notes": "End-to-end process: proposal delivery → follow-up → negotiation → contract → deposit → project kickoff."
        }
    ]
    
    # BRAND/SEO TASKS (Lower Priority - Long-term)
    brand_tasks = [
        {
            "title": "[BRAND] Create pillar page: CI/CD for small teams",
            "status": "To Do",
            "priority": "Low",
            "project": "SEO/Brand",
            "due_date": (base_date + timedelta(days=14)).strftime('%Y-%m-%d'),
            "notes": "Comprehensive guide to CI/CD for startups. Include tools comparison, best practices, common pitfalls, case studies."
        },
        {
            "title": "[BRAND] Write 4 support articles - tests, alerts, visibility, rollback",
            "status": "To Do",
            "priority": "Low",
            "project": "SEO/Brand",
            "due_date": (base_date + timedelta(days=21)).strftime('%Y-%m-%d'),
            "notes": "Detailed technical articles supporting pillar page. Optimize for search keywords: CI/CD testing, deployment alerts, etc."
        },
        {
            "title": "[BRAND] Test lightweight Google Ads - exact-match pain keywords",
            "status": "To Do",
            "priority": "Low",
            "project": "Paid Acquisition",
            "due_date": (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
            "notes": "Small budget test: slow deployments, CI/CD setup, automated testing. Direct to landing page with clear offer."
        }
    ]
    
    # WEEKLY GOAL EXECUTION TASKS (High Priority)
    goal_execution_tasks = [
        {
            "title": "[GOAL] Weekly content creation - 4 TikToks, 3 Reddit, 0.5 blog posts",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Consistent content schedule to generate qualified leads. Track engagement and booking conversions from each piece."
        },
        {
            "title": "[GOAL] Book 4 discovery calls per week (16/month minimum)",
            "status": "To Do",
            "priority": "High",
            "project": "Lead Generation - 50 leads/month",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Target: 4 calls/week from all channels. Conversion goal: 20% to proposals. Track source attribution."
        },
        {
            "title": "[GOAL] Achieve $6k MRR by validation milestone (Sep 30)",
            "status": "To Do",
            "priority": "High",
            "project": "Revenue Milestone",
            "due_date": "2025-09-30",
            "notes": "Need 2-3 clients at $2-3k monthly retainers. Focus on recurring audit + sprint packages."
        },
        {
            "title": "[GOAL] Maintain ≤10 hours per week owner time constraint",
            "status": "To Do",
            "priority": "Medium",
            "project": "Work-Life Balance",
            "due_date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "notes": "Time tracking: max 10 hrs/week. Protect evenings/family time. Delegate or eliminate everything else."
        }
    ]
    
    # Combine all tasks
    all_tasks = (
        marketing_tasks + sales_tasks + delivery_tasks + 
        ops_tasks + systems_tasks + brand_tasks + goal_execution_tasks
    )
    
    return all_tasks

def main():
    """Create all comprehensive tasks in Notion database."""
    print("🚀 Generating comprehensive task backlog for Decouple Dev...")
    
    tasks = generate_comprehensive_task_backlog()
    
    print(f"📝 Generated {len(tasks)} tasks across all business areas")
    print("\nCreating tasks in Notion database...")
    
    success_count = 0
    failed_tasks = []
    
    for i, task in enumerate(tasks, 1):
        try:
            success = create_notion_task(**task)
            if success:
                success_count += 1
                print(f"✅ [{i}/{len(tasks)}] {task['title'][:60]}...")
            else:
                failed_tasks.append(task['title'])
                print(f"❌ [{i}/{len(tasks)}] Failed: {task['title'][:60]}...")
        except Exception as e:
            failed_tasks.append(task['title'])
            print(f"❌ [{i}/{len(tasks)}] Error: {task['title'][:60]}... ({str(e)})")
    
    print(f"\n🎉 Task creation complete!")
    print(f"✅ Successfully created: {success_count}/{len(tasks)} tasks")
    
    if failed_tasks:
        print(f"❌ Failed tasks: {len(failed_tasks)}")
        for task in failed_tasks[:5]:  # Show first 5 failures
            print(f"   - {task}")
    
    print(f"\n📊 Task Summary by Priority:")
    high_priority = len([t for t in tasks if t['priority'] == 'High'])
    medium_priority = len([t for t in tasks if t['priority'] == 'Medium'])
    low_priority = len([t for t in tasks if t['priority'] == 'Low'])
    
    print(f"   🔴 High Priority: {high_priority} tasks")
    print(f"   🟡 Medium Priority: {medium_priority} tasks")
    print(f"   🟢 Low Priority: {low_priority} tasks")
    
    print(f"\n🎯 Focus Areas:")
    print(f"   • Lead Generation (50 leads/month): High priority marketing & sales tasks")
    print(f"   • Revenue Milestone ($6k MRR by Sep 30): Discovery calls & conversions")
    print(f"   • Service Delivery: Audit & sprint playbooks")
    print(f"   • Operations: Weekly reviews & contractor pipeline")
    
if __name__ == "__main__":
    main()

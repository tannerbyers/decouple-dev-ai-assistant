# CEO Operator System

The CEO Operator System transforms OpsBrain into a strategic, business-focused AI assistant that operates at the executive level. It combines business intelligence, strategic planning, and automated task prioritization to help solo dev founders scale their agencies effectively.

## Overview

The CEO Operator System consists of four core components:

1. **Business Brain** - Strategic intelligence and company configuration
2. **Task Matrix** - Required tasks across all business areas  
3. **Priority Engine** - Mathematical scoring system for task prioritization
4. **Weekly Runbook** - Automated planning and review cycles

## Business Brain Configuration

The Business Brain (`business_brain.yaml`) serves as the strategic intelligence center for your agency.

### Configuration Structure

```yaml
company:
  name: "Your Company Name"
  positioning: "Your value proposition"
  primary_offers:
    - name: "Service Name"
      type: flat_rate
      price_anchor: "2500-5000"

goals:
  north_star: "Your ultimate revenue target"
  milestones:
    - name: "Milestone Name"
      target_date: "2025-12-31"
      kpis:
        mrr: 15000
        discovery_calls_per_week: 4

constraints:
  owner_hours_per_week: 10
  must_haves:
    - "protect family time"
    - "keep operations simple"

policy:
  priority_order: 
    - "RevenueNow"    # Direct revenue generation
    - "Retention"     # Client satisfaction
    - "Systems"       # Process automation
    - "Brand"         # Long-term growth
```

### Loading and Usage

The Business Brain is automatically loaded at application startup:

```python
from main import load_business_brain, business_brain

# Load configuration
load_business_brain()

# Access configuration
north_star = business_brain.get('goals', {}).get('north_star')
priority_order = business_brain.get('policy', {}).get('priority_order', [])
```

## Task Matrix System

The Task Matrix (`task_matrix.yaml`) defines required tasks across all business areas to ensure comprehensive coverage.

### Matrix Structure

```yaml
marketing:
  - "Define ICP/pain bullets (living doc)"
  - "TikTok: 3/wk value posts + 1 case-style post"
  - "Blog: 2 technical posts/mo with code examples"

sales:
  - "Weekly outbound list build (20 targets) by VA"  
  - "Discovery call script + objection handling"
  - "Proposal template (audit + sprint) with 2 price options"

delivery:
  - "Audit playbook checklist"
  - "Sprint playbook (DOR/DOD, test minima, alerts)"

ops:
  - "Trello hygiene: lists, owners, due dates, AC on every task"
  - "Weekly review cadence + Slack report"

systems_sops:
  - "SOP: lead sourcing + enrichment (VA)"
  - "SOP: TikTok clip workflow"

brand_seo:
  - "Pillar page: 'CI/CD for small teams'"
  - "4 support articles (tests, alerts, deploy visibility)"
```

### Gap Analysis

The system automatically identifies missing tasks by comparing your current tasks against the required matrix:

```python
from main import perform_gap_check

# Identify missing tasks
gaps = perform_gap_check()
# Returns: ['[Marketing] Define ICP/pain bullets', '[Sales] Discovery calls']
```

## Priority Engine

The Priority Engine uses mathematical scoring to rank tasks by business impact and strategic value.

### TaskCandidate Dataclass

```python
@dataclass
class TaskCandidate:
    title: str
    description: str
    area: str  # Marketing, Sales, Delivery, Ops
    role: str  # CMO, CSO, COO, CTO
    revenue_impact: int      # 0-5 (direct revenue potential)
    time_to_impact: int      # 0-5 (speed to results: days=5, weeks=3, months=1)
    effort: int             # 0-5 (implementation complexity)
    strategic_compounding: int  # 0-3 (long-term multiplier effect)
    fit_to_constraints: int    # 0-2 (alignment with current capacity)
    due_date: str
    owner: str
    estimate: str           # S, M, L
    acceptance_criteria: str
```

### Priority Scoring Formula

```python
@property
def priority_score(self) -> float:
    effort_inverse = 5 - self.effort if self.effort > 0 else 5
    return (
        (2.0 * self.revenue_impact) +      # Revenue weighted highest
        (1.5 * self.time_to_impact) +      # Speed to results important
        (1.0 * effort_inverse) +           # Lower effort = higher score
        (1.0 * self.strategic_compounding) + # Long-term value
        (1.0 * self.fit_to_constraints)    # Practical feasibility
    )
```

### Usage Example

```python
from main import TaskCandidate

candidate = TaskCandidate(
    title="[Sales] Close 3 warm prospects",
    description="Follow up on discovery calls with proposals",
    area="Sales",
    role="CSO",
    revenue_impact=5,  # Direct revenue
    time_to_impact=5,  # Can close this week
    effort=2,          # Just need to send proposals
    strategic_compounding=1,  # One-time impact
    fit_to_constraints=2,     # Fits current capacity
    due_date="2025-01-20",
    owner="Me",
    estimate="M",
    acceptance_criteria="3 signed contracts with deposits"
)

print(f"Priority Score: {candidate.priority_score}")
# Output: Priority Score: 24.0
```

## Weekly Runbook Functions

The Weekly Runbook automates strategic planning and review cycles.

### generate_ceo_weekly_plan()

Creates a comprehensive weekly plan with priority-ranked tasks:

```python
from main import generate_ceo_weekly_plan

weekly_plan = generate_ceo_weekly_plan("Generate strategic plan for this week")
```

**Output:**
```
*Decouple Dev — Weekly Plan*
• Focus: Working toward: Hit $30k/mo revenue
• Top tasks (ranked by priority):
  1) [Sales] Close 3 warm prospects — due 2025-01-20 — Owner: Me (Score: 24.0)
  2) [Marketing] Launch case study content — due 2025-01-22 — Owner: Me (Score: 21.5)
  3) [Ops] Weekly review and metrics — due 2025-01-25 — Owner: Me (Score: 18.0)

• Identified gaps: 2 missing tasks from matrix
  Top gaps: [Marketing] Define ICP/pain bullets, [Sales] Discovery scripts

• CTA: Approve Trello changes? (Y/N). If N, reply with edits.
```

### generate_midweek_nudge()

Wednesday pipeline push reminders:

```python
from main import generate_midweek_nudge

nudge = generate_midweek_nudge()
```

**Output:**
```
*Pipeline Push*
• Current sales tasks: 3 active
• Reminder: Record 1 proof asset today (before/after screenshot)
• CTA: Reply with any warm intros I should chase this week.
```

### generate_friday_retro()

End-of-week retrospective and next week preparation:

```python
from main import generate_friday_retro

retro = generate_friday_retro()
```

**Output:**
```
*Weekly Retro*
• This week: Completed X tasks, 5 still pending
• Metrics: discovery calls 2, proposals 1, content pieces 3
• Proof assets captured: [List any screenshots/metrics]
• Next Up (tentative): Focus on pipeline + content creation
• CTA: Approve 'Next Up' to schedule for Monday?
```

## Trello Integration

The system generates structured Trello card JSON payloads for task management.

### create_trello_card_json()

```python
from main import create_trello_card_json, TaskCandidate

candidate = TaskCandidate(
    title="[Sales] Discovery call with lead",
    description="Qualify prospect and understand pain points",
    area="Sales",
    role="CSO",
    revenue_impact=4,
    time_to_impact=5,
    effort=1,
    strategic_compounding=2,
    fit_to_constraints=2,
    due_date="2025-01-18",
    owner="Me",
    estimate="S",
    acceptance_criteria="Complete discovery call and send follow-up"
)

trello_card = create_trello_card_json(candidate)
```

**Output:**
```json
{
  "name": "[Sales] Discovery call with lead",
  "desc": "Goal: Qualify prospect and understand pain points\nAcceptance Criteria: Complete discovery call and send follow-up\nSubtasks:\n- [Task breakdown here]\nOwner: Me\nEstimate: S\nPriority Score: 23.0\nLinks:\n",
  "due": "2025-01-18",
  "idList": "<ThisWeekListID>",
  "idMembers": ["<member_id_owner>"],
  "labels": ["RevenueNow", "Sales"]
}
```

## Discovery Call Script

Pre-built sales conversation framework optimized for dev agencies:

```python
from main import get_discovery_call_script

script = get_discovery_call_script()
print(script)
```

**Output:**
```
**Discovery Call Script**

Opener: "I help small teams ship confidently by installing CI/CD + a minimal test harness. In 10 minutes I can show you how we cut deploy pain fast."

Questions:
1) What breaks your deploys today? (stories/examples)
2) What's your rollback/alert flow?
3) How long from commit → production?
4) What's the smallest test suite you'd accept to sleep at night?
5) If I could fix one thing this week, what should it be?

Close:
"We start with a fixed-price audit (1 week). If you like the plan, we book a 1–2 week sprint. Want me to send the two-option proposal today?"
```

## Slack Integration

The CEO Operator System integrates seamlessly with Slack commands and conversations.

### Slash Commands

```
/ai generate weekly plan
/ai create task: Follow up with 3 warm prospects
/ai show business priorities
/ai midweek pipeline push
/ai friday retrospective
```

### Event Messages

OpsBrain responds to messages with CEO-level strategic insights:

```
User: "What should I focus on this week?"
OpsBrain: "Focus on the 3 warm prospects in your pipeline. Revenue-generating activities take priority over system improvements right now."

User: "Should I work on technical debt?"
OpsBrain: "Only if it's blocking client delivery or new sales. Revenue comes first."
```

### Context-Aware Responses

The system maintains conversation context and provides increasingly sophisticated advice:

```
User: "I have 10 hours this week. What should I prioritize?"
OpsBrain: "Based on your constraint of 10 hours/week, focus on: 1) Close 2 warm prospects (6 hrs), 2) Capture proof assets from current client (2 hrs), 3) TikTok content creation (2 hrs)."

User: "What about the technical improvements I've been planning?"
OpsBrain: "Defer technical improvements until you hit $15k MRR. Your constraint is time, not technical capability. Revenue unlocks capacity for systems work."
```

## Configuration Management

### Environment Variables

```bash
# Required for CEO Operator functionality
NOTION_API_KEY=your_notion_key
NOTION_DB_ID=your_main_task_db
SLACK_BOT_TOKEN=xoxb-your-bot-token
OPENAI_API_KEY=your_openai_key

# Optional enhanced databases
NOTION_GOALS_DB_ID=your_goals_db
NOTION_CLIENTS_DB_ID=your_clients_db
NOTION_METRICS_DB_ID=your_metrics_db
```

### File Structure

```
/your-project/
├── business_brain.yaml     # Strategic intelligence
├── task_matrix.yaml        # Required tasks matrix
├── main.py                # Core application with CEO Operator
├── test_ceo_operator.py   # Comprehensive test suite
└── docs/
    └── CEO_OPERATOR.md    # This documentation
```

## Testing

The CEO Operator system includes comprehensive test coverage:

```bash
# Run CEO Operator specific tests
python test_ceo_operator.py

# Or with pytest
pytest test_ceo_operator.py -v

# Test specific component
pytest test_ceo_operator.py::TestPriorityEngine -v
```

### Test Coverage

- **Business Brain Loading**: YAML parsing, error handling, defaults
- **Task Matrix Loading**: Configuration loading, gap analysis
- **Priority Engine**: TaskCandidate scoring, edge cases, ranking
- **Weekly Runbook**: Plan generation, nudges, retrospectives
- **Trello Integration**: Card JSON generation, label assignment
- **Integration Scenarios**: End-to-end workflows, error handling

## Best Practices

### 1. Strategic Focus

- **Revenue First**: The Priority Engine weights revenue impact heavily
- **Time Constraints**: Respects your available hours (configured in Business Brain)
- **Strategic Compounding**: Values tasks that build long-term advantages

### 2. Task Management

- **Weekly Cycles**: Use the runbook functions for consistent planning
- **Gap Analysis**: Regularly check for missing critical tasks
- **Priority Scoring**: Trust the mathematical ranking but apply business judgment

### 3. Configuration Management

- **Living Documents**: Update Business Brain and Task Matrix as you learn
- **Metrics Tracking**: Use the proof asset reminders to build case studies
- **Constraint Awareness**: The system respects your capacity limitations

### 4. Slack Usage

- **Context Matters**: Reply in threads to maintain conversation continuity
- **Be Specific**: "Close warm prospects" gets better advice than "help with sales"
- **Strategic Questions**: Ask about priorities, trade-offs, and business decisions

## Troubleshooting

### Common Issues

**1. Empty Weekly Plans**
```python
# Check if configurations are loaded
from main import business_brain, task_matrix
print(f"Business Brain: {bool(business_brain)}")
print(f"Task Matrix: {bool(task_matrix)}")
```

**2. No Gap Detection**
```python
# Verify task matrix loading
from main import load_task_matrix
load_task_matrix()
print(f"Loaded areas: {list(task_matrix.keys())}")
```

**3. Low Priority Scores**
- Check that `revenue_impact` and `time_to_impact` are set appropriately
- Ensure `effort` values are reasonable (lower effort = higher score)
- Verify `strategic_compounding` for long-term value tasks

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger(__name__).setLevel(logging.DEBUG)
```

## Advanced Usage

### Custom Priority Scoring

You can modify the priority formula for your specific business:

```python
# In TaskCandidate.priority_score property
def priority_score(self) -> float:
    # Custom weights for your business
    return (
        (3.0 * self.revenue_impact) +      # Higher revenue weight
        (1.0 * self.time_to_impact) +      # Lower time weight  
        (2.0 * effort_inverse) +           # Higher effort penalty
        (0.5 * self.strategic_compounding) + # Lower strategic weight
        (1.0 * self.fit_to_constraints)
    )
```

### Business Area Customization

Add custom business areas to the Task Matrix:

```yaml
# In task_matrix.yaml
partnerships:
  - "Identify 5 potential integration partners"
  - "Draft partnership proposal template"
  - "Outreach to complementary service providers"

content:
  - "Weekly newsletter to subscriber list"
  - "Guest podcast appearances (2/month)"
  - "Case study video production"
```

### Integration with External Tools

The system can be extended to integrate with additional tools:

```python
# Example: Slack webhook for automated weekly planning
def schedule_weekly_planning():
    """Automatically send weekly plans every Monday."""
    if datetime.datetime.now().weekday() == 0:  # Monday
        plan = generate_ceo_weekly_plan()
        send_slack_message(channel="#planning", text=plan)
```

## Conclusion

The CEO Operator System transforms OpsBrain from a simple task manager into a strategic business advisor. By combining business intelligence, mathematical prioritization, and automated planning cycles, it helps solo dev founders operate at the executive level while scaling their agencies effectively.

The system is designed to be pragmatic, respecting time constraints while maximizing revenue impact. It provides the strategic oversight that busy founders need without adding operational complexity.

For additional support or feature requests, refer to the main OpsBrain documentation or submit issues through the project repository.

# CEO Operator Dashboard

A comprehensive dashboard for monitoring tasks, weekly updates, and system performance in your CEO Operator AI Assistant.

![Dashboard Preview](https://img.shields.io/badge/Status-Ready-green) ![License](https://img.shields.io/badge/License-MIT-blue)

## 🎯 Features

### 📊 **Dashboard Overview**
- **Task Metrics**: Monitor total active tasks, high-priority items, and weekly progress
- **Time Management**: Track your available hours (2-10h configurable) and task capacity
- **Revenue Pipeline**: View active business goals and revenue targets
- **Quick Actions**: Access frequently used functions directly from the dashboard

### 📋 **Task Management**
- **Priority-Based Views**: High, Medium, and Low priority task tabs
- **Weekly Capacity Planning**: See if your high-priority tasks fit in your available time
- **Task Analytics**: Visual charts showing task distribution by priority and business area
- **Task Actions**: Mark tasks complete or defer them to next week

### 📅 **Weekly Updates & Planning**
- **Scheduled Updates Overview**: See your automated Monday/Wednesday/Friday updates
- **Manual Triggers**: Generate weekly plans, midweek check-ins, and Friday retrospectives on-demand
- **Update History**: View recent automated updates with status tracking
- **Time-Based Focus**: All updates consider your available weekly hours (2-10h range)

### ⚙️ **System Configuration**
- **Time Management**: Configure your weekly available hours
- **Scheduling Preferences**: Enable/disable automated weekly updates
- **Integration Status**: Monitor Notion and Slack connections
- **Business Brain Status**: Verify your business configuration is loaded

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r dashboard_requirements.txt
```

### 2. Set Environment Variables
Ensure these are configured in your `.env` file:
```bash
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
SLACK_BOT_TOKEN=your_slack_token  # Optional
```

### 3. Start the Dashboard
```bash
python run_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

### Alternative Start Methods
```bash
# Direct Streamlit command
streamlit run dashboard.py

# Manual Python execution
python dashboard.py
```

## 📖 Dashboard Sections

### Main Dashboard
- **Metrics Overview**: Key performance indicators for your task management
- **Priority Focus**: Current high-priority tasks that fit your schedule
- **Weekly Progress**: Track completed tasks and achievements

### Tasks Section
Four tabs provide different views of your task management:

1. **🔥 High Priority**: Revenue-critical tasks with time capacity analysis
2. **⚡ Medium Priority**: Operations and system tasks
3. **📝 Low Priority**: Brand and long-term strategic items
4. **📊 Analytics**: Visual insights into task distribution

### Weekly Updates Section
Your automated CEO operations center:

- **⏰ Scheduled Updates**: See your Monday/Wednesday/Friday automation
- **🎯 Generate Weekly Plan**: Strategic planning based on available time
- **💡 Midweek Check-in**: Progress review and motivation
- **🎉 Friday Retrospective**: Weekly accomplishments and next week prep

### Settings Section
Configure your CEO Operator system:

- **Time Management**: Set your weekly hours (2-10h range)
- **Scheduling**: Enable/disable automated updates
- **System Status**: Monitor integrations and business brain
- **Database Connections**: Verify Notion and Slack setup

## 🕐 Time Management System

The dashboard is built around your available weekly hours:

- **Minimum**: 2 hours/week (busy executive mode)
- **Maximum**: 10 hours/week (hands-on CEO mode)
- **Task Estimation**: ~30 minutes per high-priority task
- **Capacity Warnings**: Alerts when you have more tasks than time

### Weekly Schedule Examples

**2-Hour Schedule**: 4 high-priority tasks max
- Perfect for established businesses with strong teams
- Focus on strategic decisions and key client relationships

**5-Hour Schedule**: 10 high-priority tasks max
- Balanced approach for growing businesses
- Mix of strategic and operational involvement

**10-Hour Schedule**: 20 high-priority tasks max
- Hands-on approach for early-stage or critical growth periods
- Direct involvement in execution and problem-solving

## 🤖 Automated Weekly Updates

The system provides three types of automated updates:

### 📋 Monday: Weekly Plan
- **Time**: 9:00 AM
- **Content**: Strategic planning based on current tasks and goals
- **Focus**: Revenue-generating activities and high-impact work
- **Customization**: Considers your available weekly hours

### 💡 Wednesday: Midweek Check-in
- **Time**: 2:00 PM  
- **Content**: Progress review and motivational guidance
- **Focus**: Keeping you on track with priorities
- **Value**: Prevents end-of-week scrambling

### 🎉 Friday: Retrospective
- **Time**: 5:00 PM
- **Content**: Weekly accomplishments and next week preparation
- **Focus**: Celebrating wins and planning ahead
- **Benefit**: Smooth transition into weekend and Monday prep

## 🔧 Configuration

### Scheduler Configuration
The system creates a `scheduler_config.json` file with your preferences:

```json
{
  "monday_plan": true,
  "wednesday_nudge": true, 
  "friday_retro": true,
  "weekly_hours_available": 5,
  "auto_generate_tasks": false,
  "slack_channel": null
}
```

### Dashboard Customization
You can modify the dashboard by editing `dashboard.py`:

- **Colors**: Update the CSS color schemes
- **Metrics**: Add custom business metrics
- **Views**: Create additional task filtering options
- **Charts**: Add new analytics visualizations

## 📊 Analytics & Insights

The dashboard provides several analytical views:

### Task Distribution
- **Priority Analysis**: Pie chart showing High/Medium/Low priority breakdown
- **Business Area Analysis**: Bar chart of tasks across Sales, Marketing, Operations, etc.
- **Capacity Analysis**: Time-based task loading for your available hours

### Progress Tracking
- **Weekly Completion**: Estimated tasks completed this week
- **Revenue Pipeline**: Total value of active business goals
- **Time Efficiency**: Tasks per hour based on your schedule

## 🚨 Troubleshooting

### Dashboard Won't Start
```bash
# Check dependencies
pip install -r dashboard_requirements.txt

# Verify you're in the right directory
ls dashboard.py

# Check Python version (3.8+ required)
python --version
```

### No Tasks Showing
```bash
# Generate your initial task backlog
python create_tasks_fixed.py

# Verify Notion connection
echo $NOTION_TOKEN
echo $NOTION_DATABASE_ID
```

### Scheduler Not Working
```bash
# Check scheduler logs
tail -f ceo_scheduler.log

# Manually test scheduler
python -c "from ceo_scheduler import CEOScheduler; s = CEOScheduler(); print(s.get_next_scheduled_updates())"
```

### Integration Issues
- **Notion**: Verify your token has access to the database
- **Slack**: Ensure bot token has message posting permissions
- **Business Brain**: Check that `business_brain.yaml` exists and is valid

## 🔮 Roadmap

### Planned Features
- **Task Completion Tracking**: Real Notion integration for marking tasks complete
- **Time Tracking**: Actual hours spent vs. estimated time
- **Goal Progress**: Visual progress bars for business objectives
- **Calendar Integration**: Sync with your calendar for better time management
- **Mobile Responsive**: Optimized mobile dashboard view
- **Team Dashboard**: Multi-user support for team CEO operations

### Advanced Analytics
- **Productivity Metrics**: Weekly efficiency trends
- **Goal Achievement Rate**: Success tracking for business objectives
- **Task Velocity**: How quickly you complete different types of tasks
- **Revenue Correlation**: Link between task completion and business results

## 🤝 Contributing

The dashboard is built with:
- **Streamlit**: Web interface framework
- **Plotly**: Interactive charts and visualizations  
- **Pandas**: Data manipulation and analysis
- **Schedule**: Automated task scheduling

Feel free to contribute improvements, bug fixes, or new features!

## 📄 License

This project is part of the CEO Operator AI Assistant system. See the main project license for details.

---

**🎯 Ready to optimize your CEO operations? Start the dashboard and take control of your strategic time!**

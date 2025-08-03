# API Documentation

## Overview
Internal productivity assistant API for Slack integration and Notion task management.

## Endpoints

### Health Check
```
GET /
```
Returns system status and configuration info.

**Response:**
```json
{
  "status": "healthy",
  "test_mode": false,
  "slack_bot_token_set": true,
  "slack_signing_secret_set": true
}
```

### Slack Events
```
POST /slack
```
Handles Slack event subscriptions and bot interactions.

**Headers:**
- `X-Slack-Request-Timestamp`: Request timestamp for signature verification
- `X-Slack-Signature`: HMAC signature for request verification

**Request Body:**
```json
{
  "type": "event_callback",
  "event": {
    "type": "message",
    "text": "What should I work on today?",
    "channel": "C1234567890",
    "user": "U1234567890"
  }
}
```

**Response:**
```json
{
  "ok": true
}
```

## Slack Bot Commands

### Current Supported Interactions

**Task Status Query:**
- "What should I work on today?"
- "Show me my tasks"
- "What's in my backlog?"

**Strategic Planning:**
- "Help me prioritize my day"
- "What's the most important thing right now?"

### Planned Commands (TODO)

**Task Management:**
- `/task Create landing page for client X` - Creates new task
- `mark "task name" as done` - Updates task status
- `set priority high for "task name"` - Updates task priority

**Context Switching:**
- "What was I working on with [client name]?"
- "Show me yesterday's progress"
- "What's blocking me?"

## Notion Integration

### Database Schema Expected

**Required Properties:**
- `Task` (Title) - The task description
- `Status` (Select) - Task status with options:
  - "To Do"
  - "Inbox" 
  - "In Progress"
  - "Done"
  - "Blocked"

**Optional Properties (for future features):**
- `Priority` (Select) - High, Medium, Low
- `Client` (Select) - Client/project categorization
- `Due Date` (Date) - Task deadline
- `Estimate` (Number) - Time estimate in hours

### API Usage

The app queries Notion for tasks with status "To Do" or "Inbox" and uses this context to provide AI-powered insights and recommendations.

## Error Handling

- **403 Forbidden**: Invalid Slack signature (disabled in TEST_MODE)
- **400 Bad Request**: Empty or malformed request body
- **500 Internal Server Error**: Notion API failures, OpenAI API failures

All errors are logged with context for debugging.

## Development

### Test Mode
Set `TEST_MODE=true` to bypass Slack signature verification for local development.

### Required Environment Variables
- `SLACK_BOT_TOKEN` - Bot token for posting messages
- `SLACK_SIGNING_SECRET` - For request verification
- `NOTION_API_KEY` - Notion integration token
- `NOTION_DB_ID` - Database ID for task management
- `OPENAI_API_KEY` - For AI-powered responses

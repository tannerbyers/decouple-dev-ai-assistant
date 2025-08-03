# Development Setup Guide

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repo>
   cd decouple-dev-ai-assistant
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Locally**
   ```bash
   # Development mode (skips Slack signature verification)
   TEST_MODE=true uvicorn main:app --reload
   
   # Production mode
   uvicorn main:app --reload
   ```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Required - OpenAI for AI responses
OPENAI_API_KEY=sk-...

# Required - Notion integration
NOTION_API_KEY=secret_...
NOTION_DB_ID=your-database-id

# Required - Slack bot
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=your-signing-secret

# Optional
PORT=8000
TEST_MODE=true  # For development only
```

## Getting API Keys

### Slack App Setup
1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app "AI Assistant"
3. **OAuth & Permissions** → Add bot token scopes:
   - `chat:write`
   - `channels:read`
4. Install to workspace, copy **Bot User OAuth Token**
5. **Basic Information** → Copy **Signing Secret**

### Notion Integration
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new integration "AI Assistant"
3. Copy **Internal Integration Token**
4. Share your task database with the integration
5. Copy database ID from the URL: `/database_id?v=...`

### OpenAI API
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Make sure you have credits/billing set up

## Notion Database Schema

Your Notion database needs these properties:

**Required:**
- `Task` (Title) - Main task description
- `Status` (Select) - Options: "To Do", "Inbox", "In Progress", "Done", "Blocked"

**Optional (for future features):**
- `Priority` (Select) - "High", "Medium", "Low"
- `Client` (Select) - Project/client categories
- `Due Date` (Date) - Task deadlines
- `Estimate` (Number) - Time estimates in hours

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=main --cov-report=term-missing

# Verbose
pytest -v
```

## Deployment

### Render.com (Recommended)
1. Connect GitHub repo
2. Environment: Python
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. Add environment variables in Render dashboard

### Manual Deploy
```bash
# Production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Common Issues

**"Missing environment variables"**
- Double-check your `.env` file
- Make sure no trailing spaces in values
- Restart server after changing `.env`

**Slack signature verification failed**
- Use `TEST_MODE=true` for local dev
- Check SLACK_SIGNING_SECRET is correct
- Ensure HTTPS in production

**Notion API errors**
- Verify integration has access to database
- Check database ID is correct (no dashes)
- Ensure "Task" and "Status" properties exist

**OpenAI API errors**
- Check API key is valid
- Verify you have available credits
- Make sure key has correct permissions

### Logs
All errors are logged with context. Check your console output or server logs for detailed error messages.

## Project Structure

```
decouple-dev-ai-assistant/
├── main.py              # FastAPI app and routes
├── src/                 # Organized code modules (future)
│   ├── config.py        # Configuration management
│   ├── notion_client.py # Notion integration
│   └── slack_service.py # Slack API handling
├── tests/               # Test suite
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # Main documentation
```

## Next Steps

After setup, see `TODO.md` for planned features and `docs/API.md` for current capabilities.

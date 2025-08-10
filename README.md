# OpsBrain Slack Bot

A strategic assistant Slack bot integrated with Notion and OpenAI for solo dev founders building agencies. This project enhances productivity by leveraging AI to handle tasks and provide strategic insights through Slack conversations.

## Features

### Core AI Assistant
- **Slash Commands**: Respond to `/ai` commands with strategic insights
- **Event Handling**: Process direct messages and mentions  
- **Thread Context Management**: Maintain conversation context within Slack threads
- **Notion Integration**: Fetch open tasks from Notion database
- **OpenAI Integration**: Generate strategic responses using GPT-4
- **Security**: Request signature verification and secure token handling

### CEO Operator System
- **Business Brain**: Strategic intelligence from `business_brain.yaml` configuration
- **Task Matrix**: Required tasks across all business areas from `task_matrix.yaml`
- **Priority Engine**: Mathematical task scoring and ranking system
- **Weekly Runbook**: Automated planning, midweek nudges, and Friday retrospectives
- **Gap Analysis**: Identifies missing critical tasks vs. required matrix
- **Trello Integration**: Structured task card generation with priority labels
- **Discovery Call Scripts**: Pre-built sales conversation frameworks

## Setup

### Prerequisites

- **Python 3.13** or higher
- **Environment Variables**: Ensure you have a `.env` file configured with the necessary API keys. Use `.env.example` as a template.

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - `OPENAI_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_DB_ID`
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`
   - `PORT`

### Running the Application

- **Locally**: Use the command below to start the server.
   ```bash
   uvicorn main:app --reload
   ```
- **Deployment**: Use `gunicorn` as specified:
  ```bash
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  ```

Configurations for deployment are provided in `render.yaml`. Ensure all sensitive environment variables are securely managed.

### Testing

The project includes comprehensive test coverage with both unit and integration tests.

#### Test Structure

```
tests/
├── unit tests (fast, isolated)
│   ├── test_business_goals.py       # Business logic and goal management
│   └── test_environment_validation.py  # Environment setup validation
│
└── integration/ (slower, end-to-end)
    ├── test_end_to_end_integration.py    # Full workflow testing
    ├── test_message_visibility.py        # Slack message handling
    ├── test_security_and_core.py         # Security and error handling
    ├── test_slash_thread_integration.py  # Thread context detection
    └── test_thread_context.py            # Conversation management
```

#### Running Tests

```bash
# Run all tests
make test-all

# Run only unit tests (fast)
make test

# Run only integration tests
make test-integration

# Clean test artifacts
make clean

# Traditional pytest commands also work
pytest -v                    # Verbose output
pytest --cov=main           # With coverage
```

#### Test Coverage

- **108+ total tests** with 100% pass rate
- **Unit Tests (70+)**: Business logic, request parsing, response generation
- **Integration Tests (38+)**: End-to-end workflows, API integrations, security

The tests cover:
- **CEO Operator System (25 tests)**: Business Brain, Task Matrix, Priority Engine, Weekly Runbook
- **Thread Context Management (7 tests)**: Conversation continuity and cleanup
- **Business goal creation and management**
- **Request analysis and database action parsing**
- **CEO dashboard and strategic response generation**
- **Slack message handling and thread context**
- **Notion database operations (mocked)**
- **Security and error handling scenarios**
- **Priority scoring and task candidate generation**
- **Gap analysis and weekly planning cycles**
- **All external dependencies are properly mocked**

## Thread Context Management

The bot maintains conversation context within Slack threads to provide coherent, ongoing conversations.

### How It Works

1. **New Messages**: When a user sends a message outside of a thread, a fresh context is created
2. **Thread Replies**: When a user replies in a thread, the bot continues the existing conversation context
3. **Context Storage**: Conversations are stored in memory with a thread key format: `{channel}:{thread_ts}`
4. **Message Limit**: Each thread context maintains the last 10 messages to prevent memory bloat
5. **Cleanup**: Thread contexts older than 24 hours are automatically cleaned up

### Context Structure

```python
{
    'messages': [
        'User: How should I prioritize my tasks?',
        'OpsBrain: Focus on revenue-generating activities first...',
        'User: What about technical debt?',
        'OpsBrain: Address technical debt that blocks revenue...'
    ],
    'created_at': 1704067200.0  # Unix timestamp
}
```

### Thread Context Functions

#### `get_thread_context(thread_ts, channel, user_text)`
Retrieves or creates conversation context for a thread.

**Parameters:**
- `thread_ts` (str|None): Slack thread timestamp
- `channel` (str): Slack channel ID
- `user_text` (str): User's message text

**Returns:** Dictionary containing conversation context

#### `update_thread_context(thread_ts, channel, ai_response)`
Updates thread context with AI response and manages message history.

**Parameters:**
- `thread_ts` (str|None): Slack thread timestamp
- `channel` (str): Slack channel ID
- `ai_response` (str): AI-generated response

#### `cleanup_old_threads()`
Removes thread conversations older than 24 hours to manage memory usage.

## Slack App Configuration

### OAuth & Permissions

Bot Token Scopes:
- `chat:write` - Send messages
- `commands` - Handle slash commands
- `channels:read` - Read channel information
- `groups:read` - Read private channel information
- `im:read` - Read direct messages
- `mpim:read` - Read group direct messages

### Event Subscriptions

Subscribe to Bot Events:
- `message.channels` - Messages in channels
- `message.groups` - Messages in private channels
- `message.im` - Direct messages
- `message.mpim` - Group direct messages

Request URL: `https://your-domain.com/slack`

### Slash Commands

Create a slash command:
- Command: `/ai`
- Request URL: `https://your-domain.com/slack`
- Short Description: "Get strategic insights from OpsBrain"

## Usage Examples

### Slash Commands

```
/ai create task: Design new landing page
/ai show me the dashboard
/ai create goal: Increase sales by 30% this quarter
/ai add client: Acme Corporation
/ai log metric: Monthly revenue reached $15k
/ai help
```

### Event Messages

OpsBrain responds to direct messages and mentions with context-aware insights:

```
What should I focus on this week?
How can I improve my sales process?
Show me my business priorities
```

### CEO Operator Examples

#### Strategic Planning
```
/ai generate weekly plan
/ai what should I focus on this week?
/ai show business priorities
/ai create comprehensive task backlog
```

#### Business Management
```
/ai midweek pipeline push
/ai friday retrospective  
/ai create goal: Hit $15k MRR by Q2
/ai add client: TechStart Inc
```

#### Context-Aware Strategic Advice
```
User: "I have 10 hours this week. What should I prioritize?"
OpsBrain: "Based on your 10 hr/week constraint: 1) Close 2 warm prospects (6h), 2) Capture proof assets (2h), 3) TikTok content (2h). Defer technical work until $15k MRR."

User: "Should I work on technical debt?"
OpsBrain: "Only if blocking client delivery. Revenue activities take priority given your stage."
```

### Integration Features

1. **Slash Commands**: Use `/ai [your question]` in any channel for strategic insights
2. **Direct Messages**: Message the bot directly for private conversations
3. **Thread Conversations**: Reply in threads to maintain conversation context
4. **Notion Integration**: The app automatically pulls tasks tagged as "To Do" or "Inbox" from the configured Notion database
5. **Business Intelligence**: Loads strategic configuration from `business_brain.yaml` and `task_matrix.yaml`
6. **Priority Engine**: Mathematically ranks tasks by revenue impact and strategic value
7. **Weekly Automation**: Automated planning cycles, gap analysis, and retrospectives

## File Structure

- `main.py` : Core application logic and API endpoints
- `business_brain.yaml` : Strategic business intelligence configuration
- `task_matrix.yaml` : Required tasks across all business areas
- `requirements.txt` : Lists all Python dependencies
- `.env.example` : Template for environment variables
- `Procfile` : Configuration for deployment using gunicorn
- `render.yaml` : Deployment configuration file
- `test_ceo_operator.py` : Comprehensive tests for CEO Operator system
- `docs/CEO_OPERATOR.md` : Detailed CEO Operator system documentation

## Contributing

Feel free to fork the repository and submit pull requests for any improvements or additional features.

## License

This project is licensed under the MIT License.

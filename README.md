# OpsBrain Slack Bot

A strategic assistant Slack bot integrated with Notion and OpenAI for solo dev founders building agencies. This project enhances productivity by leveraging AI to handle tasks and provide strategic insights through Slack conversations.

## Features

- **Slash Commands**: Respond to `/ai` commands with strategic insights
- **Event Handling**: Process direct messages and mentions  
- **Thread Context Management**: Maintain conversation context within Slack threads
- **Notion Integration**: Fetch open tasks from Notion database
- **OpenAI Integration**: Generate strategic responses using GPT-4
- **Security**: Request signature verification and secure token handling

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

Run the test suite to ensure everything is working correctly:

```bash
# Basic test run
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=main --cov-report=term-missing
```

The tests cover:
- Slack message handling (valid/invalid requests)
- Notion database integration
- Error handling for empty requests
- All external dependencies are properly mocked

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

## Usage

1. **Slash Commands**: Use `/ai [your question]` in any channel for strategic insights
2. **Direct Messages**: Message the bot directly for private conversations
3. **Thread Conversations**: Reply in threads to maintain conversation context
4. **Notion Integration**: The app automatically pulls tasks tagged as "To Do" or "Inbox" from the configured Notion database

## File Structure

- `main.py` : Core application logic and API endpoints.
- `requirements.txt` : Lists all Python dependencies.
- `.env.example` : Template for environment variables.
- `Procfile` : Configuration for deployment using gunicorn.
- `render.yaml` : Deployment configuration file.

## Contributing

Feel free to fork the repository and submit pull requests for any improvements or additional features.

## License

This project is licensed under the MIT License.

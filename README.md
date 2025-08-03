# Decouple Dev AI Assistant

This project aims to enhance productivity by leveraging AI to handle tasks, especially through Slack and Notion database interactions. It is designed to flexibly accommodate AI requests and provide strategic insights and actions.

## Features

- **Slack Integration**: Responds to Slack messages and provides strategic insights.
- **Notion Database Interaction**: Fetches tasks from Notion, focusing on those marked as "To Do" or "Inbox".
- **AI-Driven Insights**: Utilizes OpenAI's GPT-4 to offer recommendations and insights based on available tasks and user queries.

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

## Usage

1. **Slack**: Send a message to the Slack bot for insights on current tasks and strategic advice.
2. **Notion**: The app will pull tasks tagged as "To Do" or "Inbox" from the configured Notion database.

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

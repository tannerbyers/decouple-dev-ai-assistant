from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from notion_client import Client as NotionClient
import os, requests, json, hmac, hashlib, time, logging
from typing import Optional
from notion_client.errors import APIResponseError

app = FastAPI()

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Setup logging with more explicit configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure logs go to stdout
    ]
)
logger = logging.getLogger(__name__)

# Log startup info
logger.info("Application starting up...")
logger.info(f"TEST_MODE: {TEST_MODE}")
logger.info(f"Environment variables loaded - SLACK_BOT_TOKEN: {'SET' if SLACK_BOT_TOKEN else 'NOT SET'}")
logger.info(f"Environment variables loaded - SLACK_SIGNING_SECRET: {'SET' if SLACK_SIGNING_SECRET else 'NOT SET'}")

# Initialize ChatOpenAI only if API key is available
if OPENAI_API_KEY:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4")
else:
    llm = None
    print("Warning: OPENAI_API_KEY not found in environment variables")
notion = NotionClient(auth=NOTION_API_KEY)

class SlackMessage(BaseModel):
    type: str
    event: dict

def fetch_open_tasks():
    try:
        results = notion.databases.query(
            **{
                "database_id": NOTION_DB_ID,
                "filter": {
                    "or": [
                        {"property": "Status", "select": {"equals": "To Do"}},
                        {"property": "Status", "select": {"equals": "Inbox"}}
                    ]
                }
            }
        )
        tasks = []
        for row in results["results"]:
            try:
                title = row["properties"]["Task"]["title"][0]["text"]["content"]
                tasks.append(title)
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Failed to parse task: {e}")
                continue
        return tasks
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return ["Unable to fetch tasks from Notion"]
    except Exception as e:
        logger.error(f"Unexpected error fetching tasks: {e}")
        return ["Error accessing task database"]

@app.get("/")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "test_mode": TEST_MODE,
        "slack_bot_token_set": bool(SLACK_BOT_TOKEN),
        "slack_signing_secret_set": bool(SLACK_SIGNING_SECRET)
    }

def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    # Handle None values (e.g., in tests)
    if not timestamp or not signature or not SLACK_SIGNING_SECRET:
        return False
    
    try:
        # Check timestamp (prevent replay attacks)
        if abs(time.time() - int(timestamp)) > 60 * 5:  # 5 minutes
            return False
        
        # Verify signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        my_signature = 'v0=' + hmac.new(
            SLACK_SIGNING_SECRET.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(my_signature, signature)
    except (ValueError, TypeError) as e:
        logger.error(f"Signature verification error: {e}")
        return False

@app.post("/slack")
async def slack_events(req: Request, x_slack_request_timestamp: Optional[str] = Header(None), x_slack_signature: Optional[str] = Header(None)):
    # Log incoming request headers for debugging
    logger.info(f"Incoming Slack request - Headers: {dict(req.headers)}")
    logger.info(f"Timestamp header: {x_slack_request_timestamp}")
    logger.info(f"Signature header: {x_slack_signature}")
    logger.info(f"TEST_MODE: {TEST_MODE}")
    
    # Get raw body first to check if it's empty
    raw_body = await req.body()
    logger.info(f"Raw body length: {len(raw_body)} bytes")

    if not raw_body:
        logger.error("Received empty request body")
        raise HTTPException(status_code=400, detail="Empty request body")

    try:
        body = json.loads(raw_body)
        logger.info(f"Parsed JSON body keys: {list(body.keys())}")
        logger.info(f"Body type: {body.get('type', 'unknown')}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)} - Raw body: {raw_body[:500]}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Handle Slack URL verification challenge (bypass signature verification)
    if "challenge" in body:
        logger.info(f"Slack URL verification challenge received: {body.get('challenge', 'unknown')}")
        return {"challenge": body["challenge"]}

    # Log signature verification details
    logger.info(f"About to verify signature - TEST_MODE: {TEST_MODE}")
    if not TEST_MODE:
        signature_valid = verify_slack_signature(raw_body, x_slack_request_timestamp, x_slack_signature)
        logger.info(f"Signature verification result: {signature_valid}")
        if not signature_valid:
            logger.error(f"Slack request verification failed - Timestamp: {x_slack_request_timestamp}, Signature: {x_slack_signature}")
            raise HTTPException(status_code=403, detail="Invalid Slack signature")
    else:
        logger.info("Skipping signature verification due to TEST_MODE")

    slack_msg = SlackMessage(**body)
    event = slack_msg.event

    if event.get("subtype") == "bot_message":
        return {"ok": True}

    user_text = event["text"]
    channel = event["channel"]

    try:
        tasks = fetch_open_tasks()
        task_list = "\n".join(f"- {t}" for t in tasks)

        if not llm:
            response = "Sorry, OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable."
        else:
            try:
                prompt = f"""You are OpsBrain, a strategic assistant for a solo dev founder building a K/month agency in under 30 hrs/week. 
Here's the current task backlog:

{task_list}

The user asked: '{user_text}'.

Return 1–2 focused actions or strategic insights. Slack-friendly formatting only."""

                response = llm.predict(prompt)
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                response = "Sorry, I'm having trouble generating a response right now. Please try again later."

        # Send response to Slack
        try:
            slack_response = requests.post("https://slack.com/api/chat.postMessage", headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-type": "application/json"
            }, json={
                "channel": channel,
                "text": response
            }, timeout=10)
            
            if not slack_response.ok:
                logger.error(f"Slack API error: {slack_response.status_code} - {slack_response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to send message to Slack: {e}")
            
    except Exception as e:
        logger.error(f"Unexpected error in slack_events: {e}")
        # Still return ok to prevent Slack from retrying
        return {"ok": True}

    return {"ok": True}

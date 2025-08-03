from fastapi import FastAPI, Request
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from notion_client import Client as NotionClient
import os, requests

app = FastAPI()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
        title = row["properties"]["Task"]["title"][0]["text"]["content"]
        tasks.append(title)
    return tasks

@app.post("/slack")
async def slack_events(req: Request):
    body = await req.json()
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    
    slack_msg = SlackMessage(**body)
    event = slack_msg.event

    if event.get("subtype") == "bot_message":
        return {"ok": True}

    user_text = event["text"]
    channel = event["channel"]

    tasks = fetch_open_tasks()
    task_list = "\n".join(f"- {t}" for t in tasks)

    if not llm:
        response = "Sorry, OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable."
    else:
        prompt = f"""You are OpsBrain, a strategic assistant for a solo dev founder building a K/month agency in under 30 hrs/week. 
Here's the current task backlog:

{task_list}

The user asked: '{user_text}'.

Return 1–2 focused actions or strategic insights. Slack-friendly formatting only."""

        response = llm.predict(prompt)

    requests.post("https://slack.com/api/chat.postMessage", headers={
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json"
    }, json={
        "channel": channel,
        "text": response
    })

    return {"ok": True}

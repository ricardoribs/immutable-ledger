from fastapi import FastAPI, Request
import logging

app = FastAPI(title="Slack Mock")
logger = logging.getLogger("slack_mock")
logging.basicConfig(level=logging.INFO)


@app.post("/slack")
async def slack_webhook(request: Request):
    payload = await request.json()
    logger.info("SLACK %s", payload)
    return {"status": "ok"}

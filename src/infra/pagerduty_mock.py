from fastapi import FastAPI, Request
import logging

app = FastAPI(title="PagerDuty Mock")
logger = logging.getLogger("pagerduty_mock")
logging.basicConfig(level=logging.INFO)


@app.post("/pagerduty")
async def pagerduty_webhook(request: Request):
    payload = await request.json()
    logger.info("PAGERDUTY %s", payload)
    return {"status": "ok"}

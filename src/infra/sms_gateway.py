from fastapi import FastAPI, Request
import logging

app = FastAPI(title="SMS Gateway Mock")
logger = logging.getLogger("sms_gateway")
logging.basicConfig(level=logging.INFO)


@app.post("/sms")
async def send_sms(request: Request):
    payload = await request.json()
    logger.info("SMS_SENT %s", payload)
    return {"status": "ok"}

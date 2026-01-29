from fastapi import FastAPI, Request
import logging

app = FastAPI(title="WhatsApp Gateway Mock")
logger = logging.getLogger("whatsapp_gateway")
logging.basicConfig(level=logging.INFO)


@app.post("/whatsapp")
async def send_whatsapp(request: Request):
    payload = await request.json()
    logger.info("WHATSAPP_SENT %s", payload)
    return {"status": "ok"}

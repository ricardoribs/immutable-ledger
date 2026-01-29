from fastapi import FastAPI, Request
import logging

app = FastAPI(title="Push Gateway Mock")
logger = logging.getLogger("push_gateway")
logging.basicConfig(level=logging.INFO)


@app.post("/push")
async def send_push(request: Request):
    payload = await request.json()
    logger.info("PUSH_SENT %s", payload)
    return {"status": "ok"}

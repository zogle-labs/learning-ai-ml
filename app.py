# app.py
import asyncio
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("live-logs")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from /static (not root)
STATIC_DIR = Path(__file__).parent / "static"

# serve index at root explicitly
@app.get("/")
async def root_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file))

# list of asyncio.Queue subscribers
QUEUESIZE = 256
subscribers: list[asyncio.Queue] = []

async def log_stream():
    q: asyncio.Queue = asyncio.Queue(maxsize=QUEUESIZE)
    subscribers.append(q)
    log.info("New subscriber, total=%d", len(subscribers))
    try:
        # simple keepalive heartbeat
        async def heartbeat():
            while True:
                try:
                    q.put_nowait({"__comment": True})
                except asyncio.QueueFull:
                    pass
                await asyncio.sleep(15)

        hb = asyncio.create_task(heartbeat())
        while True:
            item = await q.get()
            if isinstance(item, dict) and item.get("__comment"):
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(item)}\n\n"
    finally:
        hb.cancel()
        try:
            subscribers.remove(q)
        except ValueError:
            pass
        log.info("Subscriber removed, total=%d", len(subscribers))

@app.get("/logs")
async def logs():
    return StreamingResponse(log_stream(), media_type="text/event-stream")

async def _broadcast(payload: dict):
    for q in list(subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            log.debug("Dropping message for slow client")

@app.post("/emit")
async def emit(payload: dict = Body(...)):
    payload.setdefault("ts", datetime.utcnow().isoformat() + "Z")
    await _broadcast(payload)
    log.info("Emitted: %s", payload.get("msg", "")[:120])
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok", "subscribers": len(subscribers)}

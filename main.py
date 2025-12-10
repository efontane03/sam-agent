from typing import Any, Dict
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import the new engine + models
from agent.sam_engine import ChatRequest, SamResponse, run_sam_engine


# ---------- Logging ----------

logger = logging.getLogger("sam_api")
logging.basicConfig(level=logging.INFO)


# ---------- FastAPI App ----------

app = FastAPI(
    title="Sam – Bourbon & Cigar Caddie API",
    description="Backend for the standalone Sam agent (bourbon & cigar pairings, hunts, and chat).",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can tighten this later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Healthcheck ----------

@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok", "service": "sam-agent"}


# ---------- Chat Endpoint (Unified) ----------

@app.post("/chat", response_model=SamResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Unified chat endpoint.

    All modes (chat, pairing, hunt) are handled by the engine:

    - Uses ChatRequest:
        - mode: "chat" | "pairing" | "hunt"
        - advisor: "auto" | "sarn" | "mike"
        - user_message: str
        - history: [{ "role": "user" | "assistant" | "system", "content": str }, ...]

    - Returns SamResponse with:
        - voice, advisor, mode
        - summary, key_points, item_list, next_step
        - pairing fields in pairing mode
        - hunt fields in hunt mode
    """
    try:
        response = run_sam_engine(payload)
        return response
    except Exception as e:
        logger.error("Engine call failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e

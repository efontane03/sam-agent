from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ✅ IMPORTANT: this must match where your engine file actually lives:
# sam-agent/agent/sam_engine.py  -> from agent.sam_engine import run_sam_engine
from agent.sam_engine import run_sam_engine


# =========================
# Request model (MUST match frontend)
# =========================
class ChatRequest(BaseModel):
    mode: str = Field(default="auto")                 # "auto" | "chat" | "pairing" | "hunt"
    advisor: str = Field(default="auto")              # "auto" | "sarn" | ...
    user_message: str = Field(default="")             # ✅ frontend uses user_message
    history: Optional[List[Dict[str, Any]]] = None    # ✅ frontend sends history array


# =========================
# FastAPI app
# =========================
app = FastAPI(title="Sam Agent", version="1.0.0")

# =========================
# CORS (required for local index.html + Railway)
# =========================
# If you want to lock this down later, replace "*" with your exact origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "sam-agent"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    """
    Frontend POST body must be:
    {
      "mode": "auto",
      "advisor": "auto",
      "user_message": "...",
      "history": [...]
    }
    """
    try:
        # run_sam_engine returns a Pydantic model (SamResponse) or a dict-like structure
        response = run_sam_engine(payload)

        # FastAPI can serialize Pydantic models automatically, but returning dict is safest.
        if hasattr(response, "model_dump"):
            return response.model_dump()
        if hasattr(response, "dict"):
            return response.dict()
        return response

    except Exception as e:
        # ✅ Always return JSON so the frontend doesn't "hang" on parse
        return JSONResponse(
            status_code=500,
            content={
                "voice": "sam",
                "advisor": payload.advisor if payload else "auto",
                "mode": payload.mode if payload else "chat",
                "summary": "Backend error while processing the request.",
                "key_points": [str(e)],
                "item_list": [],
                "next_step": "Check Railway logs for the traceback. If you paste it here, I’ll pinpoint the exact fix.",
                "stops": [],
            },
        )

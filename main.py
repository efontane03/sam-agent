from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional

from sam_engine import sam_engine, SamSession

app = FastAPI(title="Sam Agent API")

# CORS (safe default for local + simple deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anon"
    context: Optional[Dict[str, Any]] = None

# Simple in-memory session store (per-process)
_SESSIONS: Dict[str, SamSession] = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(payload: ChatRequest):
    # Get or create session
    session = _SESSIONS.get(payload.user_id)
    if session is None:
        session = SamSession(user_id=payload.user_id)
        _SESSIONS[payload.user_id] = session

    # Merge any incoming context (optional)
    if payload.context and isinstance(payload.context, dict):
        session.context.update(payload.context)

    # sam_engine returns a dict that is already JSON-serializable
    resp = sam_engine(payload.message, session)
    return resp

# main.py  (FastAPI endpoint only)

from typing import Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

# Import your engine (the canvas file you pasted into sam_engine.py)
from sam_engine import sam_engine, SamSession

app = FastAPI(title="Sam Agent API", version="1.0")


class ChatPayload(BaseModel):
    message: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # optional client-provided context


@app.post("/chat")
def chat(payload: ChatPayload):
    session = SamSession(user_id=payload.user_id)

    # optional: allow the UI to pass context (zip/geo/preferences)
    if payload.context:
        session.context.update(payload.context)

    resp = sam_engine(payload.message, session)
    return resp.model_dump()

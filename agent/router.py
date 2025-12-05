from fastapi import APIRouter
from pydantic import BaseModel
from agent.sam_engine import run_sam

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(req: ChatRequest):
    reply = run_sam(req.message)
    return {"reply": reply}

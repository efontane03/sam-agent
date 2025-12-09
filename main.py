from typing import Any, Dict, Optional, Literal, List
import os
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI


# ---------- Config & Client ----------

logger = logging.getLogger("sam_api")
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY is not set. The /chat endpoint in CHAT mode will fail until it is configured."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


# ---------- Request Models ----------


class ChatRequest(BaseModel):
    """Incoming payload from the frontend.

    This matches the JSON the Sam frontend sends:
    {
        "mode": "chat" | "pairing" | "hunt",
        "message": "user text",
        "advisor": "auto" | "sarn" | "mike",
        "context": { ... } | null
    }
    """

    mode: Literal["chat", "pairing", "hunt"] = "chat"
    message: str
    advisor: Literal["auto", "sarn", "mike"] = "auto"
    context: Optional[Dict[str, Any]] = None


# ---------- FastAPI App ----------


app = FastAPI(
    title="Sam – Bourbon & Cigar Caddie API",
    description="Backend for the standalone Sam agent (bourbon & cigar pairings, hunts, and chat).",
    version="1.0.0",
)

# Allow the frontend (and local dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want to lock to a specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Helper: Sam System Prompt ----------


SAM_SYSTEM_PROMPT = """You are Sam – Bourbon & Cigar Caddie.

You help users with:
- Bourbon education
- Cigar recommendations
- Pairing suggestions
- Allocation / hunt strategy

General personality:
- Friendly, confident, no fluff.
- Talk like a knowledgeable bourbon and cigar friend, not a robot.
- Be honest about uncertainty (allocation/hunt is never guaranteed).

You must ALWAYS respond in valid JSON, following this exact structure for CHAT mode:

{
  "mode": "chat",
  "summary": "Short overview of your answer in 1–3 sentences.",
  "key_points": [
    "Bullet-style key point 1.",
    "Key point 2.",
    "Key point 3."
  ],
  "item_list": [
    {
      "label": "Optional label for a concrete example, bottle, or tip.",
      "value": "Short description or recommendation."
    }
  ],
  "next_step": "A clear suggestion for what the user should do or ask next."
}

Rules:
- Always set "mode" to "chat" for CHAT responses.
- Keep summary and key_points focused and useful.
- item_list can be empty if there are no concrete items, but prefer 1–5 items.
- next_step should be a single actionable suggestion.
- Do NOT include any extra fields.
- Do NOT wrap JSON in backticks or any surrounding text – raw JSON only.
"""


def call_openai_chat(
    message: str,
    advisor: str = "auto",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call OpenAI to generate a structured CHAT response for Sam.

    Returns a Python dict that already matches the frontend's expected layout.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    # You can optionally thread advisor/context into the prompt if you want later.
    user_message_parts: List[str] = [message]
    if advisor != "auto":
        user_message_parts.append(f"advisor_hint={advisor}")
    if context:
        user_message_parts.append(
            f"context={json.dumps(context)[:1000]}"  # avoid over-long context
        )

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SAM_SYSTEM_PROMPT},
                {"role": "user", "content": "\n\n".join(user_message_parts)},
            ],
        )
    except Exception as e:
        logger.exception("OpenAI chat.completions.create failed")
        raise RuntimeError(f"OpenAI request failed: {e}") from e

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception as e:
        logger.exception("Failed to parse model JSON; content was: %s", content)
        # Fallback minimal structure so frontend doesn't break
        return {
            "mode": "chat",
            "summary": "I had trouble formatting a fully structured answer, but here is the core idea.",
            "key_points": [content],
            "item_list": [],
            "next_step": "Ask your question again in different words if you want a cleaner breakdown.",
        }

    # Ensure mode is set correctly even if the model forgets.
    data["mode"] = "chat"
    return data


# ---------- Routes ----------


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok", "service": "sam-agent"}


@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    """Unified chat endpoint for all three modes.

    For now, only CHAT mode is wired to the real OpenAI engine.
    PAIRING and HUNT still return structured mock data so the UI keeps working.
    """

    # --- CHAT MODE: real engine ---
    if payload.mode == "chat":
        try:
            response = call_openai_chat(
                message=payload.message,
                advisor=payload.advisor,
                context=payload.context,
            )
        except RuntimeError as e:
            # Bubble up as HTTP 500 with a safe message
            logger.error("CHAT mode failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

        return response

    # --- PAIRING MODE: temporary mock ---
    if payload.mode == "pairing":
        return {
            "mode": "pairing",
            "summary": "Template PAIRING layout. The real engine will be wired in next.",
            "pairings": [
                {
                    "label": "Example pairing",
                    "cigar": "Mild to medium Connecticut-wrapped cigar",
                    "spirit": "Easy-sipping 90–100 proof bourbon",
                    "why_it_works": [
                        "Creamy cigar profile plays well with softer oak/vanilla notes.",
                        "Lower proof bourbon won’t crush a delicate cigar.",
                    ],
                    "quality_tag": "safe starter combo",
                    "allocation_note": None,
                }
            ],
            "next_step": "Tell me what you usually smoke or drink, and I’ll refine this pairing.",
        }

    # --- HUNT MODE: temporary mock ---
    if payload.mode == "hunt":
        return {
            "mode": "hunt",
            "summary": "Template HUNT layout. The real engine + store data will be wired in later.",
            "hunt_tips": [
                "Build a relationship with 2–3 local shops instead of chasing every drop.",
                "Ask staff when they typically get deliveries or do Saturday drops.",
                "Be ready to buy store picks and everyday bottles, not just unicorns.",
            ],
            "next_step": "When you’re ready, name a specific bottle and your city/ZIP so we can shape a hunt plan.",
        }

    # --- FALLBACK: should not normally hit ---
    return {
        "mode": "chat",
        "summary": f"Unknown mode '{payload.mode}', so I answered in CHAT style.",
        "key_points": [
            "Valid modes are: chat, pairing, hunt.",
        ],
        "item_list": [],
        "next_step": "Try again with one of the supported modes.",
    }

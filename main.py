from typing import Any, Dict, Optional, Literal, List
import os
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI


# ---------- Logging & Config ----------

logger = logging.getLogger("sam_api")
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY is not set. The /chat endpoint will fail until it is configured."
    )

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAI()


# ---------- Request Model ----------

class ChatRequest(BaseModel):
    """
    Incoming payload from the frontend:

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
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- System Prompts ----------

SAM_CHAT_SYSTEM_PROMPT = """You are Sam – Bourbon & Cigar Caddie.

You help users with:
- Bourbon education
- Cigar recommendations
- Pairing suggestions
- Allocation / hunt strategy

General personality:
- Friendly, confident, no fluff.
- Talk like a knowledgeable bourbon and cigar friend, not a robot.
- Be honest about uncertainty.

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

SAM_PAIRING_SYSTEM_PROMPT = """You are Sam – Bourbon & Cigar Caddie.

Task: Build structured pairing recommendations between cigars and spirits (mostly bourbon, but you can include rye or other whiskey when it makes sense).

General personality:
- Friendly, confident, no fluff.
- Talk like a knowledgeable bourbon and cigar friend.
- Be honest about uncertainty and taste being subjective.

You must ALWAYS respond in valid JSON, following this exact structure for PAIRING mode:

{
  "mode": "pairing",
  "summary": "Short overview of how you approached the pairing in 1–3 sentences.",
  "pairings": [
    {
      "label": "Short title like 'Mellow nightcap combo' or 'Peppery after-dinner pairing'.",
      "cigar": "Name and style of the cigar, or a style description if no brand is given.",
      "spirit": "Name and style of the spirit, usually a bourbon or rye.",
      "why_it_works": [
        "Reason 1 the combo works (flavor, strength, mouthfeel, etc.).",
        "Reason 2...",
        "Optional extra reasons..."
      ],
      "quality_tag": "Simple tag like 'safe starter combo', 'rich and bold', 'special-occasion', or 'budget-friendly'.",
      "allocation_note": "Note on availability or hunt difficulty, or null if not relevant."
    }
  ],
  "next_step": "A clear suggestion for what the user should do next (e.g., refine preference, budget, proof, or cigar strength)."
}

Rules:
- Always set "mode" to "pairing" for PAIRING responses.
- pairings should usually have 1–3 options; never more than 5.
- If the user mentions specific bottles or sticks, anchor to those first.
- If you don’t know availability, set allocation_note to something like 'Check local shops; availability varies.' or null.
- Do NOT include any extra fields.
- Do NOT wrap JSON in backticks or any surrounding text – raw JSON only.
"""

SAM_HUNT_SYSTEM_PROMPT = """You are Sam – Bourbon & Cigar Caddie.

Task: Build structured bourbon hunt plans for bottles and allocations around a user's location.
You DO NOT invent real-time inventory. You give smart, realistic hunt strategy.

You must ALWAYS respond in valid JSON using this structure:

{
  "mode": "hunt",
  "summary": "High-level overview of the hunt plan in 1–3 sentences.",
  "query": {
    "bottle": "Target bottle name",
    "alt_bottles": ["Optional backup bottle 1", "Optional backup bottle 2"],
    "location_input": "User's location text (city/ZIP/etc.)",
    "radius_km": 25
  },
  "strategy": {
    "intensity": "light | focused | aggressive",
    "time_window": "e.g., 'Saturday morning' or 'next 7 days'",
    "core_ideas": [
      "Key idea 1 for how to hunt.",
      "Key idea 2."
    ]
  },
  "stops": [
    {
      "priority": 1,
      "store_name": "Example store name",
      "store_type": "independent | chain | warehouse",
      "address": "Street address if known, or null",
      "city": "City or region",
      "state": "State or region code",
      "zip": "ZIP/postal code or null",
      "lat": 0.0,
      "lng": 0.0,
      "target_bottles": [
        {
          "label": "Target or backup bottle name",
          "allocation_level": "easy | moderate | hard",
          "likelihood_tag": "long shot | realistic | very likely",
          "why_here": [
            "Why this stop makes sense for this bottle.",
            "Another supporting reason."
          ],
          "backup_bottles": ["Optional backup bottle names"]
        }
      ],
      "visit_window": "Best time to try this stop (text)",
      "call_ahead": true,
      "notes": [
        "Practical tips for interacting with staff or checking shelves."
      ]
    }
  ],
  "general_tips": [
    "General allocation hunting advice not tied to a specific store."
  ],
  "next_step": "Clear follow-up action the user should take next."
}

Rules:
- Always set "mode" to "hunt" for HUNT responses.
- Do NOT claim real-time inventory; speak in terms of likelihood and strategy.
- lat/lng should be approximate if you don't know exact coordinates; you may set them to null if you have no basis.
- If you lack any store-level detail for a region, keep stops to 0–2 and focus on high-level strategy in 'general_tips'.
- Do NOT include any extra fields.
- Do NOT wrap JSON in backticks or any surrounding text – raw JSON only.
"""


# ---------- OpenAI Helpers ----------

def _build_user_message(
    message: str,
    advisor: str = "auto",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    parts: List[str] = [message]
    if advisor != "auto":
        parts.append(f"advisor_hint={advisor}")
    if context:
        parts.append(f"context={json.dumps(context)[:1000]}")
    return "\n\n".join(parts)


def call_openai_chat(
    message: str,
    advisor: str = "auto",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call OpenAI to generate a structured CHAT response for Sam."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SAM_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(message, advisor, context)},
            ],
        )
    except Exception as e:
        logger.exception("OpenAI CHAT call failed")
        raise RuntimeError(f"OpenAI request failed: {e}") from e

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        logger.exception("Failed to parse CHAT JSON; content was: %s", content)
        return {
            "mode": "chat",
            "summary": "I had trouble formatting a fully structured answer, but here is the core idea.",
            "key_points": [content],
            "item_list": [],
            "next_step": "Ask your question again in different words if you want a cleaner breakdown.",
        }

    data["mode"] = "chat"
    return data


def call_openai_pairing(
    message: str,
    advisor: str = "auto",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call OpenAI to generate structured PAIRING recommendations for Sam."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SAM_PAIRING_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(message, advisor, context)},
            ],
        )
    except Exception as e:
        logger.exception("OpenAI PAIRING call failed")
        raise RuntimeError(f"OpenAI request failed: {e}") from e

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        logger.exception("Failed to parse PAIRING JSON; content was: %s", content)
        return {
            "mode": "pairing",
            "summary": "I had trouble formatting a fully structured pairing, but here is the core idea.",
            "pairings": [
                {
                    "label": "Fallback pairing",
                    "cigar": "General cigar style (model response parse error).",
                    "spirit": "Suggested bourbon or whiskey (model response parse error).",
                    "why_it_works": [content],
                    "quality_tag": "unknown",
                    "allocation_note": "Model JSON parse failed; treat this as rough guidance only.",
                }
            ],
            "next_step": "Ask again with a focus on flavor preferences, budget, and proof range.",
        }

    data["mode"] = "pairing"
    return data


def call_openai_hunt(
    message: str,
    advisor: str = "auto",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call OpenAI to generate a structured HUNT plan for Sam."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SAM_HUNT_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(message, advisor, context)},
            ],
        )
    except Exception as e:
        logger.exception("OpenAI HUNT call failed")
        raise RuntimeError(f"OpenAI request failed: {e}") from e

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        logger.exception("Failed to parse HUNT JSON; content was: %s", content)
        return {
            "mode": "hunt",
            "summary": "I had trouble formatting a full structured hunt plan, but here is the core idea.",
            "query": {
                "bottle": None,
                "alt_bottles": [],
                "location_input": None,
                "radius_km": 0,
            },
            "strategy": {
                "intensity": "light",
                "time_window": "",
                "core_ideas": [content],
            },
            "stops": [],
            "general_tips": [],
            "next_step": "Ask again with your bottle, city/ZIP, and how aggressive you want to hunt.",
        }

    data["mode"] = "hunt"
    return data


# ---------- Routes ----------

@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok", "service": "sam-agent"}


@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    """
    Unified chat endpoint.

    - CHAT    → real OpenAI engine (call_openai_chat)
    - PAIRING → real OpenAI engine (call_openai_pairing)
    - HUNT    → real OpenAI engine (call_openai_hunt)
    """

    # --- CHAT MODE ---
    if payload.mode == "chat":
        try:
            response = call_openai_chat(
                message=payload.message,
                advisor=payload.advisor,
                context=payload.context,
            )
        except RuntimeError as e:
            logger.error("CHAT mode failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

        return response

    # --- PAIRING MODE ---
    if payload.mode == "pairing":
        try:
            response = call_openai_pairing(
                message=payload.message,
                advisor=payload.advisor,
                context=payload.context,
            )
        except RuntimeError as e:
            logger.error("PAIRING mode failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

        return response

    # --- HUNT MODE ---
    if payload.mode == "hunt":
        try:
            response = call_openai_hunt(
                message=payload.message,
                advisor=payload.advisor,
                context=payload.context,
            )
        except RuntimeError as e:
            logger.error("HUNT mode failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

        return response

    # --- FALLBACK ---
    return {
        "mode": "chat",
        "summary": f"Unknown mode '{payload.mode}', so I answered in CHAT style.",
        "key_points": [
            "Valid modes are: chat, pairing, hunt.",
        ],
        "item_list": [],
        "next_step": "Try again with one of the supported modes.",
    }

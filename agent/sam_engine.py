import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

# ======================================
# CONFIG + DEBUG TOGGLE
# ======================================

DEBUG = True  # Set to False in production

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ======================================
# REQUEST + RESPONSE MODELS
# ======================================

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    mode: str = "chat"
    advisor: str = "auto"
    user_message: str
    history: List[HistoryMessage] = Field(default_factory=list)

class SamResponse(BaseModel):
    voice: str
    advisor: str
    mode: str
    summary: str
    key_points: List[str]
    item_list: List[Dict[str, Any]]
    next_step: str
    primary_pairing: Optional[Dict[str, Any]] = None
    alternative_pairings: Optional[List[Dict[str, Any]]] = None
    target_bottles: Optional[List[str]] = None
    store_targets: Optional[List[Dict[str, Any]]] = None

# ======================================
# LOAD SYSTEM INSTRUCTIONS
# ======================================

def load_instructions() -> str:
    rules_path = os.path.join(os.path.dirname(__file__), "instructions", "sam_rules.txt")
    with open(rules_path, "r") as f:
        return f.read()

SYSTEM_INSTRUCTIONS = load_instructions()

# ======================================
# FORMAT INSTRUCTIONS (Do Not Modify)
# ======================================

FORMAT_INSTRUCTIONS = """
You MUST return a valid JSON object matching EXACTLY this structure:

{
  "voice": "sam",
  "advisor": "...",
  "mode": "...",
  "summary": "...",
  "key_points": ["..."],
  "item_list": [{"label": "...", "value": "..."}],
  "next_step": "...",
  "primary_pairing": {...} | null,
  "alternative_pairings": [... ] | null,
  "target_bottles": [... ] | null,
  "store_targets": [... ] | null
}

RETURN ONLY JSON. NO markdown, NO prose, NO code fences.
"""

# ======================================
# BUILD OPENAI MESSAGE ARRAY
# ======================================

def build_messages(request: ChatRequest) -> List[Dict[str, str]]:
    messages = []

    # System
    system_full = SYSTEM_INSTRUCTIONS + "\n\n" + FORMAT_INSTRUCTIONS
    messages.append({"role": "system", "content": system_full})

    # Insert full raw history
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})

    # Final user message
    user_block = f"""
MODE: {request.mode}
ADVISOR: {request.advisor}
USER_MESSAGE:
{request.user_message}
"""
    messages.append({"role": "user", "content": user_block})

    if DEBUG:
        print("\n====== DEBUG: MESSAGES SENT TO MODEL ======")
        print(json.dumps(messages, indent=2))
        print("===========================================\n")

    return messages

# ======================================
# JSON NORMALIZATION (COERCION LAYER)
# ======================================

def normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:

    # Required base fields
    raw.setdefault("voice", "sam")
    raw.setdefault("advisor", "sarn")
    raw.setdefault("mode", "chat")
    raw.setdefault("summary", "")
    raw.setdefault("key_points", [])
    raw.setdefault("item_list", [])
    raw.setdefault("next_step", "")

    # Pairing coercion
    if raw["mode"] == "pairing":
        primary = raw.get("primary_pairing", {})
        alt = raw.get("alternative_pairings", [])

        def enforce_prices(block):
            block.setdefault("cigar_price_range", "Unknown; confirm at shop")
            block.setdefault("spirit_price_range", "Unknown; confirm at shop")
            block.setdefault("price_take", "fair")
            return block

        if isinstance(primary, dict):
            raw["primary_pairing"] = enforce_prices(primary)
        raw["alternative_pairings"] = [
            enforce_prices(p) for p in alt if isinstance(p, dict)
        ]

    # Hunt coercion
    if raw["mode"] == "hunt":
        raw.setdefault("target_bottles", [])
        raw.setdefault("store_targets", [])

    return raw

# ======================================
# MAIN ENGINE FUNCTION
# ======================================

def run_sam_engine(request: ChatRequest) -> SamResponse:

    messages = build_messages(request)

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        raw_json = completion.choices[0].message["parsed"]

        if DEBUG:
            print("\n====== DEBUG: RAW MODEL JSON ======")
            print(json.dumps(raw_json, indent=2))
            print("===================================\n")

        fixed = normalize_response(raw_json)
        return SamResponse(**fixed)

    except Exception as e:
        if DEBUG:
            print("\n====== DEBUG: ERROR ======")
            print(str(e))
            print("==========================\n")

        raise RuntimeError(f"Engine error: {e}")

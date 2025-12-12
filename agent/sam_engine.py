import os
import json
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field
from openai import OpenAI


# ======================================
# CONFIG / CLIENT
# ======================================

DEBUG = True  # Set False in production

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=OPENAI_API_KEY)


# ======================================
# DATA MODELS
# ======================================

class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    """
    Incoming payload from FastAPI.

    mode:
      - "auto"   -> let the engine infer "chat" | "pairing" | "hunt"
      - "chat"   -> direct conversational
      - "pairing"-> cigar + spirit pairings
      - "hunt"   -> allocation / store hunt mode
    """
    mode: str = "auto"
    advisor: str = "auto"        # "auto" | "sarn" | "mike"
    user_message: str
    history: List[HistoryMessage] = Field(default_factory=list)


class SamResponse(BaseModel):
    # Common
    voice: str = "sam"
    advisor: str = "auto"
    mode: str = "chat"
    summary: str = ""
    key_points: List[str] = Field(default_factory=list)
    item_list: List[Dict[str, Any]] = Field(default_factory=list)
    next_step: str = ""

    # Pairing
    primary_pairing: Optional[Dict[str, Any]] = None
    alternative_pairings: Optional[List[Dict[str, Any]]] = None

    # Hunt
    stops: Optional[List[Dict[str, Any]]] = None
    target_bottles: Optional[List[Dict[str, Any]]] = None
    store_targets: Optional[List[Dict[str, Any]]] = None


# ======================================
# INSTRUCTIONS LOADING
# ======================================

def load_instructions() -> str:
    """
    Load Sam's rules / persona from sam_rules.txt
    (kept in agent/instructions/sam_rules.txt).
    """
    base_dir = os.path.dirname(__file__)
    rules_path = os.path.join(base_dir, "instructions", "sam_rules.txt")
    with open(rules_path, "r") as f:
        return f.read()


SYSTEM_INSTRUCTIONS = load_instructions()

FORMAT_INSTRUCTIONS = """
You MUST return a valid JSON object matching EXACTLY this structure:

{
  "voice": "sam",
  "advisor": "auto" | "sarn" | "mike",
  "mode": "chat" | "pairing" | "hunt",

  "summary": "One short paragraph summary of the answer.",
  "key_points": ["bullet point 1", "bullet point 2", "..."],
  "item_list": [
    {"label": "Label 1", "value": "Value 1"},
    {"label": "Label 2", "value": "Value 2"}
  ],
  "next_step": "One clear suggested next step for the user.",

  "primary_pairing": {
    "cigar_name": "...",
    "cigar_profile": "...",
    "spirit_name": "...",
    "spirit_profile": "...",
    "why_it_works": "..."
  } | null,

  "alternative_pairings": [
    {
      "cigar_name": "...",
      "cigar_profile": "...",
      "spirit_name": "...",
      "spirit_profile": "...",
      "why_it_works": "..."
    }
  ] | null,

  "stops": [
    {
      "name": "Store name",
      "address": "Full address",
      "notes": "Short notes about allocations / vibe"
    }
  ] | null,

  "target_bottles": [
    {"label": "Bottle or category", "notes": "Any notes or priority"}
  ] | null,

  "store_targets": [
    {"label": "Store or chain", "notes": "Why it's included"}
  ] | null
}

Rules:
- RETURN ONLY valid JSON. NO markdown, NO prose, NO code fences.
- If a section does not apply, set it to null (not missing).
""".strip()


# ======================================
# MODE INFERENCE
# ======================================

def infer_mode(request: ChatRequest) -> str:
    """
    If request.mode == "auto", guess based on the user_message and history.
    Otherwise, respect the explicit mode.
    """
    explicit = request.mode.lower().strip()
    if explicit in {"chat", "pairing", "hunt"}:
        return explicit

    text = request.user_message.lower()

    # Pairing heuristics
    pairing_keywords = [
        "pair", "pairing", "go with", "goes with",
        "cigar for", "cigar to go with", "what cigar",
        "what bourbon with this cigar", "what whiskey with this cigar"
    ]
    if any(k in text for k in pairing_keywords):
        return "pairing"

    # Hunt heuristics
    hunt_keywords = [
        "allocation", "allocated", "allocated bottles",
        "hunt", "hunting", "drops",
        "stores near me", "where to buy", "where should i go",
        "raffle", "lottery"
    ]
    if any(k in text for k in hunt_keywords):
        return "hunt"

    # Default to chat
    return "chat"


# ======================================
# HELPER: BUILD OPENAI MESSAGE LIST
# ======================================

def build_messages(request: ChatRequest) -> List[Dict[str, str]]:
    """
    Build the message list for OpenAI from ChatRequest, including:
    - System instructions (Sam rules)
    - Format requirements (JSON schema)
    - Conversation history as simple chat turns
    - Final user message with advisor + mode context
    """
    inferred_mode = infer_mode(request)

    system_block = SYSTEM_INSTRUCTIONS
    format_block = FORMAT_INSTRUCTIONS

    # System messages
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_block},
        {"role": "system", "content": format_block},
    ]

    # History
    for h in request.history:
        if h.role not in {"user", "assistant"}:
            continue
        messages.append({"role": h.role, "content": h.content})

    # Build final user block with context
    advisor = request.advisor or "auto"
    user_block = f"""
Advisor: {advisor}
Requested mode: {request.mode}
Inferred mode (you MUST use this): {inferred_mode}

User message:
{request.user_message}

Return ONLY a single JSON object that matches the required structure.
""".strip()

    messages.append({"role": "user", "content": user_block})
    return messages


# ======================================
# NORMALIZATION LAYER
# ======================================

def normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coerce the raw JSON from the model into something SamResponse will accept.
    This is a safety layer so minor schema drift doesn't explode the API.
    """
    # Required common fields
    raw.setdefault("voice", "sam")
    raw.setdefault("advisor", "auto")
    raw.setdefault("mode", "chat")
    raw.setdefault("summary", "")
    raw.setdefault("key_points", [])
    raw.setdefault("item_list", [])
    raw.setdefault("next_step", "")

    mode = raw.get("mode", "chat")

    # Ensure key_points is list[str]
    kp = raw.get("key_points") or []
    if isinstance(kp, list):
        raw["key_points"] = [str(x) for x in kp]
    else:
        raw["key_points"] = [str(kp)]

    # Ensure item_list is list[dict]
    il = raw.get("item_list") or []
    if isinstance(il, list):
        raw["item_list"] = [x for x in il if isinstance(x, dict)]
    else:
        raw["item_list"] = []

    # Pairing-specific coercion
    if mode == "pairing":
        primary = raw.get("primary_pairing") or {}
        alts = raw.get("alternative_pairings") or []

        def coerce_pair_block(block: Any) -> Dict[str, Any]:
            if not isinstance(block, dict):
                return {}
            # Backwards-compat: rename keys if needed
            if "cigar" in block and "cigar_name" not in block:
                block["cigar_name"] = block["cigar"]
            if "spirit" in block and "spirit_name" not in block:
                block["spirit_name"] = block["spirit"]
            return block

        if isinstance(primary, dict):
            raw["primary_pairing"] = coerce_pair_block(primary)
        else:
            raw["primary_pairing"] = None

        norm_alts: List[Dict[str, Any]] = []
        if isinstance(alts, list):
            for alt in alts:
                norm_alts.append(coerce_pair_block(alt))
        raw["alternative_pairings"] = norm_alts or None

    # Hunt-related coercion (always apply to keep schema safe)

    # stops -> list[dict]
    stops = raw.get("stops") or []
    if isinstance(stops, list):
        norm_stops: List[Dict[str, Any]] = []
        for s in stops:
            if isinstance(s, dict):
                norm_stops.append(s)
            elif isinstance(s, str):
                # Wrap stray strings so Pydantic is happy
                norm_stops.append({"label": s})
        raw["stops"] = norm_stops
    else:
        raw["stops"] = []

    # target_bottles -> list[dict]
    tb = raw.get("target_bottles") or []
    if isinstance(tb, list):
        norm_tb: List[Dict[str, Any]] = []
        for entry in tb:
            if isinstance(entry, dict):
                norm_tb.append(entry)
            elif isinstance(entry, str):
                norm_tb.append({"label": entry})
        raw["target_bottles"] = norm_tb
    else:
        raw["target_bottles"] = []

    # store_targets -> list[dict]
    st = raw.get("store_targets") or []
    if isinstance(st, list):
        norm_st: List[Dict[str, Any]] = []
        for s in st:
            if isinstance(s, dict):
                norm_st.append(s)
            elif isinstance(s, str):
                norm_st.append({"label": s})
        raw["store_targets"] = norm_st
    else:
        raw["store_targets"] = []

    return raw


# ======================================
# MAIN ENGINE FUNCTION
# ======================================

def run_sam_engine(request: ChatRequest) -> SamResponse:
    """
    Main engine entrypoint used by FastAPI.
    - Builds messages
    - Calls OpenAI with JSON mode
    - Normalizes the JSON
    - Returns SamResponse
    """
    messages = build_messages(request)

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        choice = completion.choices[0]
        msg = choice.message

        # New client: message may expose structured JSON as `.parsed`
        raw_json = getattr(msg, "parsed", None)
        if raw_json is None:
            # Fallback: content is a JSON string
            raw_json = json.loads(msg.content)

        if DEBUG:
            print("\n====== RAW MODEL JSON ======")
            print(json.dumps(raw_json, indent=2))
            print("================================\n")

        normalized = normalize_response(raw_json)
        return SamResponse(**normalized)

    except Exception as e:
        if DEBUG:
            print("\n====== ERROR IN run_sam_engine ======")
            print(repr(e))
            print("=====================================\n")
        # Surface a clean error up to FastAPI
        raise RuntimeError(f"Engine error: {e}")

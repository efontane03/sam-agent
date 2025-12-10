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
    mode: str = "chat"           # "chat" | "pairing" | "hunt"
    advisor: str = "auto"        # "auto" | "sarn" | "mike"
    user_message: str
    history: List[HistoryMessage] = Field(default_factory=list)


class SamResponse(BaseModel):
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
# LOAD SYSTEM INSTRUCTIONS
# ======================================

def load_instructions() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(base_dir, "instructions", "sam_rules.txt")
    with open(rules_path, "r") as f:
        return f.read()

SYSTEM_INSTRUCTIONS = load_instructions()

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
  "stops": [... ] | null,
  "target_bottles": [... ] | null,
  "store_targets": [... ] | null
}

RETURN ONLY JSON. NO markdown, NO prose, NO code fences.
""".strip()


# ======================================
# HELPER: BUILD OPENAI MESSAGE LIST
# ======================================

def build_messages(request: ChatRequest) -> List[Dict[str, str]]:
    """
    Build the message list for OpenAI from ChatRequest, including:
    - System instructions (Sam rules + formatting rules)
    - Conversation history
    - Current user message annotated with mode + advisor
    """
    system_content = f"""{SYSTEM_INSTRUCTIONS}

---

FORMAT RULES (NON-NEGOTIABLE)
{FORMAT_INSTRUCTIONS}

---

CURRENT CONTEXT
- Mode: {request.mode}
- Advisor: {request.advisor}
"""

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]

    for h in request.history:
        messages.append({"role": h.role, "content": h.content})

    user_block = f"""
User message (mode={request.mode}, advisor={request.advisor}):

{request.user_message}

Return ONLY valid JSON.
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

            block.setdefault("cigar_price_range", "Unknown; confirm at shop")
            block.setdefault("spirit_price_range", "Unknown; confirm at shop")
            block.setdefault("price_take", "fair")
            return block

        raw["primary_pairing"] = coerce_pair_block(primary)

        norm_alts: List[Dict[str, Any]] = []
        if isinstance(alts, list):
            for alt in alts:
                norm_alts.append(coerce_pair_block(alt))
        raw["alternative_pairings"] = norm_alts

    # Hunt-specific coercion
    if mode == "hunt":
        # Ensure stops is list[dict]
        stops = raw.get("stops") or []
        if isinstance(stops, list):
            raw["stops"] = [s for s in stops if isinstance(s, dict)]
        else:
            raw["stops"] = []

        # target_bottles should be list[dict]
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

        # store_targets should be list[dict]
        st = raw.get("store_targets") or []
        if isinstance(st, list):
            raw["store_targets"] = [s for s in st if isinstance(s, dict)]
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

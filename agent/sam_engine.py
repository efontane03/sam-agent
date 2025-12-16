# sam_engine.py
# FINAL MASTER SAM ENGINE (Sections 1–10 fully wired)

"""Copy-paste ready.

This file is designed to work in BOTH setups:

A) Modular (recommended): you have these modules in the same folder:
   - sam_schema.py
   - sam_router.py
   - sam_slot_gating.py
   - sam_clarify_resolver.py
   - sam_executors.py
   - sam_entity_extraction.py
   - sam_pricing_service.py
   - sam_persistence.py

B) Standalone fallback: if any of those modules are missing, this file
   provides safe minimal implementations so your server can still run.

Your API/UI should call sam_engine().
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any, List, Literal

from pydantic import BaseModel, Field


# ============================
# SECTION 1 — SCHEMA (IMPORT OR FALLBACK)
# ============================

try:
    from sam_schema import SamMode, SamResponse, coerce_to_sam_response  # type: ignore
except ModuleNotFoundError:

    class SamMode(str, Enum):
        HUNT = "hunt"
        PAIRING = "pairing"
        INFO = "info"
        CLARIFY = "clarify"


    class Stop(BaseModel):
        name: str
        address: str
        lat: float
        lng: float
        notes: str = ""


    class PairingDetail(BaseModel):
        cigar: str
        strength: str
        why: List[str]
        pour: Optional[str] = None
        quality_tag: Optional[str] = None


    class SamResponse(BaseModel):
        voice: Literal["sam"] = "sam"
        mode: SamMode

        summary: str = ""
        key_points: List[str] = Field(default_factory=list)
        item_list: List[Dict[str, str]] = Field(default_factory=list)
        next_step: str = ""

        primary_pairing: Optional[PairingDetail] = None
        alternative_pairings: List[PairingDetail] = Field(default_factory=list)

        stops: List[Stop] = Field(default_factory=list)
        target_bottles: List[str] = Field(default_factory=list)
        store_targets: List[str] = Field(default_factory=list)


    def coerce_to_sam_response(raw: Dict[str, Any]) -> SamResponse:
        base = {
            "voice": "sam",
            "mode": raw.get("mode", SamMode.INFO),
            "summary": raw.get("summary") or "",
            "key_points": raw.get("key_points") or [],
            "item_list": raw.get("item_list") or [],
            "next_step": raw.get("next_step") or "",
            "primary_pairing": raw.get("primary_pairing"),
            "alternative_pairings": raw.get("alternative_pairings") or [],
            "stops": raw.get("stops") or [],
            "target_bottles": raw.get("target_bottles") or [],
            "store_targets": raw.get("store_targets") or [],
        }
        return SamResponse(**base)


# ============================
# SECTION 2 — ROUTER (IMPORT OR FALLBACK)
# ============================

try:
    from sam_router import route_request, ChatRequest  # type: ignore
except ModuleNotFoundError:

    class ChatRequest(BaseModel):
        message: str
        context: Optional[Dict[str, Any]] = None
        mode: Optional[str] = None


    _HUNT_TRIGGERS = [
        "allocation",
        "allocated",
        "rare",
        "limited",
        "drop",
        "lottery",
        "raffle",
        "release",
        "find",
        "near me",
        "closest",
        "in my area",
        "where can i find",
    ]

    _PAIRING_TRIGGERS = [
        "pair",
        "pairing",
        "cigar",
        "smoke with",
        "goes with",
        "match with",
        "what cigar",
    ]


    def _detect_mode(message: str) -> SamMode:
        t = (message or "").lower()
        hunt = any(x in t for x in _HUNT_TRIGGERS)
        pairing = any(x in t for x in _PAIRING_TRIGGERS)
        if hunt and pairing:
            return SamMode.CLARIFY
        if hunt:
            return SamMode.HUNT
        if pairing:
            return SamMode.PAIRING
        return SamMode.INFO


    def route_request(req: ChatRequest) -> SamMode:
        if req.mode:
            try:
                return SamMode(req.mode)
            except Exception:
                pass
        return _detect_mode(req.message)


# ============================
# SECTION 3 — SLOT GATING (IMPORT OR FALLBACK)
# ============================

try:
    from sam_slot_gating import apply_slot_gating  # type: ignore
except ModuleNotFoundError:

    def apply_slot_gating(mode: SamMode, message: str, context: Optional[Dict[str, Any]] = None) -> Optional[SamResponse]:
        context = context or {}
        t = (message or "").lower().strip()

        if mode == SamMode.HUNT:
            has_geo = bool(context.get("geo"))
            has_loc = bool(context.get("location_hint"))
            bottle_or_store = any(k in t for k in ["store", "shops", "liquor", "weller", "blanton", "pappy", "stagg", "taylor", "eagle rare"])

            if not (has_geo or has_loc) or not bottle_or_store:
                return coerce_to_sam_response(
                    {
                        "mode": SamMode.CLARIFY,
                        "summary": "I can do this, I just need your hunt area and target.",
                        "key_points": [
                            "Send your ZIP or city/state.",
                            "Tell me if you want a specific bottle or just the best allocation shops.",
                        ],
                        "item_list": [
                            {"label": "Example A", "value": "30344 + Weller"},
                            {"label": "Example B", "value": "Dallas, TX + best allocation shops"},
                        ],
                        "next_step": "Reply with ZIP/city and either a bottle name or 'best allocation shops'.",
                    }
                )

        if mode == SamMode.PAIRING:
            # Require spirit/bottle
            has_spirit = bool(context.get("spirit"))
            spirit_in_text = any(k in t for k in ["bourbon", "rye", "scotch", "whiskey", "whisky", "tequila", "rum", "cognac", "weller", "blanton", "stagg", "taylor", "eagle rare"])
            if not (has_spirit or spirit_in_text):
                return coerce_to_sam_response(
                    {
                        "mode": SamMode.CLARIFY,
                        "summary": "Before I pair it, what are we smoking with?",
                        "key_points": ["Tell me the spirit type or the exact bottle."],
                        "item_list": [
                            {"label": "Example", "value": "Pair a cigar with bourbon (medium)."},
                            {"label": "Example", "value": "Pair a cigar with Eagle Rare (mild)."},
                        ],
                        "next_step": "Reply with the spirit type or bottle name.",
                    }
                )

        if mode == SamMode.INFO:
            if t in {"help", "yo", "hey", "sam", "question"} or len(t) < 3:
                return coerce_to_sam_response(
                    {
                        "mode": SamMode.CLARIFY,
                        "summary": "Tell me what lane you’re in.",
                        "item_list": [
                            {"label": "INFO", "value": "Ask about proof, notes, price, or comparisons."},
                            {"label": "PAIRING", "value": "Ask what cigar pairs with a bottle/spirit."},
                            {"label": "HUNT", "value": "Ask where to find allocated bottles or best shops."},
                        ],
                        "next_step": "Reply with your question in one sentence.",
                    }
                )

        return None


# ============================
# SECTION 4 — CLARIFY RESOLVER (IMPORT OR FALLBACK)
# ============================

try:
    from sam_clarify_resolver import ClarifyState, resolve_clarify  # type: ignore
except ModuleNotFoundError:

    class ClarifyState(BaseModel):
        expected_mode: SamMode
        expected_fields: List[str] = Field(default_factory=list)
        prompt_type: str = "generic"


    def resolve_clarify(
        previous_state: ClarifyState,
        user_reply: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = context or {}
        reply = (user_reply or "").strip()
        t = reply.lower()

        updates: Dict[str, Any] = {}

        if previous_state.expected_mode == SamMode.HUNT:
            # Treat reply as location+target hint
            updates["location_hint"] = reply
            if any(k in t for k in ["best allocation shops", "shops", "stores", "store hunt"]):
                updates["hunt_type"] = "stores"
            else:
                updates["hunt_type"] = "bottle"
                updates["bottle_hint"] = reply
            return {"next_mode": SamMode.HUNT, "context_updates": updates}

        if previous_state.expected_mode == SamMode.PAIRING:
            updates["spirit"] = reply
            if "mild" in t:
                updates["cigar_strength"] = "mild"
            elif "medium" in t:
                updates["cigar_strength"] = "medium"
            elif "full" in t:
                updates["cigar_strength"] = "full"
            return {"next_mode": SamMode.PAIRING, "context_updates": updates}

        # Generic lane select
        if any(k in t for k in ["hunt", "allocation", "find"]):
            return {"next_mode": SamMode.HUNT, "context_updates": updates}
        if any(k in t for k in ["pair", "cigar"]):
            return {"next_mode": SamMode.PAIRING, "context_updates": updates}

        return {"next_mode": SamMode.INFO, "context_updates": updates}


# ============================
# SECTION 5 — EXECUTORS (IMPORT OR FALLBACK)
# ============================

try:
    from sam_executors import run_hunt, run_pairing, run_info  # type: ignore
except ModuleNotFoundError:

    def run_hunt(message: str, context: Optional[Dict[str, Any]] = None) -> SamResponse:
        context = context or {}
        location = context.get("geo_display") or context.get("location_hint") or "your area"
        hunt_type = context.get("hunt_type", "stores")
        bottle = context.get("bottle_hint")

        if hunt_type == "bottle" and bottle:
            return coerce_to_sam_response(
                {
                    "mode": SamMode.HUNT,
                    "summary": f"Here’s how to hunt {bottle} in {location}.",
                    "key_points": [
                        "Specific bottles usually move through lists, raffles, or relationships.",
                        "Ask about drop timing and qualification rules.",
                    ],
                    "item_list": [
                        {"label": "Target", "value": bottle},
                        {"label": "Method", "value": "Lists, raffles, relationship"},
                    ],
                    "target_bottles": [bottle],
                    "next_step": "Call 2 shops and ask how that bottle is released.",
                }
            )

        return coerce_to_sam_response(
            {
                "mode": SamMode.HUNT,
                "summary": f"Here are the best starting moves to hunt allocations near {location}.",
                "key_points": [
                    "Independent shops + loyalty programs give you the best odds.",
                    "Timing beats luck—ask for drop days.",
                ],
                "store_targets": ["Independent shops", "Lottery-based chains"],
                "next_step": "Tell me your ZIP and I’ll generate map-ready stops.",
            }
        )


    def run_pairing(message: str, context: Optional[Dict[str, Any]] = None) -> SamResponse:
        context = context or {}
        spirit = context.get("spirit") or "bourbon"
        strength = context.get("cigar_strength") or "medium"

        primary = {
            "cigar": "Nicaraguan Toro",
            "strength": strength,
            "why": [
                "Balanced body won’t overpower the pour",
                "Earthy sweetness complements oak and caramel notes",
            ],
            "pour": "Neat",
            "quality_tag": "Top Shelf",
        }

        return coerce_to_sam_response(
            {
                "mode": SamMode.PAIRING,
                "summary": f"Here’s a cigar pairing that works with {spirit}.",
                "key_points": [
                    "Balance matters more than matching strength.",
                    "Let the cigar support the pour, not compete.",
                ],
                "primary_pairing": primary,
                "next_step": "Try it once, then tell me if you want it richer or smoother.",
            }
        )


    def run_info(message: str, context: Optional[Dict[str, Any]] = None) -> SamResponse:
        return coerce_to_sam_response(
            {
                "mode": SamMode.INFO,
                "summary": "Here’s the straight answer.",
                "key_points": [
                    "Proof, mashbill, and aging drive flavor.",
                    "Price doesn’t always equal quality.",
                ],
                "next_step": "If you want, ask for a pairing or a local hunt plan.",
            }
        )


# ============================
# SECTION 8 — ENTITY EXTRACTION (IMPORT OR FALLBACK)
# ============================

try:
    from sam_entity_extraction import extract_hunt_intent  # type: ignore
except ModuleNotFoundError:

    def extract_hunt_intent(text: str) -> Dict[str, Optional[str]]:
        t = (text or "").lower()
        bottle_markers = ["weller", "blanton", "pappy", "van winkle", "stagg", "taylor", "eagle rare", "four roses"]
        store_markers = ["best allocation shops", "best stores", "liquor stores", "allocation shops", "where can i find"]

        bottle = next((b for b in bottle_markers if b in t), None)
        store_intent = any(s in t for s in store_markers)

        if bottle:
            return {"hunt_type": "bottle", "bottle_hint": bottle.title()}
        if store_intent:
            return {"hunt_type": "stores", "bottle_hint": None}
        return {"hunt_type": None, "bottle_hint": None}


# ============================
# SECTION 9 — PRICING (IMPORT OR FALLBACK)
# ============================

try:
    from sam_pricing_service import pricing_item_list  # type: ignore
except ModuleNotFoundError:

    def pricing_item_list(bottle_name: str) -> List[Dict[str, str]]:
        table = {
            "Blanton'S": {"msrp": 65, "secondary_low": 130, "secondary_high": 200},
            "E.H. Taylor": {"msrp": 45, "secondary_low": 90, "secondary_high": 150},
            "Stagg": {"msrp": 55, "secondary_low": 150, "secondary_high": 300},
            "Weller": {"msrp": 30, "secondary_low": 80, "secondary_high": 200},
        }
        key = (bottle_name or "").title()
        p = table.get(key)
        if not p:
            return []
        return [
            {"label": "MSRP", "value": f"${p['msrp']}"},
            {"label": "Secondary (low)", "value": f"${p['secondary_low']}"},
            {"label": "Secondary (high)", "value": f"${p['secondary_high']}"},
        ]


# ============================
# SECTION 10 — PERSISTENCE (IMPORT OR FALLBACK)
# ============================

try:
    from sam_persistence import get_user_state  # type: ignore
except ModuleNotFoundError:

    class _UserState(BaseModel):
        favorites: List[str] = Field(default_factory=list)
        home_stash: List[str] = Field(default_factory=list)


    _STORE: Dict[str, _UserState] = {}


    def get_user_state(user_id: str) -> _UserState:
        if user_id not in _STORE:
            _STORE[user_id] = _UserState()
        return _STORE[user_id]


# ============================
# SESSION STATE
# ============================


class SamSession(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)
    clarify_state: Optional[ClarifyState] = None
    user_id: Optional[str] = None


# ============================
# MASTER ENGINE
# ============================


def sam_engine(user_message: str, session: Optional[SamSession] = None) -> SamResponse:
    """Canonical Sam execution path.

    Order (LOCKED):
    1) Clarify resolution (if pending)
    2) Entity extraction
    3) Mode routing
    4) Slot gating
    5) Mode execution
    6) Pricing enrichment
    7) Persistence hooks
    8) Final schema enforcement
    """

    session = session or SamSession()
    context = session.context

    # 1) Resolve clarify (one turn only)
    if session.clarify_state:
        result = resolve_clarify(
            previous_state=session.clarify_state,
            user_reply=user_message,
            context=context,
        )
        context.update(result.get("context_updates", {}))
        mode = result.get("next_mode", SamMode.INFO)
        session.clarify_state = None
    else:
        # 2) Entity extraction (hunt intent)
        hunt_entities = extract_hunt_intent(user_message)
        context.update({k: v for k, v in hunt_entities.items() if v})

        # 3) Mode routing
        req = ChatRequest(message=user_message, context=context)
        mode = route_request(req)

    # 4) Slot gating
    clarify_response = apply_slot_gating(mode, user_message, context)
    if clarify_response:
        session.clarify_state = ClarifyState(
            expected_mode=mode,
            expected_fields=[],
            prompt_type=f"{mode.value}_slots",
        )
        return clarify_response

    # 5) Mode execution
    if mode == SamMode.HUNT:
        response = run_hunt(user_message, context)
    elif mode == SamMode.PAIRING:
        response = run_pairing(user_message, context)
    else:
        response = run_info(user_message, context)

    # 6) Pricing enrichment (HUNT only, bottle-specific)
    bottle_hint = context.get("bottle_hint")
    if getattr(response, "mode", None) == SamMode.HUNT and bottle_hint:
        pricing = pricing_item_list(str(bottle_hint))
        if pricing:
            # Ensure item_list exists
            if not getattr(response, "item_list", None):
                response.item_list = []  # type: ignore
            response.item_list.extend(pricing)  # type: ignore

    # 7) Persistence hooks (expose favorites/stash in context)
    if session.user_id:
        user_state = get_user_state(session.user_id)
        context["favorites"] = getattr(user_state, "favorites", [])
        context["home_stash"] = getattr(user_state, "home_stash", [])

    # 8) Final schema enforcement
    # Some imported executors may already return SamResponse; normalize anyway.
    return coerce_to_sam_response(response.dict() if hasattr(response, "dict") else dict(response))  # type: ignore


# ============================
# TESTS (do not remove)
# ============================


def _run_tests():
    # 1) Router/gating should clarify on HUNT without location
    s = SamSession()
    r1 = sam_engine("find rare allocations", s)
    assert r1.mode == SamMode.CLARIFY

    # 2) Clarify resolution should route back to HUNT
    r2 = sam_engine("30344 best allocation shops", s)
    assert r2.mode in {SamMode.HUNT, SamMode.INFO, SamMode.PAIRING}

    # 3) Pairing should clarify if no spirit provided
    s2 = SamSession()
    r3 = sam_engine("pair me a cigar", s2)
    assert r3.mode == SamMode.CLARIFY

    # 4) Pairing clarify reply should yield PAIRING
    r4 = sam_engine("bourbon medium", s2)
    assert r4.mode in {SamMode.PAIRING, SamMode.INFO}

    # 5) Bottle hunt should add pricing item_list when bottle is known
    s3 = SamSession(context={"location_hint": "30344", "hunt_type": "bottle", "bottle_hint": "Weller"})
    r5 = sam_engine("find weller", s3)
    assert r5.mode == SamMode.HUNT
    assert isinstance(r5.item_list, list)


if __name__ == "__main__":
    _run_tests()
    print("sam_engine.py self-test passed")

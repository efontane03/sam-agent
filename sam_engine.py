"""sam_engine.py
Standalone Sam engine (single-file) that:
- Enforces a locked response schema (SamResponse)
- Routes between INFO / PAIRING / HUNT / CLARIFY
- Supports slot-filling (clarify -> resolve) with session context
- Captures ZIP (5-digit) from messages to satisfy HUNT gating

This file is designed to be imported by main.py:
    from sam_engine import sam_engine, SamSession

No external modules required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import re


# ===============================
# Locked schema
# ===============================

class SamMode(str, Enum):
    INFO = "info"
    PAIRING = "pairing"
    HUNT = "hunt"
    CLARIFY = "clarify"


@dataclass
class Pairing:
    cigar: str
    strength: str
    pour: Optional[str] = None
    quality_tag: Optional[str] = None
    why: List[str] = field(default_factory=list)


@dataclass
class Stop:
    name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


@dataclass
class SamResponse:
    voice: str = "sam"
    mode: str = SamMode.INFO.value
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    item_list: List[Dict[str, str]] = field(default_factory=list)
    next_step: str = ""

    # Pairing fields
    primary_pairing: Optional[Dict[str, Any]] = None
    alternative_pairings: List[Dict[str, Any]] = field(default_factory=list)

    # Hunt fields
    stops: List[Dict[str, Any]] = field(default_factory=list)
    target_bottles: List[str] = field(default_factory=list)
    store_targets: List[str] = field(default_factory=list)


def _pairing_to_dict(p: Pairing) -> Dict[str, Any]:
    return {
        "cigar": p.cigar,
        "strength": p.strength,
        "pour": p.pour,
        "quality_tag": p.quality_tag,
        "why": list(p.why or []),
    }


def _stop_to_dict(s: Stop) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": s.name,
        "address": s.address,
        "notes": s.notes,
        "lat": s.lat,
        "lng": s.lng,
    }
    # Remove None keys to keep payload clean
    return {k: v for k, v in out.items() if v is not None}


def coerce_to_sam_response(obj: Any) -> Dict[str, Any]:
    """Return JSON-serializable dict matching the locked schema."""
    if isinstance(obj, SamResponse):
        return {
            "voice": obj.voice,
            "mode": obj.mode,
            "summary": obj.summary,
            "key_points": obj.key_points,
            "item_list": obj.item_list,
            "next_step": obj.next_step,
            "primary_pairing": obj.primary_pairing,
            "alternative_pairings": obj.alternative_pairings,
            "stops": obj.stops,
            "target_bottles": obj.target_bottles,
            "store_targets": obj.store_targets,
        }
    if isinstance(obj, dict):
        # best-effort normalization
        base = SamResponse()
        for k, v in obj.items():
            if hasattr(base, k):
                setattr(base, k, v)
        return coerce_to_sam_response(base)
    raise TypeError("Unsupported response type")


# ===============================
# Session
# ===============================

@dataclass
class SamSession:
    user_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    pending_clarify: Optional[Dict[str, Any]] = None


# ===============================
# Intent extraction
# ===============================

_HUNT_WORDS = (
    "allocation",
    "allocated",
    "hunt",
    "drop",
    "raffle",
    "where can i find",
    "near me",
    "best allocation shops",
    "liquor store",
    "store",
    "shop",
)

_PAIRING_WORDS = (
    "pair",
    "pairing",
    "cigar",
)

_SPIRIT_WORDS = (
    "bourbon",
    "rye",
    "scotch",
    "whiskey",
    "whisky",
    "tequila",
    "rum",
    "gin",
    "vodka",
)


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def extract_zip(text: str) -> Optional[str]:
    m = re.search(r"\b\d{5}\b", text or "")
    return m.group(0) if m else None


def is_hunt_intent(text: str) -> bool:
    t = _norm(text)
    if extract_zip(t):
        return True
    return any(w in t for w in _HUNT_WORDS)


def is_pairing_intent(text: str) -> bool:
    t = _norm(text)
    return any(w in t for w in _PAIRING_WORDS)


def extract_hunt_intent(text: str) -> Dict[str, Any]:
    t = _norm(text)
    out: Dict[str, Any] = {}

    # store vs bottle
    if "best allocation" in t or "best shops" in t or "shops" in t or "stores" in t:
        out["hunt_type"] = "stores"
    else:
        out["hunt_type"] = "bottle" if ("weller" in t or "blanton" in t or "eh taylor" in t or "eagle rare" in t) else "stores"

    # bottle hint (simple)
    for b in ["weller", "blanton", "eh taylor", "eagle rare", "stagg", "michter", "four roses", "booker"]:
        if b in t:
            out["bottle_hint"] = b.title()
            break

    # location
    z = extract_zip(t)
    if z:
        out["location_hint"] = z

    return out


def extract_pairing_intent(text: str) -> Dict[str, Any]:
    t = _norm(text)
    out: Dict[str, Any] = {}

    # spirit type
    spirit = None
    for w in _SPIRIT_WORDS:
        if w in t:
            spirit = w
            break
    if spirit:
        out["spirit_type"] = spirit

    # strength
    strength = None
    if "mild" in t:
        strength = "mild"
    elif "medium" in t:
        strength = "medium"
    elif "full" in t or "strong" in t:
        strength = "full"
    if strength:
        out["cigar_strength"] = strength

    # specific spirit/bottle hint (simple)
    for b in ["eagle rare", "weller", "blanton", "stagg", "four roses", "booker", "michter"]:
        if b in t:
            out["spirit_hint"] = b.title()
            break

    return out


# ===============================
# Clarify builder
# ===============================

def clarify_for_hunt(session: SamSession) -> SamResponse:
    return SamResponse(
        mode=SamMode.CLARIFY.value,
        summary="I can do this, I just need your hunt area and target.",
        key_points=[
            "Send your ZIP or city/state.",
            "Tell me if you want a specific bottle or just the best allocation shops.",
        ],
        item_list=[
            {"label": "Example A", "value": "30344 + Weller"},
            {"label": "Example B", "value": "Dallas, TX + best allocation shops"},
        ],
        next_step="Reply with ZIP/city and either a bottle name or 'best allocation shops'.",
    )


def clarify_for_pairing(session: SamSession) -> SamResponse:
    return SamResponse(
        mode=SamMode.CLARIFY.value,
        summary="Quick couple details so I can nail the pairing.",
        key_points=[
            "What are you pairing for: bourbon, rye, scotch, or something else?",
            "Do you want a mild, medium, or full cigar?",
        ],
        item_list=[
            {"label": "Example", "value": "bourbon + medium"},
        ],
        next_step="Reply with spirit type + cigar strength.",
    )


# ===============================
# Core engine
# ===============================

def sam_engine(user_message: str, session: Optional[SamSession] = None) -> Dict[str, Any]:
    """Main entry.

    Returns a JSON-serializable dict matching SamResponse schema.
    """
    if session is None:
        session = SamSession()

    user_message = user_message or ""
    text = user_message.strip()
    t = _norm(text)

    # ---- Context handle ----
    ctx = session.context

    # Capture ZIP/location directly from the message (critical for HUNT gating)
    z = extract_zip(text)
    if z and not ctx.get("location_hint"):
        ctx["location_hint"] = z

    # If we have a pending clarify, try to resolve it first
    if session.pending_clarify:
        pending = session.pending_clarify
        pending_type = pending.get("type")

        if pending_type == "hunt":
            # update hunt intent from reply
            ctx.update({k: v for k, v in extract_hunt_intent(text).items() if v})
            # require location
            if not ctx.get("location_hint"):
                return coerce_to_sam_response(clarify_for_hunt(session))
            # resolved
            session.pending_clarify = None
            return coerce_to_sam_response(_run_hunt(session, text))

        if pending_type == "pairing":
            ctx.update({k: v for k, v in extract_pairing_intent(text).items() if v})
            if not ctx.get("spirit_type") and not ctx.get("spirit_hint"):
                return coerce_to_sam_response(clarify_for_pairing(session))
            if not ctx.get("cigar_strength"):
                return coerce_to_sam_response(clarify_for_pairing(session))
            session.pending_clarify = None
            return coerce_to_sam_response(_run_pairing(session, text))

        # Unknown pending clarify -> clear it
        session.pending_clarify = None

    # ---- Mode routing ----
    if is_hunt_intent(text):
        ctx.update({k: v for k, v in extract_hunt_intent(text).items() if v})

        # Gate: must have location
        if not ctx.get("location_hint"):
            session.pending_clarify = {"type": "hunt"}
            return coerce_to_sam_response(clarify_for_hunt(session))

        return coerce_to_sam_response(_run_hunt(session, text))

    if is_pairing_intent(text):
        ctx.update({k: v for k, v in extract_pairing_intent(text).items() if v})

        # Gate: must have spirit + strength
        if not (ctx.get("spirit_type") or ctx.get("spirit_hint")) or not ctx.get("cigar_strength"):
            session.pending_clarify = {"type": "pairing"}
            return coerce_to_sam_response(clarify_for_pairing(session))

        return coerce_to_sam_response(_run_pairing(session, text))

    # Default INFO
    return coerce_to_sam_response(_run_info(session, text))


# ===============================
# Behaviors
# ===============================

def _run_info(session: SamSession, text: str) -> SamResponse:
    # Simple, safe info response pattern
    return SamResponse(
        mode=SamMode.INFO.value,
        summary="Tell me what you’re working with and what you want out of it, and I’ll guide you cleanly.",
        key_points=[
            "If you want a cigar pairing, say the spirit and desired cigar strength.",
            "If you want an allocation hunt, include your ZIP or city/state.",
        ],
        item_list=[],
        next_step="Try: 'pair a cigar with Eagle Rare' or '30344 best allocation shops'.",
    )


def _run_pairing(session: SamSession, text: str) -> SamResponse:
    ctx = session.context
    spirit = (ctx.get("spirit_hint") or ctx.get("spirit_type") or "bourbon").title()
    strength = (ctx.get("cigar_strength") or "medium").lower()

    # Basic pairing logic (deterministic placeholders)
    primary = Pairing(
        cigar="Padron 2000 Maduro" if strength != "mild" else "Montecristo White",
        strength=strength,
        pour=f"{spirit}",
        quality_tag="balanced",
        why=[
            "Sweetness and oak meet the wrapper’s cocoa notes.",
            "Strength stays aligned so one doesn’t bully the other.",
        ],
    )

    alt1 = Pairing(
        cigar="Oliva Serie V" if strength in {"medium", "full"} else "Romeo y Julieta 1875",
        strength=strength,
        pour=f"{spirit}",
        quality_tag="spice-forward",
        why=[
            "Pepper and cedar pop without washing the pour out.",
        ],
    )

    return SamResponse(
        mode=SamMode.PAIRING.value,
        summary=f"Here’s a clean pairing for {spirit} with a {strength} cigar.",
        primary_pairing=_pairing_to_dict(primary),
        alternative_pairings=[_pairing_to_dict(alt1)],
        key_points=[
            "If your pour is high-proof, consider a slightly fuller cigar.",
            "If you want sweeter, go Maduro wrapper.",
        ],
        item_list=[],
        next_step="Tell me the exact bottle (or proof) and I’ll fine-tune the pick.",
    )


def _run_hunt(session: SamSession, text: str) -> SamResponse:
    ctx = session.context
    location = ctx.get("location_hint")
    hunt_type = ctx.get("hunt_type") or "stores"
    bottle = ctx.get("bottle_hint")

    # NOTE: Real store lookup / geo comes later. For now we return structured HUNT response.
    # If bottle is present, add simple price guidance items.
    items: List[Dict[str, str]] = []
    targets: List[str] = []

    if bottle:
        targets.append(bottle)
        items.append({"label": "Pricing", "value": "Tell me your state and I’ll give MSRP vs. typical shelf vs. secondary ranges."})
        items.append({"label": "Tactic", "value": "Ask stores if they do raffles, loyalty allocations, or drop-day posts."})

    summary = f"In {location}, here’s how I’d run the hunt." if location else "Here’s how I’d run the hunt."

    key_points = [
        "Availability changes fast, treat this like reconnaissance.",
        "Ask the allocation question directly, don’t dance around it.",
    ]

    # Placeholder stops (empty by default) — keeps map hidden until you add lat/lng later.
    stops: List[Dict[str, Any]] = []

    next_step = "Reply with your target bottle" if hunt_type == "stores" and not bottle else "Want shops, raffles, or both?"

    return SamResponse(
        mode=SamMode.HUNT.value,
        summary=summary,
        key_points=key_points,
        item_list=items,
        next_step=next_step,
        stops=stops,
        target_bottles=targets,
        store_targets=[],
    )


# ===============================
# Self-tests (optional)
# ===============================

def _run_tests():
    # 1) Router/gating should clarify on HUNT without location
    s = SamSession()
    r1 = coerce_to_sam_response(sam_engine("find rare allocations", s))
    assert r1["mode"] == SamMode.CLARIFY.value

    # 2) HUNT with ZIP in message should NOT clarify
    s_zip = SamSession()
    r2 = coerce_to_sam_response(sam_engine("30344 best allocation shops", s_zip))
    assert r2["mode"] == SamMode.HUNT.value

    # 3) Clarify resolution path should route back to HUNT
    s2 = SamSession()
    _ = sam_engine("find allocation shops near me", s2)
    r3 = coerce_to_sam_response(sam_engine("30344 best allocation shops", s2))
    assert r3["mode"] == SamMode.HUNT.value

    # 4) Pairing should clarify if no spirit + strength
    s3 = SamSession()
    r4 = coerce_to_sam_response(sam_engine("pair me a cigar", s3))
    assert r4["mode"] == SamMode.CLARIFY.value

    # 5) Pairing clarify reply should yield PAIRING
    r5 = coerce_to_sam_response(sam_engine("bourbon medium", s3))
    assert r5["mode"] == SamMode.PAIRING.value


if __name__ == "__main__":
    _run_tests()
    print("sam_engine.py self-test passed")

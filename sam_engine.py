"""sam_engine.py

Drop-in engine for Sam Agent.

- No external module imports (no sam_schema dependency).
- Returns a JSON-serializable dict matching the locked response schema every time.
- Designed to be called from FastAPI main.py:

    from sam_engine import sam_engine, SamSession
    resp = sam_engine(payload.message, session)

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, Tuple
import re
import json
import urllib.request
import urllib.parse
import urllib.error

# ==============================
# Locked schema helpers
# ==============================

SamMode = Literal["info", "pairing", "hunt", "clarify"]


def _blank_response(mode: SamMode = "info") -> Dict[str, Any]:
    """Return a fully-populated response dict with all required keys."""
    return {
        "voice": "sam",
        "mode": mode,
        "summary": "",
        "key_points": [],
        "item_list": [],
        "next_step": "",
        "primary_pairing": None,
        "alternative_pairings": [],
        "stops": [],
        "target_bottles": [],
        "store_targets": [],
    }


def _item(label: str, value: str) -> Dict[str, str]:
    return {"label": str(label), "value": str(value)}


def _stop(
    name: str,
    address: str = "",
    notes: str = "",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": str(name),
        "address": str(address),
        "notes": str(notes),
    }
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        out["lat"] = float(lat)
        out["lng"] = float(lng)
    return out
# ==============================
# Lightweight map sourcing (OSM)
# ==============================

_OSM_UA = "SamBourbonCaddie/1.0 (contact: local-dev)"  # keep a UA for OSM services


def _http_get_json(url: str, timeout: int = 8) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _OSM_UA,
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _nominatim_geocode(q: str) -> Optional[Tuple[float, float, str]]:
    # Nominatim: https://nominatim.openstreetmap.org/search?format=json&q=...
    params = {
        "format": "json",
        "q": q,
        "limit": "1",
    }
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    try:
        data = _http_get_json(url, timeout=8)
        if not data:
            return None
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        name = str(data[0].get("display_name", q))
        return lat, lng, name
    except Exception:
        return None


def _overpass_liquor_stores(lat: float, lng: float, radius_m: int = 8000, limit: int = 8) -> List[Dict[str, Any]]:
    # Overpass API query for liquor stores around a point
    # We primarily use shop=alcohol, and include shop=beverages as a fallback.
    query = f"""
    [out:json][timeout:10];
    (
      node["shop"="alcohol"](around:{radius_m},{lat},{lng});
      way["shop"="alcohol"](around:{radius_m},{lat},{lng});
      relation["shop"="alcohol"](around:{radius_m},{lat},{lng});
      node["shop"="beverages"](around:{radius_m},{lat},{lng});
      way["shop"="beverages"](around:{radius_m},{lat},{lng});
      relation["shop"="beverages"](around:{radius_m},{lat},{lng});
    );
    out center {limit};
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        # Overpass is POST-friendly, but GET works if small. We'll do POST.
        body = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "User-Agent": _OSM_UA,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}

        name = str(tags.get("name") or "Liquor Store")
        # IMPORTANT: do NOT prefix "Stop X —" here; the UI already does that.
        addr_parts = []
        if tags.get("addr:housenumber"):
            addr_parts.append(str(tags["addr:housenumber"]))
        if tags.get("addr:street"):
            addr_parts.append(str(tags["addr:street"]))
        if tags.get("addr:city"):
            addr_parts.append(str(tags["addr:city"]))
        if tags.get("addr:state"):
            addr_parts.append(str(tags["addr:state"]))
        if tags.get("addr:postcode"):
            addr_parts.append(str(tags["addr:postcode"]))
        address = " ".join(addr_parts).strip()

        notes = "Call and ask about allocation process (raffle, list, drops)."

        # node has lat/lon, ways/relations have center
        el_lat = el.get("lat")
        el_lng = el.get("lon")
        center = el.get("center") or {}
        if el_lat is None:
            el_lat = center.get("lat")
        if el_lng is None:
            el_lng = center.get("lon")

        if isinstance(el_lat, (int, float)) and isinstance(el_lng, (int, float)):
            out.append(_stop(name=name, address=address, notes=notes, lat=float(el_lat), lng=float(el_lng)))

        if len(out) >= limit:
            break

    return out


def _build_hunt_stops(area_hint: str) -> Tuple[str, List[Dict[str, Any]]]:
    # Returns (resolved_area_label, stops)
    hint = str(area_hint or "").strip()
    if not hint:
        hint = "Atlanta, GA"

    geo = _nominatim_geocode(hint)
    if not geo:
        # fallback to Atlanta center
        lat, lng, label = 33.7490, -84.3880, hint
        return label, []

    lat, lng, label = geo
    stops = _overpass_liquor_stores(lat, lng, radius_m=8000, limit=8)
    return label, stops


def _pairing(
    cigar: str,
    strength: str,
    pour: Optional[str] = None,
    why: Optional[List[str]] = None,
    quality_tag: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "cigar": cigar,
        "strength": strength,
        "pour": pour,
        "why": why or [],
        "quality_tag": quality_tag,
    }


def _coerce_jsonable(obj: Any) -> Any:
    """Best-effort conversion to JSON-serializable primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _coerce_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce_jsonable(v) for v in obj]
    # Fallback
    return str(obj)


# ==============================
# Session / memory
# ==============================


@dataclass
class SamSession:
    user_id: str
    context: Dict[str, Any] = field(default_factory=dict)

    # Internal memory (do not expose directly)
    last_mode: SamMode = "info"

    # Hunt state
    hunt_area: Optional[str] = None  # zip/city/state
    hunt_target_bottle: Optional[str] = None
    hunt_waiting_for_area: bool = False
    hunt_waiting_for_target: bool = False

    # Pairing state
    pairing_spirit: Optional[str] = None
    pairing_strength: Optional[str] = None
    pairing_waiting_for_spirit: bool = False
    pairing_waiting_for_strength: bool = False


# ==============================
# Parsing / inference
# ==============================


_RE_ZIP = re.compile(r"\b\d{5}\b")


def _extract_zip(text: str) -> Optional[str]:
    m = _RE_ZIP.search(text or "")
    return m.group(0) if m else None


def _looks_like_location(text: str) -> bool:
    if _extract_zip(text):
        return True
    t = (text or "").lower()
    # crude city/state pattern and common phrases
    if "," in t and any(s.strip() for s in t.split(",")[:2]):
        return True
    if "near me" in t or "closest" in t or "in my area" in t:
        return True
    return False


def _infer_mode(text: str, session: SamSession) -> SamMode:
    t = (text or "").lower().strip()

    hunt_hits = [
        "allocation",
        "allocated",
        "drop",
        "raffle",
        "store",
        "shop",
        "shops",
        "near me",
        "closest",
        "where can i find",
        "hunt",
    ]
    pairing_hits = ["pair", "pairing", "cigar", "stick", "smoke", "maduro", "connecticut"]

    if any(h in t for h in hunt_hits) or _extract_zip(t):
        return "hunt"

    if any(h in t for h in pairing_hits):
        return "pairing"

    # If we're mid-flow, keep the mode sticky
    if session.hunt_waiting_for_area or session.hunt_waiting_for_target:
        return "hunt"
    if session.pairing_waiting_for_spirit or session.pairing_waiting_for_strength:
        return "pairing"

    return "info"


def _normalize_strength(text: str) -> Optional[str]:
    t = (text or "").lower()
    if any(x in t for x in ["mild", "light"]):
        return "mild"
    if "medium" in t:
        return "medium"
    if any(x in t for x in ["full", "strong"]):
        return "full"
    return None


# ==============================
# Core behaviors
# ==============================


def sam_engine(message: str, session: SamSession) -> Dict[str, Any]:
    """Main entry. Always returns a dict following the locked schema."""

    msg = (message or "").strip()
    t = msg.lower()

    # Merge optional context the UI might send
    # (FastAPI main.py already does session.context.update(payload.context))
    # but we tolerate additional nesting.
    if isinstance(session.context, dict):
        # Some UIs pass {"location_hint": "30344"}
        loc_hint = session.context.get("location_hint")
        if isinstance(loc_hint, str) and loc_hint.strip():
            session.hunt_area = session.hunt_area or loc_hint.strip()

    # Determine mode
    mode: SamMode = _infer_mode(msg, session)

    # Route
    if mode == "hunt":
        resp = _handle_hunt(msg, session)
    elif mode == "pairing":
        resp = _handle_pairing(msg, session)
    else:
        resp = _handle_info(msg, session)

    # Persist last_mode
    session.last_mode = resp.get("mode", mode)  # type: ignore

    # Ensure schema completeness + JSON-serializable
    base = _blank_response(resp.get("mode", mode))
    base.update(resp)
    return _coerce_jsonable(base)


# ------------------------------
# INFO
# ------------------------------


def _handle_info(msg: str, session: SamSession) -> Dict[str, Any]:
    r = _blank_response("info")

    r["summary"] = (
        "Tell me what you’re working with and what you want out of it, and I’ll guide you cleanly."
    )
    r["key_points"] = [
        "If you want a cigar pairing, say the spirit and desired cigar strength.",
        "If you want an allocation hunt, include your ZIP or city/state.",
    ]
    r["next_step"] = "Try: ‘pair a cigar with Eagle Rare’ or ‘30344 best allocation shops’."

    # Light personalization using stash if present
    stash = None
    if isinstance(session.context, dict):
        stash = session.context.get("home_stash")
    if isinstance(stash, dict) and stash.get("items"):
        r["item_list"].append(_item("Home Stash detected", "I can prioritize what you already own."))

    return r


# ------------------------------
# PAIRING
# ------------------------------


def _handle_pairing(msg: str, session: SamSession) -> Dict[str, Any]:
    r = _blank_response("pairing")

    # If we're waiting for missing pieces, treat the user's next message as the answer.
    strength = _normalize_strength(msg)

    if session.pairing_waiting_for_spirit:
        session.pairing_spirit = msg
        session.pairing_waiting_for_spirit = False
        # Ask for strength next
        session.pairing_waiting_for_strength = True
        return _pairing_clarify_strength(session)

    if session.pairing_waiting_for_strength:
        session.pairing_strength = strength or msg
        session.pairing_waiting_for_strength = False
        return _pairing_result(session)

    # Fresh pairing request
    # Try to pull spirit and strength
    inferred_strength = strength

    # crude spirit extraction: remove common pairing words
    spirit_guess = re.sub(r"\b(pair|pairing|with|a|an|me|cigar|stick|smoke|for)\b", " ", msg, flags=re.I)
    spirit_guess = re.sub(r"\s+", " ", spirit_guess).strip()

    if not spirit_guess:
        session.pairing_waiting_for_spirit = True
        return _pairing_clarify_spirit(session)

    session.pairing_spirit = spirit_guess

    if not inferred_strength:
        session.pairing_waiting_for_strength = True
        return _pairing_clarify_strength(session)

    session.pairing_strength = inferred_strength
    return _pairing_result(session)


def _pairing_clarify_spirit(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("clarify")
    r["summary"] = "I can do that, I just need the spirit you’re pairing with."
    r["key_points"] = ["Tell me the bourbon/whiskey/rum you’re using."]
    r["item_list"] = [
        _item("Example", "Eagle Rare"),
        _item("Example", "Wild Turkey 101"),
    ]
    r["next_step"] = "Reply with the spirit name."
    return r


def _pairing_clarify_strength(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("clarify")
    spirit = session.pairing_spirit or "that pour"
    r["summary"] = f"Got it. For {spirit}, what cigar strength do you want?"
    r["key_points"] = ["Pick one: mild, medium, or full."]
    r["item_list"] = [
        _item("Mild", "Creamy, smooth, low pepper"),
        _item("Medium", "Balanced spice + sweetness"),
        _item("Full", "Bold pepper, espresso, dark cocoa"),
    ]
    r["next_step"] = "Reply: mild / medium / full."
    return r


def _pairing_result(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("pairing")
    spirit = session.pairing_spirit or "your pour"
    strength = (session.pairing_strength or "medium").lower()

    r["summary"] = f"Here’s a clean pairing for {spirit} (target: {strength})."

    # Very simple deterministic rules
    if strength == "mild":
        primary = _pairing(
            cigar="Connecticut shade robusto",
            strength="mild",
            pour=spirit,
            quality_tag="easy-sipper",
            why=["Keeps the whiskey in front", "Cream + toasted nut notes match well"],
        )
        alt1 = _pairing(
            cigar="Mild Ecuador Connecticut toro",
            strength="mild",
            pour=spirit,
            quality_tag="smooth",
            why=["More body without pepper overload"],
        )
        alt2 = _pairing(
            cigar="Mild Cameroon wrapper",
            strength="mild",
            pour=spirit,
            quality_tag="sweet-spice",
            why=["Adds a little cinnamon sweetness"],
        )
    elif strength == "full":
        primary = _pairing(
            cigar="Nicaraguan ligero-forward toro",
            strength="full",
            pour=spirit,
            quality_tag="bold",
            why=["Pepper + oak can stand up to proof", "Dark cocoa / espresso bridge"],
        )
        alt1 = _pairing(
            cigar="Maduro robusto",
            strength="full",
            pour=spirit,
            quality_tag="dessert",
            why=["Chocolate + caramel synergy"],
        )
        alt2 = _pairing(
            cigar="Broadleaf maduro",
            strength="full",
            pour=spirit,
            quality_tag="rich",
            why=["Thick smoke, heavy sweetness"],
        )
    else:
        primary = _pairing(
            cigar="Habano wrapper robusto",
            strength="medium",
            pour=spirit,
            quality_tag="balanced",
            why=["Spice meets sweetness", "Won’t wash out the pour"],
        )
        alt1 = _pairing(
            cigar="Medium-bodied Nicaraguan corona",
            strength="medium",
            pour=spirit,
            quality_tag="clean",
            why=["Sharper cedar profile"],
        )
        alt2 = _pairing(
            cigar="Medium maduro toro",
            strength="medium",
            pour=spirit,
            quality_tag="round",
            why=["Adds dark sweetness without being heavy"],
        )

    r["primary_pairing"] = primary
    r["alternative_pairings"] = [alt1, alt2]
    r["key_points"] = [
        "Take a small sip first, then a few puffs, then sip again.",
        "If the cigar dominates, step down in strength.",
    ]

    # Optional: price guidance placeholder
    r["item_list"] = [
        _item("Budget tip", "If you want a cheaper version of the same profile, tell me your price ceiling."),
    ]

    r["next_step"] = "Tell me the exact cigar you have (or your budget) and I’ll tighten this to a specific stick."
    return r


# ------------------------------
# HUNT
# ------------------------------


def _handle_hunt(msg: str, session: SamSession) -> Dict[str, Any]:
    # 1) If waiting for area, treat this as the area
    if session.hunt_waiting_for_area:
        session.hunt_area = _extract_zip(msg) or msg
        session.hunt_waiting_for_area = False
        # After area, ask for target
        session.hunt_waiting_for_target = True
        return _hunt_clarify_target(session)

    # 2) If waiting for target bottle, treat this message as the target bottle
    #    This is the key fix you called out.
    if session.hunt_waiting_for_target:
        session.hunt_target_bottle = msg
        session.hunt_waiting_for_target = False
        return _hunt_plan(session)

    # Fresh hunt request
    area = _extract_zip(msg) or session.hunt_area

    if not area and not _looks_like_location(msg):
        session.hunt_waiting_for_area = True
        return _hunt_clarify_area(session)

    # Store area
    session.hunt_area = area or msg

    # If the user provided “best allocation shops” without a bottle, we ask for a target
    # but still give a quick plan.
    if "best" in msg.lower() and "allocation" in msg.lower() and not session.hunt_target_bottle:
        session.hunt_waiting_for_target = True
        return _hunt_quick_plan_then_ask_target(session)

    # If message looks like a bottle-only follow-up, ask area
    if not area and session.hunt_area is None:
        session.hunt_waiting_for_area = True
        return _hunt_clarify_area(session)

    # If we have area but no bottle, ask for bottle
    if not session.hunt_target_bottle:
        session.hunt_waiting_for_target = True
        return _hunt_clarify_target(session)

    # Otherwise, run hunt plan
    return _hunt_plan(session)


def _hunt_clarify_area(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")

    r["summary"] = "I can do this, I just need your hunt area and target."
    r["key_points"] = [
        "Send your ZIP or city/state.",
        "Tell me if you want a specific bottle or just the best allocation shops.",
    ]
    r["item_list"] = [
        _item("Example A", "30344 + Weller"),
        _item("Example B", "Dallas, TX + best allocation shops"),
    ]
    r["next_step"] = "Reply with ZIP/city and either a bottle name or ‘best allocation shops’."
    return r


def _hunt_clarify_target(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")

    area = session.hunt_area or "your area"
    r["summary"] = f"In {area}, what’s the target bottle (or do you want ‘best allocation shops’)?"
    r["key_points"] = [
        "Give me 1–3 targets, or say ‘best allocation shops’.",
        "I’ll tailor the hunt plan around how these bottles typically drop.",
    ]
    r["item_list"] = [
        _item("Target example", "Weller Special Reserve"),
        _item("Target example", "Blanton’s"),
        _item("Option", "best allocation shops"),
    ]
    r["next_step"] = "Reply with your target bottle."
    return r


def _hunt_quick_plan_then_ask_target(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    area = session.hunt_area or "your area"
    r["summary"] = f"In {area}, here’s how I’d run the hunt."
    r["key_points"] = [
        "Availability changes fast, treat this like reconnaissance.",
        "Ask the allocation question directly, don’t dance around it.",
    ]
    r["next_step"] = "Reply with your target bottle."
    return r


def _hunt_plan(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    area = session.hunt_area or "your area"
    target = session.hunt_target_bottle or "your target"

    # Very lightweight “plan” response (real store lookup can come later)
    r["summary"] = f"Alright. Hunt plan for {target} in {area}."

    r["key_points"] = [
        "Call 3–5 top shops and ask their allocation process (raffle, list, drops).",
        "Show up on delivery days, be consistent, don’t ask for favors on visit #1.",
        "If it’s a lottery bottle, ask how to qualify and what counts (spend, visits, points).",
    ]

    r["item_list"] = [
        _item("Ask this", "Do you do allocated bottles via raffle, list, or first-come drops?"),
        _item("Ask this", "What day/time do deliveries usually land?"),
        _item("Ask this", "What’s the fairest way to qualify here?"),
    ]

    # TEMP STUB STOPS (to prove end-to-end wiring for the map/list)
    # Frontend requires stops[*].lat and stops[*].lng to be numbers.
       # Real store lookup (OSM). Prefer location_hint → hunt_area → area label.
    area_hint = (session.context or {}).get("location_hint") or session.hunt_area or area
    resolved_area, stops = _build_hunt_stops(area_hint)

    # Update area label if we got a clearer geocode label back
    if resolved_area:
        area = resolved_area

    # If Overpass returns results, use them
    if stops:
        r["stops"] = stops
    else:
        # Fallback to simple stub stops (NO "Stop X —" prefix in the name)
        loc_hint = str(area_hint or "").strip()
        center_lat, center_lng = 33.7490, -84.3880
        zip_centers = {
            "30344": (33.6796, -84.4394),
            "30318": (33.7925, -84.4519),
            "30309": (33.7984, -84.3896),
            "30324": (33.8233, -84.3530),
            "30305": (33.8324, -84.3857),
        }
        if loc_hint.isdigit() and len(loc_hint) == 5 and loc_hint in zip_centers:
            center_lat, center_lng = zip_centers[loc_hint]

        r["stops"] = [
            _stop(
                name="Allocation-Friendly Shop (Fallback)",
                address=f"Near {loc_hint or area}",
                notes="Fallback pin to validate mapping. Real lookup may be rate-limited temporarily.",
                lat=center_lat + 0.010,
                lng=center_lng - 0.010,
            ),
            _stop(
                name="Bottle Drop Spot (Fallback)",
                address=f"Near {loc_hint or area}",
                notes="Ask about delivery mornings and raffles.",
                lat=center_lat + 0.006,
                lng=center_lng + 0.012,
            ),
            _stop(
                name="Rewards Program Store (Fallback)",
                address=f"Near {loc_hint or area}",
                notes="Ask how to qualify, points, spend, visit count.",
                lat=center_lat - 0.008,
                lng=center_lng + 0.008,
            ),
            _stop(
                name="High-Turnover Liquor Store (Fallback)",
                address=f"Near {loc_hint or area}",
                notes="Check early on delivery days.",
                lat=center_lat - 0.012,
                lng=center_lng - 0.006,
            ),
            _stop(
                name="Specialty Bourbon Shop (Fallback)",
                address=f"Near {loc_hint or area}",
                notes="Relationship shop, ask their allocation rules.",
                lat=center_lat + 0.002,
                lng=center_lng - 0.015,
            ),
        ]

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ======================================================
# SCHEMAS
# ======================================================

class ChatRequest(BaseModel):
    mode: str = "auto"                    # "auto" | "chat" | "pairing" | "hunt"
    advisor: str = "auto"                 # "auto" | "sarn" | ...
    user_message: str = Field(default="")
    history: Optional[List[Dict[str, Any]]] = None


class Item(BaseModel):
    label: str
    value: Optional[str] = None
    notes: Optional[str] = None


class Stop(BaseModel):
    name: str
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class SamResponse(BaseModel):
    voice: str = "sam"
    advisor: str = "auto"
    mode: str = "chat"
    summary: str = ""
    key_points: List[str] = Field(default_factory=list)
    item_list: List[Dict[str, Any]] = Field(default_factory=list)

    next_step: Optional[str] = None

    # pairing fields (kept as-is)
    primary_pairing: Optional[Dict[str, Any]] = None
    alternative_pairings: Optional[List[Dict[str, Any]]] = None

    # hunt fields
    stops: Optional[List[Dict[str, Any]]] = None
    target_bottles: Optional[List[Dict[str, Any]]] = None
    store_targets: Optional[List[Dict[str, Any]]] = None


# ======================================================
# MODE INFERENCE
# ======================================================

def infer_mode(req: ChatRequest) -> str:
    """Lightweight heuristic so the backend can infer mode even if UI sends mode='auto'."""
    m = (req.mode or "").lower().strip()
    if m in {"chat", "pairing", "hunt"}:
        return m

    txt = (req.user_message or "").lower()
    hunt_terms = ["allocation", "allocated", "near", "closest", "zip", "store", "shops", "hunt"]
    pairing_terms = ["pair", "pairing", "cigar", "wrapper", "vitola", "proof", "bourbon +", "whiskey +"]

    if any(t in txt for t in hunt_terms) or re.search(r"\b\d{5}\b", txt):
        return "hunt"
    if any(t in txt for t in pairing_terms):
        return "pairing"
    return "chat"


# ======================================================
# NORMALIZATION
# ======================================================

def normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Defensive normalization so UI rendering never breaks on type mismatches."""
    if not isinstance(raw, dict):
        return {
            "voice": "sam",
            "advisor": "auto",
            "mode": "chat",
            "summary": "I ran into a formatting issue on my side. Try that again.",
            "key_points": [],
            "item_list": [],
        }

    # Ensure required keys exist
    raw.setdefault("voice", "sam")
    raw.setdefault("advisor", "auto")
    raw.setdefault("mode", "chat")
    raw.setdefault("summary", "")
    raw.setdefault("key_points", [])
    raw.setdefault("item_list", [])

    # Coerce key_points
    kp = raw.get("key_points")
    if kp is None:
        raw["key_points"] = []
    elif isinstance(kp, list):
        raw["key_points"] = [str(x) for x in kp]
    else:
        raw["key_points"] = [str(kp)]

    # Coerce item_list
    il = raw.get("item_list")
    if il is None:
        raw["item_list"] = []
    elif isinstance(il, list):
        fixed: List[Dict[str, Any]] = []
        for x in il:
            if isinstance(x, dict):
                fixed.append(x)
            else:
                fixed.append({"label": str(x), "value": ""})
        raw["item_list"] = fixed
    else:
        raw["item_list"] = [{"label": "Info", "value": str(il)}]

    # Coerce store_targets to list[dict]
    st = raw.get("store_targets")
    if st is None:
        raw["store_targets"] = None
    elif isinstance(st, list):
        fixed_st: List[Dict[str, Any]] = []
        for s in st:
            if isinstance(s, dict):
                fixed_st.append(s)
            elif isinstance(s, str):
                fixed_st.append({"label": s, "notes": ""})
        raw["store_targets"] = fixed_st
    else:
        raw["store_targets"] = []

    # Hunt-specific coercion
    # stops -> list[dict]
    stops = raw.get("stops")
    if stops is None:
        raw["stops"] = None
    elif isinstance(stops, list):
        raw["stops"] = [s for s in stops if isinstance(s, dict)]
    else:
        raw["stops"] = []

    # target_bottles -> list[dict]
    tb = raw.get("target_bottles") or []
    if isinstance(tb, list):
        norm_tb: List[Dict[str, Any]] = []
        for b in tb:
            if isinstance(b, dict):
                norm_tb.append(b)
            elif isinstance(b, str):
                norm_tb.append({"label": b})
        raw["target_bottles"] = norm_tb
    else:
        raw["target_bottles"] = []

    return raw


# ======================================
# HUNT HELPERS
# ======================================

_ZIP_RE = re.compile(r"\b\d{5}\b")

# Tiny centroid lookup so pins can render even without real geo search.
# If a ZIP isn't in the dict, we fall back to (Atlanta, GA) center.
ZIP_CENTROIDS: Dict[str, tuple] = {
    "30344": (33.6770, -84.4390),  # Atlanta (East Point area)
    "30340": (33.8850, -84.2910),  # Doraville
    "30324": (33.8130, -84.3540),  # Buckhead / Lindbergh
    "30327": (33.8400, -84.4220),  # Buckhead / West
    "30339": (33.8790, -84.4630),  # Cumberland / Smyrna-ish
}

def extract_zip(text: str) -> Optional[str]:
    if not text:
        return None
    m = _ZIP_RE.search(text)
    return m.group(0) if m else None


def fallback_hunt_stops(zip_code: Optional[str]) -> List[Dict[str, Any]]:
    """Return a deterministic set of stops so the UI always has something to render."""
    z = (zip_code or "").strip()

    # Default base location: Atlanta center
    lat0, lng0 = ZIP_CENTROIDS.get(z, (33.74900, -84.38798))

    offsets = [
        (0.012, 0.008),
        (-0.010, 0.006),
        (0.006, -0.011),
        (-0.007, -0.009),
        (0.015, -0.004),
    ]

    # Atlanta-focused default list (matches your current UI expectations)
    templates = [
        ("Tower Beer, Wine & Spirits", "5877 Buford Hwy NE, Atlanta, GA 30340", "Large selection, regular raffles for allocated bourbon, strong bourbon wall."),
        ("Green’s Beverages", "2619 Buford Hwy NE, Atlanta, GA 30324", "Well-known for bourbon drops, join their email list for allocation announcements."),
        ("Camp Creek World of Beverage", "3780 Princeton Lakes Pkwy SW, Atlanta, GA 30331", "Local favorite with occasional special releases, build a relationship for heads-up on drops."),
        ("Ace Beverage", "3423 Main St, Atlanta, GA 30337", "Independent shop, sometimes gets unique single barrels, friendly to regulars."),
        ("Total Wine & More", "2955 Cobb Pkwy SE, Atlanta, GA 30339", "Big chain, runs lotteries and special releases, sign up for rewards."),
    ]

    stops: List[Dict[str, Any]] = []
    for i, (name, addr, notes) in enumerate(templates[:5]):
        dlat, dlng = offsets[i % len(offsets)]
        stops.append(
            {
                "name": name,
                "address": addr,
                "lat": float(lat0 + dlat),
                "lng": float(lng0 + dlng),
                "notes": notes,
            }
        )
    return stops


# ======================================
# MAIN ENGINE FUNCTION
# ======================================

DEBUG = False  # set True locally if you want console prints

def run_sam_engine(request: ChatRequest) -> SamResponse:
    """
    This function should call your model and return a SamResponse-shaped object.
    If your OpenAI call returns JSON, normalize it, then apply safeguards.
    """
    try:
        # ------------------------------------------
        # NOTE:
        # Replace this block with your actual OpenAI call.
        # raw_json must end up as a Python dict.
        # ------------------------------------------

        # Example placeholder (you likely already replaced this with a real call):
        raw_json: Dict[str, Any] = {
            "voice": "sam",
            "advisor": request.advisor or "auto",
            "mode": infer_mode(request),
            "summary": "Tell me what you’re after and I’ll help.",
            "key_points": [],
            "item_list": [],
        }

        if DEBUG:
            print("\n====== RAW MODEL JSON ======")
            print(json.dumps(raw_json, indent=2))
            print("================================\n")

        normalized = normalize_response(raw_json)

        # HUNT safeguard: always give the UI something to render
        inferred_mode = infer_mode(request)
        effective_mode = (normalized.get("mode") or inferred_mode or "chat").lower()
        normalized["mode"] = effective_mode

        if effective_mode == "hunt":
            stops = normalized.get("stops") or []
            if not isinstance(stops, list):
                stops = []
            # If we have fewer than 4 stops, use deterministic fallback stops
            if len(stops) < 4:
                z = extract_zip(getattr(request, "user_message", "") or "")
                stops = fallback_hunt_stops(z)
            # Ensure each stop has lat/lng so the map can render
            z2 = extract_zip(getattr(request, "user_message", "") or "")
            lat0, lng0 = ZIP_CENTROIDS.get(z2 or "", (33.74900, -84.38798))
            offsets = [(0.012, 0.008), (-0.010, 0.006), (0.006, -0.011), (-0.007, -0.009), (0.015, -0.004)]
            for i, s in enumerate(stops):
                if not isinstance(s, dict):
                    continue
                if not isinstance(s.get("lat"), (int, float)) or not isinstance(s.get("lng"), (int, float)):
                    dlat, dlng = offsets[i % len(offsets)]
                    s["lat"] = float(lat0 + dlat)
                    s["lng"] = float(lng0 + dlng)
            normalized["stops"] = stops

            # Also ensure these exist so the front end "store targets" blocks can render
            normalized.setdefault("store_targets", [
                {"label": "Independent bottle shops", "notes": "Best bet for picks and allocation lists."},
                {"label": "Chains with loyalty programs", "notes": "Some run predictable drops or raffles."},
            ])
            normalized.setdefault("target_bottles", [
                {"label": "Store picks", "notes": "Often easier to land and drink great."},
                {"label": "Allocation-adjacent bottles", "notes": "Similar profile, less chase."},
            ])

        return SamResponse(**normalized)

    except Exception as e:
        if DEBUG:
            print("\n====== ERROR IN run_sam_engine ======")
            print(repr(e))
            print("====================================\n")

        # Return a safe structured response so frontend never "goes blank"
        return SamResponse(
            voice="sam",
            advisor=request.advisor or "auto",
            mode=infer_mode(request),
            summary="I hit an internal engine error. Try again, and if it repeats, we’ll check logs.",
            key_points=[str(e)],
            item_list=[],
        )

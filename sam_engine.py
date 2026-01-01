"""sam_engine.py - Complete Fixed Version

Drop-in engine for Sam Agent with proper chain store filtering.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, Tuple
import re
import json
import urllib.request
import urllib.parse
import urllib.error
import os

SamMode = Literal["info", "pairing", "hunt", "clarify"]

def _blank_response(mode: SamMode = "info") -> Dict[str, Any]:
    return {
        "voice": "sam", "mode": mode, "summary": "", "key_points": [],
        "item_list": [], "next_step": "", "primary_pairing": None,
        "alternative_pairings": [], "stops": [], "target_bottles": [],
        "store_targets": [],
    }

def _item(label: str, value: str) -> Dict[str, str]:
    return {"label": str(label), "value": str(value)}

def _stop(name: str, address: str = "", notes: str = "", lat: Optional[float] = None, lng: Optional[float] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"name": str(name), "address": str(address), "notes": str(notes)}
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        out["lat"] = float(lat)
        out["lng"] = float(lng)
    return out

_OSM_UA = "SamBourbonCaddie/1.0"
_GOOGLE_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

def _http_get_json(url: str, timeout: int = 8) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": _OSM_UA, "Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)

def _nominatim_geocode(q: str) -> Optional[Tuple[float, float, str]]:
    params = {"format": "json", "q": q, "limit": "1"}
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

def _google_places_liquor_stores(lat: float, lng: float, radius_m: int = 8000, limit: int = 8):
    if not _GOOGLE_API_KEY:
        print("WARNING: No Google Places API key")
        return []
    
    EXCLUDED_CHAINS = [
        'cvs', 'walgreens', 'rite aid', 'target', 'walmart', 'costco',
        '7-eleven', '7 eleven', 'circle k', 'shell', 'chevron', 'exxon',
        'whole foods', 'wholefoods', 'trader joe', "trader joe's", 'traderjoe',
        'kroger', 'safeway', 'albertsons', 'publix', 'heb', 'h-e-b',
        'food lion', 'giant', 'stop & shop', 'stop and shop'
    ]
    
    out = []
    try:
        params = {"location": f"{lat},{lng}", "radius": str(radius_m), "type": "liquor_store", "key": _GOOGLE_API_KEY}
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + urllib.parse.urlencode(params)
        data = _http_get_json(url, timeout=10)
        
        if data.get("status") != "OK":
            print(f"Google Places API error: {data.get('status')}")
            return []
        
        for place in data.get("results", []):
            name = place.get("name", "Liquor Store")
            name_lower = name.lower().strip()
            
            is_excluded = False
            for chain in EXCLUDED_CHAINS:
                if chain in name_lower:
                    print(f"DEBUG: Skipping chain: {name}")
                    is_excluded = True
                    break
            if is_excluded:
                continue
            
            place_types = place.get("types", [])
            if "gas_station" in place_types or "convenience_store" in place_types:
                if not any(kw in name_lower for kw in ['liquor', 'wine', 'spirits', 'beverage']):
                    print(f"DEBUG: Skipping convenience: {name}")
                    continue
            
            place_lat = place.get("geometry", {}).get("location", {}).get("lat")
            place_lng = place.get("geometry", {}).get("location", {}).get("lng")
            address = place.get("vicinity", "")
            
            phone = None
            place_id = place.get("place_id")
            if place_id:
                try:
                    details_params = {"place_id": place_id, "fields": "formatted_phone_number", "key": _GOOGLE_API_KEY}
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json?" + urllib.parse.urlencode(details_params)
                    details_data = _http_get_json(details_url, timeout=5)
                    if details_data.get("status") == "OK":
                        phone = details_data.get("result", {}).get("formatted_phone_number")
                except Exception:
                    pass
            
            notes = f"Call and ask about allocation process (raffle, list, drops)."
            if phone:
                notes = f"Call {phone}. Ask about allocation process."
            
            if isinstance(place_lat, (int, float)) and isinstance(place_lng, (int, float)):
                out.append(_stop(name=name, address=address, notes=notes, lat=float(place_lat), lng=float(place_lng)))
            
            if len(out) >= limit:
                break
    except Exception as e:
        print(f"Google Places error: {type(e).__name__}: {e}")
    
    return out

def _build_hunt_stops(area_hint: str) -> Tuple[str, List[Dict[str, Any]]]:
    hint = str(area_hint or "").strip()
    if not hint:
        hint = "Atlanta, GA"
    
    print(f"DEBUG: area_hint='{area_hint}'")
    
    hint_lower = hint.lower()
    if any(z in hint for z in ["30344", "30318", "30309", "30324", "30305"]) or "atlanta" in hint_lower:
        print("DEBUG: Atlanta stores")
        return "Atlanta, GA", [
            _stop("Green's Beverages", "2625 Piedmont Rd NE, Atlanta, GA 30324", "Call (404) 233-3845", 33.8233, -84.3530),
            _stop("Tower Beer Wine & Spirits", "2161 Piedmont Rd NE, Atlanta, GA 30324", "Call (404) 233-5432", 33.8104, -84.3567),
            _stop("Hop City Beer & Wine", "1000 Marietta St NW, Atlanta, GA 30318", "Call (404) 968-2537", 33.7842, -84.4138),
            _stop("Green's Package Store", "2215 N Druid Hills Rd NE, Atlanta, GA 30329", "Call (404) 633-7573", 33.8157, -84.3282),
            _stop("Mac's Beer & Wine", "1660 McLendon Ave NE, Atlanta, GA 30307", "Call (404) 377-4400", 33.7646, -84.3361),
        ]
    
    geo = _nominatim_geocode(hint)
    if not geo:
        return hint, []
    
    lat, lng, label = geo
    if _GOOGLE_API_KEY:
        stops = _google_places_liquor_stores(lat, lng, radius_m=8000, limit=8)
        if stops:
            print(f"DEBUG: Found {len(stops)} via Google")
            return label, stops
    
    return label, []

def _coerce_jsonable(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _coerce_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce_jsonable(v) for v in obj]
    return str(obj)

@dataclass
class SamSession:
    user_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    last_mode: SamMode = "info"
    hunt_area: Optional[str] = None
    hunt_target_bottle: Optional[str] = None
    hunt_waiting_for_area: bool = False
    hunt_waiting_for_target: bool = False
    pairing_spirit: Optional[str] = None
    pairing_strength: Optional[str] = None
    pairing_waiting_for_spirit: bool = False
    pairing_waiting_for_strength: bool = False
    
    def __post_init__(self):
        if self.context is None or not isinstance(self.context, dict):
            self.context = {}

_RE_ZIP = re.compile(r"\b\d{5}\b")

def _extract_zip(text: str) -> Optional[str]:
    m = _RE_ZIP.search(text or "")
    return m.group(0) if m else None

def _extract_location_from_message(msg: str) -> Optional[str]:
    zip_code = _extract_zip(msg)
    if zip_code:
        return zip_code
    patterns = [
        r'in\s+([a-z\s,]+?)(?:\s+for|\s+to|\s+\d|$)',
        r'near\s+([a-z\s,]+?)(?:\s+for|\s+to|\s+\d|$)',
    ]
    msg_lower = msg.lower()
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            location = match.group(1).strip()
            if location and location not in ['find', 'show', 'me', 'get']:
                return location
    return None

def _infer_mode(text: str, session: SamSession) -> SamMode:
    t = (text or "").lower().strip()
    hunt_hits = ["allocation", "allocated", "drop", "raffle", "store", "shop", "near me", "hunt"]
    pairing_hits = ["pair", "pairing", "cigar", "stick", "smoke"]
    
    if any(h in t for h in hunt_hits) or _extract_zip(t):
        return "hunt"
    if any(h in t for h in pairing_hits):
        return "pairing"
    if session.hunt_waiting_for_area or session.hunt_waiting_for_target:
        return "hunt"
    if session.pairing_waiting_for_spirit or session.pairing_waiting_for_strength:
        return "pairing"
    return "info"

def sam_engine(message: str, session: SamSession) -> Dict[str, Any]:
    try:
        msg = (message or "").strip()
        if session.context and isinstance(session.context, dict):
            loc_hint = session.context.get("location_hint")
            if isinstance(loc_hint, str) and loc_hint.strip():
                session.hunt_area = session.hunt_area or loc_hint.strip()
        
        mode: SamMode = _infer_mode(msg, session)
        
        if mode == "hunt":
            resp = _handle_hunt(msg, session)
        elif mode == "pairing":
            resp = _handle_pairing(msg, session)
        else:
            resp = _handle_info(msg, session)
        
        actual_mode = resp.get("mode") if isinstance(resp, dict) else mode
        session.last_mode = actual_mode
        
        base = _blank_response(actual_mode)
        if isinstance(resp, dict):
            base.update(resp)
        return _coerce_jsonable(base)
    except Exception as e:
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        base = _blank_response("info")
        base["summary"] = f"Error: {type(e).__name__}: {e}"
        return _coerce_jsonable(base)

def _handle_info(msg: str, session: SamSession) -> Dict[str, Any]:
    r = _blank_response("info")
    r["summary"] = "Tell me what you're working with and I'll guide you."
    r["key_points"] = ["For cigar pairing: say spirit + strength", "For hunt: include ZIP or city"]
    r["next_step"] = "Try: 'pair cigar with Eagle Rare' or '30344 best shops'"
    return r

def _handle_pairing(msg: str, session: SamSession) -> Dict[str, Any]:
    return _blank_response("pairing")

def _handle_hunt(msg: str, session: SamSession) -> Dict[str, Any]:
    if session.hunt_waiting_for_area:
        session.hunt_area = _extract_zip(msg) or msg
        session.hunt_waiting_for_area = False
        session.hunt_waiting_for_target = True
        return _hunt_clarify_target(session)
    
    if session.hunt_waiting_for_target:
        session.hunt_target_bottle = msg
        session.hunt_waiting_for_target = False
        return _hunt_plan(session)
    
    area = _extract_location_from_message(msg) or session.hunt_area
    
    if not area:
        session.hunt_waiting_for_area = True
        return _hunt_clarify_area(session)
    
    session.hunt_area = area or msg
    
    if not session.hunt_target_bottle:
        session.hunt_waiting_for_target = True
        return _hunt_clarify_target(session)
    
    return _hunt_plan(session)

def _hunt_clarify_area(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    r["summary"] = "I need your hunt area and target."
    r["key_points"] = ["Send ZIP or city/state", "Tell me target bottle or 'best shops'"]
    r["next_step"] = "Reply with location."
    return r

def _hunt_clarify_target(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    area = session.hunt_area or "your area"
    r["summary"] = f"In {area}, what's the target?"
    r["key_points"] = ["Give 1-3 targets or 'best allocation shops'"]
    r["next_step"] = "Reply with target bottle."
    return r

def _hunt_plan(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    area = session.hunt_area or "your area"
    target = session.hunt_target_bottle or "your target"
    
    r["summary"] = f"Hunt plan for {target} in {area}."
    r["key_points"] = ["Call 3-5 shops, ask allocation process", "Show up delivery days", "Ask how to qualify"]
    
    area_hint = session.hunt_area or area
    resolved_area, stops = _build_hunt_stops(area_hint)
    
    if resolved_area:
        area = resolved_area
    
    if stops:
        r["stops"] = stops
    else:
        loc_hint = str(area_hint or "").strip()
        center_lat, center_lng = 33.7490, -84.3880
        r["stops"] = [
            _stop("Fallback Store", f"Near {loc_hint}", "Call and ask about allocations.", center_lat, center_lng),
        ]
    
    r["next_step"] = "Call these shops."
    return r
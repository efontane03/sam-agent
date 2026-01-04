"""sam_engine.py - Integrated Version with Curated Database + Google Places

Combines curated allocation store database with live Google Places search.
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

# Import curated databases
from allocation_stores import ALLOCATION_STORES, CITY_ALIASES, get_allocation_stores_for_city
from cigar_pairings import (
    get_pairing_for_cigar_strength, 
    get_pairing_for_bourbon,
    CLASSIC_PAIRINGS,
    PAIRING_TIPS
)
from bourbon_knowledge import get_bourbon_info, BOURBON_KNOWLEDGE

# Anthropic API for dynamic bourbon research
try:
    from anthropic import Anthropic
    ANTHROPIC_CLIENT = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    ANTHROPIC_AVAILABLE = True
except:
    ANTHROPIC_CLIENT = None
    ANTHROPIC_AVAILABLE = False
    print("WARNING: Anthropic API not available - bourbon research will be limited to database")

def _research_bourbon_with_claude(bourbon_name: str) -> Optional[Dict[str, Any]]:
    """Use Claude API to research a bourbon and return structured information."""
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_CLIENT:
        return None
    
    try:
        prompt = f"""Research the bourbon called "{bourbon_name}" and provide detailed information in this exact format:

Name: [Full official name]
Distillery: [Distillery name and location]
Proof: [Proof number]
Age: [Age statement or "No age statement"]
Price Range: [Typical retail price range]
Availability: [Widely available/Semi-allocated/Allocated/Ultra-rare]
Mashbill: [Grain percentages or description]

Tasting Notes (provide exactly 4 bullet points):
- [Note 1]
- [Note 2]
- [Note 3]
- [Note 4]

Why It's Great: [One sentence about what makes this bourbon special]

Fun Fact: [One interesting fact about this bourbon]

If this bourbon doesn't exist or you can't find reliable information, respond with: "BOURBON_NOT_FOUND"
"""
        
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text.strip()
        
        # Check if bourbon was not found
        if "BOURBON_NOT_FOUND" in content:
            return None
        
        # Parse the response into structured format
        lines = content.split('\n')
        bourbon_info = {
            "name": "",
            "distillery": "",
            "location": "",
            "proof": 0,
            "age": "",
            "price_range": "",
            "availability": "",
            "mashbill": "",
            "tasting_notes": [],
            "why_its_great": "",
            "fun_fact": ""
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Name:"):
                bourbon_info["name"] = line.replace("Name:", "").strip()
            elif line.startswith("Distillery:"):
                bourbon_info["distillery"] = line.replace("Distillery:", "").strip()
            elif line.startswith("Proof:"):
                proof_str = line.replace("Proof:", "").strip()
                try:
                    bourbon_info["proof"] = int(''.join(filter(str.isdigit, proof_str)))
                except:
                    bourbon_info["proof"] = proof_str
            elif line.startswith("Age:"):
                bourbon_info["age"] = line.replace("Age:", "").strip()
            elif line.startswith("Price Range:"):
                bourbon_info["price_range"] = line.replace("Price Range:", "").strip()
            elif line.startswith("Availability:"):
                bourbon_info["availability"] = line.replace("Availability:", "").strip()
            elif line.startswith("Mashbill:"):
                bourbon_info["mashbill"] = line.replace("Mashbill:", "").strip()
            elif "Tasting Notes" in line:
                current_section = "tasting"
            elif line.startswith("Why It's Great:"):
                bourbon_info["why_its_great"] = line.replace("Why It's Great:", "").strip()
                current_section = None
            elif line.startswith("Fun Fact:"):
                bourbon_info["fun_fact"] = line.replace("Fun Fact:", "").strip()
                current_section = None
            elif current_section == "tasting" and line.startswith("-"):
                bourbon_info["tasting_notes"].append(line.replace("-", "").strip())
        
        # Validate we got enough information
        if bourbon_info["name"] and bourbon_info["distillery"]:
            return bourbon_info
        
        return None
        
    except Exception as e:
        print(f"Error researching bourbon with Claude: {e}")
        return None

def _provide_bourbon_research_guidance(bourbon_name: str) -> Dict[str, Any]:
    """Provide guidance on researching a bourbon not in our database."""
    return {
        "name": bourbon_name.title(),
        "summary": f"I don't have {bourbon_name.title()} in my database yet, but I can guide you on what to look for!",
        "research_tips": [
            f"Search '{bourbon_name} bourbon review' for detailed tasting notes",
            f"Check '{bourbon_name} distillery' to learn who makes it",
            f"Look for '{bourbon_name} MSRP' to find retail pricing",
            f"Try '{bourbon_name} proof ABV' for strength information"
        ],
        "trusted_sources": [
            "BreakingBourbon.com - Professional reviews",
            "BourbonCulture.com - Community ratings",
            "Reddit r/bourbon - Real user experiences",
            "Distiller.com - Comprehensive database"
        ],
        "what_to_look_for": [
            "Distillery and location",
            "Proof/ABV and age statement",
            "Mashbill (corn, rye, wheat percentages)",
            "Tasting notes and finish",
            "Price range and availability"
        ]
    }

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
    """Geocode a location query. Handles US zip codes specially."""
    query = str(q).strip()
    
    # Check if it's a US zip code (5 digits)
    if re.match(r'^\d{5}$', query):
        # Add USA to zip code queries to avoid international confusion
        query = f"{query}, USA"
    
    params = {"format": "json", "q": query, "limit": "1"}
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
    """Search for liquor stores using Google Places API with chain filtering."""
    if not _GOOGLE_API_KEY:
        print("WARNING: No Google Places API key")
        return []
    
    EXCLUDED_CHAINS = [
        'cvs', 'walgreens', 'rite aid', 'target', 'walmart', 'costco',
        '7-eleven', '7 eleven', 'circle k', 'shell', 'chevron', 'exxon',
        'whole foods', 'wholefoods', 'trader joe', "trader joe's", 'traderjoe',
        'kroger', 'safeway', 'albertsons', 'publix', 'heb', 'h-e-b',
        'food lion', 'giant', 'stop & shop', 'stop and shop',
        'food store', 'grocery', 'market', 'deli', 'meat market',
        'gas station', 'convenience', 'mini mart', 'smoke shop'
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
            
            # Check excluded chains
            is_excluded = False
            for chain in EXCLUDED_CHAINS:
                if chain in name_lower:
                    print(f"DEBUG: Skipping chain: {name}")
                    is_excluded = True
                    break
            if is_excluded:
                continue
            
            # Additional name-based filtering for food stores, delis, markets
            food_keywords = ['food store', 'food market', 'deli', 'meat market', 'butcher', 'grocery']
            if any(keyword in name_lower for keyword in food_keywords):
                # Only keep if name ALSO has strong liquor indicators
                if not any(liquor_kw in name_lower for liquor_kw in ['liquor', 'wine & spirits', 'wine and spirits', 'beverage depot']):
                    print(f"DEBUG: Skipping food-focused store: {name}")
                    continue
            
            place_types = place.get("types", [])
            
            # Skip gas stations and convenience stores unless they're clearly liquor-focused
            if "gas_station" in place_types or "convenience_store" in place_types:
                if not any(kw in name_lower for kw in ['liquor', 'wine', 'spirits', 'beverage']):
                    print(f"DEBUG: Skipping convenience: {name}")
                    continue
            
            # Skip grocery stores, delis, and food-focused places
            if any(t in place_types for t in ["grocery_or_supermarket", "supermarket", "store"]):
                # Only keep if they have "liquor_store" type AND liquor-related keywords in name
                if "liquor_store" not in place_types or not any(kw in name_lower for kw in ['liquor', 'wine', 'spirits', 'beverage', 'beer']):
                    print(f"DEBUG: Skipping grocery/food store: {name}")
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

def _convert_curated_to_stops(curated_stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert curated store format to stops format."""
    stops = []
    for store in curated_stores:
        # Build detailed notes with allocation type and tips
        allocation_type = store.get("allocation_type", "unknown")
        base_notes = store.get("notes", "")
        
        notes_parts = []
        if allocation_type == "raffle":
            notes_parts.append("🎟️ RAFFLE system.")
        elif allocation_type == "lottery":
            notes_parts.append("🎰 LOTTERY system.")
        elif allocation_type == "list":
            notes_parts.append("📋 ALLOCATION LIST.")
        elif allocation_type == "points":
            notes_parts.append("⭐ POINTS system.")
        elif allocation_type == "first_come":
            notes_parts.append("🏃 FIRST-COME drops.")
        elif allocation_type == "spend_based":
            notes_parts.append("💰 SPEND-BASED allocation.")
        
        notes_parts.append(base_notes)
        
        phone = store.get("phone")
        if phone:
            notes_parts.insert(0, f"Call {phone}.")
        
        social = store.get("social_media")
        if social:
            notes_parts.append(social)
        
        notes = " ".join(notes_parts)
        
        stop = _stop(
            name=store["name"],
            address=store.get("address", ""),
            notes=notes,
            lat=store.get("lat"),
            lng=store.get("lng")
        )
        stops.append(stop)
    
    return stops

def _build_hunt_stops(area_hint: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Build hunt stops by:
    1. First checking curated database
    2. Falling back to Google Places if no curated data
    3. Merging both if available
    """
    hint = str(area_hint or "").strip()
    if not hint:
        hint = "Atlanta, GA"
    
    print(f"DEBUG: Building stops for area_hint='{area_hint}'")
    
    # Step 1: Check curated database
    curated_stores = get_allocation_stores_for_city(hint)
    curated_stops = []
    
    if curated_stores:
        print(f"DEBUG: Found {len(curated_stores)} curated stores for {hint}")
        curated_stops = _convert_curated_to_stops(curated_stores)
    
    # Step 2: Get geocode for Google Places search
    geo = _nominatim_geocode(hint)
    google_stops = []
    resolved_area = hint
    
    if geo:
        lat, lng, resolved_area = geo
        print(f"DEBUG: Geocoded '{hint}' to {lat}, {lng}")
        
        if _GOOGLE_API_KEY:
            # Search with Google Places
            google_stops = _google_places_liquor_stores(lat, lng, radius_m=8000, limit=8)
            if google_stops:
                print(f"DEBUG: Found {len(google_stops)} stores via Google Places")
    
    # Step 3: Merge results
    # Priority: curated stores first (they're verified), then Google Places
    all_stops = curated_stops + google_stops
    
    # Deduplicate by name (case-insensitive)
    seen_names = set()
    unique_stops = []
    for stop in all_stops:
        name_key = stop["name"].lower().strip()
        if name_key not in seen_names:
            seen_names.add(name_key)
            unique_stops.append(stop)
    
    # Limit to top 10
    final_stops = unique_stops[:10]
    
    if final_stops:
        print(f"DEBUG: Returning {len(final_stops)} total stops ({len(curated_stops)} curated + {len(google_stops)} Google)")
        return resolved_area, final_stops
    
    # Fallback if nothing found
    print("DEBUG: No stores found, returning fallback")
    return hint, []

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
    # Conversation memory
    last_bourbon_discussed: Optional[str] = None
    last_bourbon_info: Optional[Dict[str, Any]] = None
    conversation_history: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.context is None or not isinstance(self.context, dict):
            self.context = {}
        if self.conversation_history is None:
            self.conversation_history = []

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
    hunt_hits = ["allocation", "allocated", "drop", "raffle", "store", "shop", "near me", "hunt", "find"]
    pairing_hits = ["pair", "pairing", "cigar", "stick", "smoke"]
    info_hits = ["tell me about", "what is", "what's", "about", "info on", "explain", "describe"]
    
    # Check for bourbon info requests
    if any(h in t for h in info_hits):
        # Check if they're asking about a known bourbon
        for bourbon_name in BOURBON_KNOWLEDGE.keys():
            if bourbon_name in t:
                return "info"
    
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
    """Handle bourbon information requests - uses database or Claude API research."""
    msg_lower = msg.lower()
    
    # Check if user is asking about a specific bourbon
    info_keywords = ["tell me about", "what is", "what's", "about", "info on", "explain", "describe"]
    is_bourbon_query = any(keyword in msg_lower for keyword in info_keywords)
    
    # Check if this is a follow-up question about the last bourbon discussed
    is_followup = False
    followup_keywords = ["how many", "what are", "which", "does it", "is it", "tell me more", "more about", "continue"]
    if session.last_bourbon_discussed and any(kw in msg_lower for kw in followup_keywords):
        is_followup = True
    
    r = _blank_response("info")
    
    # Handle follow-up questions with Claude
    if is_followup and ANTHROPIC_AVAILABLE and session.last_bourbon_discussed:
        try:
            # Use Claude to answer follow-up about the bourbon
            context_info = ""
            if session.last_bourbon_info:
                context_info = f"Previous bourbon discussed: {session.last_bourbon_info.get('name', '')}"
            
            prompt = f"""{context_info}

User's follow-up question: "{msg}"

Provide a concise, informative answer to their follow-up question about this bourbon. Keep it to 2-3 sentences."""
            
            response = ANTHROPIC_CLIENT.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text.strip()
            
            r["summary"] = f"About {session.last_bourbon_discussed.title()}:"
            r["key_points"] = [answer]
            r["next_step"] = "Any other questions about this bourbon?"
            
            return r
            
        except Exception as e:
            print(f"Error in follow-up: {e}")
            # Fall through to normal handling
    
    if is_bourbon_query:
        # Extract the bourbon name from the query
        bourbon_name = msg_lower
        for keyword in info_keywords:
            bourbon_name = bourbon_name.replace(keyword, "").strip()
        bourbon_name = bourbon_name.strip()
        
        # First check hardcoded database for instant results
        bourbon_info = get_bourbon_info(bourbon_name)
        
        if not bourbon_info and ANTHROPIC_AVAILABLE:
            # Not in database - research with Claude API
            print(f"Researching '{bourbon_name}' with Claude API...")
            bourbon_info = _research_bourbon_with_claude(bourbon_name)
        
        if bourbon_info:
            # Found info (either from database or Claude research)
            # Store in session for follow-ups
            session.last_bourbon_discussed = bourbon_info.get("name", bourbon_name)
            session.last_bourbon_info = bourbon_info
            
            r["summary"] = f"{bourbon_info['name']} - {bourbon_info['distillery']}"
            
            r["item_list"] = [
                _item("Distillery", bourbon_info["distillery"]),
                _item("Proof", str(bourbon_info["proof"])),
                _item("Age", bourbon_info["age"]),
                _item("Price Range", bourbon_info["price_range"]),
                _item("Availability", bourbon_info["availability"]),
                _item("Mashbill", bourbon_info["mashbill"])
            ]
            
            r["key_points"] = bourbon_info["tasting_notes"]
            r["next_step"] = f"{bourbon_info['why_its_great']} Fun fact: {bourbon_info['fun_fact']}"
            
        else:
            # Could not find info even with Claude - provide research guidance
            research = _provide_bourbon_research_guidance(bourbon_name)
            
            r["summary"] = research["summary"]
            
            r["item_list"] = [
                _item("What to look for", ", ".join(research["what_to_look_for"][:3]))
            ]
            
            r["key_points"] = [
                "Here's how to research this bourbon:",
                f"• Search: '{bourbon_name} bourbon review'",
                f"• Check trusted sources: {research['trusted_sources'][0]}",
                "• Look for distillery, proof, age, and tasting notes"
            ]
            
            r["next_step"] = f"I couldn't find reliable information on {bourbon_name.title()}. Try BreakingBourbon.com or r/bourbon for reviews."
        
    else:
        # General info mode
        r["summary"] = "Tell me what you're working with and I'll guide you."
        r["key_points"] = [
            "For bourbon info: 'tell me about Eagle Rare'",
            "For cigar pairing: 'pair cigar with Maker's Mark'",
            "For hunt: include ZIP or city like '30344 best shops'"
        ]
        r["next_step"] = "Try asking about a bourbon, pairing, or hunting for allocations!"
    
    return r

def _handle_pairing(msg: str, session: SamSession) -> Dict[str, Any]:
    """Handle cigar and bourbon pairing requests."""
    msg_lower = msg.lower()
    
    # Normalize common variations
    msg_normalized = msg_lower.replace("4 roses", "four roses").replace("wt", "wild turkey")
    
    # Check ALL bourbons in our databases instead of hardcoded keywords
    found_bourbon = None
    
    # Check bourbon knowledge database
    for bourbon_name in BOURBON_KNOWLEDGE.keys():
        if bourbon_name in msg_normalized:
            found_bourbon = bourbon_name
            break
    
    # Check bourbon recommendations database (all tiers)
    if not found_bourbon:
        from cigar_pairings import BOURBON_RECOMMENDATIONS
        for tier_name, bourbons in BOURBON_RECOMMENDATIONS.items():
            for bourbon in bourbons:
                bourbon_lower = bourbon["name"].lower()
                # Check full name and common abbreviations
                if bourbon_lower in msg_normalized or any(word in msg_normalized for word in bourbon_lower.split()):
                    found_bourbon = bourbon["name"].lower()
                    break
            if found_bourbon:
                break
    
    found_cigar_strength = None
    if "mild" in msg_lower or "light" in msg_lower:
        found_cigar_strength = "mild"
    elif "full" in msg_lower or "strong" in msg_lower or "bold" in msg_lower:
        found_cigar_strength = "full"
    elif "medium" in msg_lower:
        found_cigar_strength = "medium"
    
    r = _blank_response("pairing")
    
    # Case 1: User mentioned a bourbon, recommend cigars (min 3)
    if found_bourbon:
        pairing_data = get_pairing_for_bourbon(found_bourbon)
        cigars = pairing_data['recommendations']
        
        r["summary"] = f"Perfect! For {found_bourbon.title()}, here are {len(cigars)} cigar recommendations across all price tiers."
        
        # Primary pairing (first recommendation)
        if cigars:
            primary = cigars[0]
            r["primary_pairing"] = {
                "cigar": primary["name"],
                "strength": primary["strength"],
                "pour": found_bourbon.title(),
                "quality_tag": f"{primary['tier']} • {primary['price']}",
                "why": [primary["notes"], f"Wrapper: {primary['wrapper']}"]
            }
        
        # Alternative pairings (remaining recommendations)
        if len(cigars) > 1:
            r["alternative_pairings"] = [
                {
                    "cigar": cigar["name"],
                    "strength": cigar["strength"],
                    "pour": found_bourbon.title(),
                    "quality_tag": f"{cigar['tier']} • {cigar['price']}",
                    "why": [cigar["notes"], f"Wrapper: {cigar['wrapper']}"]
                }
                for cigar in cigars[1:]
            ]
        
        r["key_points"] = [
            f"All cigars match {pairing_data['bourbon_strength']} bourbon strength",
            "Price range from budget to premium options",
            "Sip bourbon neat or with one large ice cube"
        ]
        
        r["next_step"] = "Pick your price tier and enjoy the pairing!"
        
    # Case 2: User mentioned cigar strength, recommend bourbons (min 3)
    elif found_cigar_strength:
        pairing_data = get_pairing_for_cigar_strength(found_cigar_strength)
        bourbons = pairing_data['recommendations']
        
        r["summary"] = f"For {found_cigar_strength} cigars, here are {len(bourbons)} bourbon recommendations across all price tiers."
        
        # Primary pairing (first recommendation)
        if bourbons:
            primary = bourbons[0]
            r["primary_pairing"] = {
                "cigar": f"{found_cigar_strength.title()}-bodied cigar",
                "strength": found_cigar_strength,
                "pour": primary["name"],
                "quality_tag": f"{primary['tier']} • {primary['price']}",
                "why": [
                    primary["notes"],
                    f"Proof: {primary['proof']} • Flavor: {primary['flavor_intensity']}"
                ]
            }
        
        # Alternative pairings (remaining recommendations)
        if len(bourbons) > 1:
            r["alternative_pairings"] = [
                {
                    "cigar": f"{found_cigar_strength.title()}-bodied cigar",
                    "strength": found_cigar_strength,
                    "pour": bourbon["name"],
                    "quality_tag": f"{bourbon['tier']} • {bourbon['price']}",
                    "why": [
                        bourbon["notes"],
                        f"Proof: {bourbon['proof']} • Flavor: {bourbon['flavor_intensity']}"
                    ]
                }
                for bourbon in bourbons[1:]
            ]
        
        r["key_points"] = [
            "Budget to premium options for every wallet",
            f"All match {found_cigar_strength} cigar strength perfectly",
            "Let bourbon rest on palate before drawing"
        ]
        
        r["next_step"] = "Choose your price tier and enjoy!"
        
    # Case 3: General pairing request
    else:
        r["summary"] = "I can help you pair bourbon with cigars! Tell me what you're working with."
        
        r["key_points"] = [
            "Tell me your bourbon or cigar strength",
            "Examples: 'pair Eagle Rare' or 'pairing for full cigar'",
            "I'll give you 3+ matches across all price tiers!"
        ]
        
        r["item_list"] = [
            _item("For mild cigars", "Buffalo Trace ($25), Eagle Rare ($40), Woodford Double Oaked ($60)"),
            _item("For medium cigars", "Wild Turkey 101 ($25), Knob Creek ($40), Old Forester 1920 ($65)"),
            _item("For full cigars", "Evan Williams SB ($30), Russell's Reserve ($45), Booker's ($80)")
        ]
        
        r["next_step"] = "Ask me about a specific bourbon or cigar strength."
    
    return r

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
    
    area_hint = session.hunt_area or area
    resolved_area, stops = _build_hunt_stops(area_hint)
    
    if resolved_area:
        area = resolved_area
    
    # Check if we have curated stores
    has_curated = any(
        "🎟️" in stop.get("notes", "") or
        "🎰" in stop.get("notes", "") or
        "📋" in stop.get("notes", "") or
        "⭐" in stop.get("notes", "") or
        "🏃" in stop.get("notes", "") or
        "💰" in stop.get("notes", "")
        for stop in stops
    )
    
    if has_curated:
        r["summary"] = f"Hunt plan for {target} in {area}. Showing verified allocation stores + additional options."
        r["key_points"] = [
            "⭐ Stores with icons (🎟️🎰📋⭐🏃💰) have VERIFIED allocation systems",
            "Call ahead to confirm current allocation process",
            "Ask about delivery days, raffle timing, or list signup"
        ]
    else:
        r["summary"] = f"Hunt plan for {target} in {area}."
        r["key_points"] = [
            "Call 3-5 shops, ask allocation process",
            "Show up delivery days (usually Thu/Fri)",
            "Ask how to qualify for allocated bottles"
        ]
    
    if stops:
        r["stops"] = stops
    else:
        # Fallback
        loc_hint = str(area_hint or "").strip()
        center_lat, center_lng = 33.7490, -84.3880
        r["stops"] = [
            _stop("Local Liquor Store", f"Near {loc_hint}", "Call and ask about allocations.", center_lat, center_lng),
        ]
    
    r["next_step"] = "Call these shops and ask about their allocation process."
    return r
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
from bourbon_knowledge_dynamic import get_bourbon_info_dynamic, add_bourbon_to_dynamic_database, BOURBON_KNOWLEDGE_DYNAMIC

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
    """Use Claude API to research a bourbon, assign tiers, and return structured information."""
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

TIER CATEGORIZATION (very important):
Price Tier: [budget ($20-40) / mid ($40-70) / premium ($70-150) / ultra_premium ($150+)]
Availability Tier: [shelf (easy to find) / semi_allocated (sometimes hard) / allocated (raffle/list) / unicorn (lottery only)]
Proof Tier: [standard (80-100) / barrel_proof (100-120) / cask_strength (120+)]
Brand Family: [buffalo_trace / jim_beam / heaven_hill / wild_turkey / four_roses / brown_forman / mgp / independent / other]

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
            "fun_fact": "",
            "price_tier": "",
            "availability_tier": "",
            "proof_tier": "",
            "brand_family": ""
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
            elif line.startswith("Why It's Great:") or line.startswith("Why Its Great:"):
                bourbon_info["why_its_great"] = line.replace("Why It's Great:", "").replace("Why Its Great:", "").strip()
                current_section = None
            elif line.startswith("Fun Fact:"):
                bourbon_info["fun_fact"] = line.replace("Fun Fact:", "").strip()
                current_section = None
            elif line.startswith("Price Tier:"):
                bourbon_info["price_tier"] = line.replace("Price Tier:", "").strip().lower()
            elif line.startswith("Availability Tier:"):
                bourbon_info["availability_tier"] = line.replace("Availability Tier:", "").strip().lower()
            elif line.startswith("Proof Tier:"):
                bourbon_info["proof_tier"] = line.replace("Proof Tier:", "").strip().lower()
            elif line.startswith("Brand Family:"):
                bourbon_info["brand_family"] = line.replace("Brand Family:", "").strip().lower()
            elif current_section == "tasting" and line.startswith("-"):
                bourbon_info["tasting_notes"].append(line.replace("-", "").strip())
        
        # Validate we got enough information
        if bourbon_info["name"] and bourbon_info["distillery"]:
            # Add to dynamic database
            add_bourbon_to_dynamic_database(bourbon_info)
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
    
    # BEER-ONLY EXCLUSIONS - Do NOT include beer-focused establishments
    BEER_EXCLUSIONS = [
        'beer garden', 'beergarden',
        'brewery', 'brewing', 'brewpub', 'brew pub',
        'taproom', 'tap room', 'tasting room',
        'beer bar', 'beer junction', 'beer only',
        'pub', 'tavern', 'alehouse', 'ale house'
    ]
    
    # VALID LIQUOR STORE TERMS (including regional variations)
    LIQUOR_STORE_INDICATORS = [
        'liquor', 'spirits', 'wine & spirits', 'wine and spirits',
        'package store', 'packie',
        'abc store', 'state store',
        'liquor outlet', 'liquor mart', 'liquor depot',
        'spirit shop', 'beverage depot'
    ]
    
    out = []
    try:
        params = {"location": f"{lat},{lng}", "radius": str(radius_m), "type": "liquor_store", "key": _GOOGLE_API_KEY}
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + urllib.parse.urlencode(params)
        data = _http_get_json(url, timeout=10)
        
        if data.get("status") != "OK":
            print(f"Google Places API error: {data.get('status')}")
            return []
        
        total_results = len(data.get("results", []))
        print(f"DEBUG: Google Places returned {total_results} total results")
        
        for place in data.get("results", []):
            name = place.get("name", "Liquor Store")
            name_lower = name.lower().strip()
            
            print(f"DEBUG: Checking place: {name}")
            
            # STEP 1: Check excluded chains
            is_excluded = False
            for chain in EXCLUDED_CHAINS:
                if chain in name_lower:
                    print(f"DEBUG: Skipping chain: {name}")
                    is_excluded = True
                    break
            if is_excluded:
                continue
            
            # STEP 2: EXCLUDE BEER-ONLY ESTABLISHMENTS
            is_beer_only = False
            for beer_term in BEER_EXCLUSIONS:
                if beer_term in name_lower:
                    print(f"DEBUG: Skipping beer establishment: {name}")
                    is_beer_only = True
                    break
            if is_beer_only:
                continue
            
            # STEP 3: Verify it's actually a liquor store (not just beer)
            has_liquor_indicator = any(indicator in name_lower for indicator in LIQUOR_STORE_INDICATORS)
            
            # If name has "beer" but no liquor indicators, skip it
            if 'beer' in name_lower and not has_liquor_indicator:
                print(f"DEBUG: Skipping beer-focused store without liquor indicators: {name}")
                continue
            
            # STEP 4: Additional name-based filtering for food stores, delis, markets
            food_keywords = ['food store', 'food market', 'deli', 'meat market', 'butcher', 'grocery']
            if any(keyword in name_lower for keyword in food_keywords):
                # Only keep if name ALSO has strong liquor indicators
                if not has_liquor_indicator:
                    print(f"DEBUG: Skipping food-focused store: {name}")
                    continue
            
            place_types = place.get("types", [])
            
            # STEP 5: Skip gas stations and convenience stores unless they're clearly liquor-focused
            if "gas_station" in place_types or "convenience_store" in place_types:
                if not has_liquor_indicator:
                    print(f"DEBUG: Skipping convenience: {name}")
                    continue
            
            # STEP 6: Skip grocery stores, delis, and food-focused places
            if any(t in place_types for t in ["grocery_or_supermarket", "supermarket", "store"]):
                # Only keep if they have "liquor_store" type AND liquor-related keywords in name
                if "liquor_store" not in place_types or not has_liquor_indicator:
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
                print(f"DEBUG: ✅ KEPT: {name}")
            
            if len(out) >= limit:
                break
    except Exception as e:
        print(f"Google Places error: {type(e).__name__}: {e}")
    
    print(f"DEBUG: Google Places final results: {len(out)} stores passed all filters")
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
    
    Search strategy:
    - CITY NAME: Wide search (25km radius) for comprehensive city-wide results
    - ZIP CODE: Focused search (8km radius) for local neighborhood stores
    """
    hint = str(area_hint or "").strip()
    if not hint:
        hint = "Atlanta, GA"
    
    print(f"DEBUG: Building stops for area_hint='{area_hint}'")
    
    # Determine if this is a ZIP code or city name
    is_zip_code = bool(_extract_zip(hint))
    
    # Set radius based on search type
    if is_zip_code:
        search_radius = 8000  # 8km (5 miles) - focused local search
        search_limit = 8
        print(f"DEBUG: ZIP code detected - using focused radius: {search_radius}m")
    else:
        search_radius = 25000  # 25km (15.5 miles) - comprehensive city-wide search
        search_limit = 15
        print(f"DEBUG: City name detected - using wide radius: {search_radius}m")
    
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
            # Search with Google Places using appropriate radius
            google_stops = _google_places_liquor_stores(lat, lng, radius_m=search_radius, limit=search_limit)
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
    
    # Limit based on search type
    max_results = 10 if is_zip_code else 15
    final_stops = unique_stops[:max_results]
    
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
    hunt_waiting_for_area: bool = False
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
    hunt_hits = ["allocation", "allocated", "drop", "raffle", "store", "shop", "near me", "hunt"]
    pairing_hits = ["pair", "pairing"]
    
    # Expanded info hits for general bourbon/whiskey/cigar knowledge
    bourbon_whiskey_keywords = [
        "whiskey", "whisky", "bourbon", "rye", "scotch", "irish", "japanese",
        "tennessee whiskey", "distillery", "distilled", "proof", "age", "barrel",
        "mashbill", "grain", "corn", "wheat", "malted", "varieties", "brands", "makes"
    ]
    
    cigar_keywords = [
        "cigar", "cigars", "stick", "smoke", "wrapper", "binder", "filler", 
        "maduro", "connecticut", "habano", "ring gauge", "vitola", 
        "torpedo", "robusto", "churchill", "cut", "light", "ash", "draw", "burn"
    ]
    
    question_patterns = [
        "tell me about", "what is", "what's", "about", "info on", "explain", "describe",
        "how is", "how do", "how does", "what makes", "what's the difference",
        "varieties", "types of", "kinds of", "difference between"
    ]
    
    # Check for bourbon/whiskey/cigar content in the query
    has_bourbon_whiskey = any(kw in t for kw in bourbon_whiskey_keywords)
    has_cigar = any(kw in t for kw in cigar_keywords)
    has_question_pattern = any(pattern in t for pattern in question_patterns)
    
    # If asking about bourbon/whiskey/cigar topics, go to info mode
    if (has_bourbon_whiskey or has_cigar) and (has_question_pattern or "?" in t):
        return "info"
    
    # Check for specific bourbon names in database
    if any(h in t for h in ["tell me about", "what is", "what's", "about", "info on"]):
        for bourbon_name in list(BOURBON_KNOWLEDGE.keys()) + list(BOURBON_KNOWLEDGE_DYNAMIC.keys()):
            if bourbon_name in t:
                return "info"
    
    # Check pairing FIRST (more specific than hunt keywords)
    if any(h in t for h in pairing_hits):
        return "pairing"
    
    # Then check hunt mode
    if any(h in t for h in hunt_hits) or _extract_zip(t):
        return "hunt"
    
    if session.hunt_waiting_for_area:
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

def _answer_general_knowledge(question: str) -> Optional[Dict[str, Any]]:
    """Use Claude API to answer general bourbon/whiskey/cigar knowledge questions."""
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_CLIENT:
        return None
    
    try:
        prompt = f"""You are Sam, a bourbon and cigar expert. Answer this question about bourbon, whiskey, or cigars:

"{question}"

Rules:
1. ONLY answer questions about bourbon, whiskey, spirits, or cigars
2. If the question is off-topic (weather, sports, politics, etc.), politely decline: "I'm your bourbon & cigar expert! Let's talk spirits and sticks. Ask me about bourbon, whiskey, or cigars!"
3. For CIGAR RECOMMENDATIONS, follow this EXACT format (example):

**Recommendation 1: Arturo Fuente Hemingway**
• Price: $9-13
• Wrapper: Cameroon
• Flavor: Cedar, nuts, subtle pepper
• Why: Perfectly balanced medium-bodied smoke

**Recommendation 2: Padron 2000 Natural**
• Price: $6-8
• Wrapper: Nicaraguan Natural
• Flavor: Earth, cocoa, leather
• Why: Exceptional value with full flavor

**Recommendation 3: Oliva Serie G**
• Price: $4-6
• Wrapper: Cameroon
• Flavor: Mild cedar, cream, toast
• Why: Budget-friendly daily smoke

CRITICAL RULES:
- Provide exactly 2-3 DIFFERENT cigars
- Each must be a UNIQUE cigar (different name)
- Start directly with **Recommendation 1:** (no intro text)
- Do NOT repeat any cigar name
- Do NOT add preamble like "here are my picks"

4. For other questions: Keep answers concise (2-4 sentences)
5. Be knowledgeable and friendly
6. If you don't know, say so honestly

Answer:"""
        
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.content[0].text.strip()
        
        print(f"\n{'='*60}")
        print("RAW CLAUDE OUTPUT:")
        print(answer)
        print(f"{'='*60}\n")
        
        # SIMPLE AND ROBUST duplicate removal
        # Split into recommendation blocks, keep only unique ones
        blocks = []
        current_block = []
        seen_cigars = set()
        
        for line in answer.split('\n'):
            if line.startswith('**Recommendation'):
                # New recommendation starting
                if current_block:
                    # Save previous block
                    blocks.append('\n'.join(current_block))
                    current_block = []
                current_block.append(line)
            elif current_block:
                # Part of current recommendation block
                current_block.append(line)
            else:
                # Not part of any recommendation, keep it
                blocks.append(line)
        
        # Don't forget last block
        if current_block:
            blocks.append('\n'.join(current_block))
        
        print(f"FOUND {len(blocks)} BLOCKS")
        for i, block in enumerate(blocks):
            print(f"\nBLOCK {i}:")
            print(block[:100] + "..." if len(block) > 100 else block)
        
        # Now filter out duplicate recommendations
        unique_blocks = []
        for block in blocks:
            if block.startswith('**Recommendation'):
                # Extract cigar name
                try:
                    first_line = block.split('\n')[0]
                    cigar_name = first_line.split(':', 1)[1].strip().rstrip('*').strip().lower()
                    print(f"\nChecking cigar: '{cigar_name}'")
                    if cigar_name not in seen_cigars:
                        print(f"  → KEEPING (unique)")
                        seen_cigars.add(cigar_name)
                        unique_blocks.append(block)
                    else:
                        print(f"  → SKIPPING (duplicate)")
                    # else: skip duplicate
                except Exception as e:
                    print(f"  → ERROR parsing: {e}, keeping anyway")
                    unique_blocks.append(block)
            else:
                unique_blocks.append(block)
        
        answer = '\n'.join(unique_blocks).strip()
        
        print(f"\n{'='*60}")
        print("CLEANED OUTPUT:")
        print(answer)
        print(f"{'='*60}\n")
        
        # Check if Claude declined (off-topic)
        if "bourbon & cigar expert" in answer or "spirits and sticks" in answer.lower():
            return {
                "summary": "Let's stay on topic!",
                "key_points": [answer],
                "next_step": "Ask me about bourbon, whiskey, cigars, or pairings!"
            }
        
        return {
            "summary": "",  # Don't duplicate in summary
            "key_points": [answer],  # Full cleaned answer here
            "next_step": "Any other bourbon, whiskey, or cigar questions?"
        }
        
    except Exception as e:
        print(f"Error in general knowledge: {e}")
        return None

def _handle_info(msg: str, session: SamSession) -> Dict[str, Any]:
    """Handle bourbon information requests - uses database or Claude API research."""
    msg_lower = msg.lower()
    
    # Check if user is asking about a specific bourbon (not a general question)
    info_keywords = ["tell me about", "what is", "what's", "about", "info on", "explain", "describe"]
    is_specific_bourbon_query = any(keyword in msg_lower for keyword in info_keywords[:4])  # Only first 4 are specific
    
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
    
    # Check if asking about a SPECIFIC bourbon (not a general question)
    if is_specific_bourbon_query:
        # Extract the bourbon name from the query
        bourbon_name = msg_lower
        for keyword in info_keywords:
            bourbon_name = bourbon_name.replace(keyword, "").strip()
        bourbon_name = bourbon_name.strip()
        
        # First check main database for instant results
        bourbon_info = get_bourbon_info(bourbon_name)
        
        # Then check dynamic database
        if not bourbon_info:
            bourbon_info = get_bourbon_info_dynamic(bourbon_name)
        
        # Finally, research with Claude API if not found
        if not bourbon_info and ANTHROPIC_AVAILABLE:
            # Not in any database - research with Claude API
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
        # General bourbon/whiskey/cigar knowledge question - use Claude API
        if ANTHROPIC_AVAILABLE:
            general_answer = _answer_general_knowledge(msg)
            if general_answer:
                r.update(general_answer)
                return r
        
        # Fallback if Claude API not available
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
    
    # Normalize common variations and apostrophes
    msg_normalized = (msg_lower
                     .replace("4 roses", "four roses")
                     .replace("wt", "wild turkey")
                     .replace("'s", "s")  # booker's → bookers
                     .replace("'", ""))    # remove remaining apostrophes
    
    # TIER 1: Check session memory first (if user just discussed a bourbon)
    found_bourbon = None
    if session.last_bourbon_discussed:
        bourbon_lower = session.last_bourbon_discussed.lower().replace("'s", "s").replace("'", "")
        bourbon_words = bourbon_lower.split()
        
        # Check if bourbon name or any significant word from it is in the message
        if bourbon_lower in msg_normalized or any(word in msg_normalized for word in bourbon_words if len(word) > 3):
            found_bourbon = session.last_bourbon_discussed.lower()
            print(f"Found bourbon from session memory: {found_bourbon}")
    
    # TIER 2: Check static databases if not found in session
    if not found_bourbon:
        # Check bourbon knowledge database with fuzzy matching
        for bourbon_name in BOURBON_KNOWLEDGE.keys():
            bourbon_normalized = bourbon_name.replace("'s", "s").replace("'", "")
            bourbon_words = bourbon_normalized.split()
            
            # Check full name or significant words
            if bourbon_normalized in msg_normalized or any(word in msg_normalized for word in bourbon_words if len(word) > 3):
                found_bourbon = bourbon_name
                print(f"Found bourbon in knowledge database: {found_bourbon}")
                break
        
        # Check dynamic database
        if not found_bourbon:
            for bourbon_name in BOURBON_KNOWLEDGE_DYNAMIC.keys():
                bourbon_normalized = bourbon_name.replace("'s", "s").replace("'", "")
                bourbon_words = bourbon_normalized.split()
                
                # Check full name or significant words
                if bourbon_normalized in msg_normalized or any(word in msg_normalized for word in bourbon_words if len(word) > 3):
                    found_bourbon = bourbon_name
                    print(f"Found bourbon in dynamic database: {found_bourbon}")
                    break
        
        # Check bourbon recommendations database (all tiers)
        if not found_bourbon:
            from cigar_pairings import BOURBON_RECOMMENDATIONS
            for tier_name, bourbons in BOURBON_RECOMMENDATIONS.items():
                for bourbon in bourbons:
                    bourbon_lower = bourbon["name"].lower().replace("'s", "s").replace("'", "")
                    bourbon_words = bourbon_lower.split()
                    
                    # Check full name or significant words
                    if bourbon_lower in msg_normalized or any(word in msg_normalized for word in bourbon_words if len(word) > 3):
                        found_bourbon = bourbon["name"].lower()
                        print(f"Found bourbon in recommendations database: {found_bourbon}")
                        break
                if found_bourbon:
                    break
    
    # TIER 3: If bourbon mentioned but not found, try to extract and research with Claude
    if not found_bourbon and ("pair" in msg_lower or "pairing" in msg_lower) and ANTHROPIC_AVAILABLE:
        # Extract bourbon name from message
        potential_bourbon = msg_normalized
        for remove_word in ["pair", "pairing", "cigar", "with", "for", "bourbon", "whiskey", "need", "want", "a", "an", "the", "good", "me"]:
            potential_bourbon = potential_bourbon.replace(remove_word, " ").strip()
        potential_bourbon = " ".join(potential_bourbon.split())  # Clean multiple spaces
        
        if potential_bourbon and len(potential_bourbon) > 2:
            print(f"Attempting to research unknown bourbon for pairing: {potential_bourbon}")
            bourbon_info = _research_bourbon_with_claude(potential_bourbon)
            if bourbon_info:
                found_bourbon = bourbon_info["name"].lower()
                print(f"✅ Researched and added: {found_bourbon}")
    
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
    
    # Case 1B: TIER 3 - User mentioned unknown bourbon, use Claude API
    elif "pair" in msg_lower and ("bourbon" in msg_lower or "whiskey" in msg_lower):
        # Extract bourbon name from message
        unknown_bourbon = msg_normalized
        for remove_word in ["pair", "pairing", "cigar", "with", "for", "bourbon", "whiskey", "need", "want", "a", "an", "the"]:
            unknown_bourbon = unknown_bourbon.replace(remove_word, "").strip()
        
        if unknown_bourbon and ANTHROPIC_AVAILABLE:
            print(f"Using Claude API to find pairing for unknown bourbon: {unknown_bourbon}")
            try:
                prompt = f"""Recommend 3-5 cigars that pair well with {unknown_bourbon} bourbon.

For each cigar, provide:
- Name
- Price range
- Strength (mild/medium/full)
- Brief tasting notes
- Why it pairs well with this bourbon

Format each as:
Cigar: [name]
Price: [range]
Strength: [strength]
Notes: [notes]
Pairing: [why it works]
---"""
                
                response = ANTHROPIC_CLIENT.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = response.content[0].text.strip()
                
                r["summary"] = f"Great choice! Here are cigar pairings for {unknown_bourbon.title()}:"
                r["key_points"] = [content]
                r["next_step"] = "These recommendations are based on the bourbon's flavor profile."
                
                return r
                
            except Exception as e:
                print(f"Claude API pairing error: {e}")
                # Fall through to generic response
        
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
    """Handle allocation store hunting - location-based only, no specific bottles."""
    
    # If waiting for location, capture it
    if session.hunt_waiting_for_area:
        session.hunt_area = _extract_zip(msg) or msg
        session.hunt_waiting_for_area = False
        return _hunt_plan(session)
    
    # Extract location from current message
    area = _extract_location_from_message(msg) or session.hunt_area
    
    # If no location found, ask for it
    if not area:
        session.hunt_waiting_for_area = True
        return _hunt_clarify_area(session)
    
    # Have location, execute hunt plan
    session.hunt_area = area
    return _hunt_plan(session)

def _hunt_clarify_area(session: SamSession) -> Dict[str, Any]:
    r = _blank_response("hunt")
    r["summary"] = "Where should I look for allocation stores?"
    r["key_points"] = [
        "Send ZIP code (e.g., 30344)",
        "Or city/state (e.g., Atlanta, GA)"
    ]
    r["next_step"] = "Reply with your location."
    return r

def _hunt_plan(session: SamSession) -> Dict[str, Any]:
    """Generate allocation store hunt plan for a location."""
    r = _blank_response("hunt")
    area = session.hunt_area or "your area"
    
    area_hint = session.hunt_area or area
    resolved_area, stops = _build_hunt_stops(area_hint)
    
    if resolved_area:
        area = resolved_area
    
    # Check if we have curated stores with allocation indicators
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
        r["summary"] = f"Hunt plan for allocation stores in {area}."
        r["key_points"] = [
            "⭐ Icons (🎟️🎰📋⭐🏃💰) show VERIFIED allocation methods",
            "Call ahead: Ask about allocation process, delivery days, raffle timing",
            "No guarantees on specific bottles - stores get different allocations"
        ]
    else:
        r["summary"] = f"Allocation stores in {area}."
        r["key_points"] = [
            "Call 3-5 shops and ask about their allocation process",
            "Ask: When do you get allocated bottles? How does your raffle/list work?",
            "Show up on delivery days (usually Thu/Fri) for best chances"
        ]
    
    if stops:
        r["stops"] = stops
    else:
        # Fallback
        loc_hint = str(area_hint or "").strip()
        center_lat, center_lng = 33.7490, -84.3880
        r["stops"] = [
            _stop("Local Liquor Store", f"Near {loc_hint}", "Call and ask about allocation process.", center_lat, center_lng),
        ]
    
    r["next_step"] = "Call these shops and ask about their allocation process."
    return r
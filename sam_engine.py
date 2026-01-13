"""sam_engine.py - Integrated Version with Curated Database + Google Places

CORRECTED VERSION with bug fixes:
1. Context preservation with typo tolerance
2. Intent classification (cigar retail vs bourbon allocation)
3. Pronoun resolution for pairing requests

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

# User learning system
try:
    from user_profiles import UserProfile, detect_preferences_from_message
    USER_PROFILES_AVAILABLE = True
except:
    USER_PROFILES_AVAILABLE = False
    print("WARNING: User profiles not available - learning features disabled")

# Anthropic API for dynamic bourbon research
try:
    from anthropic import Anthropic
    ANTHROPIC_CLIENT = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    ANTHROPIC_AVAILABLE = True
except:
    ANTHROPIC_CLIENT = None
    ANTHROPIC_AVAILABLE = False
    print("WARNING: Anthropic API not available - bourbon research will be limited to database")

# ============================================================================
# PATCH 1: Import debugging and retail search modules (NEW)
# ============================================================================

try:
    from session_debugger import debugger, log_context_decision
    DEBUGGER_AVAILABLE = True
except:
    DEBUGGER_AVAILABLE = False
    print("WARNING: session_debugger not available - debugging disabled")
    # Create dummy debugger if not available
    class DummyDebugger:
        def log_session_state(self, *args, **kwargs): pass
    debugger = DummyDebugger()
    def log_context_decision(*args, **kwargs): pass

try:
    from cigar_retail_search import CigarRetailSearch, IntentClassifier
    CIGAR_RETAIL_AVAILABLE = True
except:
    CIGAR_RETAIL_AVAILABLE = False
    print("WARNING: cigar_retail_search not available - cigar retail search disabled")


# ============================================================================
# PATCH 2: Message Preprocessing Class (NEW)
# ============================================================================

class MessagePreprocessor:
    """
    Preprocess messages to handle typos and infer context
    Fixes: Context loss when user has typos like "mor robust optins"
    """
    
    # Common typos mapping
    COMMON_TYPOS = {
        "mor": "more",
        "moar": "more",
        "optins": "options",
        "optoins": "options",
        "reccomendation": "recommendation",
        "recomendation": "recommendation",
        "fid": "find",
        "teh": "the",
        "thse": "these",
        "thoes": "those",
        "cigr": "cigar",
        "burboun": "bourbon",
        "bourban": "bourbon",
        "whisy": "whiskey",
    }
    
    @classmethod
    def correct_typos(cls, message: str) -> str:
        """Correct common typos in message"""
        corrected = message
        
        for typo, correction in cls.COMMON_TYPOS.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(typo) + r'\b'
            corrected = re.sub(pattern, correction, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    @classmethod
    def infer_subject_from_context(cls, message: str, session) -> Optional[str]:
        """
        Infer what the user is asking about based on context
        Returns: "cigar", "bourbon", or None
        """
        message_lower = message.lower()
        
        # Check for explicit mentions first
        if any(w in message_lower for w in ["cigar", "cigars", "smoke", "stick", "stogie"]):
            return "cigar"
        elif any(w in message_lower for w in ["bourbon", "whiskey", "bottle", "pour"]):
            return "bourbon"
        
        # No explicit mention - infer from session context
        if hasattr(session, 'conversation_history') and session.conversation_history:
            # Check last 2 turns
            recent_turns = session.conversation_history[-2:] if len(session.conversation_history) >= 2 else session.conversation_history
            for turn in reversed(recent_turns):
                if isinstance(turn, str):
                    content_lower = turn.lower()
                else:
                    content_lower = str(turn).lower()
                    
                if "cigar" in content_lower or "smoke" in content_lower:
                    return "cigar"
                elif "bourbon" in content_lower or "whiskey" in content_lower:
                    return "bourbon"
        
        # Check what's in session state
        if hasattr(session, 'last_cigar_discussed') and session.last_cigar_discussed:
            if not hasattr(session, 'last_bourbon_discussed') or not session.last_bourbon_discussed:
                return "cigar"
        
        if hasattr(session, 'last_bourbon_discussed') and session.last_bourbon_discussed:
            if not hasattr(session, 'last_cigar_discussed') or not session.last_cigar_discussed:
                return "bourbon"
        
        return None
    
    @classmethod
    def detect_more_options_request(cls, message: str) -> bool:
        """
        Detect if user is asking for more options/recommendations
        Handles: "more", "list five more", "can you list more", "give me another", etc.
        """
        message_lower = message.lower()
        
        # Expanded keywords to catch more variations
        more_keywords = ["more", "other", "another", "different", "additional", "else"]
        option_keywords = ["option", "recommendation", "choice", "suggestion", "alternative", "list", "five", "three", "one", "two"]
        number_words = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        
        has_more = any(kw in message_lower for kw in more_keywords)
        has_option = any(kw in message_lower for kw in option_keywords)
        has_number = any(num in message_lower for num in number_words) or any(char.isdigit() for char in message_lower)
        
        # "can you list five more" = has_option (list) + has_number (five) + has_more (more)
        # "give me another" = has_more (another)
        # "more options" = has_more + has_option
        
        return (has_more and has_option) or (has_more and has_number) or (has_number and "list" in message_lower)


# ============================================================================
# PATCH 3: Pronoun Resolver Class (NEW)
# ============================================================================

class PronounResolver:
    """
    Resolve pronouns like "it", "that", "them" to correct entities
    Fixes: "what bourbon pairs with it" after discussing cigars
    """
    
    @staticmethod
    def resolve_pairing_pronoun(message: str, session) -> Dict[str, Any]:
        """
        Resolve pronouns in pairing requests
        """
        message_lower = message.lower()
        
        # Detect pronouns
        pronouns = ["it", "that", "them", "these", "those"]
        detected_pronoun = None
        
        for pronoun in pronouns:
            if pronoun in message_lower:
                detected_pronoun = pronoun
                break
        
        if not detected_pronoun:
            return {"has_pronoun": False}
        
        # Detect pairing keywords
        pairing_keywords = ["pair", "pairs", "pairing", "goes with", "match", "matches"]
        is_pairing_request = any(kw in message_lower for kw in pairing_keywords)
        
        if not is_pairing_request:
            return {"has_pronoun": True, "is_pairing": False}
        
        # Determine pairing direction
        # If mentions "bourbon" or "whiskey", user wants bourbon recommendations (cigar→bourbon)
        if "bourbon" in message_lower or "whiskey" in message_lower:
            return {
                "has_pronoun": True,
                "is_pairing": True,
                "direction": "cigar_to_bourbon",
                "refers_to": getattr(session, 'last_cigar_discussed', None),
                "refers_to_type": "cigar"
            }
        
        # If mentions "cigar", user wants cigar recommendations (bourbon→cigar)
        elif "cigar" in message_lower or "smoke" in message_lower:
            return {
                "has_pronoun": True,
                "is_pairing": True,
                "direction": "bourbon_to_cigar",
                "refers_to": getattr(session, 'last_bourbon_discussed', None),
                "refers_to_type": "bourbon"
            }
        
        # No clear direction - use most recently discussed item
        else:
            if hasattr(session, 'conversation_history') and session.conversation_history:
                if session.conversation_history:
                    last_message = str(session.conversation_history[-1]).lower()
                    
                    if "cigar" in last_message:
                        return {
                            "has_pronoun": True,
                            "is_pairing": True,
                            "direction": "cigar_to_bourbon",
                            "refers_to": getattr(session, 'last_cigar_discussed', None),
                            "refers_to_type": "cigar"
                        }
                    elif "bourbon" in last_message:
                        return {
                            "has_pronoun": True,
                            "is_pairing": True,
                            "direction": "bourbon_to_cigar",
                            "refers_to": getattr(session, 'last_bourbon_discussed', None),
                            "refers_to_type": "bourbon"
                        }
        
        return {"has_pronoun": True, "is_pairing": False}


# ============================================================================
# REST OF YOUR ORIGINAL FILE CONTINUES HERE
# ============================================================================

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
        "summary": f"I couldn't find reliable information on {bourbon_name.title()}. Try BreakingBourbon.com or r/bourbon for reviews.",
        "research_tips": [
            f"• Search: '{bourbon_name} bourbon review'",
            f"• Check trusted sources: BreakingBourbon.com - Professional reviews",
            f"• Look for distillery, proof, age, and tasting notes"
        ],
        "what_to_look_for": [
            "Distillery and location",
            "Proof/ABV and age statement",
            "Mashbill (corn, rye, wheat percentages)",
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
    # Conversation memory - track BOTH bourbon and cigar
    last_bourbon_discussed: Optional[str] = None
    last_bourbon_info: Optional[Dict[str, Any]] = None
    last_cigar_discussed: Optional[str] = None
    last_cigar_info: Optional[Dict[str, Any]] = None
    conversation_history: List[str] = field(default_factory=list)
    # User learning
    user_profile: Optional[Any] = None  # UserProfile instance
    
    def __post_init__(self):
        if self.context is None or not isinstance(self.context, dict):
            self.context = {}
        if self.conversation_history is None:
            self.conversation_history = []
        # Initialize user profile
        if USER_PROFILES_AVAILABLE and self.user_profile is None:
            try:
                self.user_profile = UserProfile(self.user_id)
            except Exception as e:
                print(f"Could not initialize user profile: {e}")
                self.user_profile = None

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

# ============================================================================
# PATCH 4: Enhanced _infer_mode with pronoun/intent detection (MODIFIED)
# ============================================================================

def _infer_mode(text: str, session: SamSession) -> SamMode:
    """
    Enhanced mode inference with:
    1. Pronoun resolution for pairings
    2. Intent classification for retail search
    3. "More options" detection
    """
    t = (text or "").lower().strip()
    
    # STEP 1: Check for pronoun in pairing request (CRITICAL FIX)
    pronoun_resolution = PronounResolver.resolve_pairing_pronoun(t, session)
    if pronoun_resolution.get("is_pairing"):
        if DEBUGGER_AVAILABLE:
            log_context_decision(
                session.user_id,
                text,
                {
                    "action": "pronoun_resolution_in_infer",
                    "direction": pronoun_resolution.get("direction"),
                    "refers_to": pronoun_resolution.get("refers_to")
                }
            )
        return "pairing"
    
    # STEP 2: Check for "more options" request (CRITICAL FIX)
    if MessagePreprocessor.detect_more_options_request(t):
        subject = MessagePreprocessor.infer_subject_from_context(t, session)
        
        if DEBUGGER_AVAILABLE:
            log_context_decision(
                session.user_id,
                text,
                {
                    "action": "more_options_detected_in_infer",
                    "inferred_subject": subject
                }
            )
        
        # If asking for more cigar options, go to info mode (cigar recommendations)
        if subject == "cigar":
            return "info"
        # Keep existing logic for bourbon
    
    # STEP 3: Check for cigar retail search (CRITICAL FIX)
    if CIGAR_RETAIL_AVAILABLE:
        try:
            intent_result = IntentClassifier.detect_retail_search_intent(t, session)
            
            if intent_result["intent"] == "cigar_retail":
                if DEBUGGER_AVAILABLE:
                    log_context_decision(
                        session.user_id,
                        text,
                        {
                            "action": "cigar_retail_detected",
                            "confidence": intent_result["confidence"]
                        }
                    )
                # Store intent in session for later
                if not session.context:
                    session.context = {}
                session.context["detected_intent"] = "cigar_retail"
                return "hunt"
        except Exception as e:
            print(f"Intent classification error: {e}")
    
    # EXISTING LOGIC CONTINUES (all your original code below)
    hunt_hits = ["allocation", "allocated", "drop", "raffle", "store", "shop", "near me", "hunt"]
    pairing_hits = ["pair", "pairing"]
    
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
    
    has_bourbon_whiskey = any(kw in t for kw in bourbon_whiskey_keywords)
    has_cigar = any(kw in t for kw in cigar_keywords)
    has_question_pattern = any(pattern in t for pattern in question_patterns)
    
    if (has_bourbon_whiskey or has_cigar) and (has_question_pattern or "?" in t):
        return "info"
    
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


# ============================================================================
# PATCH 5: Main sam_engine function with typo correction (MODIFIED)
# ============================================================================

def sam_engine(message: str, session: SamSession) -> Dict[str, Any]:
    """Main entry point with bug fixes for context, typos, and intent"""
    try:
        msg = (message or "").strip()
        
        # STEP 1: TYPO CORRECTION (NEW)
        corrected_msg = MessagePreprocessor.correct_typos(msg)
        
        if corrected_msg != msg and DEBUGGER_AVAILABLE:
            log_context_decision(
                session.user_id,
                msg,
                {
                    "action": "typo_correction",
                    "original": msg,
                    "corrected": corrected_msg
                }
            )
        
        # Use corrected message from here on
        msg = corrected_msg
        
        # STEP 2: LOG SESSION STATE (NEW)
        if DEBUGGER_AVAILABLE:
            debugger.log_session_state(
                session.user_id,
                "message_received",
                {
                    "user_message": msg,
                    "last_bourbon": session.last_bourbon_discussed,
                    "last_cigar": session.last_cigar_discussed,
                }
            )
        
        # EXISTING LOGIC CONTINUES
        if session.context and isinstance(session.context, dict):
            loc_hint = session.context.get("location_hint")
            if isinstance(loc_hint, str) and loc_hint.strip():
                session.hunt_area = session.hunt_area or loc_hint.strip()
        
        # Auto-detect and store preferences from message
        if session.user_profile and USER_PROFILES_AVAILABLE:
            try:
                detected_prefs = detect_preferences_from_message(msg)
                for pref_type, value in detected_prefs.items():
                    session.user_profile.update_preference(pref_type, value)
            except Exception as e:
                print(f"Could not update preferences: {e}")
        
        mode: SamMode = _infer_mode(msg, session)
        
        if mode == "hunt":
            resp = _handle_hunt(msg, session)
        elif mode == "pairing":
            resp = _handle_pairing(msg, session)
        else:
            resp = _handle_info(msg, session)
        
        # Log interaction for learning
        if session.user_profile and USER_PROFILES_AVAILABLE:
            try:
                session.user_profile.log_interaction(
                    bourbon=session.last_bourbon_discussed,
                    cigar=session.last_cigar_discussed,
                    interaction_type=mode
                )
            except Exception as e:
                print(f"Could not log interaction: {e}")
        
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

def _answer_general_knowledge(question: str, session: Optional[SamSession] = None) -> Optional[Dict[str, Any]]:
    """Use Claude API to answer general bourbon/whiskey/cigar knowledge questions."""
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_CLIENT:
        return None
    
    try:
        # Build context-aware information
        context_info = ""
        if session:
            if session.last_cigar_discussed:
                context_info += f"\n\nCONTEXT: User was just discussing {session.last_cigar_discussed} cigars."
            if session.last_bourbon_discussed:
                context_info += f"\n\nCONTEXT: User was just discussing {session.last_bourbon_discussed} bourbon."
            if hasattr(session, 'conversation_history') and session.conversation_history:
                recent_messages = session.conversation_history[-3:]  # Last 3 messages
                if recent_messages:
                    context_info += f"\n\nRECENT CONVERSATION:\n"
                    for msg in recent_messages:
                        context_info += f"- {msg}\n"
        
        prompt = f"""You are Sam, a bourbon and cigar enthusiast. You're the friend people text when they need a recommendation - knowledgeable but never pretentious.

User asked: "{question}"{context_info}

YOUR PERSONALITY:
- Talk like you're texting a friend, not writing a review
- Vary your sentence structure - mix short punchy lines with longer thoughts
- Use contractions (it's, you're, I'd) naturally
- Show enthusiasm without sounding fake
- Drop in personal preferences casually ("this is what I reach for...")

CRITICAL FORMATTING RULES:
1. NEVER use the same structure twice in a row
2. Mix narrative with occasional bullets (not pure bullets)
3. For cigar recommendations, vary your approach:
   
   Style 1 (Conversational):
   "Looking for [style]? Start with [Name] - it's got this [flavor] thing going on. 
   Around [price]. [Why it works]."
   
   Style 2 (Mixed):
   "[Name] is where I'd go. [Why]. You're looking at [price], and it's worth it for [benefit].
   
   Quick specs: [wrapper], [strength], [flavor notes]"
   
   Style 3 (Casual bullets):
   "Grab a [Name]. Here's why:
   - [Reason 1 in natural language]
   - [Reason 2]
   Price sits around [price]."

4. NEVER start with "**Recommendation 1:**" - that's robotic
5. Change up your language - don't repeat phrases like "absolute perfection" or "incredibly consistent"
6. If recommending multiple cigars, use COMPLETELY different structures for each

CONTEXT AWARENESS:
- If user said "more" or "another" or "list five more", they want MORE of what you just discussed
- Use the CONTEXT and RECENT CONVERSATION above to understand what they're referring to
- Don't ask for clarification if context is clear

RULES:
1. ONLY answer questions about bourbon, whiskey, spirits, or cigars
2. If off-topic, say: "I'm your bourbon & cigar expert! Let's talk spirits and sticks."
3. Keep responses authentic and varied - never formulaic
4. For "list X more", provide X different recommendations using varied formats

Answer naturally:"""
        
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
        
        # Track cigars mentioned in the response (for context)
        if session:
            KNOWN_CIGAR_BRANDS = [
                "rocky patel", "padron", "arturo fuente", "oliva", "cohiba", "montecristo",
                "davidoff", "ashton", "my father", "liga privada", "drew estate", "macanudo",
                "romeo y julieta", "partagas", "hoyo de monterrey", "punch", "cao", "acid"
            ]
            
            question_lower = question.lower()
            answer_lower = answer.lower()
            
            # Check if user asked about a specific cigar OR if it appears in the response
            for brand in KNOWN_CIGAR_BRANDS:
                if brand in question_lower or brand in answer_lower:
                    session.last_cigar_discussed = brand.title()
                    print(f"Tracked cigar in session: {session.last_cigar_discussed}")
                    break
        
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
        print(f"Error calling Claude API: {e}")
        return None
        print(f"Error in general knowledge: {e}")
        return None

def _handle_info(msg: str, session: SamSession) -> Dict[str, Any]:
    """Handle bourbon/cigar information requests - uses database or Claude API research."""
    msg_lower = msg.lower()
    
    # Check for greeting/hello
    greeting_keywords = ["hello", "hi", "hey", "howdy", "sup", "what's up"]
    is_greeting = any(keyword in msg_lower for keyword in greeting_keywords) and len(msg.split()) <= 3
    
    if is_greeting and session.user_profile and USER_PROFILES_AVAILABLE:
        try:
            personalized_greeting = session.user_profile.get_personalized_greeting()
            if personalized_greeting:
                r = _blank_response("info")
                r["summary"] = personalized_greeting
                r["key_points"] = ["What can I help you with today?"]
                r["next_step"] = "Ask me about bourbon, whiskey, cigars, or pairings!"
                return r
        except Exception as e:
            print(f"Could not get personalized greeting: {e}")
    
    # Known cigar brands for context awareness
    KNOWN_CIGAR_BRANDS = [
        "rocky patel", "padron", "arturo fuente", "oliva", "cohiba", "montecristo",
        "davidoff", "ashton", "my father", "liga privada", "drew estate", "macanudo",
        "romeo y julieta", "partagas", "hoyo de monterrey", "punch", "cao", "acid"
    ]
    
    # Check if this is about a cigar (not a bourbon)
    is_cigar_query = False
    mentioned_cigar_brand = None
    for brand in KNOWN_CIGAR_BRANDS:
        if brand in msg_lower:
            is_cigar_query = True
            mentioned_cigar_brand = brand
            print(f"Detected cigar brand query: {brand}")
            break
    
    # If it's about a cigar, use general knowledge mode (Claude API)
    if is_cigar_query and ANTHROPIC_AVAILABLE:
        return _answer_general_knowledge(msg, session)
    
    # Check if user is asking about a specific bourbon (not a general question)
    info_keywords = ["tell me about", "what is", "what's", "about", "info on", "explain", "describe"]
    is_specific_bourbon_query = any(keyword in msg_lower for keyword in info_keywords[:4])  # Only first 4 are specific
    
    # SMART CONTEXT DETECTION: Figure out what "it" refers to
    # Is the user asking about a bourbon OR asking about bourbon pairings for a cigar?
    is_followup_bourbon = False
    is_followup_cigar_pairing = False
    
    followup_keywords = ["how many", "what are", "which", "does it", "is it", "tell me more", "more about", "continue"]
    pronoun_keywords = ["they", "it", "that", "this", "their", "its", "them", "those", "these"]
    ambiguous_keywords = ["other batches", "other expressions", "other bottles", "what else", "more info"]
    
    # Detect if asking about bourbon pairings (for a cigar)
    pairing_keywords = ["pair", "pairing", "bourbon", "whiskey", "what bourbon", "which bourbon", "what whiskey"]
    
    # Check if user is asking about bourbon pairings for the last cigar
    if session.last_cigar_discussed and any(pair_kw in msg_lower for pair_kw in pairing_keywords):
        # They're asking about bourbon pairings for the cigar
        if any(pronoun in msg_lower for pronoun in pronoun_keywords):
            is_followup_cigar_pairing = True
            print(f"Detected: User asking about bourbon pairings for cigar: {session.last_cigar_discussed}")
    
    # Otherwise check if asking about the bourbon
    elif session.last_bourbon_discussed:
        # Explicit follow-up keywords
        if any(kw in msg_lower for kw in followup_keywords):
            is_followup_bourbon = True
        # Ambiguous pronoun references (when no bourbon name is in the message)
        elif any(pronoun in msg_lower for pronoun in pronoun_keywords):
            # Check if there's no specific bourbon name mentioned
            has_bourbon_name = False
            for bourbon_name in list(BOURBON_KNOWLEDGE.keys()) + list(BOURBON_KNOWLEDGE_DYNAMIC.keys()):
                if bourbon_name.lower() in msg_lower:
                    has_bourbon_name = True
                    break
            if not has_bourbon_name:
                is_followup_bourbon = True
                print(f"Detected ambiguous pronoun reference - assuming user means: {session.last_bourbon_discussed}")
        # Ambiguous phrases like "other batches"
        elif any(phrase in msg_lower for phrase in ambiguous_keywords):
            is_followup_bourbon = True
            print(f"Detected ambiguous question - assuming user means: {session.last_bourbon_discussed}")
    
    # Handle cigar pairing follow-ups (bourbon recommendations for a cigar)
    if is_followup_cigar_pairing:
        # User wants bourbon recommendations for the cigar they just discussed
        print(f"Routing to pairing mode: bourbon recommendations for {session.last_cigar_discussed}")
        
        # Get bourbon pairings for the cigar strength
        # First, determine the cigar's strength from session
        cigar_strength = "medium"  # default
        if session.last_cigar_info:
            cigar_strength = session.last_cigar_info.get("strength", "medium").lower()
        
        # Get bourbon recommendations
        pairing_data = get_pairing_for_cigar_strength(cigar_strength)
        bourbons = pairing_data['recommendations']
        
        r = _blank_response("pairing")
        r["summary"] = f"You're asking what bourbons pair well with {session.last_cigar_discussed}, right? Here's what I'd pour:"
        
        # Primary pairing
        if bourbons:
            primary = bourbons[0]
            r["primary_pairing"] = {
                "cigar": f"{session.last_cigar_discussed}",
                "strength": cigar_strength,
                "pour": primary["name"],
                "quality_tag": f"{primary['tier']} • {primary['price']}",
                "why": [
                    primary["notes"],
                    f"Proof: {primary['proof']} • Flavor: {primary['flavor_intensity']}"
                ]
            }
        
        # Alternative pairings
        if len(bourbons) > 1:
            r["alternative_pairings"] = [
                {
                    "cigar": f"{session.last_cigar_discussed}",
                    "strength": cigar_strength,
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
            f"All bourbons match {cigar_strength}-bodied cigar profile",
            "Price range from budget to premium options",
            "Sip neat or with one large ice cube"
        ]
        
        r["next_step"] = "Pick your bottle and enjoy the pairing!"
        return r
    
    r = _blank_response("info")
    
    # Handle bourbon follow-up questions with Claude + confirmation
    if is_followup_bourbon and ANTHROPIC_AVAILABLE and session.last_bourbon_discussed:
        try:
            # Use Claude to answer follow-up about the bourbon WITH CONFIRMATION
            context_info = f"Previous bourbon discussed: {session.last_bourbon_discussed}"
            if session.last_bourbon_info:
                context_info += f"\n{session.last_bourbon_info.get('name', '')}"
            
            prompt = f"""You're Sam chatting with a friend about bourbon. They just asked an ambiguous follow-up question.

{context_info}

User's ambiguous question: "{msg}"

IMPORTANT: Since their question was ambiguous (using "they", "it", "other batches", etc.), you need to:
1. Start by CONFIRMING you're talking about {session.last_bourbon_discussed}
2. Then briefly answer their question

Format:
"You're asking about [bourbon name from context], right? [Brief 1-2 sentence answer]"

Example:
"You're asking about Four Roses batches, right? They've got several great expressions - Small Batch, Single Barrel, and their limited edition releases."

Keep it conversational and natural."""
            
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
            
            r["key_points"] = research["research_tips"]
            
            r["next_step"] = f"I couldn't find reliable information on {bourbon_name.title()}. Try BreakingBourbon.com or r/bourbon for reviews."
        
    else:
        # General bourbon/whiskey/cigar knowledge question - use Claude API
        if ANTHROPIC_AVAILABLE:
            general_answer = _answer_general_knowledge(msg, session)
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


# ============================================================================
# PATCH 8: _handle_pairing with Pronoun Resolution (MODIFIED)
# ============================================================================

def _handle_pairing(msg: str, session: SamSession) -> Dict[str, Any]:
    """Handle pairing requests with pronoun resolution"""
    
    # STEP 1: Check for pronoun resolution (NEW)
    pronoun_resolution = PronounResolver.resolve_pairing_pronoun(msg, session)
    
    if pronoun_resolution.get("is_pairing"):
        direction = pronoun_resolution.get("direction")
        refers_to = pronoun_resolution.get("refers_to")
        
        if DEBUGGER_AVAILABLE:
            log_context_decision(
                session.user_id,
                msg,
                {
                    "action": "pronoun_pairing_resolution",
                    "direction": direction,
                    "refers_to": refers_to
                }
            )
        
        # Handle cigar→bourbon pairing
        if direction == "cigar_to_bourbon" and refers_to:
            session.pairing_spirit = refers_to
            session.pairing_strength = session.last_cigar_info.get("strength") if session.last_cigar_info else None
            session.pairing_waiting_for_spirit = False
            session.pairing_waiting_for_strength = False
            
            # Get bourbon pairings for the cigar
            strength = session.pairing_strength or "medium"
            pairing_data = get_pairing_for_cigar_strength(strength)
            
            items = []
            if pairing_data and pairing_data.get("bourbons"):
                for bourbon in pairing_data["bourbons"][:3]:
                    items.append(_item("Bourbon", bourbon.get("name", "Unknown")))
                    items.append(_item("Profile", bourbon.get("profile", "N/A")))
                    items.append(_item("Why", bourbon.get("why_pairs", "Complements the cigar")))
                    items.append(_item("", ""))  # Separator
            
            summary = f"You're asking about {refers_to}, right? Here's what I'd pour:\n\n"
            summary += pairing_data.get("overview", "") if pairing_data else ""
            
            return {
                "mode": "pairing",
                "summary": summary,
                "items": items
            }
        
        # Handle bourbon→cigar pairing
        elif direction == "bourbon_to_cigar" and refers_to:
            session.pairing_spirit = refers_to
            session.pairing_waiting_for_spirit = False
            
            # Get cigar pairings for the bourbon
            pairing_data = get_pairing_for_bourbon(refers_to)
            
            items = []
            if pairing_data and pairing_data.get("cigars"):
                for cigar in pairing_data["cigars"][:3]:
                    items.append(_item("Cigar", cigar.get("name", "Unknown")))
                    items.append(_item("Strength", cigar.get("strength", "N/A")))
                    items.append(_item("Why", cigar.get("why_pairs", "Complements the bourbon")))
                    items.append(_item("", ""))  # Separator
            
            summary = f"For {refers_to}, I'd go with:\n\n"
            summary += pairing_data.get("overview", "") if pairing_data else ""
            
            return {
                "mode": "pairing",
                "summary": summary,
                "items": items
            }
    
    # EXISTING PAIRING LOGIC CONTINUES
    session.pairing_waiting_for_spirit = False
    session.pairing_waiting_for_strength = False
    
    spirit_match = None
    for key in CLASSIC_PAIRINGS.keys():
        if key.lower() in msg.lower():
            spirit_match = key
            break
    
    strength_match = None
    for strength in ["mild", "medium", "full"]:
        if strength in msg.lower():
            strength_match = strength
            break
    
    if spirit_match:
        session.pairing_spirit = spirit_match
    if strength_match:
        session.pairing_strength = strength_match
    
    if not session.pairing_spirit:
        return {
            "mode": "pairing",
            "summary": "What bourbon or whiskey would you like to pair? (e.g., Buffalo Trace, Four Roses, etc.)",
            "items": []
        }
    
    if not session.pairing_strength:
        return {
            "mode": "pairing",
            "summary": f"What cigar strength would you like to pair with {session.pairing_spirit}? (mild, medium, or full-bodied)",
            "items": []
        }
    
    # Get pairing recommendations
    pairing_data = get_pairing_for_bourbon(session.pairing_spirit)
    
    if not pairing_data:
        # Fallback to strength-based pairing
        pairing_data = get_pairing_for_cigar_strength(session.pairing_strength)
    
    items = []
    summary = ""
    
    if pairing_data:
        summary = pairing_data.get("overview", f"Pairing suggestions for {session.pairing_spirit}:")
        
        if pairing_data.get("cigars"):
            for cigar in pairing_data["cigars"][:3]:
                items.append(_item("Cigar", cigar.get("name", "Unknown")))
                items.append(_item("Strength", cigar.get("strength", "N/A")))
                items.append(_item("Wrapper", cigar.get("wrapper", "N/A")))
                items.append(_item("Why", cigar.get("why_pairs", "Great pairing")))
                items.append(_item("", ""))
    else:
        summary = f"I don't have specific pairings for {session.pairing_spirit} yet, but here are some general tips:\n\n"
        summary += PAIRING_TIPS.get("general", "Match intensity: mild with mild, full with full.")
    
    return {
        "mode": "pairing",
        "summary": summary,
        "items": items
    }


# ============================================================================
# PATCH 6 & 7: _handle_hunt with cigar retail detection (MODIFIED)
# ============================================================================

def _handle_hunt(msg: str, session: SamSession) -> Dict[str, Any]:
    """Handle hunt mode with cigar retail detection"""
    
    # STEP 1: Check if this is actually a cigar retail search (NEW)
    if session.context and session.context.get("detected_intent") == "cigar_retail":
        # Clear the intent flag
        session.context["detected_intent"] = None
        
        # Handle cigar retail search
        return _handle_cigar_retail_search(msg, session)
    
    # EXISTING HUNT LOGIC CONTINUES
    session.hunt_waiting_for_area = False
    
    area = _extract_location_from_message(msg)
    if area:
        session.hunt_area = area
    
    if not session.hunt_area:
        session.hunt_waiting_for_area = True
        return _hunt_clarify_area(session)
    
    return _hunt_plan(session)


def _hunt_clarify_area(session: SamSession) -> Dict[str, Any]:
    """Ask user for their location"""
    return {
        "mode": "hunt",
        "summary": "Where should I look for allocation stores?\n\nKey points:\n• Send ZIP code (e.g., 30344)\n• Or city/state (e.g., Atlanta, GA)\n\nNext: Reply with your location.",
        "items": []
    }


def _hunt_plan(session: SamSession) -> Dict[str, Any]:
    """Build hunt plan with stops"""
    area = session.hunt_area or "your area"
    resolved_area, stops = _build_hunt_stops(session.hunt_area)
    
    items = []
    for stop in stops:
        items.append(stop)
    
    if not items:
        summary = f"I couldn't find any verified allocation stores near {resolved_area}.\n\n"
        summary += "Try:\n• Searching online for local bourbon groups\n• Checking state liquor control sites\n• Asking at local liquor stores about their allocation process"
    else:
        summary = f"Here are the allocation stores near {resolved_area}:\n\n"
        summary += f"Found {len(items)} stores. Check their social media or call ahead to learn about their allocation process."
    
    return {
        "mode": "hunt",
        "summary": summary,
        "items": items
    }


def _handle_cigar_retail_search(msg: str, session: SamSession) -> Dict[str, Any]:
    """
    Handle requests to find cigar retailers (NEW)
    Example: "where can I find these cigars near me"
    """
    
    if not CIGAR_RETAIL_AVAILABLE:
        return {
            "mode": "info",
            "summary": "For cigar retail locations, try checking your local tobacco shops or online retailers like Famous Smoke Shop.",
            "items": []
        }
    
    # Initialize cigar retail search
    cigar_search = CigarRetailSearch(google_api_key=os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_PLACES_API_KEY", "")))
    
    # Extract location from message
    location = _extract_location_from_message(msg)
    
    if not location:
        cigar_name = session.last_cigar_discussed or "those cigars"
        return {
            "mode": "info",
            "summary": f"Hey! I'd love to help you track down {cigar_name}, but I need to know where you're located.\n\nWhat's your ZIP code or city/state?\n\nOnce you tell me, I can point you toward some solid cigar shops in your area.",
            "items": []
        }
    
    # Search for retailers
    retailers = cigar_search.find_cigar_retailers(location=location)
    
    if retailers:
        cigar_name = session.last_cigar_discussed or "those cigars"
        response_text = f"Great! Here's where you can find {cigar_name} near {location}:\n\n"
        response_text += cigar_search.format_retailers_for_response(retailers)
        
        return {
            "mode": "info",
            "summary": response_text,
            "items": []
        }
    else:
        return {
            "mode": "info",
            "summary": f"I'm having trouble finding cigar shops near {location}.\n\nYour best bets are:\n• Check out local tobacco shops or cigar lounges\n• Try online retailers like Famous Smoke Shop or Cigars International\n• Call ahead to make sure they have what you're looking for",
            "items": []
        }
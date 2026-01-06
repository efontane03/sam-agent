"""
State-aware store filtering for bourbon allocation hunting.
This module provides filtering logic that adapts to different state retail systems.
"""

from state_retail_systems import (
    get_state_retail_system,
    should_include_chain,
    get_state_search_terms
)


def filter_stores_by_state_system(places, state_abbrev, debug=False):
    """
    Filter stores based on state-specific retail system.
    
    Args:
        places: List of place dictionaries from Google Places API
        state_abbrev: Two-letter state abbreviation
        debug: If True, print debug information
    
    Returns:
        list: Filtered stores appropriate for the state's retail system
    """
    system_type, config = get_state_retail_system(state_abbrev)
    filter_strategy = config["filter_strategy"]
    
    if debug:
        print(f"DEBUG: Filtering for {state_abbrev} using '{filter_strategy}' strategy")
        print(f"DEBUG: Market type: {config['name']}")
    
    if filter_strategy == "strict_independent":
        return filter_independent_stores(places, config, debug)
    
    elif filter_strategy == "selective_chain":
        return filter_chain_friendly_stores(places, config, state_abbrev, debug)
    
    elif filter_strategy == "government_stores":
        return filter_government_stores(places, config, state_abbrev, debug)
    
    return places


def filter_independent_stores(places, config, debug=False):
    """
    Filter for independent liquor stores, excluding chains and non-liquor retailers.
    Used in states where independent stores dominate allocations.
    """
    from state_retail_systems import STATE_RETAIL_SYSTEMS
    
    filtered = []
    exclude_types = config.get("exclude_types", [])
    exclude_chains = config.get("exclude_chains", [])
    
    # Also exclude allocation chains from chain-friendly states
    chain_friendly_config = STATE_RETAIL_SYSTEMS.get("chain_friendly", {})
    allocation_chains = chain_friendly_config.get("approved_chains", [])
    all_excluded_chains = exclude_chains + allocation_chains
    
    for place in places:
        name = place.get("name", "").lower()
        types = place.get("types", [])
        
        # Skip excluded place types
        if any(excluded_type in types for excluded_type in exclude_types):
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - excluded type: {types}")
            continue
        
        # Skip known chain stores (including allocation chains)
        is_chain = any(chain in name for chain in all_excluded_chains)
        if is_chain:
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - chain store")
            continue
        
        # Must be a liquor store
        if "liquor_store" in types or "liquor" in name or "spirits" in name or "wine" in name:
            filtered.append(place)
            if debug:
                print(f"DEBUG: ✓ Including '{place.get('name')}' - independent liquor store")
        else:
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - not a liquor store")
    
    return filtered


def filter_chain_friendly_stores(places, config, state_abbrev, debug=False):
    """
    Filter for stores in chain-friendly markets.
    Includes approved allocation chains while still excluding grocery stores.
    """
    filtered = []
    approved_chains = config.get("approved_chains", [])
    exclude_chains = config.get("exclude_chains", [])
    exclude_types = config.get("exclude_types", [])
    
    for place in places:
        name = place.get("name", "").lower()
        types = place.get("types", [])
        
        # Skip excluded types (restaurants, bars, etc.)
        if any(excluded_type in types for excluded_type in exclude_types):
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - excluded type: {types}")
            continue
        
        # Check if it's an approved allocation chain
        is_approved_chain = any(chain in name for chain in approved_chains)
        if is_approved_chain:
            filtered.append(place)
            if debug:
                print(f"DEBUG: ✓ Including '{place.get('name')}' - approved allocation chain")
            continue
        
        # Skip explicitly excluded chains (grocery stores)
        is_excluded_chain = any(chain in name for chain in exclude_chains)
        if is_excluded_chain:
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - excluded chain")
            continue
        
        # Include liquor stores (independent or smaller chains)
        if "liquor_store" in types or "liquor" in name or "spirits" in name:
            # Additional check: skip if it's a grocery despite having "liquor" in name
            if "grocery" not in name and "market" not in " ".join(types):
                filtered.append(place)
                if debug:
                    print(f"DEBUG: ✓ Including '{place.get('name')}' - liquor store")
            else:
                if debug:
                    print(f"DEBUG: Skipping '{place.get('name')}' - grocery/market")
        else:
            if debug:
                print(f"DEBUG: Skipping '{place.get('name')}' - not a liquor store")
    
    return filtered


def filter_government_stores(places, config, state_abbrev, debug=False):
    """
    Filter for state-controlled markets.
    Looks for ABC stores, state liquor stores, and government-operated retailers.
    """
    filtered = []
    state_terms = config.get("state_specific_terms", {}).get(state_abbrev.upper(), [])
    
    # Combine generic government terms with state-specific ones
    government_keywords = ["abc", "state liquor", "liquor control", "state store"] + state_terms
    
    for place in places:
        name = place.get("name", "").lower()
        types = place.get("types", [])
        
        # Look for government/ABC store indicators
        is_government_store = any(keyword in name for keyword in government_keywords)
        
        if is_government_store:
            filtered.append(place)
            if debug:
                print(f"DEBUG: ✓ Including '{place.get('name')}' - government/ABC store")
        else:
            # Also include generic liquor stores (might be state-licensed agents)
            if "liquor_store" in types or "liquor" in name:
                # But exclude obvious non-government stores
                if not any(exclude in name for exclude in ["total wine", "bevmo", "grocery"]):
                    filtered.append(place)
                    if debug:
                        print(f"DEBUG: ✓ Including '{place.get('name')}' - liquor store (possible state agent)")
                else:
                    if debug:
                        print(f"DEBUG: Skipping '{place.get('name')}' - private retailer in state-controlled market")
            else:
                if debug:
                    print(f"DEBUG: Skipping '{place.get('name')}' - not a state store")
    
    return filtered


def build_search_query(city, state_abbrev):
    """
    Build state-aware search query for Google Places API.
    
    Args:
        city: City name
        state_abbrev: Two-letter state abbreviation
    
    Returns:
        str: Optimized search query for the state's retail system
    """
    system_type, config = get_state_retail_system(state_abbrev)
    keywords = get_state_search_terms(state_abbrev)
    
    # Build query with relevant keywords
    if system_type == "state_controlled":
        # For state-controlled, prioritize government store terms
        primary_keywords = keywords[:2]  # First 2 are most relevant
        query = f"{' '.join(primary_keywords)} {city} {state_abbrev}"
    
    elif system_type == "chain_friendly":
        # For chain-friendly, include both chains and general liquor stores
        query = f"bourbon liquor store allocation {city} {state_abbrev}"
    
    else:  # independent_dominant
        # For independent markets, focus on liquor stores
        query = f"liquor store wine spirits {city} {state_abbrev}"
    
    return query


def enhance_places_with_allocation_likelihood(places, state_abbrev):
    """
    Add allocation likelihood score to each place based on state system and store type.
    
    Args:
        places: List of place dictionaries
        state_abbrev: Two-letter state abbreviation
    
    Returns:
        list: Places with added 'allocation_score' field (0-100)
    """
    system_type, config = get_state_retail_system(state_abbrev)
    
    for place in places:
        name = place.get("name", "").lower()
        types = place.get("types", [])
        score = 50  # Base score
        
        # Boost for known allocation chains (in chain-friendly states)
        if system_type == "chain_friendly":
            approved_chains = config.get("approved_chains", [])
            if any(chain in name for chain in approved_chains):
                score += 30
        
        # Boost for government stores (in state-controlled markets)
        if system_type == "state_controlled":
            state_terms = config.get("state_specific_terms", {}).get(state_abbrev.upper(), [])
            if any(term in name for term in ["abc", "state"] + state_terms):
                score += 30
        
        # Boost for liquor_store type
        if "liquor_store" in types:
            score += 15
        
        # Boost for bourbon-related keywords
        bourbon_keywords = ["bourbon", "whiskey", "spirits", "barrel"]
        if any(keyword in name for keyword in bourbon_keywords):
            score += 10
        
        place["allocation_score"] = min(score, 100)
    
    # Sort by allocation score (highest first)
    places.sort(key=lambda x: x.get("allocation_score", 0), reverse=True)
    
    return places


# Export main functions
__all__ = [
    'filter_stores_by_state_system',
    'build_search_query',
    'enhance_places_with_allocation_likelihood'
]

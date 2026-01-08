# State-Aware Retail System Integration Guide

This guide explains how to integrate the state-aware retail system into your existing `sam_engine.py`.

## Files to Add to Your Project

1. **state_retail_systems.py** - State configuration and classification
2. **store_filters.py** - State-aware filtering logic

Copy both files to your `sam-agent` backend directory.

## Step 1: Update Imports in sam_engine.py

Add these imports at the top of your `sam_engine.py`:

```python
from state_retail_systems import (
    get_state_retail_system,
    format_hunt_response,
    get_hunt_plan_template
)
from store_filters import (
    filter_stores_by_state_system,
    build_search_query,
    enhance_places_with_allocation_likelihood
)
```

## Step 2: Update Your _hunt_plan Method

Replace your existing `_hunt_plan` method with this state-aware version:

```python
def _hunt_plan(self, session: SamSession, city: str, state: str) -> Dict[str, Any]:
    """
    Generate location-specific allocation hunting plan with state-aware retail system logic.
    
    Args:
        session: Current session
        city: Target city
        state: Two-letter state abbreviation
    
    Returns:
        Dict containing hunt plan with stores and steps
    """
    print(f"\n{'='*50}")
    print(f"HUNT PLAN REQUEST: {city}, {state}")
    print(f"{'='*50}\n")
    
    # Get state retail system info
    system_type, config = get_state_retail_system(state)
    print(f"DEBUG: State retail system: {system_type}")
    print(f"DEBUG: Market type: {config['name']}")
    
    # Search for stores using state-aware query
    stores = self._search_allocation_stores(city, state, system_type, config)
    
    # Format response with state-specific guidance
    response_text = format_hunt_response(state, city, stores)
    
    # Build structured response
    hunt_plan = {
        "location": f"{city}, {state}",
        "retail_system": config['name'],
        "system_type": system_type,
        "description": config['description'],
        "strategy": config['allocation_tip'],
        "stores": stores[:10] if stores else [],  # Limit to top 10
        "response": response_text
    }
    
    # Add state website for state-controlled markets
    if system_type == "state_controlled" and state.upper() in config.get("websites", {}):
        hunt_plan["state_website"] = config["websites"][state.upper()]
    
    print(f"\nDEBUG: Hunt plan generated with {len(stores)} stores")
    print(f"{'='*50}\n")
    
    return hunt_plan
```

## Step 3: Update Your _search_allocation_stores Method

Replace your existing store search method with this state-aware version:

```python
def _search_allocation_stores(self, city: str, state: str, system_type: str, config: dict) -> List[Dict]:
    """
    Search for allocation stores using state-appropriate strategy.
    
    Args:
        city: Target city
        state: Two-letter state abbreviation
        system_type: Type of retail system (independent_dominant, chain_friendly, state_controlled)
        config: State retail system configuration
    
    Returns:
        List of store dictionaries with location and details
    """
    print(f"DEBUG: Searching for stores in {city}, {state}")
    print(f"DEBUG: Using strategy: {config['filter_strategy']}")
    
    # Build state-aware search query
    query = build_search_query(city, state)
    print(f"DEBUG: Search query: {query}")
    
    # Search using Google Places API
    places = self._google_places_search(query, city, state)
    
    if not places:
        print(f"DEBUG: No places found from Google Places API")
        return []
    
    print(f"DEBUG: Google Places returned {len(places)} results")
    
    # Filter stores based on state retail system
    filtered_stores = filter_stores_by_state_system(places, state, debug=True)
    
    print(f"DEBUG: After filtering: {len(filtered_stores)} stores passed")
    
    if not filtered_stores:
        print("DEBUG: No stores passed filters, checking fallback options...")
        # For chain-friendly states, try a second search with specific chain names
        if system_type == "chain_friendly":
            approved_chains = config.get("approved_chains", [])
            for chain in approved_chains[:3]:  # Try top 3 chains
                chain_query = f"{chain} {city} {state}"
                print(f"DEBUG: Trying specific chain search: {chain_query}")
                chain_places = self._google_places_search(chain_query, city, state)
                if chain_places:
                    filtered_stores.extend(chain_places)
    
    # Enhance stores with allocation likelihood scores
    if filtered_stores:
        filtered_stores = enhance_places_with_allocation_likelihood(filtered_stores, state)
    
    return filtered_stores
```

## Step 4: Update Your _google_places_search Method

Make sure your Google Places search method returns properly formatted place dictionaries:

```python
def _google_places_search(self, query: str, city: str, state: str) -> List[Dict]:
    """
    Search Google Places API for stores.
    
    Returns:
        List of place dictionaries with keys: name, address, types, place_id, etc.
    """
    # Your existing Google Places API call
    # Make sure it returns dictionaries with at least these keys:
    # - name: str
    # - address: str (formatted_address from API)
    # - types: List[str] (from API)
    # - place_id: str (optional, for future use)
    
    # Example return format:
    # [
    #     {
    #         "name": "Total Wine & More",
    #         "address": "123 Main St, Seattle, WA 98101",
    #         "types": ["liquor_store", "store"],
    #         "place_id": "ChIJ..."
    #     },
    #     ...
    # ]
    pass  # Your existing implementation
```

## Step 5: Update Response Formatting

When returning the hunt plan to your frontend, make sure to include the formatted response:

```python
# In your chat endpoint or wherever you process the hunt mode response:

if mode == "hunt":
    hunt_plan = engine._hunt_plan(session, city, state)
    
    # Return the formatted response text to display to user
    return {
        "response": hunt_plan["response"],  # Formatted markdown text
        "stores": hunt_plan["stores"],       # Store list for potential UI rendering
        "retail_system": hunt_plan["retail_system"],
        "next_step": "Call these shops and ask about their allocation process"
    }
```

## Step 6: Test the Integration

Test with different states to verify the system works:

```python
# Test independent market (Kentucky)
hunt_plan = engine._hunt_plan(session, "Louisville", "KY")

# Test chain-friendly market (Seattle)
hunt_plan = engine._hunt_plan(session, "Seattle", "WA")

# Test state-controlled market (Pennsylvania)
hunt_plan = engine._hunt_plan(session, "Philadelphia", "PA")
```

## Expected Behavior Changes

### Before Integration:
- Seattle search returns 0 stores (all filtered out as chains)
- Generic "call local liquor stores" advice for all states
- Same filtering logic regardless of state

### After Integration:
- Seattle search includes Total Wine, BevMo, and independent shops
- State-specific advice (e.g., "Check Total Wine lottery" for WA vs "Build relationships with local shops" for KY)
- Pennsylvania shows ABC store info and state website
- Each state gets appropriate filtering and guidance

## Debug Output

With debug=True, you'll see output like:

```
==================================================
HUNT PLAN REQUEST: Seattle, WA
==================================================

DEBUG: State retail system: chain_friendly
DEBUG: Market type: Chain-Inclusive Market
DEBUG: Searching for stores in Seattle, WA
DEBUG: Using strategy: selective_chain
DEBUG: Search query: bourbon liquor store allocation Seattle WA
DEBUG: Google Places returned 15 results
DEBUG: ✓ Including 'Total Wine & More' - approved allocation chain
DEBUG: Skipping 'Fred Meyer' - excluded chain
DEBUG: ✓ Including 'McCarthy & Schiering Wine Merchants' - liquor store
DEBUG: After filtering: 8 stores passed
DEBUG: Hunt plan generated with 8 stores
==================================================
```

## Troubleshooting

### Issue: Still getting 0 stores for Seattle
- Check that `state_retail_systems.py` is imported correctly
- Verify the state abbreviation is uppercase: "WA" not "wa"
- Enable debug mode to see which filters are being applied

### Issue: Wrong stores showing up
- Check the `approved_chains` list in `state_retail_systems.py`
- Adjust the `exclude_chains` list for your specific needs
- Use debug mode to see which stores pass/fail filters

### Issue: State-controlled markets not working
- Verify the state is in the `state_controlled` list
- Check that `state_specific_terms` includes the right keywords for that state
- Some state-controlled markets may need custom search queries

## Next Steps

After integration:
1. Test with multiple cities in different states
2. Monitor your logs to see which stores are being found/filtered
3. Adjust the approved/excluded chain lists based on real-world results
4. Consider adding user feedback: "Was this store helpful?" to improve the system
5. Add more states to the configuration as needed

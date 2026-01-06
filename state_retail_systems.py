"""
State-specific liquor retail system configurations for bourbon allocation hunting.
This module categorizes US states by their liquor retail models and provides
appropriate search and filtering strategies for each system type.
"""

STATE_RETAIL_SYSTEMS = {
    "independent_dominant": {
        "name": "Independent Store Market",
        "states": [
            "KY", "TN", "TX", "GA", "FL", "IN", "OH", "MI", 
            "NY", "NJ", "SC", "OK", "KS", "NE", "SD", "ND", 
            "IA", "MN", "AR", "CT", "DE", "MA", "RI", "MD"
        ],
        "description": "Independent liquor stores dominate the market. Local shops handle most allocations through direct relationships with distributors.",
        "allocation_tip": "Build relationships with local liquor store owners and managers. Ask about allocation lists and delivery days (typically Thursday/Friday).",
        "filter_strategy": "strict_independent",
        "search_keywords": ["liquor store", "wine and spirits", "package store", "bottle shop"],
        "exclude_types": ["grocery_or_supermarket", "restaurant", "bar", "cafe", "department_store"],
        "exclude_chains": [
            "walmart", "target", "costco", "kroger", "safeway", "whole foods",
            "trader joe", "fred meyer", "publix", "wegmans", "giant eagle"
        ],
        "hunt_steps": [
            {
                "step": "Identify Local Shops",
                "action": "Find independent liquor stores in your area",
                "tip": "Look for stores with 'liquor', 'spirits', or 'wine' in the name"
            },
            {
                "step": "Call and Ask About Allocations",
                "action": "Call 3-5 shops and ask: 'Do you get allocated bourbon? How does your allocation process work?'",
                "tip": "Best times to call: Tuesday-Thursday mornings"
            },
            {
                "step": "Visit and Build Relationships",
                "action": "Visit stores, make purchases, and ask to be added to allocation lists",
                "tip": "Some stores require purchase history before allocations"
            },
            {
                "step": "Learn Delivery Schedules",
                "action": "Ask what day allocated bottles typically arrive",
                "tip": "Show up on delivery days (usually Thu/Fri) in the morning"
            }
        ]
    },
    
    "chain_friendly": {
        "name": "Chain-Inclusive Market",
        "states": [
            "WA", "CA", "AZ", "NV", "CO", "NM", "LA", "MO", "WI", "IL"
        ],
        "description": "Private retail market where major chains and specialty retailers handle significant allocation volume alongside independent stores.",
        "allocation_tip": "Check both major chains (Total Wine, BevMo) and independent specialty shops. Many chains use lottery or waitlist systems.",
        "filter_strategy": "selective_chain",
        "search_keywords": ["liquor store", "wine and spirits", "total wine", "bevmo", "specialty liquor"],
        "approved_chains": [
            "total wine", "bevmo", "binny's", "k&l wine merchants", 
            "spec's", "twin liquors", "hi-time", "mission liquor",
            "remedy liquor", "justin's house of bourbon"
        ],
        "exclude_types": ["restaurant", "bar", "cafe"],
        "exclude_chains": [
            "walmart", "target", "kroger", "safeway", "whole foods",
            "trader joe", "fred meyer", "costco"
        ],
        "hunt_steps": [
            {
                "step": "Check Major Chain Lotteries",
                "action": "Visit Total Wine, BevMo websites and sign up for allocation lotteries",
                "tip": "Some chains require in-store signup - call to confirm"
            },
            {
                "step": "Find Specialty Retailers",
                "action": "Search for independent liquor stores known for good bourbon selection",
                "tip": "Check local bourbon Facebook groups for recommendations"
            },
            {
                "step": "Ask About Allocation Process",
                "action": "Call stores and ask if they use waitlists, lotteries, or first-come systems",
                "tip": "Chains often have formal online systems; independents may be relationship-based"
            },
            {
                "step": "Monitor Release Schedules",
                "action": "Sign up for email notifications and check websites regularly",
                "tip": "Allocated drops often announced 24-48 hours in advance"
            }
        ]
    },
    
    "state_controlled": {
        "name": "State-Controlled Market",
        "states": [
            "PA", "UT", "NC", "VA", "AL", "ID", "NH", "MS", 
            "MT", "OR", "VT", "WY", "WV", "ME"
        ],
        "description": "State government operates liquor stores or tightly controls distribution. Allocations typically handled through lottery systems or centralized releases.",
        "allocation_tip": "Monitor your state ABC/liquor control website for lottery announcements and release schedules. Most allocations are online lottery-based.",
        "filter_strategy": "government_stores",
        "search_keywords": ["abc store", "state liquor", "liquor control", "state spirits"],
        "state_specific_terms": {
            "PA": ["fine wine & good spirits", "fwgs", "plcb"],
            "NC": ["abc store", "north carolina abc"],
            "VA": ["virginia abc", "vabc"],
            "OR": ["olcc", "liquor store"],
            "UT": ["utah liquor store", "dabs"],
            "NH": ["new hampshire liquor", "nh liquor"],
            "AL": ["alabama abc"],
            "ID": ["idaho state liquor"],
            "MS": ["mississippi abc"],
            "MT": ["montana liquor"],
            "VT": ["vermont liquor"],
            "WY": ["wyoming liquor"],
            "WV": ["west virginia abc"],
            "ME": ["maine liquor"]
        },
        "websites": {
            "PA": "https://www.finewineandgoodspirits.com",
            "NC": "https://abc.nc.gov",
            "VA": "https://www.abc.virginia.gov",
            "OR": "https://www.oregon.gov/olcc",
            "UT": "https://webapps.abc.utah.gov",
            "NH": "https://www.liquorandwineoutlets.com",
        },
        "hunt_steps": [
            {
                "step": "Find Your State's ABC Website",
                "action": "Search for '[Your State] ABC liquor control' and bookmark the official site",
                "tip": "State websites announce lottery dates and rules"
            },
            {
                "step": "Sign Up for Notifications",
                "action": "Register for email alerts about allocated bottle releases",
                "tip": "Some states require account creation for lottery entry"
            },
            {
                "step": "Learn the Lottery System",
                "action": "Read the rules - entry periods, pickup windows, purchase limits",
                "tip": "Lottery windows are often short (24-48 hours)"
            },
            {
                "step": "Monitor Release Schedules",
                "action": "Check website regularly - many states have quarterly or seasonal drops",
                "tip": "Fall (Sept-Nov) typically has highest allocation volume"
            }
        ]
    }
}


def get_state_retail_system(state_abbrev):
    """
    Returns the retail system configuration for a given state.
    
    Args:
        state_abbrev: Two-letter state abbreviation (e.g., 'WA', 'KY')
    
    Returns:
        tuple: (system_type, config_dict)
    """
    state = state_abbrev.upper().strip()
    
    for system_type, config in STATE_RETAIL_SYSTEMS.items():
        if state in config["states"]:
            return system_type, config
    
    # Default to independent dominant if state not found
    return "independent_dominant", STATE_RETAIL_SYSTEMS["independent_dominant"]


def get_state_search_terms(state_abbrev):
    """
    Returns appropriate search keywords for a given state's retail system.
    
    Args:
        state_abbrev: Two-letter state abbreviation
    
    Returns:
        list: Search keywords appropriate for the state
    """
    system_type, config = get_state_retail_system(state_abbrev)
    keywords = config["search_keywords"].copy()
    
    # Add state-specific terms for state-controlled systems
    if system_type == "state_controlled":
        state_terms = config.get("state_specific_terms", {}).get(state_abbrev.upper(), [])
        keywords.extend(state_terms)
    
    return keywords


def should_include_chain(store_name, state_abbrev):
    """
    Determines if a chain store should be included based on state retail system.
    
    Args:
        store_name: Name of the store
        state_abbrev: Two-letter state abbreviation
    
    Returns:
        bool: True if chain should be included, False otherwise
    """
    system_type, config = get_state_retail_system(state_abbrev)
    store_lower = store_name.lower()
    
    # Check if it's an excluded chain (always exclude)
    excluded = config.get("exclude_chains", [])
    if any(chain in store_lower for chain in excluded):
        return False
    
    # For chain-friendly states, check approved chains
    if system_type == "chain_friendly":
        approved = config.get("approved_chains", [])
        if any(chain in store_lower for chain in approved):
            return True
        # If not in approved list, allow it (might be independent)
        return True
    
    # For state-controlled, look for state-specific terms
    if system_type == "state_controlled":
        state_terms = config.get("state_specific_terms", {}).get(state_abbrev.upper(), [])
        if any(term in store_lower for term in state_terms):
            return True
        # Allow generic liquor stores too
        return True
    
    # For independent_dominant states, exclude known allocation chains
    if system_type == "independent_dominant":
        # Get the approved chains from chain_friendly config
        chain_friendly_config = STATE_RETAIL_SYSTEMS.get("chain_friendly", {})
        allocation_chains = chain_friendly_config.get("approved_chains", [])
        # Exclude these chains in independent markets
        if any(chain in store_lower for chain in allocation_chains):
            return False
    
    # Default: include (likely independent store)
    return True


def get_hunt_plan_template(state_abbrev, city=None):
    """
    Returns a formatted hunt plan template for a given state.
    
    Args:
        state_abbrev: Two-letter state abbreviation
        city: Optional city name for context
    
    Returns:
        dict: Formatted hunt plan with steps and guidance
    """
    system_type, config = get_state_retail_system(state_abbrev)
    
    location = f"{city}, {state_abbrev}" if city else state_abbrev
    
    plan = {
        "location": location,
        "retail_system": config["name"],
        "description": config["description"],
        "strategy": config["allocation_tip"],
        "steps": config["hunt_steps"]
    }
    
    # Add state website for state-controlled markets
    if system_type == "state_controlled":
        websites = config.get("websites", {})
        if state_abbrev.upper() in websites:
            plan["state_website"] = websites[state_abbrev.upper()]
    
    return plan


def format_hunt_response(state_abbrev, city, stores):
    """
    Formats a complete hunt response with state-specific guidance.
    
    Args:
        state_abbrev: Two-letter state abbreviation
        city: City name
        stores: List of store dictionaries
    
    Returns:
        str: Formatted response text
    """
    system_type, config = get_state_retail_system(state_abbrev)
    plan = get_hunt_plan_template(state_abbrev, city)
    
    response = f"""**Bourbon allocation hunting in {city}, {state_abbrev}**

**Market Type:** {plan['retail_system']}
{plan['description']}

**Best Strategy:** {plan['strategy']}
"""
    
    # Add state website for state-controlled
    if "state_website" in plan:
        response += f"\n**State Website:** {plan['state_website']}\n"
    
    # Add stores if found
    if stores and len(stores) > 0:
        response += "\n**Stores to check:**\n"
        for i, store in enumerate(stores[:10], 1):  # Limit to top 10
            name = store.get("name", "Unknown")
            address = store.get("address", "Address not available")
            response += f"{i}. **{name}**\n   {address}\n\n"
    else:
        response += "\n*No specific stores found in search results.*\n"
    
    # Add hunt steps
    response += "\n**Hunting Steps:**\n\n"
    for i, step in enumerate(plan['steps'], 1):
        response += f"**Step {i}: {step['step']}**\n"
        response += f"{step['action']}\n"
        response += f"*Tip: {step['tip']}*\n\n"
    
    return response


# Export main functions
__all__ = [
    'STATE_RETAIL_SYSTEMS',
    'get_state_retail_system',
    'get_state_search_terms',
    'should_include_chain',
    'get_hunt_plan_template',
    'format_hunt_response'
]

"""
Curated database of stores known for bourbon allocations.
Sources: Reddit r/bourbon, bourbon.io, local bourbon groups, enthusiast reports
"""

ALLOCATION_STORES = {
    "louisville_ky": [
        {
            "name": "Westport Whiskey & Wine",
            "address": "1115 Herr Ln, Louisville, KY 40222",
            "phone": "(502) 618-4683",
            "lat": 38.2454,
            "lng": -85.6532,
            "allocation_type": "raffle",
            "notes": "Known for fair raffle system. Follow on social media for raffle announcements. Must be present to win.",
            "social_media": "Instagram: @westportwhiskey",
        },
        {
            "name": "Old Town Liquors",
            "address": "1529 Bardstown Rd, Louisville, KY 40205",
            "phone": "(502) 451-8591",
            "lat": 38.2343,
            "lng": -85.7089,
            "allocation_type": "points",
            "notes": "Points-based system. Earn points through purchases. Known for getting BTAC, Weller, Blanton's.",
        },
        {
            "name": "Julio's Liquors",
            "address": "4327 Bishop Ln, Louisville, KY 40218",
            "phone": "(502) 485-0200",
            "lat": 38.2021,
            "lng": -85.6744,
            "allocation_type": "list",
            "notes": "Sign up for allocation list in-store. Long-time customers get priority. Fair pricing.",
        },
    ],
    
    "nashville_tn": [
        {
            "name": "Frugal MacDoogal",
            "address": "1950 Gallatin Pike N, Madison, TN 37115",
            "phone": "(615) 868-0450",
            "lat": 36.2559,
            "lng": -86.7019,
            "allocation_type": "first_come",
            "notes": "First-come first-served drops on delivery days (usually Thursday mornings). Get there early. Known for BTAC drops.",
        },
        {
            "name": "Corkdorks Wine Spirits Beer Midtown",
            "address": "1610 Church Street, Nashville, TN 37203",
            "phone": "(615) 327-3874",
            "lat": 36.1540,
            "lng": -86.7965,
            "allocation_type": "raffle",
            "notes": "Raffle system for allocated bottles. Sign up in-store. Loyal customers prioritized.",
        },
        {
            "name": "Red Dog Wine & Spirits",
            "address": "2410 Elliston Pl, Nashville, TN 37203",
            "phone": "(615) 327-9893",
            "lat": 36.1531,
            "lng": -86.7987,
            "allocation_type": "list",
            "notes": "Allocation list system. Build relationship first. Known for store picks.",
        },
    ],
    
    "dallas_tx": [
        {
            "name": "Goody Goody Liquor",
            "address": "Multiple DFW locations",
            "phone": "(214) 350-6973",
            "lat": 32.7767,
            "lng": -96.7970,
            "allocation_type": "lottery",
            "notes": "Online lottery system. Sign up on their website. Winners notified by email. Fair and transparent process.",
            "website": "goodygoody.com",
        },
        {
            "name": "Spec's Wine, Spirits & Finer Foods",
            "address": "Multiple DFW locations",
            "phone": "Varies by location",
            "lat": 32.7767,
            "lng": -96.7970,
            "allocation_type": "spend_based",
            "notes": "Loyalty program required. Higher spenders get first access. Join Spec's Card program.",
        },
        {
            "name": "Times Ten Cellars",
            "address": "6324 Prospect Ave, Dallas, TX 75214",
            "phone": "(214) 824-9463",
            "lat": 32.8271,
            "lng": -96.7678,
            "allocation_type": "list",
            "notes": "Known for excellent bourbon selection and fair allocation process. Build relationship with staff.",
        },
    ],
    
    "atlanta_ga": [
        {
            "name": "Green's Beverages",
            "address": "2625 Piedmont Rd NE, Atlanta, GA 30324",
            "phone": "(404) 233-3845",
            "lat": 38.8233,
            "lng": -84.3530,
            "allocation_type": "list",
            "notes": "Sign up for allocation list. Known for getting Weller, BTAC, Blanton's. Fair pricing.",
        },
        {
            "name": "Tower Beer Wine & Spirits",
            "address": "2161 Piedmont Rd NE, Atlanta, GA 30324",
            "phone": "(404) 233-5432",
            "lat": 33.8104,
            "lng": -84.3567,
            "allocation_type": "raffle",
            "notes": "Raffle system for allocated bottles. Follow on social media for announcements.",
        },
        {
            "name": "Hop City Beer & Wine",
            "address": "1000 Marietta St NW, Atlanta, GA 30318",
            "phone": "(404) 968-2537",
            "lat": 33.7842,
            "lng": -84.4138,
            "allocation_type": "first_come",
            "notes": "Drops announced on Instagram. First-come basis. Known for store picks.",
        },
    ],
    
    "chicago_il": [
        {
            "name": "Binny's Beverage Depot",
            "address": "Multiple Chicago locations",
            "phone": "Varies by location",
            "lat": 41.8781,
            "lng": -87.6298,
            "allocation_type": "lottery",
            "notes": "Online lottery system. Must be Binny's card member. Winners drawn randomly. Very fair process.",
            "website": "binnys.com",
        },
        {
            "name": "Warehouse Liquors",
            "address": "2900 N Ashland Ave, Chicago, IL 60657",
            "phone": "(773) 278-6750",
            "lat": 41.9345,
            "lng": -87.6689,
            "allocation_type": "list",
            "notes": "Allocation list. Build relationship with owner. Great bourbon selection.",
        },
    ],
    
    "denver_co": [
        {
            "name": "Argonaut Wine & Liquor",
            "address": "760 E Colfax Ave, Denver, CO 80203",
            "phone": "(303) 831-7788",
            "lat": 39.7402,
            "lng": -104.9789,
            "allocation_type": "list",
            "notes": "Legendary bourbon selection. Allocation list for regulars. Best selection in Denver.",
        },
        {
            "name": "Daveco Liquors",
            "address": "300 S Pearl St, Denver, CO 80209",
            "phone": "(303) 777-3615",
            "lat": 39.7134,
            "lng": -104.9789,
            "allocation_type": "points",
            "notes": "Points system. Earn points through purchases. Known for BTAC, Pappy drops.",
        },
    ],
}

# City aliases for matching
CITY_ALIASES = {
    "louisville": "louisville_ky",
    "lexington": "louisville_ky",  # Use Louisville stores as proxy
    "nashville": "nashville_tn",
    "memphis": "nashville_tn",  # Use Nashville as proxy
    "dallas": "dallas_tx",
    "fort worth": "dallas_tx",
    "dfw": "dallas_tx",
    "houston": "dallas_tx",  # Use Dallas as proxy for now
    "austin": "dallas_tx",  # Use Dallas as proxy for now
    "atlanta": "atlanta_ga",
    "chicago": "chicago_il",
    "denver": "denver_co",
}

def get_allocation_stores_for_city(city_query: str):
    """
    Get curated allocation stores for a given city.
    
    Args:
        city_query: City name or area (e.g., "Dallas", "Nashville, TN", "30344")
    
    Returns:
        List of store dictionaries or None if no curated data
    """
    city_lower = city_query.lower().strip()
    
    # Try direct match
    for alias, db_key in CITY_ALIASES.items():
        if alias in city_lower:
            return ALLOCATION_STORES.get(db_key)
    
    return None

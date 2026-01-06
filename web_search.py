"""
Web search integration for finding bourbon allocation stores.
Uses Brave Search API (free tier: 2000 searches/month)
"""

import os
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any

BRAVE_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

def search_allocation_stores(city: str, state: str = "") -> List[Dict[str, Any]]:
    """
    Search the web for stores known to have bourbon allocations.
    
    Args:
        city: City name (e.g., "Miami", "Portland")
        state: State abbreviation (e.g., "FL", "OR")
    
    Returns:
        List of findings from web search
    """
    if not BRAVE_API_KEY:
        print("WARNING: No Brave Search API key found")
        return []
    
    location = f"{city}, {state}" if state else city
    
    # Search queries to find allocation stores
    queries = [
        f"bourbon allocation stores {location}",
        f"where to buy allocated bourbon {location}",
        f"Blanton's Weller drops {location}",
        f"{location} bourbon raffle lottery",
    ]
    
    findings = []
    
    for query in queries[:2]:  # Limit to 2 queries to save API calls
        try:
            results = _brave_search(query)
            findings.extend(_parse_allocation_info(results, location))
        except Exception as e:
            print(f"Search error for '{query}': {e}")
    
    return findings


def _brave_search(query: str, count: int = 10) -> Dict[str, Any]:
    """Make a Brave Search API request."""
    params = {
        "q": query,
        "count": count,
    }
    
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY,
        },
        method="GET",
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    
    return json.loads(raw)


def _parse_allocation_info(search_results: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """
    Parse search results to extract store information.
    
    Looks for:
    - Reddit threads about local stores
    - Store websites with allocation info
    - Bourbon community posts
    - Social media mentions
    """
    findings = []
    
    web_results = search_results.get("web", {}).get("results", [])
    
    for result in web_results:
        title = result.get("title", "")
        description = result.get("description", "")
        url = result.get("url", "")
        
        # Look for indicators that this mentions allocation stores
        allocation_keywords = ["allocation", "raffle", "lottery", "drop", "btac", "weller", "blanton"]
        store_keywords = ["liquor", "wine", "spirits", "beverage", "store"]
        
        title_lower = title.lower()
        desc_lower = description.lower()
        
        has_allocation = any(kw in title_lower or kw in desc_lower for kw in allocation_keywords)
        has_store = any(kw in title_lower or kw in desc_lower for kw in store_keywords)
        
        if has_allocation and has_store:
            findings.append({
                "title": title,
                "description": description,
                "url": url,
                "source_type": _classify_source(url),
            })
    
    return findings


def _classify_source(url: str) -> str:
    """Classify the type of source."""
    url_lower = url.lower()
    
    if "reddit.com" in url_lower:
        return "reddit"
    elif "facebook.com" in url_lower or "instagram.com" in url_lower:
        return "social_media"
    elif any(domain in url_lower for domain in [".com", ".net", ".org"]):
        # Check if it's a store website
        if any(kw in url_lower for kw in ["liquor", "wine", "spirits"]):
            return "store_website"
        return "article"
    
    return "unknown"


def extract_store_names_from_findings(findings: List[Dict[str, Any]]) -> List[str]:
    """
    Extract likely store names from search findings.
    This is a simple heuristic - could be improved with NLP.
    """
    store_names = []
    
    for finding in findings:
        title = finding.get("title", "")
        desc = finding.get("description", "")
        
        # Look for patterns like "Store Name - City" or "Visit Store Name for"
        # This is simplified - real implementation would use better parsing
        if "liquor" in title.lower() or "wine" in title.lower():
            # Extract first part before " - " or " | "
            parts = title.split(" - ")[0].split(" | ")[0]
            store_names.append(parts.strip())
    
    return list(set(store_names))  # Remove duplicates

import os
import requests

RAILWAY_API_URL = os.getenv("RAILWAY_API_URL")

def lookup_allocations(zip_code: str, radius_km: float = 25):
    """
    Call your Railway allocation API and return JSON.
    """
    if not RAILWAY_API_URL:
        raise RuntimeError("RAILWAY_API_URL is not set in .env")

    url = f"{RAILWAY_API_URL}/allocations/search-nearby"
    params = {"zip": zip_code, "radius_km": radius_km}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


"""
Cigar Retail Search Module
Separate from bourbon allocation hunting - focuses on finding cigar retailers
"""

import requests
from typing import List, Dict, Optional
import os
from dataclasses import dataclass


@dataclass
class CigarRetailer:
    """Represents a cigar retailer"""
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None
    rating: Optional[float] = None
    website: Optional[str] = None
    distance_miles: Optional[float] = None
    place_id: Optional[str] = None


class CigarRetailSearch:
    """
    Search for cigar retailers using Google Places API
    Separate from bourbon allocation hunting
    """
    
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
        # Curated list of known quality cigar retailers by city
        self.curated_retailers = {
            "philadelphia": [
                {"name": "Holt's Cigar Company", "address": "1522 Walnut St, Philadelphia, PA 19102"},
                {"name": "Smoke", "address": "210 W Rittenhouse Square, Philadelphia, PA 19103"},
            ],
            "new york": [
                {"name": "Davidoff of Geneva", "address": "535 Madison Ave, New York, NY 10022"},
                {"name": "Barclay Rex", "address": "7 Maiden Ln, New York, NY 10038"},
                {"name": "Nat Sherman", "address": "12 E 42nd St, New York, NY 10017"},
            ],
            "chicago": [
                {"name": "Iwan Ries & Co", "address": "19 S Wabash Ave, Chicago, IL 60603"},
                {"name": "Up Down Cigar", "address": "1550 N Wells St, Chicago, IL 60610"},
            ],
            "miami": [
                {"name": "El Titan de Bronze", "address": "1071 SW 8th St, Miami, FL 33130"},
                {"name": "Smoke Inn", "address": "8970 S Dixie Hwy, Miami, FL 33156"},
            ],
            "los angeles": [
                {"name": "Maxamar", "address": "10918 Weyburn Ave, Los Angeles, CA 90024"},
                {"name": "Cigars Etc", "address": "12657 Ventura Blvd, Studio City, CA 91604"},
            ],
        }
        
        # Chains to EXCLUDE (they don't carry premium cigars)
        self.exclude_chains = [
            "cvs", "walgreens", "walmart", "target", "whole foods",
            "trader joe", "safeway", "kroger", "7-eleven", "circle k"
        ]
    
    def find_cigar_retailers(
        self,
        location: str = None,
        zip_code: str = None,
        city_state: str = None,
        radius_miles: int = 10
    ) -> List[CigarRetailer]:
        """
        Find cigar retailers near a location
        
        Args:
            location: Free-form location string
            zip_code: ZIP code
            city_state: "City, State" format
            radius_miles: Search radius in miles
        
        Returns:
            List of CigarRetailer objects
        """
        
        # Determine search location
        search_location = self._resolve_location(location, zip_code, city_state)
        
        if not search_location:
            return []
        
        # Try curated retailers first
        curated = self._get_curated_retailers(search_location)
        
        # Search Google Places
        google_results = self._search_google_places(search_location, radius_miles)
        
        # Combine and deduplicate
        all_retailers = curated + google_results
        unique_retailers = self._deduplicate_retailers(all_retailers)
        
        return unique_retailers[:10]  # Return top 10
    
    def _resolve_location(self, location: str, zip_code: str, city_state: str) -> Optional[str]:
        """Resolve location to a searchable format"""
        if zip_code:
            return zip_code
        elif city_state:
            return city_state
        elif location:
            return location
        else:
            return None
    
    def _get_curated_retailers(self, location: str) -> List[CigarRetailer]:
        """Get curated retailers for known cities"""
        location_lower = location.lower()
        
        for city, retailers in self.curated_retailers.items():
            if city in location_lower:
                return [
                    CigarRetailer(
                        name=r["name"],
                        address=r["address"],
                        city=city.title(),
                        state=self._extract_state(r["address"]),
                        zip_code=self._extract_zip(r["address"])
                    )
                    for r in retailers
                ]
        
        return []
    
    def _search_google_places(self, location: str, radius_miles: int) -> List[CigarRetailer]:
        """Search Google Places API for cigar shops"""
        
        # Convert miles to meters
        radius_meters = int(radius_miles * 1609.34)
        
        try:
            # First, geocode the location
            geocode_url = f"{self.base_url}/textsearch/json"
            geocode_params = {
                "query": f"cigar shop near {location}",
                "key": self.google_api_key,
                "radius": radius_meters,
                "type": "store"
            }
            
            response = requests.get(geocode_url, params=geocode_params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            results = data.get("results", [])
            
            # Filter and convert to CigarRetailer objects
            retailers = []
            
            for result in results:
                name = result.get("name", "")
                
                # Skip excluded chains
                if any(chain in name.lower() for chain in self.exclude_chains):
                    continue
                
                # Skip if not a cigar shop
                if not self._is_cigar_retailer(name, result.get("types", [])):
                    continue
                
                retailer = CigarRetailer(
                    name=name,
                    address=result.get("formatted_address", ""),
                    city=self._extract_city(result.get("formatted_address", "")),
                    state=self._extract_state(result.get("formatted_address", "")),
                    zip_code=self._extract_zip(result.get("formatted_address", "")),
                    rating=result.get("rating"),
                    place_id=result.get("place_id")
                )
                
                retailers.append(retailer)
            
            return retailers
        
        except Exception as e:
            print(f"Error searching Google Places: {e}")
            return []
    
    def _is_cigar_retailer(self, name: str, types: List[str]) -> bool:
        """Check if a place is actually a cigar retailer"""
        name_lower = name.lower()
        
        # Positive indicators
        cigar_keywords = ["cigar", "tobacco", "smoke shop", "humidor"]
        
        return any(keyword in name_lower for keyword in cigar_keywords)
    
    def _deduplicate_retailers(self, retailers: List[CigarRetailer]) -> List[CigarRetailer]:
        """Remove duplicate retailers"""
        seen_names = set()
        unique = []
        
        for retailer in retailers:
            name_key = retailer.name.lower().strip()
            
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique.append(retailer)
        
        return unique
    
    def _extract_city(self, address: str) -> str:
        """Extract city from address"""
        parts = address.split(",")
        if len(parts) >= 2:
            return parts[-2].strip()
        return ""
    
    def _extract_state(self, address: str) -> str:
        """Extract state from address"""
        parts = address.split(",")
        if len(parts) >= 2:
            state_zip = parts[-1].strip()
            state = state_zip.split()[0]
            return state
        return ""
    
    def _extract_zip(self, address: str) -> str:
        """Extract ZIP code from address"""
        parts = address.split()
        for part in reversed(parts):
            if part.isdigit() and len(part) == 5:
                return part
        return ""
    
    def format_retailers_for_response(self, retailers: List[CigarRetailer]) -> str:
        """Format retailers for Sam's response"""
        if not retailers:
            return "I couldn't find any cigar retailers near you. Try checking online retailers like Famous Smoke Shop, Cigars International, or Thompson Cigar."
        
        response = "Here are some cigar shops near you:\n\n"
        
        for i, retailer in enumerate(retailers, 1):
            response += f"**{i}. {retailer.name}**\n"
            response += f"   • Address: {retailer.address}\n"
            
            if retailer.phone:
                response += f"   • Phone: {retailer.phone}\n"
            
            if retailer.rating:
                response += f"   • Rating: {retailer.rating}/5.0\n"
            
            if retailer.website:
                response += f"   • Website: {retailer.website}\n"
            
            response += "\n"
        
        return response


# Integration with Sam's intent detection
class IntentClassifier:
    """
    Improved intent classification to distinguish between:
    - Cigar retail search (where to buy cigars)
    - Bourbon allocation hunting (where to find allocated bourbon)
    """
    
    @staticmethod
    def detect_retail_search_intent(message: str, session) -> Dict[str, any]:
        """
        Detect if user is asking about where to find cigars vs bourbon
        
        Returns:
            {
                "intent": "cigar_retail" | "bourbon_allocation" | "unknown",
                "subject": "cigar" | "bourbon",
                "confidence": float
            }
        """
        message_lower = message.lower()
        
        # Keywords for retail search
        retail_keywords = ["where can i find", "where to buy", "where do i get", 
                          "shop near me", "store near me", "buy near me"]
        
        allocation_keywords = ["allocation", "allocated", "hard to find", "rare bourbon"]
        
        # Determine subject from context
        subject = None
        
        # Check explicit mentions
        if any(word in message_lower for word in ["cigar", "cigars", "smoke", "stick"]):
            subject = "cigar"
        elif any(word in message_lower for word in ["bourbon", "whiskey", "bottle"]):
            subject = "bourbon"
        else:
            # Use session context
            if hasattr(session, 'last_cigar_discussed') and session.last_cigar_discussed:
                subject = "cigar"
            elif hasattr(session, 'last_bourbon_discussed') and session.last_bourbon_discussed:
                subject = "bourbon"
        
        # Determine intent
        is_retail_search = any(keyword in message_lower for keyword in retail_keywords)
        is_allocation = any(keyword in message_lower for keyword in allocation_keywords)
        
        if is_allocation:
            return {
                "intent": "bourbon_allocation",
                "subject": "bourbon",
                "confidence": 0.9
            }
        elif is_retail_search and subject == "cigar":
            return {
                "intent": "cigar_retail",
                "subject": "cigar",
                "confidence": 0.8
            }
        elif is_retail_search and subject == "bourbon":
            return {
                "intent": "bourbon_allocation",
                "subject": "bourbon",
                "confidence": 0.7
            }
        else:
            return {
                "intent": "unknown",
                "subject": subject,
                "confidence": 0.0
            }


# Example usage in sam_engine.py:
"""
from cigar_retail_search import CigarRetailSearch, IntentClassifier

# In your SamEngine class
class SamEngine:
    def __init__(self):
        self.cigar_retail_search = CigarRetailSearch(
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    def handle_message(self, session, message):
        # Classify intent
        intent_result = IntentClassifier.detect_retail_search_intent(message, session)
        
        if intent_result["intent"] == "cigar_retail":
            # User is looking for cigar shops
            retailers = self.cigar_retail_search.find_cigar_retailers(
                location=self._extract_location(message)
            )
            
            return self.cigar_retail_search.format_retailers_for_response(retailers)
        
        elif intent_result["intent"] == "bourbon_allocation":
            # User is looking for allocated bourbon (your existing logic)
            return self.handle_allocation_hunt(session, message)
        
        else:
            # Regular conversation (your existing logic)
            return self.process_regular_message(session, message)
"""
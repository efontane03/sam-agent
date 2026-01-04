"""
Curated bourbon and cigar pairing recommendations.
Based on strength matching, flavor profiles, and classic pairings.
"""

# Cigar strength categories
CIGAR_STRENGTHS = {
    "mild": ["Connecticut", "Claro", "Candela"],
    "medium": ["Habano", "Corojo", "Natural"],
    "full": ["Maduro", "Oscuro", "Ligero"]
}

# Bourbon/Whiskey categories by proof and flavor
BOURBON_PROFILES = {
    "light_sweet": {
        "bottles": [
            "Buffalo Trace",
            "Maker's Mark",
            "Woodford Reserve",
            "Four Roses Small Batch",
            "Elijah Craig Small Batch"
        ],
        "proof_range": "80-94",
        "flavor_notes": "Vanilla, caramel, light oak",
        "best_for_cigars": "mild to medium"
    },
    "medium_balanced": {
        "bottles": [
            "Eagle Rare 10 Year",
            "Knob Creek 9 Year",
            "Russell's Reserve 10 Year",
            "Old Forester 1920",
            "Wild Turkey 101"
        ],
        "proof_range": "95-115",
        "flavor_notes": "Balanced oak, spice, fruit",
        "best_for_cigars": "medium to full"
    },
    "high_proof_bold": {
        "bottles": [
            "Booker's",
            "Stagg Jr.",
            "Elijah Craig Barrel Proof",
            "Weller Full Proof",
            "Old Forester 1920"
        ],
        "proof_range": "115-130+",
        "flavor_notes": "Bold oak, dark fruit, intense spice",
        "best_for_cigars": "full-bodied only"
    },
    "wheated_smooth": {
        "bottles": [
            "Maker's Mark",
            "Weller Special Reserve",
            "Weller Antique 107",
            "Larceny",
            "Rebel Yell"
        ],
        "proof_range": "80-107",
        "flavor_notes": "Smooth, wheat sweetness, honey",
        "best_for_cigars": "mild to medium"
    },
    "rye_spicy": {
        "bottles": [
            "Bulleit Rye",
            "Rittenhouse Rye",
            "High West Double Rye",
            "Pikesville Rye",
            "WhistlePig 10 Year"
        ],
        "proof_range": "90-110",
        "flavor_notes": "Spice, pepper, mint, herbal",
        "best_for_cigars": "medium to full"
    }
}

# Classic pairings
CLASSIC_PAIRINGS = [
    {
        "cigar_type": "Mild Connecticut",
        "cigar_examples": ["Ashton Classic", "Macanudo Cafe", "Montecristo White"],
        "bourbon": "Maker's Mark or Buffalo Trace",
        "why": "Light, sweet bourbons won't overpower delicate Connecticut wrappers. The vanilla and caramel notes complement the cigar's creamy, nutty flavors.",
        "strength": "mild",
        "profile": "light_sweet"
    },
    {
        "cigar_type": "Medium Habano",
        "cigar_examples": ["Padron 2000", "Arturo Fuente Hemingway", "Rocky Patel Vintage 1990"],
        "bourbon": "Eagle Rare 10 Year or Knob Creek",
        "why": "Medium-bodied bourbons match the cigar's balanced spice and earthiness. The oak and fruit notes create harmony without competing.",
        "strength": "medium",
        "profile": "medium_balanced"
    },
    {
        "cigar_type": "Full Maduro",
        "cigar_examples": ["Padron 1964 Maduro", "Liga Privada No. 9", "My Father Le Bijou"],
        "bourbon": "Booker's or Stagg Jr.",
        "why": "Bold, high-proof bourbons stand up to rich, chocolatey maduros. The intense oak and spice complement dark tobacco oils.",
        "strength": "full",
        "profile": "high_proof_bold"
    },
    {
        "cigar_type": "Medium-Full Corojo",
        "cigar_examples": ["Tatuaje Black", "Illusione Rothchildes", "Drew Estate Undercrown"],
        "bourbon": "Wild Turkey 101 or Old Forester 1920",
        "why": "Spicy, flavorful bourbons match the pepper and leather in Corojo wrappers. The higher proof cuts through rich tobacco.",
        "strength": "medium-full",
        "profile": "medium_balanced"
    },
    {
        "cigar_type": "Mild-Medium Natural",
        "cigar_examples": ["Oliva Serie G", "Romeo y Julieta Reserva Real", "Perdomo Champagne"],
        "bourbon": "Four Roses Small Batch or Weller Special Reserve",
        "why": "Smooth, approachable bourbons enhance the cigar's cedar and toast notes without overwhelming. Wheated bourbons especially pair well.",
        "strength": "medium",
        "profile": "wheated_smooth"
    },
    {
        "cigar_type": "Full-Bodied Nicaraguan",
        "cigar_examples": ["Padron 1926", "Oliva Serie V", "Drew Estate Liga Privada"],
        "bourbon": "Elijah Craig Barrel Proof or Weller Full Proof",
        "why": "High-proof, complex bourbons match the intensity of Nicaraguan tobacco. Bold flavors create a powerful, satisfying combination.",
        "strength": "full",
        "profile": "high_proof_bold"
    }
]

# Pairing tips
PAIRING_TIPS = [
    "Match strength with strength - don't let one overpower the other",
    "Start mild and work up - begin with lighter pairings, progress to bolder",
    "Higher proof cuts through rich tobacco oils",
    "Wheated bourbons pair beautifully with Connecticut wrappers",
    "Rye whiskeys complement peppery cigars",
    "Let the bourbon rest on your palate before taking a draw",
    "Sip neat or with a single large ice cube - avoid mixers",
    "Take small sips to avoid palate fatigue"
]

def get_pairing_for_cigar_strength(strength: str):
    """Get bourbon recommendations for a given cigar strength."""
    strength_lower = strength.lower()
    
    if "mild" in strength_lower or "light" in strength_lower:
        return {
            "strength": "mild",
            "recommended_profiles": ["light_sweet", "wheated_smooth"],
            "specific_bottles": [
                "Maker's Mark",
                "Buffalo Trace", 
                "Weller Special Reserve",
                "Four Roses Small Batch"
            ]
        }
    elif "full" in strength_lower or "bold" in strength_lower or "strong" in strength_lower:
        return {
            "strength": "full",
            "recommended_profiles": ["high_proof_bold", "medium_balanced"],
            "specific_bottles": [
                "Booker's",
                "Stagg Jr.",
                "Elijah Craig Barrel Proof",
                "Wild Turkey Rare Breed"
            ]
        }
    else:  # medium
        return {
            "strength": "medium",
            "recommended_profiles": ["medium_balanced", "rye_spicy"],
            "specific_bottles": [
                "Eagle Rare 10 Year",
                "Knob Creek",
                "Wild Turkey 101",
                "Old Forester 1920"
            ]
        }

def get_pairing_for_bourbon(bourbon_name: str):
    """Get cigar recommendations for a given bourbon."""
    bourbon_lower = bourbon_name.lower()
    
    # Check which profile the bourbon belongs to
    for profile_name, profile_data in BOURBON_PROFILES.items():
        bottles_lower = [b.lower() for b in profile_data["bottles"]]
        if any(bourbon_lower in bottle or bottle in bourbon_lower for bottle in bottles_lower):
            best_for = profile_data["best_for_cigars"]
            
            # Get matching classic pairings
            matching_pairings = [
                p for p in CLASSIC_PAIRINGS 
                if p["profile"] == profile_name or best_for in p["strength"]
            ]
            
            return {
                "bourbon_profile": profile_name,
                "proof_range": profile_data["proof_range"],
                "flavor_notes": profile_data["flavor_notes"],
                "recommended_cigar_strength": best_for,
                "cigar_examples": matching_pairings[0]["cigar_examples"] if matching_pairings else [],
                "pairing_notes": matching_pairings[0]["why"] if matching_pairings else ""
            }
    
    # Default if bourbon not found
    return {
        "bourbon_profile": "unknown",
        "recommended_cigar_strength": "medium",
        "cigar_examples": ["Padron 2000", "Arturo Fuente Hemingway"],
        "pairing_notes": "For most bourbons, a medium-bodied cigar provides good balance."
    }

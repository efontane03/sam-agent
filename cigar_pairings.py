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

# Bourbon/Whiskey recommendations with pricing and tiers
BOURBON_RECOMMENDATIONS = {
    "budget": [
        {
            "name": "Buffalo Trace",
            "price": "$25-30",
            "tier": "Budget",
            "flavor_intensity": "Mild-Medium",
            "proof": 90,
            "notes": "Vanilla, caramel, light oak. Perfect everyday sipper.",
            "best_cigar_strength": "mild to medium"
        },
        {
            "name": "Evan Williams Single Barrel",
            "price": "$30-35",
            "tier": "Budget",
            "flavor_intensity": "Medium",
            "proof": 86.6,
            "notes": "Honey, vanilla, fruit. Great value vintage bourbon.",
            "best_cigar_strength": "mild to medium"
        },
        {
            "name": "Wild Turkey 101",
            "price": "$25-30",
            "tier": "Budget",
            "flavor_intensity": "Medium-Full",
            "proof": 101,
            "notes": "Spice, oak, caramel. Classic high-rye bourbon.",
            "best_cigar_strength": "medium to full"
        },
        {
            "name": "Old Forester 100 Proof",
            "price": "$25-28",
            "tier": "Budget",
            "flavor_intensity": "Medium",
            "proof": 100,
            "notes": "Baking spice, cherry, oak. Solid everyday bourbon.",
            "best_cigar_strength": "medium"
        }
    ],
    "mid_range": [
        {
            "name": "Eagle Rare 10 Year",
            "price": "$35-45",
            "tier": "Mid-range",
            "flavor_intensity": "Medium",
            "proof": 90,
            "notes": "Toffee, orange peel, balanced oak. Smooth and complex.",
            "best_cigar_strength": "medium"
        },
        {
            "name": "Knob Creek 9 Year",
            "price": "$35-40",
            "tier": "Mid-range",
            "flavor_intensity": "Medium-Full",
            "proof": 100,
            "notes": "Rich oak, vanilla, nuts. Full-bodied classic.",
            "best_cigar_strength": "medium to full"
        },
        {
            "name": "Russell's Reserve 10 Year",
            "price": "$40-45",
            "tier": "Mid-range",
            "flavor_intensity": "Medium-Full",
            "proof": 90,
            "notes": "Honey, spice, leather. Well-aged Turkey.",
            "best_cigar_strength": "medium to full"
        },
        {
            "name": "Maker's Mark Cask Strength",
            "price": "$40-50",
            "tier": "Mid-range",
            "flavor_intensity": "Medium",
            "proof": 110,
            "notes": "Wheated sweetness, vanilla, fruit. Smooth despite proof.",
            "best_cigar_strength": "medium"
        },
        {
            "name": "Old Forester 1920 Prohibition Style",
            "price": "$60-70",
            "tier": "Mid-range",
            "flavor_intensity": "Full",
            "proof": 115,
            "notes": "Bold chocolate, cherry, oak. Rich and intense.",
            "best_cigar_strength": "full"
        }
    ],
    "premium": [
        {
            "name": "Booker's",
            "price": "$70-90",
            "tier": "Premium",
            "flavor_intensity": "Full",
            "proof": 125,
            "notes": "Uncut, unfiltered power. Peanut, oak, leather.",
            "best_cigar_strength": "full"
        },
        {
            "name": "Elijah Craig Barrel Proof",
            "price": "$65-75",
            "tier": "Premium",
            "flavor_intensity": "Full",
            "proof": 120,
            "notes": "Intense caramel, dark fruit, oak. Complex heat.",
            "best_cigar_strength": "full"
        },
        {
            "name": "Stagg Jr.",
            "price": "$55-70",
            "tier": "Premium",
            "flavor_intensity": "Full",
            "proof": 130,
            "notes": "Cherry cola, dark chocolate, bold spice. BTAC baby brother.",
            "best_cigar_strength": "full"
        },
        {
            "name": "Woodford Reserve Double Oaked",
            "price": "$55-65",
            "tier": "Premium",
            "flavor_intensity": "Medium-Full",
            "proof": 90.4,
            "notes": "Extra oak, dark fruit, chocolate. Luxurious smoothness.",
            "best_cigar_strength": "medium to full"
        },
        {
            "name": "Four Roses Limited Edition Small Batch",
            "price": "$130-150",
            "tier": "Premium",
            "flavor_intensity": "Full",
            "proof": 108,
            "notes": "Floral, spice, dark fruit. Annual release masterpiece.",
            "best_cigar_strength": "full"
        }
    ]
}

# Cigar recommendations with pricing and tiers
CIGAR_RECOMMENDATIONS = {
    "budget": [
        {
            "name": "Arturo Fuente 8-5-8",
            "price": "$6-8",
            "tier": "Budget",
            "strength": "Mild-Medium",
            "wrapper": "Natural",
            "notes": "Cedar, cream, subtle spice. Classic Connecticut shade.",
            "pairs_with": "Buffalo Trace, Maker's Mark"
        },
        {
            "name": "Padron 2000",
            "price": "$7-9",
            "tier": "Budget",
            "strength": "Medium",
            "wrapper": "Natural/Maduro",
            "notes": "Cocoa, espresso, earth. Nicaraguan consistency.",
            "pairs_with": "Eagle Rare, Wild Turkey 101"
        },
        {
            "name": "Rocky Patel Vintage 1990",
            "price": "$7-10",
            "tier": "Budget",
            "strength": "Mild-Medium",
            "wrapper": "Connecticut",
            "notes": "Smooth, creamy, nutty. Easy morning smoke.",
            "pairs_with": "Buffalo Trace, Evan Williams Single Barrel"
        },
        {
            "name": "Oliva Serie G",
            "price": "$5-7",
            "tier": "Budget",
            "strength": "Medium",
            "wrapper": "Cameroon",
            "notes": "Coffee, cedar, spice. Great value Nicaraguan.",
            "pairs_with": "Wild Turkey 101, Knob Creek"
        }
    ],
    "mid_range": [
        {
            "name": "Padron 1964 Anniversary",
            "price": "$15-20",
            "tier": "Mid-range",
            "strength": "Medium-Full",
            "wrapper": "Natural/Maduro",
            "notes": "Rich cocoa, espresso, leather. Box-pressed excellence.",
            "pairs_with": "Knob Creek, Russell's Reserve 10"
        },
        {
            "name": "Arturo Fuente Hemingway",
            "price": "$12-16",
            "tier": "Mid-range",
            "strength": "Medium",
            "wrapper": "Cameroon",
            "notes": "Cedar, cream, slight pepper. Elegant figurado.",
            "pairs_with": "Eagle Rare, Maker's Mark Cask Strength"
        },
        {
            "name": "My Father Le Bijou 1922",
            "price": "$12-15",
            "tier": "Mid-range",
            "strength": "Full",
            "wrapper": "Habano Oscuro",
            "notes": "Black pepper, dark chocolate, espresso. Bold Nicaraguan.",
            "pairs_with": "Old Forester 1920, Booker's"
        },
        {
            "name": "Ashton VSG",
            "price": "$12-18",
            "tier": "Mid-range",
            "strength": "Medium-Full",
            "wrapper": "Ecuador Sumatra",
            "notes": "Spice, leather, earth. Well-balanced Dominican.",
            "pairs_with": "Knob Creek, Woodford Double Oaked"
        }
    ],
    "premium": [
        {
            "name": "Padron 1926 Serie",
            "price": "$20-30",
            "tier": "Premium",
            "strength": "Full",
            "wrapper": "Natural/Maduro",
            "notes": "Complex cocoa, coffee, leather. Anniversary masterpiece.",
            "pairs_with": "Booker's, Elijah Craig Barrel Proof"
        },
        {
            "name": "Davidoff Nicaragua",
            "price": "$18-25",
            "tier": "Premium",
            "strength": "Medium-Full",
            "wrapper": "Habano",
            "notes": "Pepper, cocoa, cedar. Swiss precision meets Nicaragua.",
            "pairs_with": "Old Forester 1920, Stagg Jr."
        },
        {
            "name": "Arturo Fuente Opus X",
            "price": "$25-40",
            "tier": "Premium",
            "strength": "Full",
            "wrapper": "Dominican Rosado",
            "notes": "Spice, leather, sweetness. Legendary Dominican puro.",
            "pairs_with": "Booker's, Four Roses Limited Edition"
        },
        {
            "name": "Liga Privada No. 9",
            "price": "$15-20",
            "tier": "Premium",
            "strength": "Full",
            "wrapper": "Connecticut Broadleaf Maduro",
            "notes": "Chocolate, espresso, earth. Drew Estate flagship.",
            "pairs_with": "Elijah Craig Barrel Proof, Stagg Jr."
        }
    ]
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
    """Get bourbon recommendations for a given cigar strength. Returns minimum 3 bourbons across price tiers."""
    strength_lower = strength.lower()
    
    # Collect matching bourbons from all tiers
    all_matches = []
    
    for tier_name, bourbons in BOURBON_RECOMMENDATIONS.items():
        for bourbon in bourbons:
            cigar_match = bourbon["best_cigar_strength"]
            
            # Match by strength
            if "mild" in strength_lower and "mild" in cigar_match:
                all_matches.append(bourbon)
            elif "full" in strength_lower and "full" in cigar_match:
                all_matches.append(bourbon)
            elif "medium" in strength_lower and "medium" in cigar_match:
                all_matches.append(bourbon)
    
    # Ensure we have at least 3 recommendations
    if len(all_matches) < 3:
        # Add some general recommendations if needed
        if "mild" in strength_lower:
            all_matches.extend([b for b in BOURBON_RECOMMENDATIONS["budget"] if "mild" in b["best_cigar_strength"]][:3])
        elif "full" in strength_lower:
            all_matches.extend([b for b in BOURBON_RECOMMENDATIONS["premium"] if "full" in b["best_cigar_strength"]][:3])
        else:
            all_matches.extend([b for b in BOURBON_RECOMMENDATIONS["mid_range"] if "medium" in b["best_cigar_strength"]][:3])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for bourbon in all_matches:
        if bourbon["name"] not in seen:
            seen.add(bourbon["name"])
            unique_matches.append(bourbon)
    
    # Return at least 3, up to 5
    return {
        "strength": strength_lower,
        "recommendations": unique_matches[:5]  # Max 5 to keep response manageable
    }

def get_pairing_for_bourbon(bourbon_name: str):
    """Get cigar recommendations for a given bourbon. Returns minimum 3 cigars across price tiers."""
    bourbon_lower = bourbon_name.lower()
    
    # Find the bourbon in our database to get its strength
    bourbon_strength = None
    for tier_name, bourbons in BOURBON_RECOMMENDATIONS.items():
        for bourbon in bourbons:
            if bourbon_lower in bourbon["name"].lower():
                bourbon_strength = bourbon["best_cigar_strength"]
                break
        if bourbon_strength:
            break
    
    # Default to medium if not found
    if not bourbon_strength:
        bourbon_strength = "medium"
    
    # Collect matching cigars from all tiers
    all_matches = []
    
    for tier_name, cigars in CIGAR_RECOMMENDATIONS.items():
        for cigar in cigars:
            cigar_strength_lower = cigar["strength"].lower()
            
            # Match by strength
            if "mild" in bourbon_strength and "mild" in cigar_strength_lower:
                all_matches.append(cigar)
            elif "full" in bourbon_strength and "full" in cigar_strength_lower:
                all_matches.append(cigar)
            elif "medium" in bourbon_strength and "medium" in cigar_strength_lower:
                all_matches.append(cigar)
    
    # Ensure we have at least 3 recommendations
    if len(all_matches) < 3:
        # Add general recommendations based on strength
        if "mild" in bourbon_strength:
            all_matches.extend(CIGAR_RECOMMENDATIONS["budget"][:3])
        elif "full" in bourbon_strength:
            all_matches.extend(CIGAR_RECOMMENDATIONS["premium"][:3])
        else:
            all_matches.extend(CIGAR_RECOMMENDATIONS["mid_range"][:3])
    
    # Remove duplicates
    seen = set()
    unique_matches = []
    for cigar in all_matches:
        if cigar["name"] not in seen:
            seen.add(cigar["name"])
            unique_matches.append(cigar)
    
    # Return at least 3, up to 5
    return {
        "bourbon_name": bourbon_name,
        "bourbon_strength": bourbon_strength,
        "recommendations": unique_matches[:5]  # Max 5 to keep response manageable
    }
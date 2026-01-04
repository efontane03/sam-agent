"""
Bourbon knowledge database - detailed information about specific bottles.
For educational purposes when users ask about specific bourbons.
"""

BOURBON_KNOWLEDGE = {
    "buffalo trace": {
        "name": "Buffalo Trace",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "proof": 90,
        "age": "No age statement (typically 8-10 years)",
        "price_range": "$25-30",
        "availability": "Widely available",
        "mashbill": "Low rye bourbon mashbill",
        "tasting_notes": [
            "Vanilla and toffee on the nose",
            "Brown sugar, oak, and dark fruit on the palate",
            "Medium body with hints of mint and molasses",
            "Smooth, balanced finish"
        ],
        "why_its_great": "Buffalo Trace is the gateway bourbon - approachable price, excellent quality, perfect for beginners and enthusiasts alike.",
        "fun_fact": "The distillery has been making bourbon for over 200 years and survived Prohibition."
    },
    
    "eagle rare": {
        "name": "Eagle Rare 10 Year",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "proof": 90,
        "age": "10 years",
        "price_range": "$35-45 (MSRP)",
        "availability": "Semi-allocated (can be hard to find)",
        "mashbill": "Buffalo Trace Mashbill #1 (low rye)",
        "tasting_notes": [
            "Toffee and orange peel",
            "Honey, leather, and oak",
            "Complex with hints of cocoa",
            "Long, dry finish with subtle spice"
        ],
        "why_its_great": "10 years of aging at an incredible price point. Punches well above its weight class.",
        "fun_fact": "Originally introduced in 1975 as a 101-proof 10-year bourbon before being reformulated."
    },
    
    "pappy van winkle": {
        "name": "Pappy Van Winkle Family Reserve",
        "distillery": "Buffalo Trace Distillery (Old Rip Van Winkle brand)",
        "location": "Frankfort, Kentucky",
        "proof": "Varies (90.4-95.6 depending on age)",
        "age": "10, 12, 15, 20, or 23 years",
        "price_range": "$300-3,000+ (secondary market)",
        "availability": "Ultra-allocated (extremely rare)",
        "mashbill": "Wheated bourbon (wheat instead of rye)",
        "tasting_notes": [
            "Caramel, vanilla, butterscotch",
            "Rich oak with dried fruit",
            "Smooth wheated character",
            "Long, luxurious finish"
        ],
        "why_its_great": "The most sought-after bourbon in America. Exceptional quality with decades of aging.",
        "fun_fact": "Only about 7,000 cases produced annually across all ages. The 23-year is one of the oldest bourbons made."
    },
    
    "weller": {
        "name": "Weller (Special Reserve, Antique 107, 12 Year, Full Proof, Single Barrel)",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "proof": "90-114 (varies by expression)",
        "age": "NAS to 12 years",
        "price_range": "$25-60 (MSRP, varies by expression)",
        "availability": "Allocated (hard to find)",
        "mashbill": "Wheated bourbon (same as Pappy Van Winkle)",
        "tasting_notes": [
            "Honey and vanilla sweetness",
            "Caramel and butterscotch",
            "Smooth wheated character",
            "Soft, approachable finish"
        ],
        "why_its_great": "Poor man's Pappy - same mashbill as Van Winkle at a fraction of the price.",
        "fun_fact": "William Larue Weller pioneered the use of wheat in bourbon in the 1800s."
    },
    
    "booker's": {
        "name": "Booker's",
        "distillery": "Jim Beam",
        "location": "Clermont, Kentucky",
        "proof": "120-130 (varies by batch)",
        "age": "6-8 years",
        "price_range": "$70-90",
        "availability": "Widely available",
        "mashbill": "77% corn, 13% rye, 10% malted barley",
        "tasting_notes": [
            "Uncut, unfiltered power",
            "Peanut, oak, and vanilla",
            "Leather and caramel",
            "Long, hot, intense finish"
        ],
        "why_its_great": "Barrel proof bourbon at its finest. What Booker Noe (Jim Beam's grandson) drank himself.",
        "fun_fact": "Named after Booker Noe, 6th generation master distiller. Each batch is bottled from a specific rack location."
    },
    
    "blanton's": {
        "name": "Blanton's Single Barrel",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "proof": 93,
        "age": "No age statement (typically 6-8 years)",
        "price_range": "$60-70 (MSRP)",
        "availability": "Allocated (hard to find in US)",
        "mashbill": "Buffalo Trace Mashbill #2 (high rye)",
        "tasting_notes": [
            "Citrus and honey",
            "Caramel, vanilla, nutmeg",
            "Medium body with spice",
            "Smooth, balanced finish"
        ],
        "why_its_great": "First modern single barrel bourbon (1984). Each bottle comes from one specific barrel.",
        "fun_fact": "The horse-and-jockey toppers spell 'BLANTONS' when you collect all 8 letters."
    },
    
    "elijah craig": {
        "name": "Elijah Craig Barrel Proof",
        "distillery": "Heaven Hill",
        "location": "Bardstown, Kentucky",
        "proof": "120-140 (varies by batch)",
        "age": "12 years",
        "price_range": "$65-75",
        "availability": "Semi-allocated",
        "mashbill": "75% corn, 13% rye, 12% malted barley",
        "tasting_notes": [
            "Dark caramel and brown sugar",
            "Rich oak and dark fruit",
            "Chocolate and espresso",
            "Long, warming finish"
        ],
        "why_its_great": "12-year barrel proof bourbon at an incredible value. Consistently excellent.",
        "fun_fact": "Named after Rev. Elijah Craig, often credited (incorrectly) with inventing bourbon."
    },
    
    "knob creek": {
        "name": "Knob Creek 9 Year",
        "distillery": "Jim Beam",
        "location": "Clermont, Kentucky",
        "proof": 100,
        "age": "9 years",
        "price_range": "$35-40",
        "availability": "Widely available",
        "mashbill": "77% corn, 13% rye, 10% malted barley",
        "tasting_notes": [
            "Rich vanilla and oak",
            "Caramel and nuts",
            "Full-bodied with nice spice",
            "Long, smooth finish"
        ],
        "why_its_great": "Pre-Prohibition style bourbon - 9 years of aging at 100 proof for under $40.",
        "fun_fact": "Part of Jim Beam's Small Batch Collection launched in 1992."
    },
    
    "maker's mark": {
        "name": "Maker's Mark",
        "distillery": "Maker's Mark Distillery",
        "location": "Loretto, Kentucky",
        "proof": 90,
        "age": "No age statement (typically 5-6 years)",
        "price_range": "$25-30",
        "availability": "Widely available",
        "mashbill": "70% corn, 16% wheat, 14% malted barley",
        "tasting_notes": [
            "Vanilla and caramel sweetness",
            "Soft fruit and wheat notes",
            "Smooth, approachable body",
            "Gentle, sweet finish"
        ],
        "why_its_great": "Iconic wheated bourbon. Approachable, smooth, consistent. That red wax seal is unmistakable.",
        "fun_fact": "The recipe was developed by Margie Samuels, and she also designed the iconic label."
    },
    
    "wild turkey 101": {
        "name": "Wild Turkey 101",
        "distillery": "Wild Turkey Distillery",
        "location": "Lawrenceburg, Kentucky",
        "proof": 101,
        "age": "No age statement (6-8 years)",
        "price_range": "$25-30",
        "availability": "Widely available",
        "mashbill": "75% corn, 13% rye, 12% malted barley",
        "tasting_notes": [
            "Spice and caramel",
            "Oak, vanilla, honey",
            "Bold, full-bodied",
            "Long, warming finish"
        ],
        "why_its_great": "The best bang-for-buck bourbon. High proof, long aging, incredible value.",
        "fun_fact": "Master Distiller Jimmy Russell has been with Wild Turkey for over 70 years."
    },
    
    "woodford reserve": {
        "name": "Woodford Reserve",
        "distillery": "Woodford Reserve Distillery",
        "location": "Versailles, Kentucky",
        "proof": 90.4,
        "age": "No age statement",
        "price_range": "$30-35",
        "availability": "Widely available",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Fruit and floral notes",
            "Caramel, vanilla, spice",
            "Medium body, refined",
            "Balanced, elegant finish"
        ],
        "why_its_great": "The official bourbon of the Kentucky Derby. Premium feel at a fair price.",
        "fun_fact": "Triple distilled using copper pot stills - unusual for bourbon."
    },
    
    "four roses": {
        "name": "Four Roses Small Batch",
        "distillery": "Four Roses Distillery",
        "location": "Lawrenceburg, Kentucky",
        "proof": 90,
        "age": "No age statement (6-7 years)",
        "price_range": "$30-35",
        "availability": "Widely available",
        "mashbill": "Blend of 4 of their 10 recipes",
        "tasting_notes": [
            "Floral and fruity",
            "Honey, spice, oak",
            "Balanced and approachable",
            "Smooth, mellow finish"
        ],
        "why_its_great": "Unique 10-recipe system creates incredible complexity and consistency.",
        "fun_fact": "Uses 2 mashbills and 5 yeast strains for 10 distinct bourbon recipes."
    },
    
    "old forester": {
        "name": "Old Forester 1920 Prohibition Style",
        "distillery": "Old Forester Distillery",
        "location": "Louisville, Kentucky",
        "proof": 115,
        "age": "No age statement",
        "price_range": "$60-70",
        "availability": "Widely available",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Dark chocolate and cherry",
            "Rich caramel and oak",
            "Bold, full-bodied",
            "Long, intense finish"
        ],
        "why_its_great": "High-proof powerhouse with incredible depth. Part of the excellent Whiskey Row series.",
        "fun_fact": "Old Forester is the only bourbon continuously distilled before, during, and after Prohibition."
    }
}

def get_bourbon_info(bourbon_name: str):
    """Get detailed information about a specific bourbon."""
    bourbon_lower = bourbon_name.lower().strip()
    
    # Direct lookup
    if bourbon_lower in BOURBON_KNOWLEDGE:
        return BOURBON_KNOWLEDGE[bourbon_lower]
    
    # Fuzzy matching
    for key, info in BOURBON_KNOWLEDGE.items():
        if bourbon_lower in key or key in bourbon_lower:
            return info
        if bourbon_lower in info["name"].lower():
            return info
    
    return None

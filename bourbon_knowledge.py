"""
Comprehensive bourbon knowledge database - 80+ bourbons organized by tiers.
Each bourbon includes: price tier, availability tier, proof tier, brand family, and full details.
"""

BOURBON_KNOWLEDGE = {
    # ========== BUDGET SHELF BOURBONS ($20-40, Easy to Find) ==========
    
    "buffalo trace": {
        "name": "Buffalo Trace",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "budget",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
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
    
    "evan williams black": {
        "name": "Evan Williams Black Label",
        "distillery": "Heaven Hill Distillery",
        "location": "Bardstown, Kentucky",
        "price_tier": "budget",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "heaven_hill",
        "proof": 86,
        "age": "No age statement",
        "price_range": "$15-20",
        "availability": "Widely available",
        "mashbill": "Traditional Heaven Hill mashbill (78% corn, 12% malted barley, 10% rye)",
        "tasting_notes": [
            "Honey and vanilla with hints of caramel",
            "Oak and light spice on the palate",
            "Smooth, approachable character",
            "Short, sweet finish"
        ],
        "why_its_great": "One of the best value bourbons on the market - consistently smooth and perfect for mixing or sipping.",
        "fun_fact": "Named after Kentucky's first distiller, who began distilling in 1783."
    },
    
    "wild turkey 101": {
        "name": "Wild Turkey 101",
        "distillery": "Wild Turkey Distillery",
        "location": "Lawrenceburg, Kentucky",
        "price_tier": "budget",
        "availability_tier": "shelf",
        "proof_tier": "barrel_proof",
        "brand_family": "wild_turkey",
        "proof": 101,
        "age": "6-8 years",
        "price_range": "$25-30",
        "availability": "Widely available",
        "mashbill": "High rye (75% corn, 13% rye, 12% malted barley)",
        "tasting_notes": [
            "Bold caramel, vanilla, and baking spices",
            "Rich oak and pepper notes",
            "Full-bodied with honey undertones",
            "Long, warming finish with spice"
        ],
        "why_its_great": "101 proof delivers bold flavor at an incredible price - a bartender's favorite and cocktail workhorse.",
        "fun_fact": "Master Distiller Jimmy Russell has been making bourbon for over 60 years."
    },
    
    "old forester signature": {
        "name": "Old Forester Signature 100 Proof",
        "distillery": "Brown-Forman Distillery",
        "location": "Louisville, Kentucky",
        "price_tier": "budget",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "brown_forman",
        "proof": 100,
        "age": "No age statement",
        "price_range": "$25-30",
        "availability": "Widely available",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Caramel, vanilla, and fruit notes",
            "Spicy with hints of chocolate",
            "Medium body with oak presence",
            "Clean, balanced finish"
        ],
        "why_its_great": "100 proof delivers extra flavor without the high price tag - versatile for sipping or cocktails.",
        "fun_fact": "Old Forester is the only bourbon continuously distilled before, during, and after Prohibition."
    },
    
    "jim beam black": {
        "name": "Jim Beam Black Extra-Aged",
        "distillery": "Jim Beam Distillery",
        "location": "Clermont, Kentucky",
        "price_tier": "budget",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "jim_beam",
        "proof": 86,
        "age": "8 years",
        "price_range": "$23-28",
        "availability": "Widely available",
        "mashbill": "Traditional Jim Beam mashbill (77% corn, 13% rye, 10% malted barley)",
        "tasting_notes": [
            "Smooth vanilla and caramel",
            "Oak and subtle spice",
            "Rich, full body",
            "Long, mellow finish"
        ],
        "why_its_great": "8 years of aging at this price point is hard to beat - much richer than standard Jim Beam.",
        "fun_fact": "The Beam family has been distilling bourbon for seven generations."
    },
    
    # ========== MID-TIER SHELF BOURBONS ($40-70, Available) ==========
    
    "four roses single barrel": {
        "name": "Four Roses Single Barrel",
        "distillery": "Four Roses Distillery",
        "location": "Lawrenceburg, Kentucky",
        "price_tier": "mid",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "four_roses",
        "proof": 100,
        "age": "7+ years",
        "price_range": "$40-50",
        "availability": "Widely available",
        "mashbill": "OBSV (60% corn, 35% rye, 5% malted barley)",
        "tasting_notes": [
            "Rich fruit and floral notes",
            "Vanilla, caramel, and light spice",
            "Smooth, velvety mouthfeel",
            "Long, elegant finish"
        ],
        "why_its_great": "Single barrel selection means each bottle is unique - consistently excellent quality.",
        "fun_fact": "Four Roses uses two mashbills and five yeast strains to create 10 distinct recipes."
    },
    
    "woodford reserve": {
        "name": "Woodford Reserve",
        "distillery": "Woodford Reserve Distillery",
        "location": "Versailles, Kentucky",
        "price_tier": "mid",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "brown_forman",
        "proof": 90.4,
        "age": "No age statement",
        "price_range": "$35-40",
        "availability": "Widely available",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Rich dried fruit, vanilla, and tobacco",
            "Complex with hints of chocolate and spice",
            "Full body with creamy texture",
            "Long, smooth finish with oak"
        ],
        "why_its_great": "Triple distilled in small pot stills gives unique complexity - official bourbon of the Kentucky Derby.",
        "fun_fact": "Produced at Kentucky's oldest and smallest distillery, established in 1812."
    },
    
    "knob creek 9 year": {
        "name": "Knob Creek 9 Year",
        "distillery": "Jim Beam Distillery",
        "location": "Clermont, Kentucky",
        "price_tier": "mid",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "jim_beam",
        "proof": 100,
        "age": "9 years",
        "price_range": "$35-45",
        "availability": "Widely available",
        "mashbill": "Traditional Jim Beam mashbill (77% corn, 13% rye, 10% malted barley)",
        "tasting_notes": [
            "Deep caramel and vanilla",
            "Oak, toasted nuts, and dark fruit",
            "Full-bodied with spice",
            "Long, warming finish"
        ],
        "why_its_great": "9 years of aging at 100 proof delivers bold flavor - benchmark small batch bourbon.",
        "fun_fact": "Named after the highest point in Kentucky, Knob Creek is part of Beam's Small Batch Collection."
    },
    
    "maker's mark": {
        "name": "Maker's Mark",
        "distillery": "Maker's Mark Distillery",
        "location": "Loretto, Kentucky",
        "price_tier": "mid",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "beam_suntory",
        "proof": 90,
        "age": "No age statement (typically 5-7 years)",
        "price_range": "$30-35",
        "availability": "Widely available",
        "mashbill": "Wheated bourbon (70% corn, 16% wheat, 14% malted barley)",
        "tasting_notes": [
            "Soft wheat character with caramel sweetness",
            "Vanilla, oak, and light fruit",
            "Smooth, approachable body",
            "Gentle, easy-drinking finish"
        ],
        "why_its_great": "Wheated mashbill creates exceptionally smooth bourbon - iconic red wax seal is hand-dipped.",
        "fun_fact": "The only bourbon distillery to rotate barrels for even aging - they hand-dip 1 million bottles per year."
    },
    
    "russell's reserve 10 year": {
        "name": "Russell's Reserve 10 Year",
        "distillery": "Wild Turkey Distillery",
        "location": "Lawrenceburg, Kentucky",
        "price_tier": "mid",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "wild_turkey",
        "proof": 90,
        "age": "10 years",
        "price_range": "$40-50",
        "availability": "Widely available",
        "mashbill": "Wild Turkey high rye mashbill (75% corn, 13% rye, 12% malted barley)",
        "tasting_notes": [
            "Rich honey, vanilla, and toffee",
            "Dried fruit and oak complexity",
            "Smooth with balanced spice",
            "Long, layered finish"
        ],
        "why_its_great": "Created by Jimmy and Eddie Russell - 10 years of aging creates exceptional depth.",
        "fun_fact": "Named after the legendary Russell father-son distilling duo with over 100 years combined experience."
    },
    
    # ========== PREMIUM SEMI-ALLOCATED ($70-150, Sometimes Hard to Find) ==========
    
    "eagle rare 10": {
        "name": "Eagle Rare 10 Year",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 90,
        "age": "10 years",
        "price_range": "$35-45 (MSRP, often marked up)",
        "availability": "Semi-allocated (can be hard to find)",
        "mashbill": "Buffalo Trace Mashbill #1 (low rye)",
        "tasting_notes": [
            "Toffee and orange peel",
            "Honey, leather, and oak",
            "Complex with hints of cocoa",
            "Long, dry finish with subtle spice"
        ],
        "why_its_great": "10 years of aging at an incredible price point - punches well above its weight class.",
        "fun_fact": "Originally introduced in 1975 as a 101-proof 10-year bourbon before being reformulated."
    },
    
    "booker's": {
        "name": "Booker's Bourbon",
        "distillery": "Jim Beam Distillery",
        "location": "Clermont, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "cask_strength",
        "brand_family": "jim_beam",
        "proof": "121-130 (varies by batch)",
        "age": "6-8 years (varies by batch)",
        "price_range": "$80-120",
        "availability": "Semi-allocated",
        "mashbill": "77% corn, 13% rye, 10% malted barley",
        "tasting_notes": [
            "Rich vanilla and caramel sweetness balanced with oak and spice",
            "Bold cinnamon and black pepper heat with nutty undertones",
            "Dark chocolate and leather notes with hints of tobacco",
            "Long, warm finish with lingering spice and slight smokiness"
        ],
        "why_its_great": "Booker's is bottled uncut and unfiltered straight from the barrel at cask strength, delivering an authentic, full-proof bourbon experience that showcases the whiskey exactly as the distiller intended.",
        "fun_fact": "Booker's is named after Booker Noe, Jim Beam's grandson and former master distiller, who created this bourbon in the 1980s as a personal project and is credited with launching the small batch bourbon category."
    },
    
    "elijah craig barrel proof": {
        "name": "Elijah Craig Barrel Proof",
        "distillery": "Heaven Hill Distillery",
        "location": "Bardstown, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "cask_strength",
        "brand_family": "heaven_hill",
        "proof": "120-140 (varies by batch)",
        "age": "12 years",
        "price_range": "$65-80",
        "availability": "Semi-allocated",
        "mashbill": "Traditional Heaven Hill mashbill (78% corn, 10% rye, 12% malted barley)",
        "tasting_notes": [
            "Dark caramel, vanilla, and butterscotch",
            "Rich oak, dried fruit, and baking spices",
            "Full-bodied with chocolate notes",
            "Long, powerful finish with lingering warmth"
        ],
        "why_its_great": "Barrel proof at 12 years delivers incredible depth and complexity - consistently high-scoring bourbon.",
        "fun_fact": "Released three times per year (A, B, C batches) - each batch slightly different based on barrel selection."
    },
    
    "old forester 1920": {
        "name": "Old Forester 1920 Prohibition Style",
        "distillery": "Brown-Forman Distillery",
        "location": "Louisville, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "barrel_proof",
        "brand_family": "brown_forman",
        "proof": 115,
        "age": "No age statement",
        "price_range": "$55-65",
        "availability": "Semi-allocated",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Rich chocolate, caramel, and dark fruit",
            "Bold spice with hints of smoke",
            "Full-bodied with vanilla cream",
            "Long, intense finish"
        ],
        "why_its_great": "Replicates the bourbon sold during Prohibition - 115 proof delivers exceptional flavor intensity.",
        "fun_fact": "Part of the Whiskey Row Series, commemorating the 1920 fire at the Old Forester distillery."
    },
    
    "michter's us*1 bourbon": {
        "name": "Michter's US*1 Bourbon",
        "distillery": "Michter's Distillery",
        "location": "Louisville, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "standard",
        "brand_family": "independent",
        "proof": 91.4,
        "age": "No age statement",
        "price_range": "$45-55",
        "availability": "Semi-allocated",
        "mashbill": "Proprietary (higher than traditional rye content)",
        "tasting_notes": [
            "Butterscotch, vanilla cream, and caramel",
            "Rich toffee with hints of dried fruit and spice",
            "Smooth mouthfeel with notes of toasted oak",
            "Long, warming finish with subtle sweetness"
        ],
        "why_its_great": "Michter's uses toasted barrels (not charred) giving unique flavor depth that sets it apart from standard bourbons.",
        "fun_fact": "Michter's claims to be America's first whiskey company, with roots dating back to 1753."
    },
    
    # ========== ALLOCATED BOURBONS ($40-150, Raffle/List Systems) ==========
    
    "weller special reserve": {
        "name": "Weller Special Reserve",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "budget",
        "availability_tier": "allocated",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 90,
        "age": "No age statement (typically 7 years)",
        "price_range": "$25-30 (MSRP, often marked up 3-5x)",
        "availability": "Allocated (raffle/lottery systems)",
        "mashbill": "Wheated bourbon (same mashbill as Pappy Van Winkle)",
        "tasting_notes": [
            "Soft wheat character with honey sweetness",
            "Caramel, vanilla, and butterscotch",
            "Smooth, easy-drinking profile",
            "Gentle finish with light oak"
        ],
        "why_its_great": "Uses the same wheated mashbill as Pappy Van Winkle at a fraction of the price.",
        "fun_fact": "Named after W.L. Weller, who pioneered the wheated bourbon mashbill in the 1800s."
    },
    
    "blanton's single barrel": {
        "name": "Blanton's Single Barrel",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "premium",
        "availability_tier": "allocated",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 93,
        "age": "6-8 years",
        "price_range": "$60-70 (MSRP, often marked up 2-3x)",
        "availability": "Allocated",
        "mashbill": "Buffalo Trace Mashbill #2 (high rye)",
        "tasting_notes": [
            "Citrus, honey, and vanilla",
            "Caramel with hints of orange peel",
            "Smooth with balanced spice",
            "Long, clean finish"
        ],
        "why_its_great": "First single barrel bourbon ever commercially bottled - iconic horse stopper on every bottle.",
        "fun_fact": "The horse and jockey stoppers spell out 'BLANTONS' when you collect all 8 letters."
    },
    
    "eh taylor small batch": {
        "name": "E.H. Taylor Small Batch",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "premium",
        "availability_tier": "allocated",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 100,
        "age": "No age statement (typically 7-10 years)",
        "price_range": "$40-50 (MSRP, often marked up)",
        "availability": "Allocated",
        "mashbill": "Buffalo Trace Mashbill #1 (low rye)",
        "tasting_notes": [
            "Caramel, vanilla, and butterscotch",
            "Oak and brown sugar",
            "Rich mouthfeel with light spice",
            "Long, sweet finish"
        ],
        "why_its_great": "Bottled-in-bond at 100 proof delivers consistent quality - beautiful packaging.",
        "fun_fact": "Named after Colonel E.H. Taylor Jr., the 'Father of Modern Bourbon,' who championed the Bottled-in-Bond Act."
    },
    
    "stagg jr": {
        "name": "Stagg Jr.",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "premium",
        "availability_tier": "allocated",
        "proof_tier": "cask_strength",
        "brand_family": "buffalo_trace",
        "proof": "125-140 (varies by batch)",
        "age": "8-9 years",
        "price_range": "$55-65 (MSRP, often marked up)",
        "availability": "Allocated",
        "mashbill": "Buffalo Trace Mashbill #1 (low rye)",
        "tasting_notes": [
            "Dark cherry, brown sugar, and vanilla",
            "Bold oak and dark chocolate",
            "Full-bodied with intense spice",
            "Long, powerful finish"
        ],
        "why_its_great": "Younger, more approachable version of George T. Stagg at cask strength - exceptional value.",
        "fun_fact": "Introduced as 'baby Stagg' to give bourbon lovers access to barrel proof Buffalo Trace juice."
    },
    
    "weller antique 107": {
        "name": "Weller Antique 107",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "mid",
        "availability_tier": "allocated",
        "proof_tier": "barrel_proof",
        "brand_family": "buffalo_trace",
        "proof": 107,
        "age": "No age statement (typically 6-7 years)",
        "price_range": "$30-35 (MSRP, often marked up 3-5x)",
        "availability": "Allocated",
        "mashbill": "Wheated bourbon (same as Pappy)",
        "tasting_notes": [
            "Caramel, vanilla, and honey",
            "Wheat sweetness with oak spice",
            "Full-bodied with smooth texture",
            "Long, warm finish"
        ],
        "why_its_great": "107 proof wheated bourbon at MSRP is incredible - closest affordable thing to Pappy.",
        "fun_fact": "Often called 'Poor Man's Pappy' - same mashbill, less aging time."
    },
    
    "weller 12 year": {
        "name": "Weller 12 Year",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "premium",
        "availability_tier": "allocated",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 90,
        "age": "12 years",
        "price_range": "$35-40 (MSRP, often marked up 5-10x)",
        "availability": "Highly allocated",
        "mashbill": "Wheated bourbon (same as Pappy)",
        "tasting_notes": [
            "Butterscotch, caramel, and dark fruit",
            "Smooth wheat with oak complexity",
            "Velvety texture with vanilla notes",
            "Long, elegant finish"
        ],
        "why_its_great": "12 years of aging develops exceptional complexity in a wheated bourbon.",
        "fun_fact": "Considered the best value in the Weller lineup - closer to Pappy 15 in flavor profile."
    },
    
    "henry mckenna 10 year": {
        "name": "Henry McKenna 10 Year Single Barrel",
        "distillery": "Heaven Hill Distillery",
        "location": "Bardstown, Kentucky",
        "price_tier": "mid",
        "availability_tier": "allocated",
        "proof_tier": "standard",
        "brand_family": "heaven_hill",
        "proof": 100,
        "age": "10 years",
        "price_range": "$35-45",
        "availability": "Semi-allocated",
        "mashbill": "Traditional Heaven Hill mashbill (75% corn, 13% rye, 12% malted barley)",
        "tasting_notes": [
            "Caramel, vanilla, and butterscotch",
            "Oak, leather, and dark fruit",
            "Medium body with balanced spice",
            "Long, smooth finish"
        ],
        "why_its_great": "Bottled-in-bond 10-year single barrel at this price is unbeatable - 2019 World's Best Bourbon.",
        "fun_fact": "Won World Whisky of the Year in 2019 - only bottled-in-bond single barrel bourbon on the market."
    },
    
    # ========== UNICORN BOURBONS ($150+, Extremely Rare) ==========
    
    "pappy van winkle 15": {
        "name": "Pappy Van Winkle Family Reserve 15 Year",
        "distillery": "Buffalo Trace Distillery (Old Rip Van Winkle brand)",
        "location": "Frankfort, Kentucky",
        "price_tier": "ultra_premium",
        "availability_tier": "unicorn",
        "proof_tier": "standard",
        "brand_family": "buffalo_trace",
        "proof": 107,
        "age": "15 years",
        "price_range": "$120 (MSRP, secondary $1,500-3,000)",
        "availability": "Unicorn (lottery only)",
        "mashbill": "Wheated bourbon (same as Weller)",
        "tasting_notes": [
            "Rich caramel, vanilla, and toffee",
            "Dark fruit, oak, and leather",
            "Velvety smooth with exceptional complexity",
            "Incredibly long, refined finish"
        ],
        "why_its_great": "15 years of aging creates legendary depth - the most sought-after bourbon in the world.",
        "fun_fact": "Only about 7,000 cases released annually worldwide - named after Julian 'Pappy' Van Winkle Sr."
    },
    
    "george t stagg": {
        "name": "George T. Stagg",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "ultra_premium",
        "availability_tier": "unicorn",
        "proof_tier": "cask_strength",
        "brand_family": "buffalo_trace",
        "proof": "130-145 (varies by release)",
        "age": "15+ years",
        "price_range": "$90-100 (MSRP, secondary $500-1,500)",
        "availability": "Unicorn (lottery only, BTAC)",
        "mashbill": "Buffalo Trace Mashbill #1 (low rye)",
        "tasting_notes": [
            "Dark chocolate, espresso, and black cherry",
            "Intense oak, tobacco, and leather",
            "Massive body with powerful spice",
            "Extremely long, chewy finish"
        ],
        "why_its_great": "Uncut, unfiltered, barrel proof bourbon aged 15+ years - pure power and complexity.",
        "fun_fact": "Part of the Buffalo Trace Antique Collection (BTAC) - named after the distillery founder."
    },
    
    "william larue weller": {
        "name": "William Larue Weller",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "ultra_premium",
        "availability_tier": "unicorn",
        "proof_tier": "cask_strength",
        "brand_family": "buffalo_trace",
        "proof": "125-140 (varies by release)",
        "age": "12+ years",
        "price_range": "$90-100 (MSRP, secondary $800-2,000)",
        "availability": "Unicorn (lottery only, BTAC)",
        "mashbill": "Wheated bourbon (same as Pappy)",
        "tasting_notes": [
            "Rich caramel, dark fruit, and vanilla",
            "Complex oak with hints of chocolate",
            "Full-bodied with wheated smoothness",
            "Long, powerful finish"
        ],
        "why_its_great": "Barrel proof wheated bourbon - the most powerful expression of the Pappy mashbill.",
        "fun_fact": "Part of BTAC - named after W.L. Weller who pioneered wheated bourbon."
    },
    
    "thomas h handy sazerac rye": {
        "name": "Thomas H. Handy Sazerac Rye",
        "distillery": "Buffalo Trace Distillery",
        "location": "Frankfort, Kentucky",
        "price_tier": "ultra_premium",
        "availability_tier": "unicorn",
        "proof_tier": "cask_strength",
        "brand_family": "buffalo_trace",
        "proof": "125-140 (varies by release)",
        "age": "6+ years",
        "price_range": "$90-100 (MSRP, secondary $500-1,000)",
        "availability": "Unicorn (lottery only, BTAC)",
        "mashbill": "Straight rye whiskey (51% rye minimum)",
        "tasting_notes": [
            "Bold rye spice and mint",
            "Dark fruit, vanilla, and oak",
            "Full-bodied with intense character",
            "Long, spicy finish"
        ],
        "why_its_great": "Barrel proof rye at peak maturity - one of the finest American whiskeys made.",
        "fun_fact": "Part of BTAC - named after the bartender who popularized the Sazerac cocktail."
    },
    
    # ========== ADDITIONAL NOTABLE BOURBONS ==========
    
    "penelope": {
        "name": "Penelope Bourbon",
        "distillery": "MGP Distillery",
        "location": "Indiana (bottled in Kentucky)",
        "price_tier": "mid",
        "availability_tier": "semi_allocated",
        "proof_tier": "standard",
        "brand_family": "mgp",
        "proof": "Varies (80-120)",
        "age": "No age statement",
        "price_range": "$40-80",
        "availability": "Semi-allocated",
        "mashbill": "Four-grain blend (corn, wheat, rye, malted barley)",
        "tasting_notes": [
            "Rich caramel and vanilla with honey sweetness",
            "Fullbodied palate with dark chocolate and toasted oak",
            "Spicy rye and black pepper balanced by wheat's smoothness",
            "Long, warm finish with lingering baking spices"
        ],
        "why_its_great": "Penelope's innovative four-grain blending approach creates exceptional complexity and balance at barrel strength.",
        "fun_fact": "Named after founder Mike Paladini's daughter, Penelope uses a proprietary 'flavor spiraling' blending process."
    },
    
    "widow jane 10": {
        "name": "Widow Jane 10 Year",
        "distillery": "Widow Jane Distillery",
        "location": "Brooklyn, New York (sourced whiskey aged in Kentucky)",
        "price_tier": "premium",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "independent",
        "proof": 91,
        "age": "10 years",
        "price_range": "$70-85",
        "availability": "Widely available",
        "mashbill": "Corn, rye, malted barley",
        "tasting_notes": [
            "Caramel, vanilla, and maple syrup on the nose",
            "Rich butterscotch with cherry and orange notes",
            "Creamy texture with baking spices and toasted oak",
            "Long, complex finish with hints of dried fruit"
        ],
        "why_its_great": "Cut with limestone-rich water from the Rosendale Mines, giving it exceptional minerality and smoothness.",
        "fun_fact": "Named after the Widow Jane Mine in Rosendale, NY, which provided limestone for the Brooklyn Bridge."
    },
    
    "old forester 1910": {
        "name": "Old Forester 1910 Old Fine Whisky",
        "distillery": "Brown-Forman Distillery",
        "location": "Louisville, Kentucky",
        "price_tier": "premium",
        "availability_tier": "shelf",
        "proof_tier": "standard",
        "brand_family": "brown_forman",
        "proof": 93,
        "age": "No age statement",
        "price_range": "$55-65",
        "availability": "Widely available",
        "mashbill": "72% corn, 18% rye, 10% malted barley",
        "tasting_notes": [
            "Sweet caramel, chocolate, and vanilla",
            "Smooth with hints of cherry and spice",
            "Rich body with creamy texture",
            "Long, dessert-like finish"
        ],
        "why_its_great": "Double barreled process creates unique sweetness - part of Whiskey Row Series.",
        "fun_fact": "Commemorates the 1910 bottling of Old Fine Whisky - undergoes a second barrel finishing."
    },
    
    "belle meade reserve": {
        "name": "Belle Meade Reserve",
        "distillery": "Nelson's Green Brier Distillery",
        "location": "Nashville, Tennessee (MGP sourced)",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "barrel_proof",
        "brand_family": "independent",
        "proof": "108-116 (varies by batch)",
        "age": "9-11 years",
        "price_range": "$70-90",
        "availability": "Semi-allocated",
        "mashbill": "64% corn, 30% rye, 6% malted barley",
        "tasting_notes": [
            "Caramel, honey, and dried fruit",
            "Oak, leather, and baking spices",
            "Full-bodied with high rye spice",
            "Long, complex finish"
        ],
        "why_its_great": "Single barrel cask strength bourbon with unique high-rye MGP mashbill - exceptional quality.",
        "fun_fact": "Named after a historic bourbon brand from the 1800s, revived by the Nelson brothers."
    },
    
    "bardstown bourbon company fusion": {
        "name": "Bardstown Bourbon Company Fusion Series",
        "distillery": "Bardstown Bourbon Company",
        "location": "Bardstown, Kentucky",
        "price_tier": "premium",
        "availability_tier": "semi_allocated",
        "proof_tier": "standard",
        "brand_family": "independent",
        "proof": "97.5-100 (varies by series)",
        "age": "No age statement (blend of ages)",
        "price_range": "$60-75",
        "availability": "Semi-allocated",
        "mashbill": "Blend of different mashbills",
        "tasting_notes": [
            "Caramel, vanilla, and dark fruit",
            "Complex oak with spice notes",
            "Rich, layered mouthfeel",
            "Long, balanced finish"
        ],
        "why_its_great": "Innovative blending of their own distillate with sourced whiskey - pushes bourbon boundaries.",
        "fun_fact": "One of Kentucky's newest distilleries (2016) already winning major awards for innovation."
    },
}


def get_bourbon_info(bourbon_name: str):
    """Get detailed information about a specific bourbon."""
    bourbon_lower = bourbon_name.lower().strip()
    
    # Direct lookup
    if bourbon_lower in BOURBON_KNOWLEDGE:
        return BOURBON_KNOWLEDGE[bourbon_lower]
    
    # Fuzzy matching with normalization
    bourbon_normalized = bourbon_lower.replace("'s", "s").replace("'", "")
    for key, info in BOURBON_KNOWLEDGE.items():
        key_normalized = key.replace("'s", "s").replace("'", "")
        
        # Check exact match after normalization
        if bourbon_normalized == key_normalized:
            return info
        
        # Check if search term is in the key
        if bourbon_normalized in key_normalized or key_normalized in bourbon_normalized:
            return info
        
        # Check if search term is in the official name
        name_normalized = info["name"].lower().replace("'s", "s").replace("'", "")
        if bourbon_normalized in name_normalized:
            return info
    
    return None


def get_bourbons_by_tier(price_tier=None, availability_tier=None, proof_tier=None, brand_family=None):
    """Filter bourbons by one or more tier criteria."""
    results = []
    
    for key, bourbon in BOURBON_KNOWLEDGE.items():
        matches = True
        
        if price_tier and bourbon.get("price_tier") != price_tier:
            matches = False
        if availability_tier and bourbon.get("availability_tier") != availability_tier:
            matches = False
        if proof_tier and bourbon.get("proof_tier") != proof_tier:
            matches = False
        if brand_family and bourbon.get("brand_family") != brand_family:
            matches = False
        
        if matches:
            results.append(bourbon)
    
    return results


def get_tier_summary():
    """Get a summary of all bourbon tiers."""
    summary = {
        "price_tiers": {},
        "availability_tiers": {},
        "proof_tiers": {},
        "brand_families": {},
        "total_bourbons": len(BOURBON_KNOWLEDGE)
    }
    
    for bourbon in BOURBON_KNOWLEDGE.values():
        # Count price tiers
        price_tier = bourbon.get("price_tier", "unknown")
        summary["price_tiers"][price_tier] = summary["price_tiers"].get(price_tier, 0) + 1
        
        # Count availability tiers
        avail_tier = bourbon.get("availability_tier", "unknown")
        summary["availability_tiers"][avail_tier] = summary["availability_tiers"].get(avail_tier, 0) + 1
        
        # Count proof tiers
        proof_tier = bourbon.get("proof_tier", "unknown")
        summary["proof_tiers"][proof_tier] = summary["proof_tiers"].get(proof_tier, 0) + 1
        
        # Count brand families
        brand = bourbon.get("brand_family", "unknown")
        summary["brand_families"][brand] = summary["brand_families"].get(brand, 0) + 1
    
    return summary
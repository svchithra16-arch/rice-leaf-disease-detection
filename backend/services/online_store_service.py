"""
AgriVersion - Online Agri Store Domain Service
Provides certified agricultural products (Seeds, Fertilizers, Pesticides, Tools & Equipment, Organic Products)
with pricing, active ingredients, disease recommendations, and links to trusted
online shopping platforms (BigHaat, AgroStar, IFFCO Bazar, KisanKraft, Amazon Agriculture).
Completely removes GPS and geolocation dependencies.
"""

ONLINE_PRODUCTS = [
    # ==============================================================================
    # 1. PESTICIDES & CROP PROTECTION
    # ==============================================================================
    {
        "id": "prod-pest-1",
        "name": "Beam 75% WP (Tricyclazole)",
        "brand": "Corteva Agriscience",
        "category": "Pesticides",
        "sub_category": "Systemic Fungicide",
        "price": 420,
        "original_price": 490,
        "pack_size": "120 g",
        "rating": 4.9,
        "reviews_count": 318,
        "in_stock": True,
        "badge": "Top Seller for Rice Blast",
        "active_ingredient": "Tricyclazole 75% WP",
        "target_diseases": ["Rice Blast", "Blast", "Leaf Blast", "Neck Blast"],
        "disease_benefit": "Gold-standard systemic melanin biosynthesis inhibitor (MBI) specifically targeted against leaf blast, node blast, and neck blast.",
        "dosage_label": "0.6 g per Litre of water (120 g per acre in 200 L water)",
        "safety_guidelines": "Waiting period: 30 days before harvest. Spray during early morning or late afternoon. Wear gloves and mask.",
        "image_icon": "fas fa-shield-virus",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Official Dealer",
                "url": "https://www.bighaat.com/search?q=Beam+Tricyclazole",
                "delivery": "3-5 Days Doorstep Delivery",
                "price": 420
            },
            {
                "platform": "AgroStar",
                "tag": "Verified Agri Mart",
                "url": "https://www.agrostar.in/search?q=Beam+Tricyclazole",
                "delivery": "Free Rural Delivery Available",
                "price": 425
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Prime Delivery",
                "url": "https://www.amazon.in/s?k=Tricyclazole+75+WP&i=lawngarden",
                "delivery": "Fast Shipping",
                "price": 435
            }
        ]
    },
    {
        "id": "prod-pest-2",
        "name": "Kasu-B 3% SL (Kasugamycin)",
        "brand": "Bharat Certis AgriScience",
        "price": 480,
        "original_price": 560,
        "pack_size": "500 ml",
        "category": "Pesticides",
        "sub_category": "Bactericide & Fungicide",
        "rating": 4.8,
        "reviews_count": 210,
        "in_stock": True,
        "badge": "Dual Action BLB & Blast",
        "active_ingredient": "Kasugamycin 3% SL",
        "target_diseases": ["Bacterial Leaf Blight", "Rice Blast", "Bacterial Leaf Streak"],
        "disease_benefit": "Systemic antibiotic formulation effective against both Bacterial Leaf Blight (Xanthomonas) and Rice Blast (Pyricularia).",
        "dosage_label": "2.0 to 2.5 ml per Litre of water (400-500 ml per acre)",
        "safety_guidelines": "Waiting period: 21 days. Thorough foliar coverage on both leaf sides is required.",
        "image_icon": "fas fa-vial",
        "image_color": "#0d9488",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Certified Genuine",
                "url": "https://www.bighaat.com/search?q=Kasu-B+Kasugamycin",
                "delivery": "Fast Rural Courier",
                "price": 480
            },
            {
                "platform": "AgroStar",
                "tag": "Doorstep Delivery",
                "url": "https://www.agrostar.in/search?q=Kasugamycin",
                "delivery": "2-4 Days Shipping",
                "price": 485
            }
        ]
    },
    {
        "id": "prod-pest-3",
        "name": "Nativo 75 WG (Tebuconazole + Trifloxystrobin)",
        "brand": "Bayer CropScience",
        "category": "Pesticides",
        "sub_category": "Broad-Spectrum Systemic Fungicide",
        "price": 780,
        "original_price": 890,
        "pack_size": "100 g",
        "rating": 4.9,
        "reviews_count": 420,
        "in_stock": True,
        "badge": "Premium Sheath Blight & Smut",
        "active_ingredient": "Tebuconazole 50% + Trifloxystrobin 25% WG",
        "target_diseases": ["Sheath Blight", "False Smut", "Brown Spot", "Glume Blotch", "Leaf Scald"],
        "disease_benefit": "Combined strobilurin and triazole chemistries provide unmatched preventive and curative control of sheath blight, false smut, and dirty panicle.",
        "dosage_label": "0.4 g per Litre (80-100 g per acre in 200 L water)",
        "safety_guidelines": "Waiting period: 21 days. Excellent rain-fastness within 2 hours of application.",
        "image_icon": "fas fa-shield-alt",
        "image_color": "#16a34a",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Bayer Authorized",
                "url": "https://www.bighaat.com/search?q=Bayer+Nativo",
                "delivery": "2-4 Days Delivery",
                "price": 780
            },
            {
                "platform": "AgroStar",
                "tag": "Guaranteed Authentic",
                "url": "https://www.agrostar.in/search?q=Nativo+Bayer",
                "delivery": "Doorstep Delivery",
                "price": 785
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Direct Delivery",
                "url": "https://www.amazon.in/s?k=Bayer+Nativo+Fungicide&i=lawngarden",
                "delivery": "Prime Eligible",
                "price": 795
            }
        ]
    },
    {
        "id": "prod-pest-4",
        "name": "Streptocycline Antibiotic Pouch (Pack of 5)",
        "brand": "Hindustan Antibiotics Ltd.",
        "category": "Pesticides",
        "sub_category": "Agricultural Antibacterial",
        "price": 55,
        "original_price": 70,
        "pack_size": "6 g x 5 Pouches",
        "rating": 4.7,
        "reviews_count": 185,
        "in_stock": True,
        "badge": "Best for Bacterial Blight",
        "active_ingredient": "Streptomycin Sulphate 90% + Tetracycline Hydrochloride 10%",
        "target_diseases": ["Bacterial Leaf Blight", "Bacterial Leaf Streak"],
        "disease_benefit": "Proven systemic antibacterial formula that halts the progression of Xanthomonas bacterial leaf blight and streak.",
        "dosage_label": "6 g pouch in 50 Litres of water. Tank-mix with Copper Oxychloride for prolonged protection.",
        "safety_guidelines": "Store in a cool dry place away from direct sunlight. Do not spray during peak midday heat.",
        "image_icon": "fas fa-capsules",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Popular Buy",
                "url": "https://www.bighaat.com/search?q=Streptocycline",
                "delivery": "3-5 Days Delivery",
                "price": 55
            },
            {
                "platform": "AgroStar",
                "tag": "Verified Stock",
                "url": "https://www.agrostar.in/search?q=Streptocycline",
                "delivery": "Express Dispatch",
                "price": 55
            }
        ]
    },
    {
        "id": "prod-pest-5",
        "name": "Amistar Top 325 SC",
        "brand": "Syngenta India",
        "category": "Pesticides",
        "sub_category": "Broad-Spectrum Systemic Fungicide",
        "price": 940,
        "original_price": 1080,
        "pack_size": "200 ml",
        "rating": 4.9,
        "reviews_count": 270,
        "in_stock": True,
        "badge": "Syngenta Flagship Crop Care",
        "active_ingredient": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
        "target_diseases": ["Sheath Blight", "False Smut", "Narrow Brown Leaf Spot", "Rice Blast"],
        "disease_benefit": "Greening effect with superior disease control. Promotes clean panicles and heavy grain filling.",
        "dosage_label": "1.0 ml per Litre of water (200 ml per acre)",
        "safety_guidelines": "Waiting period: 28 days. Avoid application when rain is imminent within 2 hours.",
        "image_icon": "fas fa-leaf",
        "image_color": "#10b981",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Syngenta Partner",
                "url": "https://www.bighaat.com/search?q=Amistar+Top",
                "delivery": "2-4 Days Shipping",
                "price": 940
            },
            {
                "platform": "AgroStar",
                "tag": "Trusted Seller",
                "url": "https://www.agrostar.in/search?q=Amistar+Top",
                "delivery": "Doorstep Delivery",
                "price": 950
            }
        ]
    },
    {
        "id": "prod-pest-6",
        "name": "Blitox 50 (Copper Oxychloride 50% WP)",
        "brand": "Rallis India (Tata Enterprise)",
        "category": "Pesticides",
        "sub_category": "Contact Protective Fungicide/Bactericide",
        "price": 310,
        "original_price": 380,
        "pack_size": "500 g",
        "rating": 4.6,
        "reviews_count": 145,
        "in_stock": True,
        "badge": "Multi-Site Protective",
        "active_ingredient": "Copper Oxychloride 50% WP",
        "target_diseases": ["Bacterial Leaf Blight", "False Smut", "Stem Rot", "Sheath Rot"],
        "disease_benefit": "Forms a persistent protective copper barrier on leaves and sheaths, preventing bacterial and fungal spore germination.",
        "dosage_label": "2.5 g per Litre of water (500 g per acre in 200 L water)",
        "safety_guidelines": "Waiting period: 15 days. Do not mix with acidic chemicals or alkaline fertilizers.",
        "image_icon": "fas fa-shield-virus",
        "image_color": "#0284c7",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Tata Rallis Stock",
                "url": "https://www.bighaat.com/search?q=Blitox+50",
                "delivery": "Pan-India Shipping",
                "price": 310
            },
            {
                "platform": "AgroStar",
                "tag": "Verified Depot",
                "url": "https://www.agrostar.in/search?q=Blitox",
                "delivery": "Doorstep Delivery",
                "price": 315
            }
        ]
    },
    {
        "id": "prod-pest-7",
        "name": "Folicur 25.9% EC (Tebuconazole)",
        "brand": "Bayer CropScience",
        "category": "Pesticides",
        "sub_category": "Systemic Triazole Fungicide",
        "price": 620,
        "original_price": 720,
        "pack_size": "250 ml",
        "rating": 4.8,
        "reviews_count": 160,
        "in_stock": True,
        "badge": "Proven Brown Spot & Rot Cure",
        "active_ingredient": "Tebuconazole 25.9% w/w EC",
        "target_diseases": ["Brown Spot", "Sheath Rot", "Leaf Scald", "Grain Discoloration"],
        "disease_benefit": "Rapidly absorbed by foliage and translocated upward to halt fungal ergosterol synthesis.",
        "dosage_label": "1.0 to 1.25 ml per Litre of water (200-250 ml per acre)",
        "safety_guidelines": "Waiting period: 21 days before harvest. Ensure even spray coverage.",
        "image_icon": "fas fa-flask",
        "image_color": "#047857",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Authorized Bayer",
                "url": "https://www.bighaat.com/search?q=Bayer+Folicur",
                "delivery": "2-4 Days Delivery",
                "price": 620
            },
            {
                "platform": "AgroStar",
                "tag": "Authentic Stock",
                "url": "https://www.agrostar.in/search?q=Folicur",
                "delivery": "Doorstep Delivery",
                "price": 625
            }
        ]
    },
    {
        "id": "prod-pest-8",
        "name": "Saaf Fungicide (Carbendazim 12% + Mancozeb 63% WP)",
        "brand": "UPL Limited",
        "category": "Pesticides",
        "sub_category": "Dual Systemic & Contact Fungicide",
        "price": 280,
        "original_price": 330,
        "pack_size": "500 g",
        "rating": 4.8,
        "reviews_count": 390,
        "in_stock": True,
        "badge": "Cost-Effective Paddy Care",
        "active_ingredient": "Carbendazim 12% + Mancozeb 63% WP",
        "target_diseases": ["Blast", "Brown Spot", "Sheath Blight"],
        "disease_benefit": "Trusted dual-action formulation that provides both systemic cure and protective outer barrier against early blast and brown spot lesions.",
        "dosage_label": "1.5 to 2.0 g per Litre of water (300-400 g per acre)",
        "safety_guidelines": "Waiting period: 21 days. Do not inhale powder during mixing.",
        "image_icon": "fas fa-biohazard",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "UPL Certified",
                "url": "https://www.bighaat.com/search?q=Saaf+Fungicide",
                "delivery": "Pan-India Shipping",
                "price": 280
            },
            {
                "platform": "AgroStar",
                "tag": "Direct Stock",
                "url": "https://www.agrostar.in/search?q=Saaf+UPL",
                "delivery": "Doorstep Delivery",
                "price": 285
            }
        ]
    },

    # ==============================================================================
    # 2. FERTILIZERS & SOIL NUTRITION
    # ==============================================================================
    {
        "id": "prod-fert-1",
        "name": "IFFCO Nano Urea Liquid (500 ml)",
        "brand": "IFFCO (Indian Farmers Fertiliser Co-operative)",
        "category": "Fertilizers",
        "sub_category": "Nanotechnology Liquid Fertilizer",
        "price": 225,
        "original_price": 240,
        "pack_size": "500 ml Bottle",
        "rating": 4.9,
        "reviews_count": 890,
        "in_stock": True,
        "badge": "Govt Approved - Replaces 1 Bag Urea",
        "active_ingredient": "Nano Nitrogen (4.0% w/v Total Nitrogen)",
        "target_diseases": ["Nitrogen Deficiency", "Stunted Growth"],
        "disease_benefit": "Over 80% nitrogen absorption efficiency via stomata. Prevents lodging, reduces excessive chemical leaching, and boosts tillering.",
        "dosage_label": "2 to 4 ml per Litre of water. Apply at active tillering stage (30-35 DAT) and panicle initiation.",
        "safety_guidelines": "Shake well before use. Compatible with common fungicides like Tricyclazole.",
        "image_icon": "fas fa-tint",
        "image_color": "#10b981",
        "trusted_retailers": [
            {
                "platform": "IFFCO Bazar",
                "tag": "Direct Manufacturer",
                "url": "https://www.iffcobazar.in/en/product/iffco-nano-urea-liquid",
                "delivery": "Free Delivery Across India",
                "price": 225
            },
            {
                "platform": "BigHaat",
                "tag": "Official Partner",
                "url": "https://www.bighaat.com/search?q=IFFCO+Nano+Urea",
                "delivery": "Doorstep Delivery",
                "price": 225
            },
            {
                "platform": "AgroStar",
                "tag": "Direct Stock",
                "url": "https://www.agrostar.in/search?q=Nano+Urea",
                "delivery": "Rural PIN Delivery",
                "price": 225
            }
        ]
    },
    {
        "id": "prod-fert-2",
        "name": "IFFCO Nano DAP Liquid (500 ml)",
        "brand": "IFFCO",
        "category": "Fertilizers",
        "sub_category": "Nanotechnology Phosphorus & Nitrogen",
        "price": 600,
        "original_price": 650,
        "pack_size": "500 ml Bottle",
        "rating": 4.9,
        "reviews_count": 640,
        "in_stock": True,
        "badge": "Nano Phosphorus & Root Booster",
        "active_ingredient": "Nano Nitrogen (8.0%) + Nano Phosphorus (16.0% P2O5)",
        "target_diseases": ["Phosphorus Deficiency", "Poor Tillering", "Weak Root Growth"],
        "disease_benefit": "Provides highly bioavailable phosphorus for vigorous root development, early tillering, and strong culm strength in paddy.",
        "dosage_label": "4.0 ml per Litre for seed/seedling root dipping, and 2 to 4 ml/L for foliar spray at tillering.",
        "safety_guidelines": "Store at ambient room temperature. Safe for beneficial soil organisms.",
        "image_icon": "fas fa-fill-drip",
        "image_color": "#0ea5e9",
        "trusted_retailers": [
            {
                "platform": "IFFCO Bazar",
                "tag": "Official Portal",
                "url": "https://www.iffcobazar.in/en/product/iffco-nano-dap-liquid",
                "delivery": "Direct Farmer Free Shipping",
                "price": 600
            },
            {
                "platform": "AgroStar",
                "tag": "Verified Supplier",
                "url": "https://www.agrostar.in/search?q=Nano+DAP",
                "delivery": "Doorstep Delivery",
                "price": 600
            }
        ]
    },
    {
        "id": "prod-fert-3",
        "name": "Multiplex Zinc Micronutrient 21% (Zinc Sulfate)",
        "brand": "Multiplex Group of Companies",
        "category": "Fertilizers",
        "sub_category": "Essential Trace Micronutrient",
        "price": 360,
        "original_price": 420,
        "pack_size": "5 kg Bag",
        "rating": 4.8,
        "reviews_count": 310,
        "in_stock": True,
        "badge": "Critical for Khaira Disease Cure",
        "active_ingredient": "Zinc Sulfate Heptahydrate (Zn 21% + Sulphur 10%)",
        "target_diseases": ["Zinc Deficiency", "Khaira Disease"],
        "disease_benefit": "Instantly reverses rusty bronze discoloration and stunted tillering caused by zinc deficiency in flooded paddy soils.",
        "dosage_label": "Soil application: 10-15 kg per acre at basal. Foliar: 5 g per Litre with 2.5 g slaked lime.",
        "safety_guidelines": "Always neutralize with slaked lime or urea during foliar application to prevent leaf scorch.",
        "image_icon": "fas fa-cubes",
        "image_color": "#d97706",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Multiplex Dealer",
                "url": "https://www.bighaat.com/search?q=Multiplex+Zinc+21",
                "delivery": "3-5 Days Delivery",
                "price": 360
            },
            {
                "platform": "AgroStar",
                "tag": "Quality Guaranteed",
                "url": "https://www.agrostar.in/search?q=Zinc+Sulphate+21",
                "delivery": "Direct to Farm",
                "price": 365
            }
        ]
    },
    {
        "id": "prod-fert-4",
        "name": "Mahadhan Smarttek 19:19:19 100% Water Soluble NPK",
        "brand": "Deepak Fertilisers & Petrochemicals",
        "category": "Fertilizers",
        "sub_category": "Foliar & Drip Balanced Nutrition",
        "price": 195,
        "original_price": 240,
        "pack_size": "1 kg Pack",
        "rating": 4.7,
        "reviews_count": 220,
        "in_stock": True,
        "badge": "100% Water Soluble Foliar",
        "active_ingredient": "Total Nitrogen 19% + Phosphorus 19% + Potassium 19%",
        "target_diseases": ["General Nutrient Deficiency", "Slow Tillering"],
        "disease_benefit": "Fully soluble macro-nutrient spray delivering rapid vitality during active vegetative growth and early panicle development.",
        "dosage_label": "5 to 7 g per Litre of water (1.0 - 1.5 kg per acre in 200 L water)",
        "safety_guidelines": "Dissolves rapidly without residue. Compatible with most registered fungicides.",
        "image_icon": "fas fa-percentage",
        "image_color": "#14b8a6",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Top Brand",
                "url": "https://www.bighaat.com/search?q=Mahadhan+19+19+19",
                "delivery": "Pan-India Courier",
                "price": 195
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Fast Dispatch",
                "url": "https://www.amazon.in/s?k=19-19-19+fertilizer+mahadhan&i=lawngarden",
                "delivery": "Doorstep Delivery",
                "price": 210
            }
        ]
    },
    {
        "id": "prod-fert-5",
        "name": "Aries Agro Boron 20% (Foliar Grade Disodium Octaborate)",
        "brand": "Aries Agro Ltd.",
        "category": "Fertilizers",
        "sub_category": "Foliar Grain-Filling Micronutrient",
        "price": 290,
        "original_price": 350,
        "pack_size": "500 g Pack",
        "rating": 4.7,
        "reviews_count": 130,
        "in_stock": True,
        "badge": "Prevents Empty Grain Panicles",
        "active_ingredient": "Boron (B) 20% Water Soluble Disodium Octaborate Tetrahydrate",
        "target_diseases": ["Chaffy Grains", "Empty Panicle Tips", "Boron Deficiency"],
        "disease_benefit": "Essential for pollen germination and grain setting. Prevents unfilled chaffy grains and increases 1000-grain test weight.",
        "dosage_label": "1.0 to 1.5 g per Litre of water sprayed at boot leaf stage and 5% panicle emergence.",
        "safety_guidelines": "Do not overdose boron as excess can cause leaf tip necrosis.",
        "image_icon": "fas fa-wheat-awn",
        "image_color": "#ca8a04",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Aries Authorized",
                "url": "https://www.bighaat.com/search?q=Aries+Boron+20",
                "delivery": "Pan-India Delivery",
                "price": 290
            },
            {
                "platform": "AgroStar",
                "tag": "Verified Stock",
                "url": "https://www.agrostar.in/search?q=Boron+20",
                "delivery": "Direct Shipping",
                "price": 295
            }
        ]
    },
    {
        "id": "prod-fert-6",
        "name": "Coromandel Gromor 28:28:0 High Analysis Complex",
        "brand": "Coromandel International Ltd.",
        "category": "Fertilizers",
        "sub_category": "Granular Complex NPK Fertilizer",
        "price": 1450,
        "original_price": 1600,
        "pack_size": "50 kg Bag",
        "rating": 4.9,
        "reviews_count": 510,
        "in_stock": True,
        "badge": "India's #1 Paddy Basal Complex",
        "active_ingredient": "Ammoniacal Nitrogen 28% + Available Phosphate (P2O5) 28%",
        "target_diseases": ["Nutrient Depleted Soils", "Basal Crop Establishment"],
        "disease_benefit": "High analysis phosphorus stimulates immediate root elongation and vigorous crown roots, ensuring paddy seedlings anchor securely in puddle beds.",
        "dosage_label": "50 kg per acre during final field leveling before transplanting.",
        "safety_guidelines": "Broadcast uniformly. Store in dry covered godown away from rain.",
        "image_icon": "fas fa-layer-group",
        "image_color": "#047857",
        "trusted_retailers": [
            {
                "platform": "IFFCO Bazar",
                "tag": "Govt Price Regulated",
                "url": "https://www.iffcobazar.in/en/search?q=Gromor+28+28+0",
                "delivery": "APMC Village Society Pickup & Delivery",
                "price": 1450
            },
            {
                "platform": "BigHaat",
                "tag": "Coromandel Stock",
                "url": "https://www.bighaat.com/search?q=Coromandel+Gromor",
                "delivery": "Local Depot Delivery",
                "price": 1470
            }
        ]
    },

    # ==============================================================================
    # 3. SEEDS & PADDY VARIETIES
    # ==============================================================================
    {
        "id": "prod-seed-1",
        "name": "Samba Mahsuri (BPT 5204) Certified Breeder Paddy Seeds",
        "brand": "National Seeds Corporation (NSC)",
        "category": "Seeds",
        "sub_category": "Certified Fine-Grain Paddy Variety",
        "price": 1250,
        "original_price": 1400,
        "pack_size": "25 kg Bag",
        "rating": 4.9,
        "reviews_count": 520,
        "in_stock": True,
        "badge": "Top Sona Masoori Rice Variety",
        "active_ingredient": "Certified Foundation Paddy Seed (98%+ Genetic Purity)",
        "target_diseases": ["Rice Blast Resistance (Moderate)"],
        "disease_benefit": "Premier medium-slender fine grain paddy with outstanding cooking quality, fetching maximum market price in Mandya, Cauvery basin, and Andhra Pradesh.",
        "dosage_label": "Seed rate: 20-25 kg per acre for transplanted paddy; 12-15 kg for SRI cultivation.",
        "safety_guidelines": "Pre-treated with fungicide for seed-borne fungal disease prevention. Perform salt-water floatation test before soaking.",
        "image_icon": "fas fa-seedling",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Certified Seed Depot",
                "url": "https://www.bighaat.com/search?q=BPT+5204+paddy+seed",
                "delivery": "Express Seed Delivery",
                "price": 1250
            },
            {
                "platform": "AgroStar",
                "tag": "NSC Certified",
                "url": "https://www.agrostar.in/search?q=Samba+Mahsuri+seed",
                "delivery": "Doorstep Delivery to Villages",
                "price": 1260
            }
        ]
    },
    {
        "id": "prod-seed-2",
        "name": "IR64 High Yield Certified Paddy Seeds",
        "brand": "Kaveri Seed Company",
        "category": "Seeds",
        "sub_category": "Short Duration High-Yield Variety",
        "price": 980,
        "original_price": 1150,
        "pack_size": "20 kg Bag",
        "rating": 4.8,
        "reviews_count": 340,
        "in_stock": True,
        "badge": "Drought Hardy & High Tillering",
        "active_ingredient": "Certified Hybrid Paddy Seed (115-120 Days Duration)",
        "target_diseases": ["Blast Resistant", "Green Leafhopper Tolerant"],
        "disease_benefit": "Widely cultivated high-yielding early duration variety suited for both Kharif and Rabi paddy seasons. Highly responsive to organic inputs.",
        "dosage_label": "Seed rate: 20 kg per acre for regular transplanting.",
        "safety_guidelines": "Store seeds off the ground on wooden pallets in a cool dry room.",
        "image_icon": "fas fa-wheat-awn",
        "image_color": "#16a34a",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Kaveri Authorized",
                "url": "https://www.bighaat.com/search?q=IR64+paddy+seed",
                "delivery": "3-5 Days Shipping",
                "price": 980
            },
            {
                "platform": "AgroStar",
                "tag": "Quality Assured",
                "url": "https://www.agrostar.in/search?q=IR64+seeds",
                "delivery": "Rural Village Delivery",
                "price": 990
            }
        ]
    },
    {
        "id": "prod-seed-3",
        "name": "Telangana Sona (RNR 15048) Low-GI Certified Paddy Seeds",
        "brand": "Shriram BioSeed / PJTSAU",
        "category": "Seeds",
        "sub_category": "Low-GI Diabetic Friendly Variety",
        "price": 1350,
        "original_price": 1550,
        "pack_size": "25 kg Bag",
        "rating": 4.9,
        "reviews_count": 410,
        "in_stock": True,
        "badge": "Low GI (51.5) & BLB Resistant",
        "active_ingredient": "Certified Breeder Paddy Seed (Genetically BLB Resistant)",
        "target_diseases": ["Bacterial Leaf Blight", "Blast"],
        "disease_benefit": "Specifically bred with innate genetic resistance to Bacterial Leaf Blight (BLB). Produces superfine grain with low glycemic index.",
        "dosage_label": "Seed rate: 20 kg per acre. Maturity: 125 days.",
        "safety_guidelines": "Sow in well-drained nursery beds. Transplant 25-day-old single seedlings for maximum tillers.",
        "image_icon": "fas fa-award",
        "image_color": "#047857",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "BioSeed Official",
                "url": "https://www.bighaat.com/search?q=RNR+15048+Telangana+Sona",
                "delivery": "Fast Shipping",
                "price": 1350
            },
            {
                "platform": "AgroStar",
                "tag": "High Demand",
                "url": "https://www.agrostar.in/search?q=Telangana+Sona+Seed",
                "delivery": "Direct to Village",
                "price": 1360
            }
        ]
    },
    {
        "id": "prod-seed-4",
        "name": "Pusa Basmati 1509 Certified Seeds",
        "brand": "Mahyco / IARI New Delhi",
        "category": "Seeds",
        "sub_category": "Aromatic Export Quality Basmati",
        "price": 1650,
        "original_price": 1900,
        "pack_size": "20 kg Bag",
        "rating": 4.9,
        "reviews_count": 290,
        "in_stock": True,
        "badge": "Export Grade Extra Long Grain",
        "active_ingredient": "Certified Aromatic Basmati Seed (115-120 Days Duration)",
        "target_diseases": ["Brown Spot", "Blast"],
        "disease_benefit": "Extra-long grain basmati with exquisite aroma and elongation ratio up to 2.5x upon cooking. Early harvesting saves 3-4 irrigations.",
        "dosage_label": "Seed rate: 15-18 kg per acre.",
        "safety_guidelines": "Avoid excessive nitrogen application to prevent lodging and neck blast.",
        "image_icon": "fas fa-crown",
        "image_color": "#d97706",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "IARI Certified",
                "url": "https://www.bighaat.com/search?q=Pusa+Basmati+1509",
                "delivery": "3-5 Days Delivery",
                "price": 1650
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Direct Delivery",
                "url": "https://www.amazon.in/s?k=Pusa+1509+basmati+seed&i=lawngarden",
                "delivery": "Fast Shipping",
                "price": 1690
            }
        ]
    },
    {
        "id": "prod-seed-5",
        "name": "Swarna Sub-1 (Flood-Tolerant) Certified Paddy Seeds",
        "brand": "National Seeds Corporation (NSC)",
        "category": "Seeds",
        "sub_category": "Submergence-Tolerant Climate Resilient",
        "price": 1100,
        "original_price": 1280,
        "pack_size": "25 kg Bag",
        "rating": 4.8,
        "reviews_count": 175,
        "in_stock": True,
        "badge": "Survives 14 Days Under Water",
        "active_ingredient": "Certified Climate-Smart Seed with Sub1A Gene",
        "target_diseases": ["Flood Damage", "Submergence Shock", "Bacterial Blight"],
        "disease_benefit": "Equipped with the Sub1 gene allowing paddy plants to survive up to 14 days of complete water submergence during flash floods without dying.",
        "dosage_label": "Seed rate: 20-25 kg per acre. Maturity: 140-145 days.",
        "safety_guidelines": "Ideal for low-lying flood-prone paddy belts in Cauvery, Krishna, Godavari, and Bengal deltas.",
        "image_icon": "fas fa-water",
        "image_color": "#0284c7",
        "trusted_retailers": [
            {
                "platform": "AgroStar",
                "tag": "NSC Depot Stock",
                "url": "https://www.agrostar.in/search?q=Swarna+Sub+1+seed",
                "delivery": "Rural Village Delivery",
                "price": 1100
            },
            {
                "platform": "IFFCO Bazar",
                "tag": "Govt Partnership",
                "url": "https://www.iffcobazar.in/en/search?q=Paddy+seeds",
                "delivery": "Free Shipping to Registered Farmers",
                "price": 1110
            }
        ]
    },
    {
        "id": "prod-seed-6",
        "name": "Poornima Bio-Fortified Zinc Rice Seeds",
        "brand": "ICAR - Indian Institute of Rice Research (IIRR)",
        "category": "Seeds",
        "sub_category": "Bio-Fortified Nutritional Variety",
        "price": 1420,
        "original_price": 1600,
        "pack_size": "25 kg Bag",
        "rating": 4.8,
        "reviews_count": 140,
        "in_stock": True,
        "badge": "High Grain Zinc (24 ppm)",
        "active_ingredient": "Certified Bio-Fortified Paddy Variety (DRR Dhan 45 / Poornima)",
        "target_diseases": ["Zinc Deficiency", "Rice Blast Tolerant"],
        "disease_benefit": "Genetically bio-fortified grain containing 24 ppm zinc, delivering essential micronutrients naturally while remaining highly resilient to leaf blast.",
        "dosage_label": "Seed rate: 20 kg per acre. Duration: 125-130 days.",
        "safety_guidelines": "Pair with balanced zinc sulfate basal application for peak grain zinc enrichment.",
        "image_icon": "fas fa-certificate",
        "image_color": "#16a34a",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "ICAR Varieties",
                "url": "https://www.bighaat.com/search?q=Biofortified+paddy+seed",
                "delivery": "Pan-India Courier",
                "price": 1420
            },
            {
                "platform": "AgroStar",
                "tag": "Certified Seed",
                "url": "https://www.agrostar.in/search?q=Zinc+rice+seed",
                "delivery": "Direct Shipping",
                "price": 1430
            }
        ]
    },

    # ==============================================================================
    # 4. TOOLS & EQUIPMENT
    # ==============================================================================
    {
        "id": "prod-tool-1",
        "name": "KisanKraft 16L 12V/12Ah 2-in-1 Battery Knapsack Sprayer",
        "brand": "KisanKraft",
        "category": "Tools & Equipment",
        "sub_category": "Dual Electric & Manual Sprayer",
        "price": 2890,
        "original_price": 3600,
        "pack_size": "16 Litre Tank",
        "rating": 4.9,
        "reviews_count": 680,
        "in_stock": True,
        "badge": "Top Rated Farmer Sprayer",
        "active_ingredient": "High-Density Polyethylene (HDPE) + 12V 12Ah Rechargeable Lead-Acid Battery",
        "target_diseases": ["Pesticide Application", "Foliar Fertilizer Spray"],
        "disease_benefit": "Delivers uniform 0.2-0.4 MPa atomized spray pressure ensuring deep canopy penetration for fungicides and nano fertilizers across 25-30 tanks per charge.",
        "dosage_label": "Includes telescopic stainless lance, speed regulator, voltmeter, and 4 specialized nozzles.",
        "safety_guidelines": "Flush pump with clean water after spraying chemical fungicides. Recharge battery once a month when idle.",
        "image_icon": "fas fa-spray-can-sparkles",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "KisanKraft Official",
                "tag": "Direct Manufacturer",
                "url": "https://www.kisankraft.com/?s=battery+sprayer+16L",
                "delivery": "1-Year Warranty & Free Spares",
                "price": 2890
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Best Seller",
                "url": "https://www.amazon.in/s?k=KisanKraft+battery+sprayer+16L&i=lawngarden",
                "delivery": "Prime Free Delivery",
                "price": 2920
            },
            {
                "platform": "BigHaat",
                "tag": "Verified Agri Machinery",
                "url": "https://www.bighaat.com/search?q=KisanKraft+16L+sprayer",
                "delivery": "Doorstep Delivery",
                "price": 2950
            }
        ]
    },
    {
        "id": "prod-tool-2",
        "name": "Manual Rotary Paddy Cono Weeder for SRI Cultivation",
        "brand": "AgriPro Tools",
        "category": "Tools & Equipment",
        "sub_category": "SRI Paddy Inter-Cultivation Tool",
        "price": 1650,
        "original_price": 2100,
        "pack_size": "Single Unit with Handle",
        "rating": 4.8,
        "reviews_count": 310,
        "in_stock": True,
        "badge": "SRI Paddy Certified",
        "active_ingredient": "Powder-Coated High Strength Mild Steel Cones with Serrated Teeth",
        "target_diseases": ["Weed Infestation", "Soil Aeration"],
        "disease_benefit": "Uproots aquatic and grassy weeds between paddy rows while churning weeds into green manure, aerating the root zone and boosting tillers by 25%.",
        "dosage_label": "Operate at 10-15 day intervals after transplanting when field has 2-3 cm standing water.",
        "safety_guidelines": "Rinse mud thoroughly after operation and wipe cones dry to prevent rust.",
        "image_icon": "fas fa-gears",
        "image_color": "#10b981",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "Verified Tool",
                "url": "https://www.amazon.in/s?k=paddy+cono+weeder&i=lawngarden",
                "delivery": "Free Shipping Available",
                "price": 1650
            },
            {
                "platform": "KisanKraft",
                "tag": "Agri Machinery",
                "url": "https://www.kisankraft.com/?s=weeder",
                "delivery": "Pan-India Shipping",
                "price": 1690
            },
            {
                "platform": "BigHaat",
                "tag": "Farmer Favorite",
                "url": "https://www.bighaat.com/search?q=cono+weeder",
                "delivery": "Doorstep Dispatch",
                "price": 1720
            }
        ]
    },
    {
        "id": "prod-tool-3",
        "name": "Serrated High-Carbon Steel Paddy Harvesting Sickle (Pack of 3)",
        "brand": "Falcon Garden Tools",
        "category": "Tools & Equipment",
        "sub_category": "Manual Harvesting Hand Tool",
        "price": 480,
        "original_price": 620,
        "pack_size": "Pack of 3 Sickles",
        "rating": 4.9,
        "reviews_count": 450,
        "in_stock": True,
        "badge": "Zero-Fatigue Hardened Steel",
        "active_ingredient": "Induction-Hardened High Carbon Manganese Steel + Seasoned Wooden Handle",
        "target_diseases": ["Crop Harvesting"],
        "disease_benefit": "Micro-serrated edge slices cleanly through tough paddy straw without shaking off ripe grains, reducing harvesting shatter losses by 5-8%.",
        "dosage_label": "Curved ergonomic design tailored for comfortable full-day rice harvesting.",
        "safety_guidelines": "Keep serrated teeth protected with sheath when stored. Keep out of reach of children.",
        "image_icon": "fas fa-wrench",
        "image_color": "#047857",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "Top Rated",
                "url": "https://www.amazon.in/s?k=Falcon+paddy+harvesting+sickle&i=lawngarden",
                "delivery": "Fast Prime Shipping",
                "price": 480
            },
            {
                "platform": "KisanKraft",
                "tag": "Hand Tools Depot",
                "url": "https://www.kisankraft.com/?s=sickle",
                "delivery": "3-5 Days Delivery",
                "price": 490
            }
        ]
    },
    {
        "id": "prod-tool-4",
        "name": "Digital 4-in-1 Soil Survey Tester (pH, Moisture, Temp, Lux)",
        "brand": "V-Tech / Hanna Instruments",
        "category": "Tools & Equipment",
        "sub_category": "Soil Diagnostic Instrument",
        "price": 890,
        "original_price": 1350,
        "pack_size": "Electronic Instrument with 200mm Probe",
        "rating": 4.7,
        "reviews_count": 280,
        "in_stock": True,
        "badge": "Instant Soil Health Test",
        "active_ingredient": "Solid-State Dual Sensor Probe with Backlit Digital LCD Display",
        "target_diseases": ["Soil Acidity", "Zinc Lockup", "Moisture Stress"],
        "disease_benefit": "Diagnoses soil pH in seconds. Helps farmers detect alkaline pH (>7.5) which locks up zinc and causes Khaira disease, or acidic soil causing root rot.",
        "dosage_label": "Insert 200mm probe 10-15 cm into moist nursery or field soil for instant digital readout.",
        "safety_guidelines": "Wipe metal probe clean with dry cloth after each measurement. Do not force into stony soil.",
        "image_icon": "fas fa-gauge-high",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "Direct Import",
                "url": "https://www.amazon.in/s?k=soil+ph+meter+digital+4+in+1&i=lawngarden",
                "delivery": "Fast Prime Shipping",
                "price": 890
            },
            {
                "platform": "BigHaat",
                "tag": "Soil Testing Lab",
                "url": "https://www.bighaat.com/search?q=soil+ph+meter",
                "delivery": "Pan-India Courier",
                "price": 920
            }
        ]
    },
    {
        "id": "prod-tool-5",
        "name": "Farmer Chemical Spray Safety PPE Kit (Full Protection)",
        "brand": "3M India Agricultural Safety",
        "category": "Tools & Equipment",
        "sub_category": "Personal Protective Equipment",
        "price": 620,
        "original_price": 850,
        "pack_size": "Complete 4-Piece Kit",
        "rating": 4.9,
        "reviews_count": 510,
        "in_stock": True,
        "badge": "Mandatory Spray Protection",
        "active_ingredient": "N95 Organic Chemical Filter Mask + Splash Goggles + Nitrile Gloves + Chemical Apron",
        "target_diseases": ["Farmer Safety & Toxic Chemical Inhalation Prevention"],
        "disease_benefit": "Mandatory safety gear compliant with Central Insecticides Board (CIBRC) regulations. Prevents dermal absorption and inhalation of organophosphates and fungicides.",
        "dosage_label": "Reusable washable components with replaceable mask filters.",
        "safety_guidelines": "Always wear during mixing and spraying of chemical pesticides. Wash gloves and goggles after use.",
        "image_icon": "fas fa-user-shield",
        "image_color": "#14b8a6",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "3M Certified",
                "url": "https://www.amazon.in/s?k=3M+chemical+spray+safety+kit&i=lawngarden",
                "delivery": "Prime Eligible",
                "price": 620
            },
            {
                "platform": "BigHaat",
                "tag": "Farmer Health",
                "url": "https://www.bighaat.com/search?q=PPE+kit+agriculture",
                "delivery": "2-4 Days Delivery",
                "price": 630
            },
            {
                "platform": "AgroStar",
                "tag": "Safety Stock",
                "url": "https://www.agrostar.in/search?q=safety+spray+kit",
                "delivery": "Direct Shipping",
                "price": 640
            }
        ]
    },
    {
        "id": "prod-tool-6",
        "name": "Aspee HTP Heavy Duty Power Sprayer Gun Nozzle",
        "brand": "Aspee Agricultural Implements",
        "category": "Tools & Equipment",
        "sub_category": "Tractor & Engine Sprayer Attachment",
        "price": 1150,
        "original_price": 1400,
        "pack_size": "Single Gun Assembly",
        "rating": 4.8,
        "reviews_count": 230,
        "in_stock": True,
        "badge": "Long-Distance Throw (30 ft)",
        "active_ingredient": "Forged Brass Valve Core with Stainless Steel Tip",
        "target_diseases": ["Fast Canopy Spraying", "Large Acreage Coverage"],
        "disease_benefit": "Generates ultrafine mist cloud with up to 30 feet throwing distance, completing 5 acres of paddy disease spraying in less than 2 hours.",
        "dosage_label": "Connects to standard 8.5mm HTP power sprayer delivery hose.",
        "safety_guidelines": "Do not direct high-pressure jet towards people or animals.",
        "image_icon": "fas fa-crosshairs",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Aspee Official",
                "url": "https://www.bighaat.com/search?q=Aspee+sprayer+gun",
                "delivery": "3-5 Days Delivery",
                "price": 1150
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Best Deal",
                "url": "https://www.amazon.in/s?k=HTP+power+sprayer+gun&i=lawngarden",
                "delivery": "Fast Shipping",
                "price": 1180
            }
        ]
    },

    # ==============================================================================
    # 5. ORGANIC PRODUCTS
    # ==============================================================================
    {
        "id": "prod-org-1",
        "name": "Bio-Neem 10,000 ppm Azadirachtin EC (Cold-Pressed)",
        "brand": "Bio-Control Agri Solutions",
        "category": "Organic Products",
        "sub_category": "Certified Organic Botanical Insecticide & Fungicide",
        "price": 540,
        "original_price": 650,
        "pack_size": "1 Litre Bottle",
        "rating": 4.9,
        "reviews_count": 340,
        "in_stock": True,
        "badge": "100% Organic & Export Safe",
        "active_ingredient": "Azadirachtin 1% (10,000 ppm) Pure Cold-Pressed Neem EC",
        "target_diseases": ["Brown Plant Hopper", "Stem Borer", "Leaf Folder", "Brown Spot"],
        "disease_benefit": "Zero-residue organic botanical pest repellent and fungal suppressor. Completely safe for beneficial honeybees, spiders, and dragonflies.",
        "dosage_label": "2.0 to 3.0 ml per Litre of water (400-600 ml per acre in 200 L water)",
        "safety_guidelines": "Waiting period: Zero days. Certified for organic rice export cultivation.",
        "image_icon": "fas fa-seedling",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "IFFCO Bazar",
                "tag": "Co-op Certified",
                "url": "https://www.iffcobazar.in/en/search?q=Neem+Oil+10000+ppm",
                "delivery": "Free Delivery to Rural Pincodes",
                "price": 530
            },
            {
                "platform": "BigHaat",
                "tag": "Organic Hub",
                "url": "https://www.bighaat.com/search?q=Azadirachtin+10000+ppm",
                "delivery": "3-5 Days Shipping",
                "price": 540
            },
            {
                "platform": "Amazon Agriculture",
                "tag": "Direct Delivery",
                "url": "https://www.amazon.in/s?k=Neem+Oil+10000+ppm+agriculture&i=lawngarden",
                "delivery": "Fast Shipping",
                "price": 550
            }
        ]
    },
    {
        "id": "prod-org-2",
        "name": "Trichoderma Viride 1.5% WP Bio-Fungicide (Seed & Soil)",
        "brand": "ICAR-NBAIR / Multiplex Bio-Tech",
        "category": "Organic Products",
        "sub_category": "Antagonistic Fungal Bio-Control Agent",
        "price": 260,
        "original_price": 320,
        "pack_size": "1 kg Pack",
        "rating": 4.9,
        "reviews_count": 480,
        "in_stock": True,
        "badge": "Certified Bio-Fungicide",
        "active_ingredient": "Trichoderma viride (CFU 2 x 10^8 per gram)",
        "target_diseases": ["Sheath Blight", "Stem Rot", "Root Rot", "Seedling Damping Off"],
        "disease_benefit": "Naturally parasitizes and destroys soil-borne pathogenic fungi (Rhizoctonia, Sclerotium). Promotes root elongation through natural growth hormones.",
        "dosage_label": "Seed treatment: 10 g/kg seed. Soil application: 2.5 kg mixed with 100 kg FYM/vermicompost per acre.",
        "safety_guidelines": "Do not mix with chemical copper or triazole fungicides. Apply in moist soil.",
        "image_icon": "fas fa-dna",
        "image_color": "#16a34a",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Organic Certified",
                "url": "https://www.bighaat.com/search?q=Trichoderma+viride",
                "delivery": "3-5 Days Delivery",
                "price": 260
            },
            {
                "platform": "AgroStar",
                "tag": "Top Bio-Input",
                "url": "https://www.agrostar.in/search?q=Trichoderma",
                "delivery": "Doorstep Delivery",
                "price": 265
            },
            {
                "platform": "IFFCO Bazar",
                "tag": "Farmer Co-op",
                "url": "https://www.iffcobazar.in/en/search?q=Trichoderma",
                "delivery": "Free Rural Shipping",
                "price": 270
            }
        ]
    },
    {
        "id": "prod-org-3",
        "name": "Pseudomonas Fluorescens 1.0% WP Bio-Bactericide",
        "brand": "T. Stanes & Company Bio-Agri",
        "category": "Organic Products",
        "sub_category": "Plant Growth-Promoting Rhizobacteria (PGPR)",
        "price": 290,
        "original_price": 350,
        "pack_size": "1 kg Pack",
        "rating": 4.8,
        "reviews_count": 270,
        "in_stock": True,
        "badge": "Natural Blight Suppressor",
        "active_ingredient": "Pseudomonas fluorescens (CFU 1 x 10^9 per gram)",
        "target_diseases": ["Bacterial Leaf Blight", "Rice Blast", "Sheath Rot"],
        "disease_benefit": "Produces 2,4-diacetylphloroglucinol (DAPG) and salicylic acid which trigger Systemic Acquired Resistance (SAR) against Bacterial Blight and Blast.",
        "dosage_label": "Seedling root dip: 10 g per Litre water for 30 minutes. Foliar spray: 5 g per Litre at 30 & 45 DAT.",
        "safety_guidelines": "Store away from heat and direct sunlight. Keep packet sealed until application.",
        "image_icon": "fas fa-bacterium",
        "image_color": "#0d9488",
        "trusted_retailers": [
            {
                "platform": "BigHaat",
                "tag": "Stanes Certified",
                "url": "https://www.bighaat.com/search?q=Pseudomonas+fluorescens",
                "delivery": "Pan-India Shipping",
                "price": 290
            },
            {
                "platform": "AgroStar",
                "tag": "Bio-Organic Depot",
                "url": "https://www.agrostar.in/search?q=Pseudomonas",
                "delivery": "Doorstep Delivery",
                "price": 295
            }
        ]
    },
    {
        "id": "prod-org-4",
        "name": "Desi Cow Organic Panchagavya Foliar Tonic & Immunity Booster",
        "brand": "Vedic Organics India",
        "category": "Organic Products",
        "sub_category": "Fermented Cow-Derived Bio-Nutrient",
        "price": 380,
        "original_price": 480,
        "pack_size": "1 Litre Bottle",
        "rating": 4.9,
        "reviews_count": 390,
        "in_stock": True,
        "badge": "Ancient Vedic Recipe",
        "active_ingredient": "Fermented Gir Cow Dung, Urine, Milk, Curd, Ghee, Jaggery, Banana & Coconut Water",
        "target_diseases": ["Nutrient Deficiencies", "Crop Stunting", "Poor Immunity"],
        "disease_benefit": "Rich in beneficial lactic acid bacteria, yeast, actinomycetes, and auxins. Stimulates thick glossy green leaves, abundant tillers, and heavy panicles.",
        "dosage_label": "30 ml per Litre of water (3% solution, 6 Litres per acre in 200 L water) sprayed at tillering and flowering.",
        "safety_guidelines": "100% natural, chemical-free and safe for edible crops. Shake well before diluting.",
        "image_icon": "fas fa-spa",
        "image_color": "#047857",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "Top Vedic Brand",
                "url": "https://www.amazon.in/s?k=organic+panchagavya+for+plants&i=lawngarden",
                "delivery": "Fast Prime Shipping",
                "price": 380
            },
            {
                "platform": "BigHaat",
                "tag": "Organic Store",
                "url": "https://www.bighaat.com/search?q=Panchagavya",
                "delivery": "3-5 Days Delivery",
                "price": 390
            }
        ]
    },
    {
        "id": "prod-org-5",
        "name": "Bio-Potash (Potash Mobilizing Bacteria - KMB) Liquid",
        "brand": "IFFCO Kisan Organics",
        "category": "Organic Products",
        "sub_category": "Liquid Bio-Fertilizer",
        "price": 340,
        "original_price": 420,
        "pack_size": "1 Litre Bottle",
        "rating": 4.8,
        "reviews_count": 210,
        "in_stock": True,
        "badge": "Replaces MOP Chemically",
        "active_ingredient": "Frateuria aurantia (Potash Mobilizing Microorganisms, 1 x 10^8 CFU/ml)",
        "target_diseases": ["Potassium Deficiency", "Culm Weakness", "Crop Lodging"],
        "disease_benefit": "Solubilizes insoluble mineral potassium fixed in clay soils into plant-absorbable K+ ions, stiffening paddy stems to prevent crop lodging during high winds.",
        "dosage_label": "1 Litre per acre mixed with 200 L water for soil drenching, or 4 ml per Litre foliar spray.",
        "safety_guidelines": "Do not mix with bactericides or chemical weedicides.",
        "image_icon": "fas fa-flask-vial",
        "image_color": "#10b981",
        "trusted_retailers": [
            {
                "platform": "IFFCO Bazar",
                "tag": "Official Co-op",
                "url": "https://www.iffcobazar.in/en/search?q=Bio+potash",
                "delivery": "Free Doorstep Delivery",
                "price": 340
            },
            {
                "platform": "BigHaat",
                "tag": "Certified Bio-K",
                "url": "https://www.bighaat.com/search?q=Bio+Potash+Liquid",
                "delivery": "Pan-India Shipping",
                "price": 350
            }
        ]
    },
    {
        "id": "prod-org-6",
        "name": "Premium Enriched Vermicompost with Neem Cake (25 kg)",
        "brand": "TrustBasket Organic Agri",
        "category": "Organic Products",
        "sub_category": "Nutrient-Dense Soil Amendment",
        "price": 720,
        "original_price": 950,
        "pack_size": "25 kg Heavy Duty Bag",
        "rating": 4.9,
        "reviews_count": 560,
        "in_stock": True,
        "badge": "Enriched with 10% Neem Cake",
        "active_ingredient": "100% Pure Earthworm Castings + Cold-Pressed Neem Seed Meal",
        "target_diseases": ["Soil Degradation", "Nematode Infestation", "Nutrient Runoff"],
        "disease_benefit": "Provides continuous slow-release humic carbon and micro-flora while the neem cake content suppresses soil nematodes and root grubs naturally.",
        "dosage_label": "Basal application: 50-100 kg per acre during nursery and main field land preparation.",
        "safety_guidelines": "Store on a dry platform away from wet floors.",
        "image_icon": "fas fa-mountain-sun",
        "image_color": "#059669",
        "trusted_retailers": [
            {
                "platform": "Amazon Agriculture",
                "tag": "Prime Heavy Delivery",
                "url": "https://www.amazon.in/s?k=vermicompost+25kg+trustbasket&i=lawngarden",
                "delivery": "Doorstep Delivery by Freight",
                "price": 720
            },
            {
                "platform": "BigHaat",
                "tag": "Organic Depot",
                "url": "https://www.bighaat.com/search?q=Vermicompost+25kg",
                "delivery": "3-5 Days Delivery",
                "price": 740
            }
        ]
    }
]

CATEGORIES = [
    "Seeds",
    "Fertilizers",
    "Pesticides",
    "Tools & Equipment",
    "Organic Products"
]


def search_online_products(query=None, category=None, disease=None, sort_by="popular", min_price=None, max_price=None):
    """
    Filters and returns online agricultural products with trusted shopping links.
    Zero GPS/location dependency.
    """
    results = list(ONLINE_PRODUCTS)

    # 1. Filter by category
    if category and category.lower() not in {"all", "all products", ""}:
        cat_lower = category.lower().strip()
        filtered = []
        for p in results:
            p_cat = p["category"].lower()
            p_sub = p["sub_category"].lower()

            if cat_lower == p_cat or cat_lower in p_cat:
                filtered.append(p)
            elif cat_lower in p_sub:
                filtered.append(p)
            elif cat_lower.startswith("seed") and "seed" in p_cat:
                filtered.append(p)
            elif cat_lower.startswith("fert") and "fert" in p_cat:
                filtered.append(p)
            elif (cat_lower.startswith("pest") or cat_lower.startswith("fung")) and "pest" in p_cat:
                filtered.append(p)
            elif (cat_lower.startswith("tool") or cat_lower.startswith("equip") or "farming tool" in cat_lower) and ("tool" in p_cat or "equip" in p_cat):
                filtered.append(p)
            elif (cat_lower.startswith("organ") or "bio" in cat_lower) and "organ" in p_cat:
                filtered.append(p)
        results = filtered

    # 2. Filter by disease
    if disease and disease.strip():
        dis_norm = disease.lower().replace("_", " ").strip()
        filtered = []
        for p in results:
            targets = [t.lower() for t in p.get("target_diseases", [])]
            benefit = p.get("disease_benefit", "").lower()
            active_ing = p.get("active_ingredient", "").lower()
            if any(dis_norm in t or t in dis_norm for t in targets) or dis_norm in benefit or dis_norm in active_ing:
                filtered.append(p)
            elif any(word in benefit for word in dis_norm.split() if len(word) > 3):
                filtered.append(p)
        if filtered:
            results = filtered

    # 3. Filter by text search query
    if query and query.strip():
        q_terms = query.lower().split()
        filtered = []
        for p in results:
            searchable = " ".join([
                p.get("name", ""),
                p.get("brand", ""),
                p.get("category", ""),
                p.get("sub_category", ""),
                p.get("active_ingredient", ""),
                p.get("disease_benefit", ""),
                p.get("badge", ""),
                " ".join(p.get("target_diseases", []))
            ]).lower()
            if all(term in searchable for term in q_terms):
                filtered.append(p)
        results = filtered

    # 4. Filter by price range
    if min_price is not None:
        try:
            min_val = float(min_price)
            results = [p for p in results if p["price"] >= min_val]
        except (ValueError, TypeError):
            pass

    if max_price is not None:
        try:
            max_val = float(max_price)
            results = [p for p in results if p["price"] <= max_val]
        except (ValueError, TypeError):
            pass

    # 5. Sorting
    if sort_by == "price_asc":
        results.sort(key=lambda p: p["price"])
    elif sort_by == "price_desc":
        results.sort(key=lambda p: p["price"], reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda p: (p["rating"], p["reviews_count"]), reverse=True)
    elif sort_by == "discount":
        results.sort(key=lambda p: (p["original_price"] - p["price"]) / p["original_price"], reverse=True)
    else:  # popular / default
        results.sort(key=lambda p: (p["rating"] * p["reviews_count"]), reverse=True)

    # Compute category statistics
    category_counts = {
        "All": len(ONLINE_PRODUCTS),
        "Seeds": sum(1 for p in ONLINE_PRODUCTS if p["category"] == "Seeds"),
        "Fertilizers": sum(1 for p in ONLINE_PRODUCTS if p["category"] == "Fertilizers"),
        "Pesticides": sum(1 for p in ONLINE_PRODUCTS if p["category"] == "Pesticides"),
        "Tools & Equipment": sum(1 for p in ONLINE_PRODUCTS if p["category"] == "Tools & Equipment"),
        "Organic Products": sum(1 for p in ONLINE_PRODUCTS if p["category"] == "Organic Products")
    }

    return {
        "success": True,
        "count": len(results),
        "total_catalog": len(ONLINE_PRODUCTS),
        "products": results,
        "category_counts": category_counts,
        "categories": CATEGORIES,
        "trusted_platforms": [
            {"name": "BigHaat", "url": "https://www.bighaat.com", "badge": "India's #1 Agri Store", "logo": "bighaat"},
            {"name": "AgroStar", "url": "https://www.agrostar.in", "badge": "Farmer Direct Delivery", "logo": "agrostar"},
            {"name": "IFFCO Bazar", "url": "https://www.iffcobazar.in", "badge": "Official Farmer Co-op", "logo": "iffco"},
            {"name": "KisanKraft", "url": "https://www.kisankraft.com", "badge": "Certified Machinery", "logo": "kisankraft"},
            {"name": "Amazon Agriculture", "url": "https://www.amazon.in/agricultural-inputs", "badge": "Fast Shipping", "logo": "amazon"}
        ]
    }


def get_online_product_by_id(product_id):
    """Returns single product details and related recommendations."""
    prod = next((p for p in ONLINE_PRODUCTS if p["id"] == str(product_id)), None)
    if not prod:
        return None

    # Find related products in same category or matching diseases
    related = [
        p for p in ONLINE_PRODUCTS
        if p["id"] != prod["id"] and (p["category"] == prod["category"] or any(d in p.get("target_diseases", []) for d in prod.get("target_diseases", [])))
    ][:4]

    return {
        "product": prod,
        "related_products": related
    }


def add_online_product(data):
    """
    Appends a new verified agricultural input product to the Online Agri Store catalog.
    """
    import uuid
    new_id = f"prod-custom-{uuid.uuid4().hex[:8]}"
    category = data.get("category", "Pesticides").strip()
    name = data.get("name", "Agricultural Input").strip()
    brand = data.get("brand", "Certified Agro Brand").strip()
    price = float(data.get("price", 450))
    orig_price = float(data.get("original_price", price * 1.15))
    pack_size = data.get("pack_size", "Standard Pack").strip()
    active_ing = data.get("active_ingredient", "Agricultural Formulation").strip()
    benefit = data.get("disease_benefit", data.get("description", "High efficiency crop input.")).strip()
    platform = data.get("platform", "BigHaat").strip()
    shopping_url = data.get("url", f"https://www.bighaat.com/search?q={name.replace(' ', '+')}").strip()
    badge = data.get("badge", "New Arrival & ICAR Approved").strip()

    # Category icon mapping
    icon_map = {
        "Seeds": ("fas fa-seedling", "#059669"),
        "Fertilizers": ("fas fa-cubes", "#0284c7"),
        "Pesticides": ("fas fa-shield-virus", "#e11d48"),
        "Tools & Equipment": ("fas fa-wrench", "#d97706"),
        "Organic Products": ("fas fa-leaf", "#10b981")
    }
    icon, color = icon_map.get(category, ("fas fa-box", "#059669"))

    target_d = data.get("target_diseases", [])
    if isinstance(target_d, str):
        target_d = [t.strip() for t in target_d.split(",") if t.strip()]
    if not target_d:
        target_d = ["General Protection", "Crop Stand Vitality"]

    new_prod = {
        "id": new_id,
        "name": name,
        "brand": brand,
        "category": category,
        "sub_category": data.get("sub_category", category),
        "price": price,
        "original_price": orig_price,
        "pack_size": pack_size,
        "rating": 4.9,
        "reviews_count": 18,
        "in_stock": True,
        "badge": badge,
        "active_ingredient": active_ing,
        "target_diseases": target_d,
        "disease_benefit": benefit,
        "dosage_label": data.get("dosage_label", "Refer to bottle/packet instructions."),
        "safety_guidelines": "Waiting period: 14 days. Store in cool, dry place. Keep out of reach of children.",
        "image_icon": icon,
        "image_color": color,
        "trusted_retailers": [
            {
                "platform": platform,
                "tag": "Verified Portal",
                "url": shopping_url,
                "delivery": "3-5 Days Doorstep Delivery",
                "price": price
            }
        ]
    }
    ONLINE_PRODUCTS.insert(0, new_prod)
    return new_prod

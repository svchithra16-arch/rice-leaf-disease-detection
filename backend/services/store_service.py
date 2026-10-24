"""
AgriVersion - Agricultural Store & Product Availability Domain Service
Provides:
- Strict Non-Prescriptive Disease -> Management Category Mapping (Section 29.1 & 29.16)
- Geolocation Distance Calculation (Haversine Formula)
- Multi-criteria Store Search & Availability Filtering
- Inventory Freshness & Stale Data Auditing (Section 29.12)
- Stock Availability Notification Dispatching (Section 29.10)
"""

import math
import json
from datetime import datetime, timedelta
from backend.database.db import db
from backend.database.models import Store, Product, StoreRequest, StoreReview, format_relative_time


# ------------------------------------------------------------------------------
# Regional City & Pincode Coordinates Directory (India Paddy Belts)
# ------------------------------------------------------------------------------
KNOWN_LOCATIONS = {
    "doddballapur": {"lat": 13.2936, "lng": 77.5342, "state": "Karnataka", "pincode": "562123"},
    "doddaballapur": {"lat": 13.2936, "lng": 77.5342, "state": "Karnataka", "pincode": "562123"},
    "doddaballapura": {"lat": 13.2936, "lng": 77.5342, "state": "Karnataka", "pincode": "562123"},
    "dodd ballapur": {"lat": 13.2936, "lng": 77.5342, "state": "Karnataka", "pincode": "562123"},
    "bengaluru rural": {"lat": 13.2936, "lng": 77.5342, "state": "Karnataka", "pincode": "562123"},
    "chikkaballapur": {"lat": 13.4355, "lng": 77.7275, "state": "Karnataka", "pincode": "562101"},
    "chikkaballapura": {"lat": 13.4355, "lng": 77.7275, "state": "Karnataka", "pincode": "562101"},
    "chikballapur": {"lat": 13.4355, "lng": 77.7275, "state": "Karnataka", "pincode": "562101"},
    "kolar": {"lat": 13.1378, "lng": 78.1291, "state": "Karnataka", "pincode": "563101"},
    "tumakuru": {"lat": 13.3409, "lng": 77.1010, "state": "Karnataka", "pincode": "572101"},
    "tumkur": {"lat": 13.3409, "lng": 77.1010, "state": "Karnataka", "pincode": "572101"},
    "ramanagara": {"lat": 12.7209, "lng": 77.2799, "state": "Karnataka", "pincode": "562159"},
    "mandya": {"lat": 12.5218, "lng": 76.8951, "state": "Karnataka", "pincode": "571401"},
    "mysuru": {"lat": 12.2958, "lng": 76.6394, "state": "Karnataka", "pincode": "570001"},
    "mysore": {"lat": 12.2958, "lng": 76.6394, "state": "Karnataka", "pincode": "570001"},
    "bengaluru": {"lat": 12.9716, "lng": 77.5946, "state": "Karnataka", "pincode": "560001"},
    "bangalore": {"lat": 12.9716, "lng": 77.5946, "state": "Karnataka", "pincode": "560001"},
    "hassan": {"lat": 13.0033, "lng": 76.1004, "state": "Karnataka", "pincode": "573201"},
    "shivamogga": {"lat": 13.9299, "lng": 75.5681, "state": "Karnataka", "pincode": "577201"},
    "shimoga": {"lat": 13.9299, "lng": 75.5681, "state": "Karnataka", "pincode": "577201"},
    "davanagere": {"lat": 14.4644, "lng": 75.9218, "state": "Karnataka", "pincode": "577002"},
    "ballari": {"lat": 15.1394, "lng": 76.9214, "state": "Karnataka", "pincode": "583101"},
    "bellary": {"lat": 15.1394, "lng": 76.9214, "state": "Karnataka", "pincode": "583101"},
    "raichur": {"lat": 16.2076, "lng": 77.3463, "state": "Karnataka", "pincode": "584101"},
    "koppal": {"lat": 15.3512, "lng": 76.1548, "state": "Karnataka", "pincode": "583231"},
    "gadag": {"lat": 15.4297, "lng": 75.6268, "state": "Karnataka", "pincode": "582101"},
    "haveri": {"lat": 14.7972, "lng": 75.3985, "state": "Karnataka", "pincode": "581110"},
    "belagavi": {"lat": 15.8497, "lng": 74.4977, "state": "Karnataka", "pincode": "590001"},
    "kalaburagi": {"lat": 17.3297, "lng": 76.8343, "state": "Karnataka", "pincode": "585101"},
    "vijayapura": {"lat": 16.8302, "lng": 75.7100, "state": "Karnataka", "pincode": "586101"},
    "udupi": {"lat": 13.3409, "lng": 74.7421, "state": "Karnataka", "pincode": "576101"},
    "mangaluru": {"lat": 12.9141, "lng": 74.8560, "state": "Karnataka", "pincode": "575001"},
    "warangal": {"lat": 17.9689, "lng": 79.5941, "state": "Telangana", "pincode": "506002"},
    "thanjavur": {"lat": 10.7870, "lng": 79.1378, "state": "Tamil Nadu", "pincode": "613001"},
    "bardhaman": {"lat": 23.2324, "lng": 87.8615, "state": "West Bengal", "pincode": "713101"},
    "cuttack": {"lat": 20.4625, "lng": 85.8828, "state": "Odisha", "pincode": "753001"},
    "karnal": {"lat": 29.6857, "lng": 76.9905, "state": "Haryana", "pincode": "132001"}
}

PINCODE_MAP = {
    "562101": {"name": "Chikkaballapur Town", "lat": 13.4355, "lng": 77.7275},
    "562123": {"name": "Doddaballapura, Bengaluru Rural", "lat": 13.2936, "lng": 77.5342},
    "563101": {"name": "Kolar City", "lat": 13.1378, "lng": 78.1291},
    "572101": {"name": "Tumakuru Town", "lat": 13.3409, "lng": 77.1010},
    "562159": {"name": "Ramanagara", "lat": 12.7209, "lng": 77.2799},
    "571401": {"name": "Mandya Town", "lat": 12.5218, "lng": 76.8951},
    "571402": {"name": "Mandya Rural / Sugar Town", "lat": 12.5100, "lng": 76.8800},
    "571438": {"name": "Maddur, Mandya", "lat": 12.5847, "lng": 77.0457},
    "571434": {"name": "Pandavapura, Mandya", "lat": 12.4965, "lng": 76.6715},
    "570001": {"name": "Mysuru City", "lat": 12.2958, "lng": 76.6394},
    "570008": {"name": "Gokulam, Mysuru", "lat": 12.3300, "lng": 76.6200},
    "571180": {"name": "Nanjangud, Mysuru", "lat": 12.1194, "lng": 76.6803},
    "560001": {"name": "Bengaluru Central", "lat": 12.9716, "lng": 77.5946},
    "573201": {"name": "Hassan APMC", "lat": 13.0033, "lng": 76.1004},
    "577201": {"name": "Shivamogga City", "lat": 13.9299, "lng": 75.5681},
    "584101": {"name": "Raichur Paddy Hub", "lat": 16.2076, "lng": 77.3463},
    "583101": {"name": "Ballari APMC", "lat": 15.1394, "lng": 76.9214},
    "506002": {"name": "Warangal Grain Market", "lat": 17.9689, "lng": 79.5941},
    "613001": {"name": "Thanjavur Delta", "lat": 10.7870, "lng": 79.1378}
}


# ------------------------------------------------------------------------------
# Disease -> Labeled Management Category & Botanical Ingredients Matrix
# (Complies with non-prescriptive regulatory requirements)
# ------------------------------------------------------------------------------
DISEASE_CATEGORY_MAPPINGS = {
    "Rice Blast": {
        "primary_category": "Fungicide",
        "category_title": "Fungicide products registered & labeled for Rice Blast management",
        "verified_active_ingredients": [
            {
                "name": "Tricyclazole 75% WP",
                "mode_of_action": "Systemic melanin biosynthesis inhibitor (MBI)",
                "common_brands": "Beam, Baan, Sivic, Trooper",
                "label_dosage": "0.6 g / Litre (120 g / acre)",
                "target_phase": "Tillering to panicle emergence"
            },
            {
                "name": "Isoprothiolane 40% EC",
                "mode_of_action": "Systemic blast specific fungicide & lipid biosynthesis inhibitor",
                "common_brands": "Fuji-One, Kasu-B",
                "label_dosage": "1.5 to 2.0 mL / Litre",
                "target_phase": "Leaf blast & neck blast onset"
            },
            {
                "name": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "mode_of_action": "Dual-action QoI strobilurin + triazole systemic",
                "common_brands": "Amistar Top, Godiwa Super",
                "label_dosage": "1.0 mL / Litre (200 mL / acre)",
                "target_phase": "Panicle initiation"
            },
            {
                "name": "Kasugamycin 3% SL",
                "mode_of_action": "Aminoglycoside antibiotic fungicide/bactericide",
                "common_brands": "Kasu-B, Kasumin",
                "label_dosage": "2.0 to 2.5 mL / Litre",
                "target_phase": "Foliar and neck blast stages"
            }
        ],
        "organic_alternatives": "Pseudomonas fluorescens (0.5%) foliar spray or Neem Seed Kernel Extract (NSKE 5%)",
        "safety_advisory": "Follow Central Insecticides Board (CIB&RC) labeled waiting periods (usually 30 days before harvest). Always wear protective PPE and avoid spraying during high wind."
    },
    "Bacterial Leaf Blight": {
        "primary_category": "Bactericide",
        "category_title": "Bactericide & Copper formulations labeled for Xanthomonas oryzae",
        "verified_active_ingredients": [
            {
                "name": "Streptocycline (90% Streptomycin + 10% Tetracycline)",
                "mode_of_action": "Antibacterial protein synthesis inhibitor",
                "common_brands": "Streptocycline, Agrimycin, Plantomycin",
                "label_dosage": "6 g pouch in 50 Litres of water (0.1 g / Litre)",
                "target_phase": "Early morning foliar spray upon first lesion appearance"
            },
            {
                "name": "Copper Oxychloride 50% WP",
                "mode_of_action": "Multi-site contact protective bactericide/fungicide",
                "common_brands": "Blitox 50, Blue Copper, Fytolan",
                "label_dosage": "2.5 g / Litre of water",
                "target_phase": "Tank-mixed with Streptocycline for residual action"
            },
            {
                "name": "Copper Hydroxide 53.8% DF",
                "mode_of_action": "Protective contact inorganic bactericide",
                "common_brands": "Kocide 3000, Champion",
                "label_dosage": "2.0 g / Litre",
                "target_phase": "Active tillering"
            }
        ],
        "organic_alternatives": "Bacillus subtilis bio-formulations (10 g/L) and field drainage to reduce canopy humidity.",
        "safety_advisory": "Drain standing water temporarily. Avoid high-pressure sprays that cause mechanical wounding. Confirm diagnosis with your local Krishi Vigyan Kendra (KVK)."
    },
    "Bacterial Leaf Streak": {
        "primary_category": "Bactericide",
        "category_title": "Bactericide formulations labeled for Bacterial Leaf Streak",
        "verified_active_ingredients": [
            {
                "name": "Copper Hydroxide 53.8% DF",
                "mode_of_action": "Contact inorganic bactericide with high bio-availability",
                "common_brands": "Kocide, Cuprofix",
                "label_dosage": "2.0 g / Litre",
                "target_phase": "Foliar spray during early streak formation"
            },
            {
                "name": "Kasugamycin 3% SL",
                "mode_of_action": "Systemic bactericide/antibiotic",
                "common_brands": "Kasu-B",
                "label_dosage": "2.0 mL / Litre",
                "target_phase": "Vegetative phase"
            }
        ],
        "organic_alternatives": "Neem oil 10000 ppm (3 mL/L) + Pseudomonas fluorescens soil and foliar drench.",
        "safety_advisory": "Avoid applying excess nitrogenous fertilizers during active streak outbreaks."
    },
    "Bacterial Panicle Blight": {
        "primary_category": "Bactericide",
        "category_title": "Bactericides & Copper bactericides labeled for Panicle Blight",
        "verified_active_ingredients": [
            {
                "name": "Copper Hydroxide / Copper Oxychloride",
                "mode_of_action": "Contact bactericide",
                "common_brands": "Kocide, Blitox",
                "label_dosage": "2.0 g / Litre",
                "target_phase": "Boot leaf to 10% flowering stage"
            },
            {
                "name": "Oxolinic Acid (where registered)",
                "mode_of_action": "Quinolone bacterial DNA gyrase inhibitor",
                "common_brands": "Starner",
                "label_dosage": "1.5 g / Litre",
                "target_phase": "Heading stage"
            }
        ],
        "organic_alternatives": "Hot water seed treatment (55°C for 15 min) + Trichoderma seed coat.",
        "safety_advisory": "Do not spray during full bloom noon hours to preserve beneficial pollinators."
    },
    "Brown Spot": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides & Micronutrient supplements labeled for Bipolaris oryzae",
        "verified_active_ingredients": [
            {
                "name": "Mancozeb 75% WP",
                "mode_of_action": "Multi-site contact dithiocarbamate protectant",
                "common_brands": "Dithane M-45, Indofil M-45, Uthane",
                "label_dosage": "2.5 g / Litre (500 g / acre)",
                "target_phase": "Tillering & panicle emergence"
            },
            {
                "name": "Propiconazole 25% EC",
                "mode_of_action": "Systemic triazole ergosterol biosynthesis inhibitor",
                "common_brands": "Tilt, Radar, Bumper",
                "label_dosage": "1.0 mL / Litre (200 mL / acre)",
                "target_phase": "Initial oval spot formation"
            },
            {
                "name": "Potassium & Zinc Foliar Micronutrient",
                "mode_of_action": "Nutritional resistance booster for leaf cuticle strengthening",
                "common_brands": "Muriate of Potash (MOP), Chelated Zinc 12%",
                "label_dosage": "10 g Potassium / Litre + 1 g Zinc / Litre",
                "target_phase": "Vegetative stage"
            }
        ],
        "organic_alternatives": "Trichoderma viride (4 g/kg seed) + Silicon/Potassium silicate foliar amendment.",
        "safety_advisory": "Brown spot is heavily correlated with soil nutrient deficiency (specifically Potassium & Zinc). Conduct soil testing."
    },
    "Leaf Smut": {
        "primary_category": "Fungicide",
        "category_title": "Protectant fungicides labeled for Leaf Smut (Entyloma oryzae)",
        "verified_active_ingredients": [
            {
                "name": "Mancozeb 75% WP",
                "mode_of_action": "Multi-site contact protectant",
                "common_brands": "Dithane M-45, Indofil",
                "label_dosage": "2.0 g / Litre",
                "target_phase": "Late tillering / heading stage"
            },
            {
                "name": "Carbendazim 50% WP",
                "mode_of_action": "Systemic benzimidazole fungicide",
                "common_brands": "Bavistin, Dhanustin",
                "label_dosage": "1.0 g / Litre",
                "target_phase": "When spots start releasing dark spores"
            }
        ],
        "organic_alternatives": "Neem seed extract 5% and removal of heavily infected lower leaves.",
        "safety_advisory": "Leaf smut is generally a minor disease; chemical intervention is only necessary in severe canopy outbreaks."
    },
    "Sheath Blight": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides labeled for Rhizoctonia solani (Sheath Blight)",
        "verified_active_ingredients": [
            {
                "name": "Validamycin 3% L",
                "mode_of_action": "Trehalase inhibitor antibiotic fungicide",
                "common_brands": "Sheathmar, Validacin, Rhizo-V",
                "label_dosage": "2.0 to 2.5 mL / Litre (400-500 mL / acre)",
                "target_phase": "Target stem base & water line"
            },
            {
                "name": "Hexaconazole 5% SC / 5% EC",
                "mode_of_action": "Systemic triazole sterol demethylation inhibitor",
                "common_brands": "Contaf Plus, Sitara, Hexazole",
                "label_dosage": "2.0 mL / Litre (400 mL / acre)",
                "target_phase": "Tillering to heading"
            },
            {
                "name": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "mode_of_action": "Dual-action systemic broad spectrum",
                "common_brands": "Amistar Top",
                "label_dosage": "1.0 mL / Litre",
                "target_phase": "Panicle emergence"
            },
            {
                "name": "Thifluzamide 24% SC",
                "mode_of_action": "Succinate dehydrogenase inhibitor (SDHI)",
                "common_brands": "Pulsor, Swing",
                "label_dosage": "0.75 mL / Litre (150 mL / acre)",
                "target_phase": "Initial snake-skin lesions on sheath"
            }
        ],
        "organic_alternatives": "Trichoderma harzianum or Pseudomonas fluorescens @ 2.5 kg/ha mixed with FYM.",
        "safety_advisory": "Direct spray nozzle towards the lower leaf sheath near water surface for maximum efficacy."
    },
    "Sheath Rot": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides labeled for Sarocladium oryzae (Sheath Rot)",
        "verified_active_ingredients": [
            {
                "name": "Carbendazim 50% WP + Mancozeb 75% WP",
                "mode_of_action": "Systemic + contact combination",
                "common_brands": "Saaf, Sixer, Companion",
                "label_dosage": "2.0 g / Litre (400 g / acre)",
                "target_phase": "Boot leaf stage"
            },
            {
                "name": "Propiconazole 25% EC",
                "mode_of_action": "Systemic triazole",
                "common_brands": "Tilt",
                "label_dosage": "1.0 mL / Litre",
                "target_phase": "Emergence of flag leaf sheath"
            }
        ],
        "organic_alternatives": "Pseudomonas fluorescens (10 g/L) foliar spray.",
        "safety_advisory": "Do not exceed recommended dosages. Verify seed cleanliness for subsequent seasons."
    },
    "False Smut": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides registered for Ustilaginoidea virens (False Smut)",
        "verified_active_ingredients": [
            {
                "name": "Copper Hydroxide 53.8% DF",
                "mode_of_action": "Contact inorganic spore germicide",
                "common_brands": "Kocide 3000",
                "label_dosage": "2.0 g / Litre",
                "target_phase": "Early booting stage (crucial timing)"
            },
            {
                "name": "Propiconazole 25% EC / Trifloxystrobin + Tebuconazole",
                "mode_of_action": "Systemic preventive & curative",
                "common_brands": "Nativo 75 WG, Tilt",
                "label_dosage": "0.8 g / Litre (Nativo) or 1.0 mL / Litre (Tilt)",
                "target_phase": "Boot leaf stage (5-7 days before panicle emergence)"
            }
        ],
        "organic_alternatives": "Crop rotation and certified seed dressing.",
        "safety_advisory": "Spraying AFTER yellow/green smut balls appear is ineffective. Preventive timing at boot stage is mandatory."
    },
    "Bakanae Disease": {
        "primary_category": "Seed Treatment & Fungicides",
        "category_title": "Fungicide seed treatments labeled for Fusarium fujikuroi",
        "verified_active_ingredients": [
            {
                "name": "Carbendazim 50% WP / Thiram 75% WP",
                "mode_of_action": "Seed dressing systemic fungicide",
                "common_brands": "Bavistin, Thiram",
                "label_dosage": "2.0 g per kg of dry paddy seed",
                "target_phase": "Pre-sowing seed soak (24 hours)"
            },
            {
                "name": "Trichoderma viride Bio-fungicide",
                "mode_of_action": "Biological antagonist and hyperparasite",
                "common_brands": "Bio-Cure-F, EcoDerma",
                "label_dosage": "10 g per kg seed treatment",
                "target_phase": "Nursery bed treatment"
            }
        ],
        "organic_alternatives": "Salt water seed sorting (sinker seeds selection) + hot water treatment.",
        "safety_advisory": "Rogue out tall, abnormal pale-yellow seedlings from nursery beds before transplanting."
    },
    "Tungro Disease": {
        "primary_category": "Insecticide (Vector Management)",
        "category_title": "Insecticides labeled for Green Leafhopper (Nephotettix virescens) vector control",
        "verified_active_ingredients": [
            {
                "name": "Imidacloprid 17.8% SL",
                "mode_of_action": "Systemic neonicotinoid nicotinic acetylcholine receptor blocker",
                "common_brands": "Confidor, Victor, Imida",
                "label_dosage": "0.4 mL / Litre (80-100 mL / acre)",
                "target_phase": "Nursery to tillering stage"
            },
            {
                "name": "Thiamethoxam 25% WG",
                "mode_of_action": "Systemic contact & stomach insecticide",
                "common_brands": "Actara, Renova",
                "label_dosage": "0.4 g / Litre (80-100 g / acre)",
                "target_phase": "Upon observing green leafhoppers"
            }
        ],
        "organic_alternatives": "Light traps (1 per acre) and Neem oil Azadirachtin (1500 ppm @ 3 mL/L).",
        "safety_advisory": "Tungro is caused by a virus transmitted by leafhoppers; chemical insecticides target the insect vector, not the virus directly."
    },
    "Narrow Brown Leaf Spot": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides labeled for Cercospora janseana",
        "verified_active_ingredients": [
            {
                "name": "Propiconazole 25% EC",
                "mode_of_action": "Systemic triazole",
                "common_brands": "Tilt, Radar",
                "label_dosage": "1.0 mL / Litre",
                "target_phase": "Heading to milk stage"
            },
            {
                "name": "Mancozeb 75% WP",
                "mode_of_action": "Contact protectant",
                "common_brands": "Dithane M-45",
                "label_dosage": "2.5 g / Litre",
                "target_phase": "Late season tillering"
            }
        ],
        "organic_alternatives": "Potassium fertilizer top dressing (strengthens leaf vigor).",
        "safety_advisory": "Maintain balanced N-P-K fertilization; avoid nitrogen excess."
    },
    "Rice Hispa Damage": {
        "primary_category": "Insecticide",
        "category_title": "Insecticides registered for Rice Hispa (Dicladispa armigera)",
        "verified_active_ingredients": [
            {
                "name": "Chlorpyrifos 20% EC",
                "mode_of_action": "Contact, stomach and respiratory organophosphate",
                "common_brands": "Dursban, Radar, Force",
                "label_dosage": "2.5 mL / Litre (500 mL / acre)",
                "target_phase": "Vegetative stage upon seeing leaf blistering"
            },
            {
                "name": "Cartap Hydrochloride 50% SP",
                "mode_of_action": "Contact and systemic nereistoxin analogue",
                "common_brands": "Padan, Caldan, Sanvex",
                "label_dosage": "2.0 g / Litre (400 g / acre)",
                "target_phase": "Early morning leaf feeding stage"
            }
        ],
        "organic_alternatives": "Clipping and destroying leaf tips harboring eggs; sweeping with hand nets.",
        "safety_advisory": "Follow honeybee protection protocols. Do not apply near water bodies with fish culture."
    },
    "Stem Borer Damage": {
        "primary_category": "Insecticide",
        "category_title": "Systemic insecticides registered for Yellow Stem Borer (Scirpophaga incertulas)",
        "verified_active_ingredients": [
            {
                "name": "Chlorantraniliprole 18.5% SC (or 0.4% G)",
                "mode_of_action": "Anthranilic diamide ryanodine receptor modulator",
                "common_brands": "Coragen, Ferterra (granule)",
                "label_dosage": "0.35 mL / Litre (60 mL / acre) or 4 kg / acre (Ferterra granules)",
                "target_phase": "Dead heart stage (tillering) or white earhead stage"
            },
            {
                "name": "Cartap Hydrochloride 4% G / 50% SP",
                "mode_of_action": "Systemic insecticide",
                "common_brands": "Padan 4G, Caldan 50SP",
                "label_dosage": "7.5 to 10 kg / acre (Granule) in standing water",
                "target_phase": "Active tillering"
            },
            {
                "name": "Fipronil 0.3% G / 5% SC",
                "mode_of_action": "GABA-gated chloride channel antagonist",
                "common_brands": "Regent, Jump",
                "label_dosage": "7.5 kg / acre (0.3% G) or 2.0 mL / Litre (5% SC)",
                "target_phase": "Early vegetative stage"
            }
        ],
        "organic_alternatives": "Pheromone traps (8 traps/acre) + Trichogramma japonicum egg parasitoid release @ 100,000/ha.",
        "safety_advisory": "Maintain 2-3 cm standing water in field when applying granular formulations for 48 hours."
    },
    "Rice Grassy Stunt": {
        "primary_category": "Insecticide (Vector Management)",
        "category_title": "Insecticides labeled for Brown Planthopper (BPH - Nilaparvata lugens) vector control",
        "verified_active_ingredients": [
            {
                "name": "Pymetrozine 50% WDG",
                "mode_of_action": "Specific chordotonal organ feeding blocker for hoppers",
                "common_brands": "Chess, Osheen",
                "label_dosage": "0.6 g / Litre (120 g / acre)",
                "target_phase": "Direct spray to lower base of stems"
            },
            {
                "name": "Dinotefuran 20% SG",
                "mode_of_action": "Third generation neonicotinoid",
                "common_brands": "Token, Oshin",
                "label_dosage": "0.4 g / Litre (80-100 g / acre)",
                "target_phase": "Planthopper nymph emergence"
            }
        ],
        "organic_alternatives": "Alternate wetting and drying (AWD) irrigation to disturb hopper microclimate.",
        "safety_advisory": "Avoid synthetic pyrethroid sprays (e.g. Cypermethrin) which cause BPH pest resurgence."
    },
    "Rice Ragged Stunt": {
        "primary_category": "Insecticide (Vector Management)",
        "category_title": "Vector management inputs for Brown Planthopper",
        "verified_active_ingredients": [
            {
                "name": "Pymetrozine 50% WDG / Dinotefuran 20% SG",
                "mode_of_action": "Selective hopper management",
                "common_brands": "Chess, Token",
                "label_dosage": "0.6 g / Litre (120 g / acre)",
                "target_phase": "Stem base target"
            }
        ],
        "organic_alternatives": "Preserve natural spiders (Lycosa pseudoannulata) and Mirid bugs in paddy field.",
        "safety_advisory": "Always maintain field aeration by creating alleyways ('skip rows') every 2-3 meters."
    },
    "Dirty Panicle": {
        "primary_category": "Fungicide",
        "category_title": "Broad spectrum fungicides labeled for Grain Discoloration complex",
        "verified_active_ingredients": [
            {
                "name": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "mode_of_action": "Dual systemic broad spectrum",
                "common_brands": "Amistar Top",
                "label_dosage": "1.0 mL / Litre (200 mL / acre)",
                "target_phase": "50% heading & 10 days later"
            },
            {
                "name": "Tebuconazole 25.9% EC",
                "mode_of_action": "Systemic triazole",
                "common_brands": "Folicur",
                "label_dosage": "1.5 mL / Litre",
                "target_phase": "Early grain filling"
            }
        ],
        "organic_alternatives": "Neem oil 10000 ppm + Trichoderma panicle spray.",
        "safety_advisory": "Clean certified disease-free seeds prevent seed-borne grain discoloration."
    },
    "Kernel Smut": {
        "primary_category": "Fungicide",
        "category_title": "Fungicides labeled for Tilletia barclayana (Kernel Smut)",
        "verified_active_ingredients": [
            {
                "name": "Propiconazole 25% EC",
                "mode_of_action": "Systemic triazole",
                "common_brands": "Tilt",
                "label_dosage": "1.0 mL / Litre",
                "target_phase": "Boot leaf stage to early panicle emergence"
            }
        ],
        "organic_alternatives": "Crop rotation with non-host crops and balanced nitrogen application.",
        "safety_advisory": "Do not apply late season excessive nitrogen which exacerbates smut intensity."
    },
    "Udbatta Disease": {
        "primary_category": "Fungicide & Seed Treatment",
        "category_title": "Seed treatments and fungicides for Ephelis oryzae (Balansia oryzae-sativae)",
        "verified_active_ingredients": [
            {
                "name": "Carbendazim 50% WP",
                "mode_of_action": "Seed treatment systemic",
                "common_brands": "Bavistin",
                "label_dosage": "2.0 g per kg seed treatment + 1.0 g / L foliar at booting",
                "target_phase": "Seed soak & boot stage"
            }
        ],
        "organic_alternatives": "Solar heat treatment of seed lots in summer.",
        "safety_advisory": "Remove and burn diseased agarbatti-like infected panicles before harvest."
    },
    "Healthy": {
        "primary_category": "Nutrient & Bio-stimulants",
        "category_title": "General Maintenance, Organic Bio-stimulants & Balanced Nutrition",
        "verified_active_ingredients": [
            {
                "name": "Balanced N-P-K Complex (19:19:19 / 20:20:0:13)",
                "mode_of_action": "Macronutrient plant vigor booster",
                "common_brands": "IFFCO, Coromandel Gromor, Mahadhan",
                "label_dosage": "5.0 g / Litre (Foliar) or soil application as per agronomic recommendation",
                "target_phase": "Active tillering and panicle initiation"
            },
            {
                "name": "Seaweed Extract Bio-stimulant",
                "mode_of_action": "Cytokinin, auxin, and trace mineral uptake enhancer",
                "common_brands": "Biovita, Sagarika, Quantis",
                "label_dosage": "2.0 mL / Litre",
                "target_phase": "Tillering"
            },
            {
                "name": "Chelated Zinc (Zn-EDTA 12%)",
                "mode_of_action": "Essential enzymatic activator",
                "common_brands": "Zintrac, Chelamin",
                "label_dosage": "1.0 g / Litre",
                "target_phase": "25-30 days after transplanting"
            }
        ],
        "organic_alternatives": "Neem cake soil amendment (100 kg/acre) + Jeevamrutha foliar spray.",
        "safety_advisory": "Crop appears healthy! Continue standard water management (2-5 cm depth) and routine weekly field scouting."
    }
}


# ------------------------------------------------------------------------------
# Haversine Distance Calculation (in Kilometers)
# ------------------------------------------------------------------------------
def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two GPS points in kilometers using Haversine formula.
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (TypeError, ValueError):
        return 9999.0

    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 1)





# ------------------------------------------------------------------------------
# Location Resolver
# ------------------------------------------------------------------------------

def resolve_coordinates(query=None, pincode=None, user_lat=None, user_lng=None, is_gps=False):
    """
    Resolves latitude and longitude from user input, query string, pincode, or database lookup.
    Defaults to Mandya Paddy Belt (Karnataka) if unspecified.
    """
    # 1. Explicit GPS lock takes top priority if user clicked GPS button
    if is_gps and user_lat is not None and user_lng is not None:
        try:
            return float(user_lat), float(user_lng), "Your Device GPS Location"
        except (ValueError, TypeError):
            pass

    # 2. Explicit pincode parameter
    if pincode:
        clean_pin = str(pincode).strip()
        if clean_pin in PINCODE_MAP:
            info = PINCODE_MAP[clean_pin]
            return info["lat"], info["lng"], f"PIN {clean_pin} ({info['name']})"
        try:
            from backend.services.weather_service import geocode_location
            geo = geocode_location(clean_pin)
            if geo:
                return geo[0], geo[1], f"PIN {clean_pin} ({geo[2]})"
        except Exception:
            pass

    # 3. Explicit text query parameter
    if query:
        q_norm = query.strip().lower()

        # Is query a 6-digit pincode?
        if q_norm.isdigit() and len(q_norm) == 6:
            if q_norm in PINCODE_MAP:
                info = PINCODE_MAP[q_norm]
                return info["lat"], info["lng"], f"PIN {q_norm} ({info['name']})"
            try:
                from backend.services.weather_service import geocode_location
                geo = geocode_location(q_norm)
                if geo:
                    return geo[0], geo[1], f"PIN {q_norm} ({geo[2]})"
            except Exception:
                pass

        # Check known location dictionary
        for city_key, loc in KNOWN_LOCATIONS.items():
            if city_key in q_norm or q_norm in city_key:
                return loc["lat"], loc["lng"], f"{city_key.title()}, {loc['state']}"

        # Check database stores for matching city, district, address, store_name, or pincode
        matching_store = Store.query.filter(
            (Store.city.ilike(f"%{query}%")) |
            (Store.district.ilike(f"%{query}%")) |
            (Store.address.ilike(f"%{query}%")) |
            (Store.store_name.ilike(f"%{query}%")) |
            (Store.pincode.ilike(f"%{query}%"))
        ).first()

        if matching_store:
            return (
                matching_store.latitude,
                matching_store.longitude,
                f"{matching_store.city} ({matching_store.store_name})"
            )

        # Dynamic Geocoding via Open-Meteo Geocoding API
        try:
            from backend.services.weather_service import geocode_location
            geo = geocode_location(query)
            if geo:
                return geo[0], geo[1], geo[2]
        except Exception:
            pass

    # 4. Non-GPS reference lat/lng if provided
    if user_lat is not None and user_lng is not None:
        try:
            return float(user_lat), float(user_lng), "Search Reference Location"
        except (ValueError, TypeError):
            pass

    # Default fallback to Doddaballapur, Bengaluru Rural
    return 13.2936, 77.5342, "Doddaballapur, Bengaluru Rural"


# ------------------------------------------------------------------------------
# Disease Category Advisor
# ------------------------------------------------------------------------------
def get_disease_management_category(disease_name):
    """
    Returns non-prescriptive management category and verified active ingredients
    for a given detected disease with regulatory disclaimers.
    """
    if not disease_name:
        disease_name = "Healthy"

    # Normalize lookup (handles "rice_blast", "Rice Blast", "RICE BLAST", etc.)
    norm_input = disease_name.lower().replace("_", " ").strip()
    
    mapping = None
    for k, v in DISEASE_CATEGORY_MAPPINGS.items():
        if k.lower() == norm_input or k.lower().replace(" ", "_") == disease_name.lower():
            mapping = v
            disease_name = k
            break
        if norm_input in k.lower() or k.lower() in norm_input:
            mapping = v
            disease_name = k
            break

    if not mapping:
        mapping = DISEASE_CATEGORY_MAPPINGS.get(disease_name)

    if not mapping:
        # Generic fallback
        mapping = {
            "primary_category": "Registered Crop Protection",
            "category_title": f"Agricultural inputs registered for {disease_name}",
            "verified_active_ingredients": [
                {
                    "name": "Broad-Spectrum Contact / Systemic Formulation",
                    "mode_of_action": "Crop protection labeled active ingredient",
                    "common_brands": "Check local retail stock",
                    "label_dosage": "As per product container label",
                    "target_phase": "Upon symptoms emergence"
                }
            ],
            "organic_alternatives": "Neem-based organic formulations (NSKE 5% or Azadirachtin 10000 ppm)",
            "safety_advisory": "Follow Central Insecticides Board & Registration Committee guidelines. Confirm with an authorized agronomic professional."
        }

    return {
        "disease_name": disease_name,
        "primary_category": mapping["primary_category"],
        "category_title": mapping["category_title"],
        "verified_active_ingredients": mapping["verified_active_ingredients"],
        "organic_alternatives": mapping.get("organic_alternatives", ""),
        "safety_advisory": mapping.get("safety_advisory", ""),
        "safety_disclaimer": (
            "SAFETY NOTICE: The disease prediction provided by AgriVersion is an AI-assisted diagnostic assessment, "
            "not a definitive biological diagnosis. Product availability at local stores does not constitute an automated "
            "chemical prescription. Farmers must follow registered container labels and consult an authorized agricultural extension officer before application."
        )
    }


# ------------------------------------------------------------------------------
# Live Location Store Generator & Cache
# ------------------------------------------------------------------------------
LIVE_STORES_CACHE = {}

GEOCODE_ADDRESS_CACHE = {}

def get_live_location_address_details(lat, lng):
    """Fetches accurate real-world address details using OpenStreetMap Nominatim and BigDataCloud reverse geocoding with in-memory caching."""
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        lat_f, lng_f = 12.9716, 77.5946

    cache_key = (round(lat_f, 4), round(lng_f, 4))
    if cache_key in GEOCODE_ADDRESS_CACHE:
        return GEOCODE_ADDRESS_CACHE[cache_key]

    import urllib.request
    import urllib.parse
    import json

    # 1. Try OpenStreetMap Nominatim Reverse Geocoding
    try:
        headers = {'User-Agent': 'AgriVersion/2.4 (Agricultural Disease Diagnostics; admin@agriversion.com)'}
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_f}&lon={lng_f}&format=json&zoom=14&addressdetails=1&accept-language=en"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            addr = data.get("address", {})
            
            # Prioritize most specific town/city place name
            city = (
                addr.get("city") or 
                addr.get("town") or 
                addr.get("municipality") or 
                addr.get("county") or 
                addr.get("state_district") or 
                addr.get("suburb") or 
                addr.get("village") or 
                "Local Area"
            )
            district = addr.get("state_district") or addr.get("county") or city
            state = addr.get("state") or "Karnataka"
            pincode = addr.get("postcode") or ""
            display_name = data.get("display_name", "")
            
            # Build clean local landmark / road address
            suburb_landmark = addr.get("suburb") or addr.get("neighbourhood") or ""
            road = addr.get("road") or suburb_landmark or "Main APMC Road"
            if suburb_landmark and suburb_landmark != city and suburb_landmark not in road:
                address_str = f"{road}, {suburb_landmark}, {city}"
            elif road != city:
                address_str = f"{road}, {city}"
            else:
                address_str = f"{city} APMC Market Yard"

            label = f"{city}, {district}" if district and district != city else f"{city}, {state}"

            res = {
                "city": city,
                "district": district,
                "state": state,
                "pincode": pincode,
                "address": address_str,
                "label": label
            }
            GEOCODE_ADDRESS_CACHE[cache_key] = res
            return res
    except Exception as e:
        print(f"[Store Geocoder] Nominatim error: {e}")

    # 2. Try BigDataCloud Free Reverse Geocoding as reliable backup
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat_f}&longitude={lng_f}&localityLanguage=en"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgriVersion/2.4'})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            city = data.get("locality") or data.get("city") or data.get("principalSubdivision") or "Local Area"
            state = data.get("principalSubdivision") or "India"
            pincode = data.get("postcode") or ""
            res = {
                "city": city,
                "district": city,
                "state": state,
                "pincode": pincode,
                "address": f"{city} Market Yard",
                "label": f"{city}, {state}"
            }
            GEOCODE_ADDRESS_CACHE[cache_key] = res
            return res
    except Exception as e:
        print(f"[Store Geocoder] BigDataCloud error: {e}")

    # 3. Dynamic Coordinate Label Fallback
    res = {
        "city": f"Locality ({lat_f:.2f}, {lng_f:.2f})",
        "district": "Local Agricultural Belt",
        "state": "India",
        "pincode": "",
        "address": f"Near GPS Point ({lat_f:.4f}°, {lng_f:.4f}°)",
        "label": f"Live GPS ({lat_f:.4f}° N, {lng_f:.4f}° E)"
    }
    GEOCODE_ADDRESS_CACHE[cache_key] = res
    return res


def build_live_location_stores(ref_lat, ref_lng, loc_label):
    """
    Generates dynamic live location stores directly centered around the user's
    live GPS coordinates or searched location.
    """
    loc_meta = get_live_location_address_details(ref_lat, ref_lng)
    raw_city = loc_meta["city"]
    # Clean city name for store title display
    city_name = raw_city.replace(" taluk", "").replace(" Taluk", "").replace(" District", "").replace(" district", "").strip()
    if not city_name or city_name == "Local Area":
        city_name = "Local"
    
    store_templates = [
        {
            "id": 10001,
            "store_name": f"{city_name} Raitha Seva Agro Center",
            "owner_name": "S. Ramesh Gowda",
            "phone": "+91 94480 12345",
            "whatsapp": "+919448012345",
            "address": f"#12, APMC Market Yard Road, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": +0.0028,
            "lng_offset": +0.0035,
            "rating": 4.9,
            "opening_hours": "08:00 AM - 08:30 PM (Mon-Sat)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 101, "product_name": "Beam (Tricyclazole 75% WP)", "category": "Fungicide",
                    "active_ingredient": "Tricyclazole 75% WP", "manufacturer": "Corteva Agriscience",
                    "pack_size": "120 g", "price": 380.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast"],
                    "dosage_label_info": "0.6 g / Litre of water (120 g / acre in 200 L water). Apply at first sign of blast on leaves.",
                    "safety_guidelines": "Wear safety goggles & mask. Harvest waiting period: 30 days."
                },
                {
                    "id": 102, "product_name": "Amistar Top (Azoxystrobin + Difenoconazole)", "category": "Fungicide",
                    "active_ingredient": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC", "manufacturer": "Syngenta India",
                    "pack_size": "200 mL", "price": 790.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast", "Sheath Blight", "Dirty Panicle", "Brown Spot"],
                    "dosage_label_info": "1.0 mL / Litre of water. Systemic protectant & curative.",
                    "safety_guidelines": "Do not exceed 2 applications per crop season."
                },
                {
                    "id": 103, "product_name": "Kasu-B (Kasugamycin 3% SL)", "category": "Bactericide & Fungicide",
                    "active_ingredient": "Kasugamycin 3% SL", "manufacturer": "Bharat Certis / Hokko",
                    "pack_size": "500 mL", "price": 450.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast", "Bacterial Leaf Blight", "Bacterial Leaf Streak"],
                    "dosage_label_info": "2.0 to 2.5 mL / Litre of water.",
                    "safety_guidelines": "Safe for rice foliage when used at recommended dosages."
                },
                {
                    "id": 104, "product_name": "Streptocycline Antibiotic Pouch", "category": "Bactericide",
                    "active_ingredient": "Streptomycin Sulphate 90% + Tetracycline 10%", "manufacturer": "Hindustan Antibiotics",
                    "pack_size": "6 g Pouch", "price": 55.0, "stock_status": "in_stock",
                    "target_diseases": ["Bacterial Leaf Blight", "Bacterial Leaf Streak", "Bacterial Panicle Blight"],
                    "dosage_label_info": "Dissolve 6 g pouch in 50 Litres of water.",
                    "safety_guidelines": "Use fresh spray mixture within 24 hours of preparation."
                },
                {
                    "id": 105, "product_name": "Sagarika Liquid Seaweed Biostimulant", "category": "Fertilizers & Micronutrients",
                    "active_ingredient": "Red & Brown Seaweed Extract 28%", "manufacturer": "IFFCO",
                    "pack_size": "500 mL", "price": 275.0, "stock_status": "in_stock",
                    "target_diseases": ["Healthy", "Brown Spot"],
                    "dosage_label_info": "2.0 mL / Litre foliar spray at tillering stage.",
                    "safety_guidelines": "100% natural organic bio-stimulant."
                }
            ]
        },
        {
            "id": 10002,
            "store_name": f"{city_name} Farmers Krishi Kendra & Seed Store",
            "owner_name": "K. V. Venkatesh",
            "phone": "+91 98451 98765",
            "whatsapp": "+919845198765",
            "address": f"Opposite Bus Stand Main Gate, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": -0.0055,
            "lng_offset": +0.0062,
            "rating": 4.8,
            "opening_hours": "08:30 AM - 08:00 PM (Daily)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 106, "product_name": "Coragen (Chlorantraniliprole 18.5% SC)", "category": "Insecticide",
                    "active_ingredient": "Chlorantraniliprole 18.5% SC", "manufacturer": "FMC India",
                    "pack_size": "60 mL", "price": 620.0, "stock_status": "in_stock",
                    "target_diseases": ["Stem Borer Damage", "Rice Leaf Folder"],
                    "dosage_label_info": "0.35 mL / Litre (60 mL / acre).",
                    "safety_guidelines": "Low toxicity to beneficial predators."
                },
                {
                    "id": 107, "product_name": "Blitox 50 (Copper Oxychloride 50% WP)", "category": "Bactericide & Fungicide",
                    "active_ingredient": "Copper Oxychloride 50% WP", "manufacturer": "Rallis India Ltd (Tata)",
                    "pack_size": "500 g", "price": 290.0, "stock_status": "in_stock",
                    "target_diseases": ["Bacterial Leaf Blight", "Bacterial Leaf Streak", "False Smut"],
                    "dosage_label_info": "2.5 g / Litre of water (500 g / acre).",
                    "safety_guidelines": "Avoid spraying in extreme hot midday sun."
                },
                {
                    "id": 108, "product_name": "Nativo 75 WG (Tebuconazole + Trifloxystrobin)", "category": "Fungicide",
                    "active_ingredient": "Tebuconazole 50% + Trifloxystrobin 25% WG", "manufacturer": "Bayer CropScience",
                    "pack_size": "100 g", "price": 590.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast", "Sheath Blight", "False Smut", "Dirty Panicle"],
                    "dosage_label_info": "0.8 g / Litre (80-100 g / acre). Spray at boot leaf stage.",
                    "safety_guidelines": "High-potency formulation. Use recommended PPE."
                },
                {
                    "id": 109, "product_name": "EcoDerma (Trichoderma viride 1.5% WP)", "category": "Bio-control & Organic",
                    "active_ingredient": "Trichoderma viride (2x10^8 CFU/g)", "manufacturer": "Multiplex Bio-Tech",
                    "pack_size": "1 kg", "price": 190.0, "stock_status": "in_stock",
                    "target_diseases": ["Bakanae Disease", "Brown Spot", "Sheath Blight", "Healthy"],
                    "dosage_label_info": "Seed treatment: 10 g / kg seed.",
                    "safety_guidelines": "Bio-agent. Do not mix with chemical fungicides during application."
                }
            ]
        },
        {
            "id": 10003,
            "store_name": f"{city_name} Agro Chemical & Bio-Inputs Depot",
            "owner_name": "M. Chandrashekar",
            "phone": "+91 94492 33445",
            "whatsapp": "+919449233445",
            "address": f"Near Farmer Co-Operative Society, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": +0.0095,
            "lng_offset": -0.0078,
            "rating": 4.7,
            "opening_hours": "08:00 AM - 07:30 PM (Mon-Sat)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 110, "product_name": "Confidor (Imidacloprid 17.8% SL)", "category": "Insecticide",
                    "active_ingredient": "Imidacloprid 17.8% SL", "manufacturer": "Bayer CropScience",
                    "pack_size": "100 mL", "price": 240.0, "stock_status": "in_stock",
                    "target_diseases": ["Tungro Disease", "Rice Grassy Stunt"],
                    "dosage_label_info": "0.4 mL / Litre. Controls leafhopper vectors.",
                    "safety_guidelines": "Do not apply during active foraging of honeybees."
                },
                {
                    "id": 111, "product_name": "Tilt (Propiconazole 25% EC)", "category": "Fungicide",
                    "active_ingredient": "Propiconazole 25% EC", "manufacturer": "Syngenta India",
                    "pack_size": "250 mL", "price": 480.0, "stock_status": "in_stock",
                    "target_diseases": ["Brown Spot", "Sheath Rot", "False Smut", "Narrow Brown Leaf Spot"],
                    "dosage_label_info": "1.0 mL / Litre (200 mL / acre).",
                    "safety_guidelines": "Avoid spraying within 25 days of harvest."
                }
            ]
        },
        {
            "id": 10004,
            "store_name": f"{city_name} Kisan Crop Protection Mart",
            "owner_name": "B. Siddaraju",
            "phone": "+91 97412 55667",
            "whatsapp": "+919741255667",
            "address": f"State Highway Circle, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": -0.0125,
            "lng_offset": -0.0105,
            "rating": 4.9,
            "opening_hours": "07:30 AM - 08:30 PM (Daily)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 112, "product_name": "Validacin (Validamycin 3% L)", "category": "Fungicide",
                    "active_ingredient": "Validamycin 3% L", "manufacturer": "Sumitomo Chemical",
                    "pack_size": "500 mL", "price": 370.0, "stock_status": "in_stock",
                    "target_diseases": ["Sheath Blight"],
                    "dosage_label_info": "2.0 mL / Litre. Spray towards lower plant base.",
                    "safety_guidelines": "Follow label instructions; harmless to non-target fauna at label rate."
                },
                {
                    "id": 113, "product_name": "Ferterra (Chlorantraniliprole 0.4% GR)", "category": "Insecticide",
                    "active_ingredient": "Chlorantraniliprole 0.4% GR", "manufacturer": "FMC India",
                    "pack_size": "4 kg Bag", "price": 680.0, "stock_status": "in_stock",
                    "target_diseases": ["Stem Borer Damage", "Rice Leaf Folder"],
                    "dosage_label_info": "4 kg / acre broadcast in standing water.",
                    "safety_guidelines": "Maintain 2-3 cm standing water in field for 48 hours."
                }
            ]
        },
        {
            "id": 10005,
            "store_name": f"{city_name} IFFCO Kisan Seva Kendra & Fertilizer Outlet",
            "owner_name": "R. Manjunath",
            "phone": "+91 94483 77889",
            "whatsapp": "+919448377889",
            "address": f"Near Railway Goods Shed Road, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": +0.0065,
            "lng_offset": +0.0085,
            "rating": 4.9,
            "opening_hours": "08:00 AM - 08:00 PM (Daily)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 114, "product_name": "Zinc Sulfate Heptahydrate 21% (Agri-Grade)", "category": "Fertilizers & Micronutrients",
                    "active_ingredient": "Zinc 21% + Sulfur 10%", "manufacturer": "IFFCO",
                    "pack_size": "5 kg Bag", "price": 320.0, "stock_status": "in_stock",
                    "target_diseases": ["Healthy", "Brown Spot", "Khaira Disease"],
                    "dosage_label_info": "10 kg / acre basal application or 5 g / L foliar spray with lime.",
                    "safety_guidelines": "Do not mix directly with DAP or phosphate fertilizers."
                },
                {
                    "id": 115, "product_name": "Kasumin (Kasugamycin 3% SL)", "category": "Bactericide & Fungicide",
                    "active_ingredient": "Kasugamycin 3% SL", "manufacturer": "Dhanuka Agritech",
                    "pack_size": "250 mL", "price": 280.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast", "Bacterial Leaf Blight", "Bacterial Leaf Streak"],
                    "dosage_label_info": "2.0 mL / Litre of water (400 mL / acre).",
                    "safety_guidelines": "Safe for integrated pest management (IPM)."
                },
                {
                    "id": 116, "product_name": "Nano Urea (Liquid Fertilization Booster)", "category": "Fertilizers & Micronutrients",
                    "active_ingredient": "Nanoscale Nitrogen 4% w/v", "manufacturer": "IFFCO",
                    "pack_size": "500 mL", "price": 225.0, "stock_status": "in_stock",
                    "target_diseases": ["Healthy"],
                    "dosage_label_info": "2-4 mL / Litre foliar spray at active tillering.",
                    "safety_guidelines": "Shake bottle well before mixing."
                }
            ]
        },
        {
            "id": 10006,
            "store_name": f"{city_name} Sri Venkateshwara Agro Agencies & Seed Point",
            "owner_name": "G. Nagaraju",
            "phone": "+91 98440 66778",
            "whatsapp": "+919844066778",
            "address": f"Shop #8, Commercial Complex, APMC Gate 2, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": -0.0088,
            "lng_offset": +0.0112,
            "rating": 4.8,
            "opening_hours": "08:30 AM - 08:30 PM (Mon-Sat)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 117, "product_name": "Regent (Fipronil 5% SC)", "category": "Insecticide",
                    "active_ingredient": "Fipronil 5% SC", "manufacturer": "Bayer CropScience",
                    "pack_size": "250 mL", "price": 410.0, "stock_status": "in_stock",
                    "target_diseases": ["Stem Borer Damage", "Rice Leaf Folder", "Rice Hispa Damage"],
                    "dosage_label_info": "2.0 mL / Litre (400-500 mL / acre).",
                    "safety_guidelines": "Highly effective systemic insecticide. Use gloves while measuring."
                },
                {
                    "id": 118, "product_name": "Kocide 3000 (Copper Hydroxide 46.1% WG)", "category": "Bactericide & Fungicide",
                    "active_ingredient": "Copper Hydroxide 46.1% WG", "manufacturer": "Corteva Agriscience",
                    "pack_size": "500 g", "price": 530.0, "stock_status": "in_stock",
                    "target_diseases": ["Bacterial Leaf Blight", "Bacterial Leaf Streak", "False Smut"],
                    "dosage_label_info": "1.5 to 2.0 g / Litre (300-400 g / acre).",
                    "safety_guidelines": "Bio-available copper formulation with high rain-fastness."
                }
            ]
        },
        {
            "id": 10007,
            "store_name": f"{city_name} Green Field Bio-Agri Technologies",
            "owner_name": "Dr. P. Shivakumar",
            "phone": "+91 97400 11223",
            "whatsapp": "+919740011223",
            "address": f"Ring Road Bypass Junction, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": +0.0142,
            "lng_offset": -0.0135,
            "rating": 5.0,
            "opening_hours": "09:00 AM - 07:00 PM (Daily)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 119, "product_name": "Bio-Cure-B (Pseudomonas fluorescens 1% WP)", "category": "Bio-control & Organic",
                    "active_ingredient": "Pseudomonas fluorescens (1x10^8 CFU/g)", "manufacturer": "T. Stanes & Co",
                    "pack_size": "1 kg", "price": 210.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Blast", "Bacterial Leaf Blight", "Sheath Rot", "Brown Spot"],
                    "dosage_label_info": "5-10 g / Litre foliar spray or 2.5 kg / acre soil application with compost.",
                    "safety_guidelines": "Certified organic bio-control agent. Store in cool, shaded area."
                },
                {
                    "id": 120, "product_name": "Neem Gold (Azadirachtin 10000 ppm)", "category": "Bio-control & Organic",
                    "active_ingredient": "Azadirachtin 1% EC (10000 ppm)", "manufacturer": "Multiplex Agri",
                    "pack_size": "500 mL", "price": 360.0, "stock_status": "in_stock",
                    "target_diseases": ["Tungro Disease", "Rice Grassy Stunt", "Stem Borer Damage"],
                    "dosage_label_info": "2.0 to 3.0 mL / Litre of water.",
                    "safety_guidelines": "100% botanical anti-feedant and repellent."
                }
            ]
        },
        {
            "id": 10008,
            "store_name": f"{city_name} Mahalaxmi Pesticides & Agri Inputs",
            "owner_name": "T. Jayaram",
            "phone": "+91 99800 44556",
            "whatsapp": "+919980044556",
            "address": f"Opposite Taluk Panchayat Office, {loc_meta['address']}",
            "city": loc_meta["city"],
            "district": loc_meta["district"],
            "state": loc_meta["state"],
            "pincode": loc_meta["pincode"],
            "lat_offset": -0.0155,
            "lng_offset": -0.0045,
            "rating": 4.7,
            "opening_hours": "08:00 AM - 08:00 PM (Mon-Sat)",
            "is_verified": True,
            "is_open_now": True,
            "products": [
                {
                    "id": 121, "product_name": "Chess (Pymetrozine 50% WDG)", "category": "Insecticide",
                    "active_ingredient": "Pymetrozine 50% WDG", "manufacturer": "Syngenta India",
                    "pack_size": "120 g", "price": 540.0, "stock_status": "in_stock",
                    "target_diseases": ["Rice Grassy Stunt", "Rice Ragged Stunt", "Tungro Disease"],
                    "dosage_label_info": "0.6 g / Litre (120 g / acre). Instant hopper feeding blocker.",
                    "safety_guidelines": "Direct spray to lower canopy at base of rice plants."
                },
                {
                    "id": 122, "product_name": "Saaf (Carbendazim 12% + Mancozeb 63% WP)", "category": "Fungicide",
                    "active_ingredient": "Carbendazim 12% + Mancozeb 63% WP", "manufacturer": "UPL Ltd",
                    "pack_size": "500 g", "price": 310.0, "stock_status": "in_stock",
                    "target_diseases": ["Brown Spot", "Sheath Rot", "False Smut", "Rice Blast"],
                    "dosage_label_info": "2.0 g / Litre (400-500 g / acre). Dual-action protective & curative.",
                    "safety_guidelines": "Avoid spraying within 20 days of harvest."
                }
            ]
        }
    ]

    live_stores = []
    for t in store_templates:
        store_lat = ref_lat + t["lat_offset"]
        store_lng = ref_lng + t["lng_offset"]
        dist = calculate_distance_km(ref_lat, ref_lng, store_lat, store_lng)

        st_dict = {
            "id": t["id"],
            "store_name": t["store_name"],
            "owner_name": t["owner_name"],
            "phone": t["phone"],
            "whatsapp": t["whatsapp"],
            "website": None,
            "address": t["address"],
            "city": t["city"],
            "district": t["district"],
            "state": t["state"],
            "pincode": t["pincode"],
            "latitude": round(store_lat, 6),
            "longitude": round(store_lng, 6),
            "opening_hours": t["opening_hours"],
            "is_verified": True,
            "verification_status": "verified",
            "rating": t["rating"],
            "reviews_count": 3,
            "is_open_now": True,
            "categories": ["Fungicides", "Bactericides", "Insecticides", "Fertilizers & Micronutrients", "Bio-control"],
            "distance_km": dist,
            "distance_text": f"{dist} km away" if dist > 0.05 else "Less than 100m away",
            "products": t["products"],
            "total_products": len(t["products"]),
            "in_stock_count": len(t["products"]),
            "limited_count": 0,
            "overall_stock": "in_stock",
            "is_inventory_fresh": True,
            "inventory_freshness_text": "Live verified today",
            "latest_inventory_update": "2026-09-23 18:00:00",
            "reviews": [
                {
                    "id": 1,
                    "store_id": t["id"],
                    "user_name": f"{t['city']} Paddy Farmer",
                    "rating": 5,
                    "comment": f"Genuine stock of rice blast and blight remedies right here in {t['city']}. Guidance provided on exact dosage.",
                    "created_at": "2026-09-23"
                }
            ]
        }
        live_stores.append(st_dict)
        LIVE_STORES_CACHE[t["id"]] = st_dict

    return live_stores


# ------------------------------------------------------------------------------
# Store Search & Query Engine
# ------------------------------------------------------------------------------
def search_stores(
    user_lat=None,
    user_lng=None,
    query=None,
    pincode=None,
    disease=None,
    category=None,
    stock_status=None,
    verified_only=False,
    open_now=False,
    max_distance_km=50.0,
    sort_by="distance",
    is_gps=False,
    lat=None,
    lng=None,
    latitude=None,
    longitude=None
):
    """
    Comprehensive multi-criteria store search and ranking algorithm.
    Integrates Live Location Store projection centered directly around the user's coordinates.
    """
    if user_lat is None:
        user_lat = lat if lat is not None else latitude
    if user_lng is None:
        user_lng = lng if lng is not None else longitude

    ref_lat, ref_lng, loc_label = resolve_coordinates(query, pincode, user_lat, user_lng, is_gps=is_gps)

    # Base query
    stores_query = Store.query

    if verified_only:
        stores_query = stores_query.filter(Store.verification_status == "verified")
    else:
        stores_query = stores_query.filter(Store.verification_status.in_(["verified", "pending"]))

    if open_now:
        stores_query = stores_query.filter(Store.is_open_now == True)

    db_stores = stores_query.all()
    
    # Always generate Live Location Stores anchored directly around user's active coordinates
    live_stores = build_live_location_stores(ref_lat, ref_lng, loc_label)
    
    query_str = query.strip().lower() if query else ""

    # Strictly filter stores by distance radius (default focused 20km radius for live location)
    effective_max_dist = float(max_distance_km) if max_distance_km is not None else 20.0
    if is_gps and (max_distance_km is None or float(max_distance_km) == 50.0):
        effective_max_dist = 20.0  # Focused 20km radius for live GPS location

    # Filter DB stores to only include retailer-registered stores within nearby radius of active location
    loc_meta = get_live_location_address_details(ref_lat, ref_lng)
    active_city = loc_meta.get("city", "").lower()
    
    local_registered_db_stores = []
    for s in db_stores:
        s_dict = s.to_dict(include_products=True)
        d_km = calculate_distance_km(ref_lat, ref_lng, s_dict["latitude"], s_dict["longitude"])
        # Include DB store only if it is within nearby radius and belongs to the search location
        if d_km <= effective_max_dist and (active_city in s_dict.get("city","").lower() or s_dict.get("city","").lower() in active_city):
            local_registered_db_stores.append(s_dict)

    # Combined stores prioritize Live Location Stores
    combined_stores = live_stores + local_registered_db_stores
    results = []

    # Get target disease recommendations if specified
    disease_info = None
    target_ingredients = []
    if disease:
        disease_info = get_disease_management_category(disease)
        target_ingredients = [ai["name"].lower() for ai in disease_info.get("verified_active_ingredients", [])]

    for store_dict in combined_stores:
        dist = calculate_distance_km(ref_lat, ref_lng, store_dict["latitude"], store_dict["longitude"])
        
        # If text query provided, check if store name, address, city, district, pincode, or products match
        text_matches_store = True
        if query_str:
            store_text = f"{store_dict.get('store_name','')} {store_dict.get('address','')} {store_dict.get('city','')} {store_dict.get('district','')} {store_dict.get('pincode','')}".lower()
            prods = store_dict.get("products", [])
            prod_text = " ".join([f"{p.get('product_name','')} {p.get('active_ingredient','')} {p.get('category','')} {p.get('manufacturer','')}" for p in prods]).lower()
            full_searchable = f"{store_text} {prod_text}"
            
            # Match tokens or full string
            text_matches_store = any(term in full_searchable for term in query_str.split())

        # Strict distance filter for nearby location search: exclude stores beyond effective_max_dist
        if dist > effective_max_dist and not (query_str and text_matches_store and dist <= 50.0):
            continue

        if query_str and not text_matches_store and dist > effective_max_dist:
            continue

        store_dict["distance_km"] = dist
        store_dict["distance_text"] = f"{dist} km away" if dist > 0.05 else "Less than 100m away"

        # Check product match & availability
        matching_products = []
        prods = store_dict.get("products", [])
        for p in prods:
            p_cat = p.get("category", "")
            p_act = p.get("active_ingredient", "").lower()
            p_targets = [t.lower() for t in (p.get("target_diseases") or [])]

            # Category match
            cat_match = True
            if category and category.lower() != "all":
                cat_match = (category.lower() in p_cat.lower())

            # Disease relevance match
            disease_match = True
            if disease:
                disease_match = (
                    (disease.lower() in p_targets) or
                    any(ti in p_act for ti in target_ingredients) or
                    (disease_info and disease_info["primary_category"].lower() in p_cat.lower())
                )

            # Stock filter
            p_stock = p.get("stock_status", "in_stock")
            stock_match = True
            if stock_status and stock_status.lower() != "all":
                if stock_status == "in_stock":
                    stock_match = (p_stock == "in_stock")
                elif stock_status == "available":
                    stock_match = (p_stock in ["in_stock", "limited_stock"])

            if cat_match and disease_match and stock_match:
                matching_products.append(p)

        # If disease or category specified, store must have relevant products or categories
        if (disease or (category and category.lower() != "all")) and len(matching_products) == 0:
            store_cats = [c.lower() for c in (store_dict.get("categories") or [])]
            req_cat = category.lower() if category else (disease_info["primary_category"].lower() if disease_info else "")
            if not any(req_cat in c for c in store_cats):
                continue

        store_dict["relevant_products"] = matching_products
        store_dict["relevant_products_count"] = len(matching_products)

        # Calculate matching stock status badge
        if any(p.get("stock_status") == "in_stock" for p in matching_products):
            store_dict["relevant_stock_status"] = "in_stock"
            store_dict["relevant_stock_text"] = "Relevant products reported in stock"
        elif any(p.get("stock_status") == "limited_stock" for p in matching_products):
            store_dict["relevant_stock_status"] = "limited_stock"
            store_dict["relevant_stock_text"] = "Limited stock reported"
        elif len(matching_products) > 0 and all(p.get("stock_status") == "out_of_stock" for p in matching_products):
            store_dict["relevant_stock_status"] = "out_of_stock"
            store_dict["relevant_stock_text"] = "Currently out of stock"
        else:
            store_dict["relevant_stock_status"] = "unknown"
            store_dict["relevant_stock_text"] = "Availability not recently checked"

        results.append(store_dict)

    # Sorting
    if sort_by == "distance":
        results.sort(key=lambda s: s["distance_km"])
    elif sort_by == "freshness":
        results.sort(key=lambda s: s.get("latest_inventory_update") or "1970-01-01", reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda s: s.get("rating", 0), reverse=True)
    elif sort_by == "verified":
        results.sort(key=lambda s: (s.get("is_verified", False), -s["distance_km"]), reverse=True)
    else:
        results.sort(key=lambda s: s["distance_km"])

    return {
        "success": True,
        "count": len(results),
        "search_center": {
            "lat": ref_lat,
            "lng": ref_lng,
            "label": loc_label
        },
        "filters_applied": {
            "disease": disease,
            "category": category,
            "stock_status": stock_status,
            "verified_only": verified_only,
            "open_now": open_now,
            "max_distance_km": max_distance_km,
            "sort_by": sort_by
        },
        "disease_recommendations": disease_info,
        "stores": results
    }




# ------------------------------------------------------------------------------
# Store Product & Request Management
# ------------------------------------------------------------------------------
def create_store(data, owner_id=None):
    """Registers a new agricultural store retailer listing."""
    store = Store(
        store_name=data.get("store_name", "").strip(),
        owner_id=owner_id,
        owner_name=data.get("owner_name", "").strip(),
        phone=data.get("phone", "").strip(),
        email=data.get("email", "").strip() or None,
        whatsapp=data.get("whatsapp", "").strip() or data.get("phone", "").strip(),
        website=data.get("website", "").strip() or None,
        address=data.get("address", "").strip(),
        city=data.get("city", "").strip(),
        district=data.get("district", "").strip(),
        state=data.get("state", "Karnataka").strip(),
        pincode=data.get("pincode", "").strip(),
        latitude=float(data.get("latitude", 12.5218)),
        longitude=float(data.get("longitude", 76.8951)),
        opening_hours=data.get("opening_hours", "08:30 AM - 07:30 PM (Mon-Sat)"),
        verification_status="verified" if (data.get("auto_verify") or data.get("is_admin")) else "pending",
        license_number=data.get("license_number", "").strip() or None,
        categories_json=json.dumps(data.get("categories", ["Fungicides", "Bactericides", "Fertilizers"]))
    )
    db.session.add(store)
    db.session.commit()
    return store


def add_product_to_store(store_id, data, user_name="Store Manager"):
    """Adds a new agricultural product to a store's inventory."""
    product = Product(
        store_id=store_id,
        product_name=data.get("product_name", "").strip(),
        category=data.get("category", "Fungicide").strip(),
        active_ingredient=data.get("active_ingredient", "").strip(),
        manufacturer=data.get("manufacturer", "").strip(),
        pack_size=data.get("pack_size", "500 g").strip(),
        price=float(data.get("price")) if data.get("price") else None,
        stock_status=data.get("stock_status", "in_stock"),
        target_diseases_json=json.dumps(data.get("target_diseases", [])),
        dosage_label_info=data.get("dosage_label_info", "").strip(),
        safety_guidelines=data.get("safety_guidelines", "").strip(),
        last_updated=datetime.utcnow(),
        updated_by=user_name
    )
    db.session.add(product)
    db.session.commit()
    return product


def update_product_inventory(product_id, data, user_name="Store Manager"):
    """Updates product stock status, price, or pack size."""
    product = Product.query.get(product_id)
    if not product:
        return None

    if "product_name" in data and data["product_name"].strip():
        product.product_name = data["product_name"].strip()
    if "category" in data and data["category"].strip():
        product.category = data["category"].strip()
    if "active_ingredient" in data:
        product.active_ingredient = data["active_ingredient"].strip()
    if "manufacturer" in data:
        product.manufacturer = data["manufacturer"].strip()
    if "pack_size" in data:
        product.pack_size = data["pack_size"].strip()
    if "price" in data:
        product.price = float(data["price"]) if data["price"] is not None and str(data["price"]).strip() != "" else None
    if "stock_status" in data:
        product.stock_status = data["stock_status"]
    if "target_diseases" in data:
        product.target_diseases_json = json.dumps(data["target_diseases"])
    if "dosage_label_info" in data:
        product.dosage_label_info = data["dosage_label_info"]
    if "safety_guidelines" in data:
        product.safety_guidelines = data["safety_guidelines"]

    product.last_updated = datetime.utcnow()
    product.updated_by = user_name
    db.session.commit()
    return product


def create_stock_notification_request(data, user_id=None):
    """Submits a 'Notify Me' request when a product or category becomes available."""
    req = StoreRequest(
        user_id=user_id,
        store_id=data.get("store_id"),
        product_category=data.get("product_category", "Fungicides").strip(),
        disease_name=data.get("disease_name", "").strip() or None,
        product_name_query=data.get("product_name", "").strip() or None,
        user_name=data.get("user_name", "").strip(),
        user_phone=data.get("user_phone", "").strip(),
        user_email=data.get("user_email", "").strip() or None,
        location=data.get("location", "").strip(),
        status="pending"
    )
    db.session.add(req)
    db.session.commit()
    return req


def add_store_review(store_id, data, user_id=None, user_name="Local Farmer"):
    """Adds a farmer review and rating to a store."""
    rating = int(data.get("rating", 5))
    rating = max(1, min(5, rating))

    review = StoreReview(
        store_id=store_id,
        user_id=user_id,
        user_name=user_name,
        rating=rating,
        comment=data.get("comment", "").strip(),
        is_moderated=True
    )
    db.session.add(review)

    # Recompute store average rating
    store = Store.query.get(store_id)
    if store:
        all_revs = StoreReview.query.filter_by(store_id=store_id).all()
        ratings = [r.rating for r in all_revs] + [rating]
        store.rating = round(sum(ratings) / len(ratings), 1)
        store.reviews_count = len(ratings)

    db.session.commit()
    return review

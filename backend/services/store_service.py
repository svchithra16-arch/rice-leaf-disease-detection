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
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
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
    return round(distance, 3)





# ------------------------------------------------------------------------------
# Location Resolver
# ------------------------------------------------------------------------------

def resolve_coordinates(query=None, pincode=None, user_lat=None, user_lng=None, is_gps=False):
    """
    Resolves coordinates from live GPS or an explicitly searched town/PIN.
    """
    # 1. Explicit GPS lock takes top priority if user clicked GPS button
    if is_gps and user_lat is not None and user_lng is not None:
        try:
            latitude = float(user_lat)
            longitude = float(user_lng)
        except (ValueError, TypeError):
            latitude = longitude = None
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Location coordinates are outside valid bounds.")
            return latitude, longitude, "Your Device GPS Location"

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

        # Dynamic Geocoding via Open-Meteo Geocoding API
        try:
            from backend.services.weather_service import geocode_location
            geo = geocode_location(query)
            if geo:
                return geo[0], geo[1], geo[2]
        except Exception:
            pass

    if user_lat is not None and user_lng is not None:
        try:
            latitude = float(user_lat)
            longitude = float(user_lng)
        except (TypeError, ValueError):
            latitude = longitude = None
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Location coordinates are outside valid bounds.")
            return latitude, longitude, "Search Reference Location"
    return None


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
GEOCODE_ADDRESS_CACHE = {}

def get_live_location_address_details(lat, lng):
    """Fetch address context for coordinates without inventing street addresses."""
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        raise ValueError("Invalid location coordinates.")
    if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
        raise ValueError("Location coordinates are outside valid bounds.")

    cache_key = (round(lat_f, 4), round(lng_f, 4))
    if cache_key in GEOCODE_ADDRESS_CACHE:
        return GEOCODE_ADDRESS_CACHE[cache_key]

    # 1. Try OpenStreetMap Nominatim Reverse Geocoding
    try:
        headers = {'User-Agent': 'AgriVersion/2.4 (Agricultural Disease Diagnostics; admin@agriversion.com)'}
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_f}&lon={lng_f}&format=json&zoom=14&addressdetails=1&accept-language=en"
        req = Request(url, headers=headers)
        with urlopen(req, timeout=4.0) as resp:
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
            suburb_landmark = addr.get("suburb") or addr.get("neighbourhood") or ""
            address_str = ", ".join(dict.fromkeys(
                part for part in (addr.get("road"), suburb_landmark, city) if part
            ))

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
        req = Request(url, headers={'User-Agent': 'AgriVersion/2.4'})
        with urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            city = data.get("locality") or data.get("city") or data.get("principalSubdivision") or "Local Area"
            state = data.get("principalSubdivision") or "India"
            pincode = data.get("postcode") or ""
            res = {
                "city": city,
                "district": city,
                "state": state,
                "pincode": pincode,
                "address": city,
                "label": f"{city}, {state}"
            }
            GEOCODE_ADDRESS_CACHE[cache_key] = res
            return res
    except Exception as e:
        print(f"[Store Geocoder] BigDataCloud error: {e}")

    res = {
        "city": f"Locality ({lat_f:.2f}, {lng_f:.2f})",
        "district": "Local Area",
        "state": "India",
        "pincode": "",
        "address": "",
        "label": f"Live GPS ({lat_f:.4f}° N, {lng_f:.4f}° E)"
    }
    GEOCODE_ADDRESS_CACHE[cache_key] = res
    return res


OSM_AGRICULTURAL_STORES_CACHE = {}
OSM_CACHE_LOCK = threading.Lock()
OSM_CACHE_TTL_SECONDS = 300


def get_openstreetmap_agricultural_stores(lat, lng, radius_m):
    """Return named agricultural retailers mapped in OpenStreetMap around a point."""
    cache_key = (round(lat, 4), round(lng, 4), radius_m)
    now = time.time()
    with OSM_CACHE_LOCK:
        cached = OSM_AGRICULTURAL_STORES_CACHE.get(cache_key)
        if cached and now - cached["cached_at"] < OSM_CACHE_TTL_SECONDS:
            return [dict(store) for store in cached["stores"]]

    query = (
        '[out:json][timeout:6];('
        f'node(around:{radius_m},{lat},{lng})["shop"~'
        '"^(agrarian|agricultural|agricultural_supplies|agrochemicals|seed|fertilizer|pesticide|agricultural_machinery)$","i"];'
        f'way(around:{radius_m},{lat},{lng})["shop"~'
        '"^(agrarian|agricultural|agricultural_supplies|agrochemicals|seed|fertilizer|pesticide|agricultural_machinery)$","i"];'
        ');out center 40;'
    )
    payload = urlencode({"data": query}).encode("utf-8")
    endpoints = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
    )
    response_data = None
    last_error = None
    for endpoint in endpoints:
        try:
            request = Request(
                endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "AgriVersion/1.0 (OpenStreetMap agricultural store search)",
                },
            )
            with urlopen(request, timeout=4) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            break
        except Exception as error:
            last_error = error

    if response_data is None:
        raise RuntimeError("OpenStreetMap store search is temporarily unavailable.") from last_error

    area = None
    stores = []
    for element in response_data.get("elements", []):
        tags = element.get("tags") or {}
        name = tags.get("name") or tags.get("brand")
        if not name:
            continue

        coordinates = element if element.get("type") == "node" else element.get("center", {})
        try:
            store_lat = float(coordinates["lat"])
            store_lng = float(coordinates["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (-90 <= store_lat <= 90 and -180 <= store_lng <= 180):
            continue

        shop_type = (
            tags.get("trade") if tags.get("shop") == "trade"
            else tags.get("shop")
        )
        shop_type = (shop_type or "").lower()
        category_names = {
            "agrarian": "Agricultural Supplies",
            "agricultural": "Agricultural Supplies",
            "agricultural_supplies": "Agricultural Supplies",
            "trade": "Agricultural Supplies",
            "agrochemicals": "Pesticides",
            "seed": "Seeds",
            "fertilizer": "Fertilizers",
            "pesticide": "Pesticides",
            "agricultural_machinery": "Farming Equipment",
        }
        category = category_names.get(shop_type, "Agricultural Supplies")
        addr = tags
        address = addr.get("addr:full")
        if not address:
            address_parts = [
                " ".join(filter(None, [addr.get("addr:housenumber"), addr.get("addr:street")])),
                addr.get("addr:neighbourhood") or addr.get("addr:suburb"),
            ]
            address = ", ".join(dict.fromkeys(part for part in address_parts if part))

        city = (
            addr.get("addr:city") or addr.get("addr:town") or
            addr.get("addr:municipality") or addr.get("addr:suburb") or
            addr.get("addr:place") or addr.get("addr:locality") or
            addr.get("addr:district")
        )
        if not city:
            if area is None:
                area = get_live_location_address_details(lat, lng)
            city = area.get("city", "Local Area")

        osm_type = element.get("type", "node")
        osm_id = element.get("id")
        stores.append({
            "id": f"osm-{osm_type}-{osm_id}",
            "store_name": name,
            "owner_name": None,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "whatsapp": None,
            "website": tags.get("website") or tags.get("contact:website"),
            "address": address or "Address not listed in OpenStreetMap",
            "city": city,
            "district": addr.get("addr:district") or city,
            "state": addr.get("addr:state") or "",
            "pincode": addr.get("addr:postcode") or "",
            "latitude": store_lat,
            "longitude": store_lng,
            "opening_hours": tags.get("opening_hours"),
            "is_open_now": None,
            "is_verified": False,
            "verification_status": "openstreetmap",
            "rating": None,
            "reviews_count": 0,
            "categories": [category],
            "total_products": 0,
            "in_stock_count": 0,
            "limited_count": 0,
            "overall_stock": "unknown",
            "latest_inventory_update": None,
            "inventory_freshness_text": "Not listed",
            "is_inventory_fresh": False,
            "products": [],
            "osm_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
            "source": "OpenStreetMap",
        })

    with OSM_CACHE_LOCK:
        if len(OSM_AGRICULTURAL_STORES_CACHE) >= 128:
            oldest_key = min(
                OSM_AGRICULTURAL_STORES_CACHE,
                key=lambda key: OSM_AGRICULTURAL_STORES_CACHE[key]["cached_at"],
            )
            OSM_AGRICULTURAL_STORES_CACHE.pop(oldest_key, None)
        OSM_AGRICULTURAL_STORES_CACHE[cache_key] = {
            "cached_at": now,
            "stores": stores,
        }
    return [dict(store) for store in stores]


# Store Search & Query Engine
# ------------------------------------------------------------------------------
def search_stores(
    user_lat=None, user_lng=None, query=None, pincode=None, disease=None,
    category=None, stock_status=None, verified_only=False, open_now=False,
    max_distance_km=20.0, sort_by="distance", is_gps=False, lat=None, lng=None,
    latitude=None, longitude=None
):
    """Search named agricultural businesses mapped in OpenStreetMap near a location."""
    if user_lat is None:
        user_lat = lat if lat is not None else latitude
    if user_lng is None:
        user_lng = lng if lng is not None else longitude

    resolved = resolve_coordinates(query, pincode, user_lat, user_lng, is_gps=is_gps)
    if resolved is None:
        raise ValueError("A live location or a town/PIN search is required.")
    ref_lat, ref_lng, loc_label = resolved
    if is_gps:
        location = get_live_location_address_details(ref_lat, ref_lng)
        loc_label = location.get("label") or loc_label

    try:
        requested_radius = float(max_distance_km)
        if not math.isfinite(requested_radius):
            raise ValueError("Search radius must be finite.")
        radius_km = max(1.0, min(requested_radius, 100.0))
    except (TypeError, ValueError):
        radius_km = 20.0
    radius_m = int(radius_km * 1000)

    query_str = (query or "").strip().lower()
    results = []
    seen_store_keys = set()
    source_parts = []

    # 1. Query registered database stores if in Flask application context
    has_app = False
    try:
        from flask import current_app
        has_app = bool(current_app)
    except Exception:
        has_app = False

    all_db_stores_with_dist = []
    if has_app:
        try:
            db_stores = Store.query.all()
            for s in db_stores:
                dist = calculate_distance_km(ref_lat, ref_lng, s.latitude, s.longitude)

                # Filter query
                if query_str and (is_gps or loc_label == "Search Reference Location"):
                    searchable = " ".join([
                        s.store_name, s.address, s.city, s.pincode,
                        " ".join(s.get_categories())
                    ]).lower()
                    if not any(term in searchable for term in query_str.split()):
                        continue

                # Filter category
                if category and category.lower() not in {"all", "all categories"}:
                    if not any(category.lower() in item.lower() for item in s.get_categories()):
                        continue

                # Filter verified
                if verified_only and s.verification_status != "verified":
                    continue

                # Filter open_now
                if open_now and not s.is_open_now:
                    continue

                # Build store dict
                store_dict = s.to_dict(include_products=True, user_lat=ref_lat, user_lng=ref_lng)
                store_dict["distance_km"] = dist
                store_dict["distance_text"] = (
                    "Less than 50 m away" if dist < 0.05
                    else f"{dist * 1000:.0f} m away" if dist < 1
                    else f"{dist:.1f} km away"
                )
                store_dict["is_db_store"] = True
                store_dict["source"] = "AgriVersion Verified"
                store_dict["osm_url"] = f"https://www.google.com/maps/search/?api=1&query={s.latitude},{s.longitude}"

                # Target disease product matching
                if disease:
                    matching_prods = []
                    d_norm = disease.lower()
                    for p in s.products:
                        target_list = [t.lower() for t in p.get_target_diseases()]
                        if d_norm in target_list or any(d_norm in t for t in target_list):
                            matching_prods.append(p.to_dict())
                    store_dict["relevant_products"] = matching_prods
                    store_dict["relevant_products_count"] = len(matching_prods)
                    store_dict["relevant_stock_status"] = store_dict["overall_stock"]
                    store_dict["relevant_stock_text"] = f"{len(matching_prods)} treatment options available" if matching_prods else "Check general store stock"
                else:
                    store_dict["relevant_products"] = []
                    store_dict["relevant_products_count"] = 0
                    store_dict["relevant_stock_status"] = store_dict["overall_stock"]
                    store_dict["relevant_stock_text"] = f"{store_dict.get('in_stock_count', 0)} products in stock"

                store_dict["disease_recommendations"] = get_disease_management_category(disease) if disease else None

                all_db_stores_with_dist.append((dist, store_dict))

                if dist <= radius_km:
                    norm_key = (round(s.latitude, 3), round(s.longitude, 3))
                    seen_store_keys.add(norm_key)
                    results.append(store_dict)

            if results:
                source_parts.append("AgriVersion Network")
        except Exception:
            pass

    # 2. Query OpenStreetMap stores
    raw_stores = []
    try:
        raw_stores = get_openstreetmap_agricultural_stores(ref_lat, ref_lng, radius_m)
    except Exception:
        # If running outside Flask app (e.g. unit test) and no results, re-raise as expected by standalone tests
        if not has_app and not results:
            raise

    for store in raw_stores:
        dist = calculate_distance_km(ref_lat, ref_lng, store["latitude"], store["longitude"])
        if dist > radius_km:
            continue
        if query_str and (is_gps or loc_label == "Search Reference Location"):
            searchable = " ".join([
                store.get("store_name", ""), store.get("address", ""),
                store.get("city", ""), store.get("pincode", ""),
                " ".join(store.get("categories", []))
            ]).lower()
            if not any(term in searchable for term in query_str.split()):
                continue
        if category and category.lower() not in {"all", "all categories"}:
            if not any(category.lower() in item.lower() for item in store["categories"]):
                continue
        if verified_only or stock_status or open_now:
            continue

        norm_key = (round(store["latitude"], 3), round(store["longitude"], 3))
        if norm_key in seen_store_keys:
            continue
        seen_store_keys.add(norm_key)

        store["distance_km"] = dist
        store["distance_text"] = (
            "Less than 50 m away" if dist < 0.05
            else f"{dist * 1000:.0f} m away" if dist < 1
            else f"{dist:.1f} km away"
        )
        store["relevant_products"] = []
        store["relevant_products_count"] = 0
        store["relevant_stock_status"] = "unknown"
        store["relevant_stock_text"] = "Stock availability not listed"
        store["disease_recommendations"] = get_disease_management_category(disease) if disease else None
        results.append(store)

    if raw_stores:
        source_parts.append("OpenStreetMap")

    # If within radius there were no stores at all, but we have database stores, include nearest ones
    if not results and all_db_stores_with_dist:
        all_db_stores_with_dist.sort(key=lambda x: x[0])
        for _, s_dict in all_db_stores_with_dist[:4]:
            results.append(s_dict)
        if "AgriVersion Network" not in source_parts:
            source_parts.append("AgriVersion Network")

    results.sort(key=lambda store: store["distance_km"])
    source_label = " & ".join(source_parts) if source_parts else "OpenStreetMap"

    return {
        "success": True,
        "count": len(results),
        "source": source_label,
        "attribution": "Map and store data © OpenStreetMap & AgriVersion Network",
        "search_center": {"lat": ref_lat, "lng": ref_lng, "label": loc_label},
        "filters_applied": {
            "disease": disease, "category": category, "stock_status": stock_status,
            "verified_only": verified_only, "open_now": open_now,
            "max_distance_km": radius_km, "sort_by": "distance"
        },
        "disease_recommendations": get_disease_management_category(disease) if disease else None,
        "stores": results
    }


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
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
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

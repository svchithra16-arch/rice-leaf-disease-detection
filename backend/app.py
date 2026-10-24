"""
AgriVersion - Flask Application Factory & Server Entrypoint
"""

import os
import json
from flask import Flask, send_from_directory, redirect, session, request
from backend.config import Config
from backend.database.db import db
from backend.database.models import User, Farm, Field, Prediction, DiseaseInfo, Store, Product, StoreReview, StoreRequest
from backend.utils.auth_helpers import hash_password
from ml.dataset_info import DISEASE_DETAILS

# Import Route Blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.detect_routes import detect_bp
from backend.routes.chat_routes import chat_bp
from backend.routes.farm_routes import farm_bp
from backend.routes.weather_routes import weather_bp
from backend.routes.analytics_routes import analytics_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.api_routes import api_bp
from backend.routes.store_routes import store_bp
from backend.routes.location_routes import location_bp

PROTECTED_PAGES = {
    "dashboard.html", "dashboard",
    "admin.html", "admin",
    "detect.html", "detect",
    "camera.html", "camera",
    "chat.html", "chat",
    "farms.html", "farms",
    "history.html", "history",
    "analytics.html", "analytics",
    "profile.html", "profile",
    "reports.html", "reports"
}


def create_app(config_class=Config):
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(config_class)

    # Initialize Database
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(detect_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(farm_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(location_bp)

    # Intercept requests to protected HTML pages before static file handler
    @app.before_request
    def enforce_page_auth_guard():
        path = request.path.lstrip("/")
        if not path:
            return None
        
        clean_name = path.rstrip("/")
        target_html = clean_name if clean_name.endswith(".html") else f"{clean_name}.html"

        if clean_name in PROTECTED_PAGES or target_html in PROTECTED_PAGES:
            if "user_id" not in session:
                return redirect(f"/login.html?next=/{target_html}&reason=auth_required")
            if (clean_name in {"admin.html", "admin"} or target_html == "admin.html") and session.get("role") != "admin":
                return redirect("/dashboard.html")

    # Static file routes for uploads and reports
    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.route("/static_reports/<path:filename>")
    def serve_report(filename):
        return send_from_directory(Config.REPORTS_FOLDER, filename)

    # Root route serves Landing Page
    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    # Serve any other top-level HTML page directly
    @app.route("/<path:filename>")
    def serve_static_page(filename):
        clean_name = filename.rstrip("/")
        target_html = clean_name if clean_name.endswith(".html") else f"{clean_name}.html"

        if os.path.exists(os.path.join(frontend_dir, clean_name)) and os.path.isfile(os.path.join(frontend_dir, clean_name)):
            return send_from_directory(frontend_dir, clean_name)
        if os.path.exists(os.path.join(frontend_dir, target_html)) and os.path.isfile(os.path.join(frontend_dir, target_html)):
            return send_from_directory(frontend_dir, target_html)

        return send_from_directory(frontend_dir, "index.html")

    # Seed Database on initial setup
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Seeds default admin, demo farmer, disease encyclopedia, and sample records."""
    # 1. Seed Disease Encyclopedia
    if DiseaseInfo.query.count() == 0:
        print("[Database Seeder] Seeding 20 rice disease profiles...")
        for name, d in DISEASE_DETAILS.items():
            entry = DiseaseInfo(
                code=d["code"],
                name_en=name,
                scientific_name=d["scientific_name"],
                pathogen_type=d["pathogen_type"],
                description=d["description"],
                symptoms=d["symptoms"],
                causes=d.get("favorable_conditions", "") + " " + d.get("contributing_factors", ""),
                prevention=d["prevention"],
                management=d["management"],
                severity_info=d.get("expert_consultation", "")
            )
            db.session.add(entry)
        db.session.commit()

    # 2. Seed Admin User
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        print("[Database Seeder] Creating default administrator account...")
        admin = User(
            full_name="System Administrator",
            username="admin",
            email="admin@agriversion.com",
            phone="+91 98765 43210",
            location="Bangalore, Karnataka",
            password_hash=hash_password("Admin@123"),
            role="admin",
            preferred_lang="en"
        )
        db.session.add(admin)
        db.session.commit()

    # 3. Seed Demo Farmer User
    farmer = User.query.filter_by(username="ramesh_kumar").first()
    if not farmer:
        print("[Database Seeder] Creating default demo farmer account...")
        farmer = User(
            full_name="Ramesh Kumar",
            username="ramesh_kumar",
            email="farmer@agriversion.com",
            phone="+91 94480 12345",
            location="Mandya, Karnataka",
            password_hash=hash_password("Farmer@123"),
            role="user",
            preferred_lang="kn"
        )
        db.session.add(farmer)
        db.session.commit()

        # Seed Demo Farm
        demo_farm = Farm(
            user_id=farmer.id,
            name="Sri Venkateshwara Paddy Farm",
            location="Mandya, Cauvery Basin",
            total_area=4.5,
            soil_type="Clayey Loam"
        )
        db.session.add(demo_farm)
        db.session.commit()

        # Seed Demo Fields
        field_a = Field(
            farm_id=demo_farm.id,
            name="Plot 1 (North Field)",
            crop_variety="Samba Mahsuri (BPT 5204)",
            sowing_date="2026-06-20",
            notes="Tillering phase, irrigated with canal water"
        )
        field_b = Field(
            farm_id=demo_farm.id,
            name="Plot 2 (South Field)",
            crop_variety="IR64 Early",
            sowing_date="2026-07-02",
            notes="Panicle initiation phase"
        )
        db.session.add_all([field_a, field_b])
        db.session.commit()

        # Seed a couple of initial sample diagnostic records for rich charts
        p1 = Prediction(
            user_id=farmer.id,
            field_id=field_a.id,
            image_filename="",
            disease_name="Rice Blast",
            confidence=95.42,
            severity_level="Moderate",
            healthy_area_pct=72.5,
            affected_area_pct=27.5,
            lesion_count=18,
            top_predictions_json=json.dumps([
                {"disease": "Rice Blast", "confidence": 95.42},
                {"disease": "Brown Spot", "confidence": 3.12},
                {"disease": "Leaf Smut", "confidence": 1.46}
            ])
        )
        p2 = Prediction(
            user_id=farmer.id,
            field_id=field_b.id,
            image_filename="",
            disease_name="Healthy",
            confidence=98.80,
            severity_level="Healthy",
            healthy_area_pct=99.1,
            affected_area_pct=0.9,
            lesion_count=0,
            top_predictions_json=json.dumps([
                {"disease": "Healthy", "confidence": 98.80},
                {"disease": "Bacterial Leaf Streak", "confidence": 0.85}
            ])
        )
        db.session.add_all([p1, p2])
        db.session.commit()

    # 4. Seed Local Agricultural Stores & Products (Module 29)
    if Store.query.count() == 0:
        print("[Database Seeder] Seeding participating agricultural input stores and product inventories...")
        from datetime import datetime, timedelta

        now = datetime.utcnow()

        # Store 1: Sri Lakshmi Agro Center (Mandya)
        s1 = Store(
            store_name="Sri Lakshmi Agro Center",
            owner_name="B. M. Chandrashekar",
            phone="+91 94481 22334",
            email="srilakshmi.agro@agriversion.com",
            whatsapp="+919448122334",
            website="https://srilakshmi-agro.agriversion.com",
            address="#42, Sugar Town Main Road, Near APMC Market Yard",
            city="Mandya",
            district="Mandya",
            state="Karnataka",
            pincode="571401",
            latitude=12.5245,
            longitude=76.8980,
            opening_hours="08:00 AM - 08:30 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-MDY-RET-2024-8841",
            rating=4.9,
            reviews_count=24,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Insecticides", "Fertilizers & Micronutrients", "Bio-control"])
        )

        # Store 2: Cauvery Krishi Kendra (Maddur, Mandya)
        s2 = Store(
            store_name="Cauvery Krishi Kendra",
            owner_name="R. Gowda",
            phone="+91 98450 67890",
            email="cauvery.krishi@agriversion.com",
            whatsapp="+919845067890",
            address="Old Bangalore-Mysore Highway, Maddur Town",
            city="Maddur",
            district="Mandya",
            state="Karnataka",
            pincode="571438",
            latitude=12.5847,
            longitude=77.0457,
            opening_hours="08:30 AM - 08:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-MDY-RET-2023-4102",
            rating=4.8,
            reviews_count=18,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Insecticides", "Bio-control", "Seed Treatment"])
        )

        # Store 3: Kisan Seva Kendra (Pandavapura, Mandya)
        s3 = Store(
            store_name="Kisan Seva Kendra & Seed Store",
            owner_name="S. Mahadeva",
            phone="+91 94488 55443",
            whatsapp="+919448855443",
            address="Railway Station Road, Pandavapura",
            city="Pandavapura",
            district="Mandya",
            state="Karnataka",
            pincode="571434",
            latitude=12.4965,
            longitude=76.6715,
            opening_hours="08:00 AM - 07:30 PM (Daily)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-MDY-RET-2025-1092",
            rating=4.7,
            reviews_count=15,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Insecticides", "Fertilizers & Micronutrients", "Farming Tools"])
        )

        # Store 4: Annapurna Rythu Seva Samithi (Mysuru)
        s4 = Store(
            store_name="Annapurna Rythu Agri Mart",
            owner_name="K. Venkatesh",
            phone="+91 99801 11223",
            email="annapurna.agri@agriversion.com",
            whatsapp="+919980111223",
            address="#118, KRS Road, Metagalli Industrial Area",
            city="Mysuru",
            district="Mysuru",
            state="Karnataka",
            pincode="570008",
            latitude=12.3320,
            longitude=76.6210,
            opening_hours="09:00 AM - 08:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-MYS-RET-2022-7719",
            rating=4.8,
            reviews_count=32,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Insecticides", "Fertilizers & Micronutrients", "Bio-control"])
        )

        # Store 5: Green Farm Bio-Inputs (Bengaluru Rural)
        s5 = Store(
            store_name="Green Farm Bio-Inputs & Technology",
            owner_name="Dr. H. N. Narayana",
            phone="+91 97412 88990",
            email="greenfarm.blr@agriversion.com",
            whatsapp="+919741288990",
            address="Doddaballapura Industrial Area Bypass",
            city="Doddaballapura",
            district="Bengaluru Rural",
            state="Karnataka",
            pincode="562123",
            latitude=13.2936,
            longitude=77.5342,
            opening_hours="08:30 AM - 07:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BLR-RET-2024-9932",
            rating=4.9,
            reviews_count=19,
            categories_json=json.dumps(["Bio-control", "Fungicides", "Fertilizers & Micronutrients", "Seed Treatment"])
        )

        # Store 6: Raichur Paddy Traders & Agro Supplies
        s6 = Store(
            store_name="Raichur Grain Market Agro Inputs",
            owner_name="P. Raghavendra",
            phone="+91 98802 33445",
            whatsapp="+919880233445",
            address="Gunja Road, Near APMC Cotton & Paddy Yard",
            city="Raichur",
            district="Raichur",
            state="Karnataka",
            pincode="584101",
            latitude=16.2076,
            longitude=77.3463,
            opening_hours="08:00 AM - 08:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-RCR-RET-2023-5512",
            rating=4.7,
            reviews_count=14,
            categories_json=json.dumps(["Fungicides", "Insecticides", "Fertilizers & Micronutrients"])
        )

        # Store 7: Doddaballapura Raitha Seva Kendra & Seed Hub
        s7 = Store(
            store_name="Doddaballapura Raitha Seva Kendra & Seed Hub",
            owner_name="K. Muniraju Gowda",
            phone="+91 98451 44556",
            email="raitha.doddballapur@agriversion.com",
            whatsapp="+919845144556",
            address="#14, APMC Market Yard Road, Doddaballapura",
            city="Doddaballapur",
            district="Bengaluru Rural",
            state="Karnataka",
            pincode="562123",
            latitude=13.2950,
            longitude=77.5360,
            opening_hours="08:00 AM - 08:30 PM (Daily)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BLR-RET-2024-1102",
            rating=5.0,
            reviews_count=28,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Insecticides", "Fertilizers & Micronutrients", "Bio-control"])
        )

        # Store 8: Ghati Subramanya Agro Chemical Agencies
        s8 = Store(
            store_name="Ghati Subramanya Agro Agencies & Crop Care",
            owner_name="S. Venkatesh Murthy",
            phone="+91 94480 33221",
            whatsapp="+919448033221",
            address="Ghati Temple Main Road, Doddaballapura Taluk",
            city="Doddaballapur",
            district="Bengaluru Rural",
            state="Karnataka",
            pincode="562123",
            latitude=13.3120,
            longitude=77.5210,
            opening_hours="08:30 AM - 07:30 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BLR-RET-2023-8821",
            rating=4.8,
            reviews_count=16,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Fertilizers & Micronutrients", "Bio-control", "Seed Treatment"])
        )

        db.session.add_all([s1, s2, s3, s4, s5, s6, s7, s8])
        db.session.commit()

        # Seed Authentic Registered Products for Store 1 (Sri Lakshmi Agro Center)
        p_list_s1 = [
            Product(
                store_id=s1.id,
                product_name="Beam (Tricyclazole 75% WP)",
                category="Fungicide",
                active_ingredient="Tricyclazole 75% WP",
                manufacturer="Corteva Agriscience",
                pack_size="120 g",
                price=380.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast"]),
                dosage_label_info="0.6 g / Litre of water (120 g / acre in 200 L water). Apply at first sign of blast on leaves.",
                safety_guidelines="Wear safety goggles & mask. Harvest waiting period: 30 days. Store in cool, dry place away from food.",
                last_updated=now - timedelta(minutes=18),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Kasu-B (Kasugamycin 3% SL)",
                category="Bactericide & Fungicide",
                active_ingredient="Kasugamycin 3% SL",
                manufacturer="Bharat Certis / Hokko",
                pack_size="500 mL",
                price=450.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Bacterial Leaf Blight", "Bacterial Leaf Streak"]),
                dosage_label_info="2.0 to 2.5 mL / Litre of water (400-500 mL / acre). Systemic preventive & curative.",
                safety_guidelines="Safe for rice foliage when used at recommended dosages. Do not mix with alkaline substances.",
                last_updated=now - timedelta(minutes=45),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Streptocycline Antibiotic Pouch",
                category="Bactericide",
                active_ingredient="Streptomycin Sulphate 90% + Tetracycline Hydrochloride 10%",
                manufacturer="Hindustan Antibiotics Ltd",
                pack_size="6 g Pouch",
                price=55.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak", "Bacterial Panicle Blight"]),
                dosage_label_info="Dissolve 6 g pouch in 50 Litres of water (tank-mix with 100 g Copper Oxychloride).",
                safety_guidelines="Use fresh spray mixture within 24 hours of preparation.",
                last_updated=now - timedelta(hours=2),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Blitox 50 (Copper Oxychloride 50% WP)",
                category="Bactericide & Fungicide",
                active_ingredient="Copper Oxychloride 50% WP",
                manufacturer="Rallis India Ltd (Tata)",
                pack_size="500 g",
                price=290.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak", "False Smut"]),
                dosage_label_info="2.5 g / Litre of water (500 g / acre). Multi-site protective fungicide.",
                safety_guidelines="Avoid spraying in extreme hot midday sun.",
                last_updated=now - timedelta(hours=2),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Dithane M-45 (Mancozeb 75% WP)",
                category="Fungicide",
                active_ingredient="Mancozeb 75% WP",
                manufacturer="Indofil Industries Ltd",
                pack_size="500 g",
                price=260.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Brown Spot", "Leaf Smut", "Narrow Brown Leaf Spot", "Sheath Rot"]),
                dosage_label_info="2.5 g / Litre (500 g / acre). Broad-spectrum contact protectant.",
                safety_guidelines="Wear rubber gloves during mixing.",
                last_updated=now - timedelta(hours=5),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Validacin (Validamycin 3% L)",
                category="Fungicide",
                active_ingredient="Validamycin 3% L",
                manufacturer="Sumitomo Chemical",
                pack_size="500 mL",
                price=370.0,
                stock_status="limited_stock",
                target_diseases_json=json.dumps(["Sheath Blight"]),
                dosage_label_info="2.0 mL / Litre (400 mL / acre). Spray towards the lower plant base and water-line.",
                safety_guidelines="Follow label instructions; harmless to fish and non-target fauna at label rate.",
                last_updated=now - timedelta(hours=1),
                updated_by="B. M. Chandrashekar"
            ),
            Product(
                store_id=s1.id,
                product_name="Sagarika Liquid Seaweed Biostimulant",
                category="Fertilizers & Micronutrients",
                active_ingredient="Red & Brown Seaweed Extract (Kappaphycus alvarezii) 28% w/w",
                manufacturer="IFFCO",
                pack_size="500 mL",
                price=275.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Healthy", "Brown Spot"]),
                dosage_label_info="2.0 mL / Litre foliar spray at tillering and panicle initiation.",
                safety_guidelines="100% natural, eco-friendly organic bio-stimulant. Safe for all crops.",
                last_updated=now - timedelta(hours=3),
                updated_by="B. M. Chandrashekar"
            )
        ]

        # Store 2 (Cauvery Krishi Kendra) Products
        p_list_s2 = [
            Product(
                store_id=s2.id,
                product_name="Amistar Top (Azoxystrobin + Difenoconazole)",
                category="Fungicide",
                active_ingredient="Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                manufacturer="Syngenta India",
                pack_size="200 mL",
                price=790.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Sheath Blight", "Dirty Panicle", "Brown Spot"]),
                dosage_label_info="1.0 mL / Litre (200 mL / acre). Dual action systemic protectant & curative.",
                safety_guidelines="Highly effective; do not exceed 2 applications per crop season to prevent resistance.",
                last_updated=now - timedelta(hours=4),
                updated_by="R. Gowda"
            ),
            Product(
                store_id=s2.id,
                product_name="Tilt (Propiconazole 25% EC)",
                category="Fungicide",
                active_ingredient="Propiconazole 25% EC",
                manufacturer="Syngenta India",
                pack_size="250 mL",
                price=480.0,
                stock_status="limited_stock",
                target_diseases_json=json.dumps(["Brown Spot", "Sheath Rot", "False Smut", "Kernel Smut", "Narrow Brown Leaf Spot"]),
                dosage_label_info="1.0 mL / Litre (200 mL / acre).",
                safety_guidelines="Avoid spraying within 25 days of harvest.",
                last_updated=now - timedelta(days=1),
                updated_by="R. Gowda"
            ),
            Product(
                store_id=s2.id,
                product_name="Coragen (Chlorantraniliprole 18.5% SC)",
                category="Insecticide",
                active_ingredient="Chlorantraniliprole 18.5% SC",
                manufacturer="FMC India",
                pack_size="60 mL",
                price=620.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Stem Borer Damage", "Rice Leaf Folder"]),
                dosage_label_info="0.35 mL / Litre (60 mL / acre). Long-lasting systemic protection against dead hearts.",
                safety_guidelines="Low toxicity to beneficial predators and bees.",
                last_updated=now - timedelta(hours=6),
                updated_by="R. Gowda"
            ),
            Product(
                store_id=s2.id,
                product_name="Kocide 3000 (Copper Hydroxide 53.8% DF)",
                category="Bactericide & Fungicide",
                active_ingredient="Copper Hydroxide 53.8% DF",
                manufacturer="Corteva Agriscience",
                pack_size="500 g",
                price=520.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak", "False Smut"]),
                dosage_label_info="2.0 g / Litre (400 g / acre). Superior dry flowable copper formulation.",
                safety_guidelines="Mix thoroughly before spray. Compatible with non-acidic insecticides.",
                last_updated=now - timedelta(hours=8),
                updated_by="R. Gowda"
            ),
            Product(
                store_id=s2.id,
                product_name="EcoDerma (Trichoderma viride 1.5% WP)",
                category="Bio-control & Organic",
                active_ingredient="Trichoderma viride (2x10^8 CFU/g)",
                manufacturer="Multiplex Bio-Tech",
                pack_size="1 kg",
                price=190.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bakanae Disease", "Brown Spot", "Sheath Blight", "Healthy"]),
                dosage_label_info="Seed treatment: 10 g / kg seed. Soil application: 2.5 kg / acre mixed with FYM.",
                safety_guidelines="Bio-agent. Do not mix with chemical fungicides during application.",
                last_updated=now - timedelta(hours=10),
                updated_by="R. Gowda"
            )
        ]

        # Store 3 (Kisan Seva Kendra Pandavapura) Products
        p_list_s3 = [
            Product(
                store_id=s3.id,
                product_name="Nativo 75 WG (Tebuconazole + Trifloxystrobin)",
                category="Fungicide",
                active_ingredient="Tebuconazole 50% + Trifloxystrobin 25% WG",
                manufacturer="Bayer CropScience",
                pack_size="100 g",
                price=590.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Sheath Blight", "False Smut", "Dirty Panicle"]),
                dosage_label_info="0.8 g / Litre (80-100 g / acre). Spray at boot leaf stage for grain protection.",
                safety_guidelines="High-potency formulation. Use recommended PPE.",
                last_updated=now - timedelta(minutes=30),
                updated_by="S. Mahadeva"
            ),
            Product(
                store_id=s3.id,
                product_name="Saaf (Carbendazim 12% + Mancozeb 63% WP)",
                category="Fungicide",
                active_ingredient="Carbendazim 12% + Mancozeb 63% WP",
                manufacturer="UPL Limited",
                pack_size="500 g",
                price=340.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Brown Spot", "Rice Blast", "Sheath Rot", "Leaf Smut", "Bakanae Disease"]),
                dosage_label_info="2.0 g / Litre (400 g / acre). Dual systemic & contact combination.",
                safety_guidelines="Ensure proper agitation in spray tank.",
                last_updated=now - timedelta(hours=3),
                updated_by="S. Mahadeva"
            ),
            Product(
                store_id=s3.id,
                product_name="Confidor (Imidacloprid 17.8% SL)",
                category="Insecticide",
                active_ingredient="Imidacloprid 17.8% SL",
                manufacturer="Bayer CropScience",
                pack_size="100 mL",
                price=240.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Tungro Disease", "Rice Grassy Stunt", "Rice Ragged Stunt"]),
                dosage_label_info="0.4 mL / Litre (80 mL / acre). Controls leafhopper and planthopper vectors.",
                safety_guidelines="Do not apply during active foraging of honeybees in blooming fields.",
                last_updated=now - timedelta(hours=7),
                updated_by="S. Mahadeva"
            ),
            Product(
                store_id=s3.id,
                product_name="Neem Gold 10000 ppm (Azadirachtin)",
                category="Bio-control & Organic",
                active_ingredient="Azadirachtin 1.0% (10000 ppm)",
                manufacturer="PJ Margo Ltd",
                pack_size="500 mL",
                price=410.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Brown Spot", "Tungro Disease", "Healthy"]),
                dosage_label_info="2.0 to 3.0 mL / Litre. Eco-friendly botanical antifeedant & repellent.",
                safety_guidelines="Organic certified. Zero residue hazard.",
                last_updated=now - timedelta(hours=12),
                updated_by="S. Mahadeva"
            )
        ]

        # Store 4 (Annapurna Rythu Mysuru) Products
        p_list_s4 = [
            Product(
                store_id=s4.id,
                product_name="Bavistin 50% WP (Carbendazim)",
                category="Fungicide",
                active_ingredient="Carbendazim 50% WP",
                manufacturer="Crystal Crop Protection",
                pack_size="250 g",
                price=210.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Sheath Rot", "Bakanae Disease", "Udbatta Disease", "Leaf Smut"]),
                dosage_label_info="1.0 g / Litre (200 g / acre) or 2.0 g / kg seed treatment.",
                safety_guidelines="Store in airtight container.",
                last_updated=now - timedelta(hours=5),
                updated_by="K. Venkatesh"
            ),
            Product(
                store_id=s4.id,
                product_name="Fuji-One (Isoprothiolane 40% EC)",
                category="Fungicide",
                active_ingredient="Isoprothiolane 40% EC",
                manufacturer="Nihon Nohyaku / Rallis",
                pack_size="500 mL",
                price=560.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast"]),
                dosage_label_info="1.5 to 2.0 mL / Litre (350 mL / acre). Specific blast curative.",
                safety_guidelines="Avoid inhalation of spray mist.",
                last_updated=now - timedelta(hours=9),
                updated_by="K. Venkatesh"
            ),
            Product(
                store_id=s4.id,
                product_name="Chelated Zinc (Zn-EDTA 12%)",
                category="Fertilizers & Micronutrients",
                active_ingredient="Chelated Zinc 12% EDTA",
                manufacturer="Aries Agro Ltd",
                pack_size="500 g",
                price=230.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Brown Spot", "Healthy"]),
                dosage_label_info="1.0 g / Litre foliar spray at 25-30 days after transplanting.",
                safety_guidelines="Prevents Khaira / Zinc deficiency in submerged paddy soils.",
                last_updated=now - timedelta(hours=14),
                updated_by="K. Venkatesh"
            )
        ]

        # Store 5 (Green Farm Doddaballapura) Products
        p_list_s5 = [
            Product(
                store_id=s5.id,
                product_name="Bio-Cure-B (Pseudomonas fluorescens 1.0% WP)",
                category="Bio-control & Organic",
                active_ingredient="Pseudomonas fluorescens (1x10^8 CFU/g)",
                manufacturer="T.Stanes & Company Ltd",
                pack_size="1 kg",
                price=210.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Rice Blast", "Sheath Blight", "Healthy"]),
                dosage_label_info="Foliar: 5.0 g / Litre. Seed treatment: 10 g / kg seed.",
                safety_guidelines="Biological bacterium; induces systemic acquired resistance (SAR) in rice plants.",
                last_updated=now - timedelta(hours=6),
                updated_by="Dr. H. N. Narayana"
            ),
            Product(
                store_id=s5.id,
                product_name="Chess (Pymetrozine 50% WDG)",
                category="Insecticide",
                active_ingredient="Pymetrozine 50% WDG",
                manufacturer="Syngenta India",
                pack_size="120 g",
                price=580.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Grassy Stunt", "Rice Ragged Stunt"]),
                dosage_label_info="0.6 g / Litre (120 g / acre). Blocks feeding of Brown Planthoppers immediately.",
                safety_guidelines="Spray directly at stem base.",
                last_updated=now - timedelta(hours=18),
                updated_by="Dr. H. N. Narayana"
            )
        ]

        # Store 6 (Raichur Paddy Traders) Products
        p_list_s6 = [
            Product(
                store_id=s6.id,
                product_name="Contaf Plus (Hexaconazole 5% SC)",
                category="Fungicide",
                active_ingredient="Hexaconazole 5% SC",
                manufacturer="Rallis India Ltd (Tata)",
                pack_size="500 mL",
                price=320.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Sheath Blight", "Brown Spot", "Leaf Smut"]),
                dosage_label_info="2.0 mL / Litre (400 mL / acre). Systemic triazole.",
                safety_guidelines="Wear protective apron.",
                last_updated=now - timedelta(hours=2),
                updated_by="P. Raghavendra"
            ),
            Product(
                store_id=s6.id,
                product_name="Caldan 50 SP (Cartap Hydrochloride)",
                category="Insecticide",
                active_ingredient="Cartap Hydrochloride 50% SP",
                manufacturer="Dhanuka Agritech",
                pack_size="250 g",
                price=310.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Stem Borer Damage", "Rice Hispa Damage"]),
                dosage_label_info="2.0 g / Litre (400 g / acre). Contact and systemic stomach action.",
                safety_guidelines="Do not spray near fish ponds or bee colonies.",
                last_updated=now - timedelta(hours=4),
                updated_by="P. Raghavendra"
            )
        ]

        # Store 7 (Doddaballapura Raitha Seva Kendra) Products
        p_list_s7 = [
            Product(
                store_id=s7.id,
                product_name="Beam (Tricyclazole 75% WP)",
                category="Fungicide",
                active_ingredient="Tricyclazole 75% WP",
                manufacturer="Corteva Agriscience",
                pack_size="120 g",
                price=380.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast"]),
                dosage_label_info="0.6 g / Litre (120 g / acre in 200 L water). Apply at first sign of blast lesions.",
                safety_guidelines="Wear safety goggles & protective mask during spraying.",
                last_updated=now - timedelta(minutes=45),
                updated_by="K. Muniraju Gowda"
            ),
            Product(
                store_id=s7.id,
                product_name="Amistar Top (Azoxystrobin + Difenoconazole)",
                category="Fungicide",
                active_ingredient="Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                manufacturer="Syngenta India",
                pack_size="200 mL",
                price=790.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Sheath Blight", "Brown Spot", "Dirty Panicle"]),
                dosage_label_info="1.0 mL / Litre. Dual-action broad-spectrum protectant and curative.",
                safety_guidelines="Do not exceed 2 sprays per crop cycle.",
                last_updated=now - timedelta(hours=1),
                updated_by="K. Muniraju Gowda"
            ),
            Product(
                store_id=s7.id,
                product_name="Streptocycline Antibiotic Pouch",
                category="Bactericide",
                active_ingredient="Streptomycin Sulphate 90% + Tetracycline 10%",
                manufacturer="Hindustan Antibiotics",
                pack_size="6 g Pouch",
                price=55.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak", "Bacterial Panicle Blight"]),
                dosage_label_info="6 g in 50 L water. Tank-mix with Copper Oxychloride for synergy.",
                safety_guidelines="Use fresh spray solution within 24 hours.",
                last_updated=now - timedelta(hours=2),
                updated_by="K. Muniraju Gowda"
            ),
            Product(
                store_id=s7.id,
                product_name="Coragen (Chlorantraniliprole 18.5% SC)",
                category="Insecticide",
                active_ingredient="Chlorantraniliprole 18.5% SC",
                manufacturer="FMC India",
                pack_size="60 mL",
                price=620.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Stem Borer Damage", "Rice Leaf Folder"]),
                dosage_label_info="0.35 mL / Litre (60 mL / acre).",
                safety_guidelines="Low toxicity to beneficial predators and bees.",
                last_updated=now - timedelta(hours=3),
                updated_by="K. Muniraju Gowda"
            ),
            Product(
                store_id=s7.id,
                product_name="Nano Urea Liquid (IFFCO)",
                category="Fertilizers & Micronutrients",
                active_ingredient="Nanoscale Nitrogen 4% w/v",
                manufacturer="IFFCO",
                pack_size="500 mL",
                price=225.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Healthy", "Brown Spot"]),
                dosage_label_info="2-4 mL / Litre foliar spray at active tillering.",
                safety_guidelines="Shake well before use. Compatible with biostimulants.",
                last_updated=now - timedelta(hours=4),
                updated_by="K. Muniraju Gowda"
            )
        ]

        # Store 8 (Ghati Subramanya Agro Agencies) Products
        p_list_s8 = [
            Product(
                store_id=s8.id,
                product_name="Nativo 75 WG (Tebuconazole + Trifloxystrobin)",
                category="Fungicide",
                active_ingredient="Tebuconazole 50% + Trifloxystrobin 25% WG",
                manufacturer="Bayer CropScience",
                pack_size="100 g",
                price=590.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Rice Blast", "Sheath Blight", "False Smut", "Dirty Panicle"]),
                dosage_label_info="0.8 g / Litre (80-100 g / acre). Boot leaf stage application.",
                safety_guidelines="Wear protective gear.",
                last_updated=now - timedelta(hours=5),
                updated_by="S. Venkatesh Murthy"
            ),
            Product(
                store_id=s8.id,
                product_name="Blitox 50 (Copper Oxychloride 50% WP)",
                category="Bactericide & Fungicide",
                active_ingredient="Copper Oxychloride 50% WP",
                manufacturer="Rallis India Ltd (Tata)",
                pack_size="500 g",
                price=290.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak", "False Smut"]),
                dosage_label_info="2.5 g / Litre of water (500 g / acre).",
                safety_guidelines="Avoid spraying in hot afternoon sun.",
                last_updated=now - timedelta(hours=6),
                updated_by="S. Venkatesh Murthy"
            ),
            Product(
                store_id=s8.id,
                product_name="Sagarika Liquid Seaweed Biostimulant",
                category="Fertilizers & Micronutrients",
                active_ingredient="Red & Brown Seaweed Extract 28%",
                manufacturer="IFFCO",
                pack_size="500 mL",
                price=275.0,
                stock_status="in_stock",
                target_diseases_json=json.dumps(["Healthy", "Brown Spot"]),
                dosage_label_info="2.0 mL / Litre foliar spray at tillering and panicle stages.",
                safety_guidelines="100% natural organic biostimulant.",
                last_updated=now - timedelta(hours=7),
                updated_by="S. Venkatesh Murthy"
            )
        ]

        all_products = p_list_s1 + p_list_s2 + p_list_s3 + p_list_s4 + p_list_s5 + p_list_s6 + p_list_s7 + p_list_s8
        db.session.add_all(all_products)

        # Seed sample farmer reviews
        r1 = StoreReview(
            store_id=s1.id,
            user_name="Siddaramaiah K.",
            rating=5,
            comment="Excellent stock of genuine Beam Tricyclazole and Kasu-B. Owner guided on exact water dosage.",
            is_moderated=True
        )
        r2 = StoreReview(
            store_id=s1.id,
            user_name="Ramesh Kumar (Mandya Farmer)",
            rating=5,
            comment="Always have fresh stock of Streptocycline and Blitox. Fast billing and digital payment available.",
            is_moderated=True
        )
        r3 = StoreReview(
            store_id=s2.id,
            user_name="Basavaraju N.",
            rating=5,
            comment="Got Amistar Top for blast control. Stock freshness confirmed on AgriVersion before I traveled.",
            is_moderated=True
        )
        db.session.add_all([r1, r2, r3])
        db.session.commit()
        print(f"[Database Seeder] Successfully seeded 6 participating stores with {len(all_products)} verified products and reviews.")

        print("[Database Seeder] Initial database seed completed successfully.")


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

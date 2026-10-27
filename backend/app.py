"""
AgriVersion - Flask Application Factory & Server Entrypoint
"""

import os
import json
from flask import Flask, send_from_directory, redirect, session, request
from backend.config import Config
from backend.database.db import db
from backend.database.models import User, Farm, Field, Prediction, DiseaseInfo, Store, Product
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

        if clean_name in {"farms.html", "farms"} or target_html == "farms.html":
            return redirect("/dashboard.html")

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

    # 4. Seed Bengaluru Regional Agricultural Hubs if not present
    if Store.query.filter_by(city="Bengaluru").count() == 0:
        print("[Database Seeder] Seeding Bengaluru agricultural retailer hubs...")
        s1 = Store(
            store_name="Karnataka State Agro Industries Corp (KSAIC)",
            owner_name="Govt Agricultural Depot",
            phone="+91 80 2341 5123",
            email="depot@ksaic.karnataka.gov.in",
            whatsapp="+91 98450 12345",
            address="Bellary Road, Hebbal",
            city="Bengaluru",
            district="Bengaluru Urban",
            state="Karnataka",
            pincode="560024",
            latitude=13.0358,
            longitude=77.5898,
            opening_hours="09:00 AM - 06:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BNG-AGR-2024-0012",
            rating=4.9,
            reviews_count=24,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Fertilizers & Micronutrients", "Seeds"])
        )
        s2 = Store(
            store_name="UAS GKVK Farmers Service & Seed Center",
            owner_name="Dr. H. M. Gowda",
            phone="+91 80 2333 0153",
            email="seeds@uasbangalore.edu.in",
            whatsapp="+91 94480 54321",
            address="GKVK Campus, Bellary Road",
            city="Bengaluru",
            district="Bengaluru Urban",
            state="Karnataka",
            pincode="560065",
            latitude=13.0760,
            longitude=77.5768,
            opening_hours="08:30 AM - 05:30 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BNG-AGR-2023-0089",
            rating=4.9,
            reviews_count=38,
            categories_json=json.dumps(["Certified Paddy Seeds", "Bio-Control", "Fungicides", "Micronutrients"])
        )
        s3 = Store(
            store_name="Krishi Seva Kendra & Agro Inputs",
            owner_name="S. N. Murthy",
            phone="+91 94481 98765",
            email="murthyagro@gmail.com",
            whatsapp="+91 94481 98765",
            address="APMC Market Yard, Yeshwanthpur - Malleshwaram",
            city="Bengaluru",
            district="Bengaluru Urban",
            state="Karnataka",
            pincode="560003",
            latitude=12.9982,
            longitude=77.5713,
            opening_hours="08:00 AM - 08:00 PM (Mon-Sat)",
            is_open_now=True,
            verification_status="verified",
            license_number="KA-BNG-RET-2022-0451",
            rating=4.7,
            reviews_count=19,
            categories_json=json.dumps(["Fungicides", "Bactericides", "Fertilizers", "Farming Equipment"])
        )
        db.session.add_all([s1, s2, s3])
        db.session.commit()

        # Seed essential treatment products for rice diseases
        prods = [
            Product(store_id=s1.id, product_name="Beam 75 WP (Tricyclazole)", category="Fungicide", active_ingredient="Tricyclazole 75% WP", manufacturer="Corteva Agriscience", pack_size="120 g", price=420.0, stock_status="in_stock", target_diseases_json=json.dumps(["Rice Blast", "Blast"])),
            Product(store_id=s1.id, product_name="Kasu-B 3% SL (Kasugamycin)", category="Bactericide & Fungicide", active_ingredient="Kasugamycin 3% SL", manufacturer="Bharat Certis", pack_size="500 ml", price=480.0, stock_status="in_stock", target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Rice Blast"])),
            Product(store_id=s1.id, product_name="Multiplex Zinc Micronutrient 21%", category="Fertilizer & Micronutrient", active_ingredient="Zinc Sulfate Heptahydrate 21%", manufacturer="Multiplex Group", pack_size="5 kg", price=360.0, stock_status="in_stock", target_diseases_json=json.dumps(["Zinc Deficiency", "Khaira Disease"])),
            Product(store_id=s2.id, product_name="BPT 5204 (Samba Mahsuri) Foundation Seed", category="Seeds", active_ingredient="Certified Breeder Seed", manufacturer="UAS Bangalore", pack_size="25 kg Bag", price=1250.0, stock_status="in_stock", target_diseases_json=json.dumps([])),
            Product(store_id=s2.id, product_name="Bio-Neem Azadirachtin 10000 ppm", category="Bio-control", active_ingredient="Azadirachtin 1% EC", manufacturer="GKVK Bio-Tech", pack_size="1 L", price=550.0, stock_status="in_stock", target_diseases_json=json.dumps(["Brown Spot", "Sheath Rot"])),
            Product(store_id=s3.id, product_name="Streptocycline 90:10", category="Bactericide", active_ingredient="Streptomycin Sulphate + Tetracycline", manufacturer="Hindustan Antibiotics", pack_size="6 g Pouch", price=55.0, stock_status="in_stock", target_diseases_json=json.dumps(["Bacterial Leaf Blight", "Bacterial Leaf Streak"])),
            Product(store_id=s3.id, product_name="Nativo 75 WG (Tebuconazole + Trifloxystrobin)", category="Fungicide", active_ingredient="Tebuconazole 50% + Trifloxystrobin 25%", manufacturer="Bayer CropScience", pack_size="100 g", price=780.0, stock_status="in_stock", target_diseases_json=json.dumps(["Sheath Blight", "False Smut", "Brown Spot"]))
        ]
        db.session.add_all(prods)
        db.session.commit()

    print("[Database Seeder] Initial database seed completed successfully.")

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

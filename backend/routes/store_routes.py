"""
AgriVersion - Local Agricultural Store & Product Availability API Routes
Endpoints for:
- Disease -> Management Category Mapping & Safety Advisory
- Geolocation & Regional Store Search
- Store Details, Full Inventory & Review Submission
- Retailer Store Registration & Inventory Management (Retailer Portal)
- Product Availability Alert / "Notify Me" Requests
- Admin Verification & Governance
"""

from flask import Blueprint, request, jsonify, session
from backend.database.db import db
from backend.database.models import Store, Product, StoreRequest, StoreReview, AdminLog
from backend.services.store_service import (
    search_stores,
    get_disease_management_category,
    create_store,
    add_product_to_store,
    update_product_inventory,
    create_stock_notification_request,
    add_store_review,
    DISEASE_CATEGORY_MAPPINGS,
    LIVE_STORES_CACHE
)
from backend.utils.auth_helpers import get_current_user, login_required, admin_required

store_bp = Blueprint("store_bp", __name__, url_prefix="/api/stores")


# ------------------------------------------------------------------------------
# 1. Public Search & Listing Endpoints
# ------------------------------------------------------------------------------

@store_bp.route("", methods=["GET"])
def get_stores():
    """
    Search and retrieve nearby participating agricultural stores.
    Supports query, pincode, geolocation, disease, category, stock, distance & sorting.
    """
    user_lat = request.args.get("lat")
    user_lng = request.args.get("lng")
    is_gps = request.args.get("is_gps", "false").lower() in ["true", "1", "yes"]
    query = request.args.get("query", "").strip()
    pincode = request.args.get("pincode", "").strip()
    disease = request.args.get("disease", "").strip()
    category = request.args.get("category", "").strip()
    stock_status = request.args.get("stock_status", "").strip()
    verified_only = request.args.get("verified_only", "false").lower() in ["true", "1", "yes"]
    open_now = request.args.get("open_now", "false").lower() in ["true", "1", "yes"]
    
    try:
        max_dist = float(request.args.get("max_distance", 50.0))
    except (ValueError, TypeError):
        max_dist = 50.0

    sort_by = request.args.get("sort_by", "distance").strip()

    result = search_stores(
        user_lat=user_lat,
        user_lng=user_lng,
        query=query,
        pincode=pincode,
        disease=disease,
        category=category,
        stock_status=stock_status,
        verified_only=verified_only,
        open_now=open_now,
        max_distance_km=max_dist,
        sort_by=sort_by,
        is_gps=is_gps
    )
    return jsonify(result)



@store_bp.route("/detect-my-location", methods=["GET"])
def detect_my_location():
    """Detects client real location using multi-provider IP geolocation with reliable user profile fallbacks."""
    import urllib.request
    import json
    from backend.utils.auth_helpers import get_current_user
    from backend.services.weather_service import geocode_location
    from backend.services.store_service import get_live_location_address_details

    # 1. Check logged-in user's profile location first
    user = get_current_user()
    if user and user.location:
        geo = geocode_location(user.location)
        if geo:
            lat, lng, res_name = geo
            return jsonify({
                "success": True,
                "city": res_name.split(",")[0].strip(),
                "region": res_name,
                "country": "India",
                "lat": lat,
                "lng": lng,
                "label": res_name,
                "source": "User Profile Location"
            })

    # 2. Try ip-api.com
    try:
        req = urllib.request.Request("http://ip-api.com/json/", headers={"User-Agent": "AgriVersion/2.4"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                lat = float(data.get("lat", 12.9753))
                lng = float(data.get("lon", 77.5910))
                info = get_live_location_address_details(lat, lng)
                return jsonify({
                    "success": True,
                    "city": info.get("city"),
                    "region": info.get("district") or info.get("state"),
                    "country": "India",
                    "lat": lat,
                    "lng": lng,
                    "label": info.get("label"),
                    "source": "IP Geolocation"
                })
    except Exception:
        pass

    # 3. Try ipwho.is as secondary provider
    try:
        req = urllib.request.Request("https://ipwho.is/", headers={"User-Agent": "AgriVersion/2.4"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            if data.get("success"):
                lat = float(data.get("latitude", 12.9753))
                lng = float(data.get("longitude", 77.5910))
                info = get_live_location_address_details(lat, lng)
                return jsonify({
                    "success": True,
                    "city": info.get("city"),
                    "region": info.get("district") or info.get("state"),
                    "country": "India",
                    "lat": lat,
                    "lng": lng,
                    "label": info.get("label"),
                    "source": "IP Geolocation"
                })
    except Exception:
        pass

    return jsonify({
        "success": True,
        "city": "Bengaluru",
        "region": "Karnataka",
        "country": "India",
        "lat": 12.9753,
        "lng": 77.5910,
        "label": "Bengaluru, Karnataka",
        "source": "Default Location"
    })


@store_bp.route("/reverse-geocode", methods=["GET"])
def reverse_geocode_api():
    """Converts GPS lat/lng into human-readable city, district, and locality label."""
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if not lat or not lng:
        return jsonify({"success": False, "message": "Missing coordinates"}), 400
    try:
        from backend.services.store_service import get_live_location_address_details
        info = get_live_location_address_details(float(lat), float(lng))
        return jsonify({"success": True, "location": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@store_bp.route("/<int:store_id>", methods=["GET"])
def get_store_detail(store_id):
    """Returns full details, complete inventory, and reviews for a single store."""
    if store_id in LIVE_STORES_CACHE:
        return jsonify({"success": True, "store": LIVE_STORES_CACHE[store_id]})

    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"success": False, "message": "Agricultural store not found."}), 404

    data = store.to_dict(include_products=True)
    return jsonify({"success": True, "store": data})


@store_bp.route("/categories", methods=["GET"])
def get_categories():
    """Returns available product categories and list of supported rice diseases."""
    categories = [
        "All Categories",
        "Fungicides",
        "Bactericides",
        "Insecticides",
        "Bio-control & Organic",
        "Fertilizers & Micronutrients",
        "Seed Treatment",
        "Farming Tools & Equipment"
    ]
    diseases = list(DISEASE_CATEGORY_MAPPINGS.keys())
    return jsonify({
        "success": True,
        "categories": categories,
        "diseases": diseases
    })


@store_bp.route("/disease-recommendations/<disease_name>", methods=["GET"])
def get_disease_recommendations(disease_name):
    """
    Returns non-prescriptive management category and verified active ingredients
    for a given detected disease with regulatory safety disclaimers.
    """
    rec = get_disease_management_category(disease_name)
    return jsonify({"success": True, "recommendations": rec})


# ------------------------------------------------------------------------------
# 2. Farmer Review & Stock Availability Request Endpoints
# ------------------------------------------------------------------------------

@store_bp.route("/<int:store_id>/reviews", methods=["POST"])
def post_store_review(store_id):
    """Allows a farmer to submit a rating and feedback review for a store."""
    store = Store.query.get(store_id)
    if not store:
        return jsonify({"success": False, "message": "Store not found."}), 404

    user = get_current_user()
    data = request.get_json() or {}
    user_name = data.get("user_name") or (user.full_name if user else "Local Farmer")
    
    review = add_store_review(
        store_id=store_id,
        data=data,
        user_id=user.id if user else None,
        user_name=user_name
    )

    return jsonify({
        "success": True,
        "message": "Review submitted successfully! Thank you for helping fellow farmers.",
        "review": review.to_dict()
    }), 201


@store_bp.route("/request-availability", methods=["POST"])
def request_stock_availability():
    """
    Submits a 'Notify Me' demand request for a product category or specific disease.
    """
    user = get_current_user()
    data = request.get_json() or {}

    if not data.get("product_category") and not data.get("disease_name") and not data.get("product_name"):
        return jsonify({"success": False, "message": "Product category or disease name is required."}), 400

    req_record = create_stock_notification_request(
        data=data,
        user_id=user.id if user else None
    )

    return jsonify({
        "success": True,
        "message": "Notification request registered! You will be alerted when participating stores report availability.",
        "request": req_record.to_dict()
    }), 201


# ------------------------------------------------------------------------------
# 3. Retailer Portal: Registration & Inventory Management
# ------------------------------------------------------------------------------

@store_bp.route("/register", methods=["POST"])
def register_store():
    """Registers a new agricultural retail store."""
    user = get_current_user()
    data = request.get_json() or {}

    store_name = data.get("store_name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    district = data.get("district", "").strip()
    pincode = data.get("pincode", "").strip()

    if not store_name or not phone or not address or not city or not pincode:
        return jsonify({"success": False, "message": "Please fill in all mandatory store fields (Name, Phone, Address, City, PIN)."}), 400

    # Auto-verify if registered by admin, otherwise pending
    is_admin = bool(user and user.role == "admin")
    data["is_admin"] = is_admin

    new_store = create_store(data, owner_id=user.id if user else None)

    # If sample products were supplied during onboarding
    if "initial_products" in data and isinstance(data["initial_products"], list):
        for prod_data in data["initial_products"]:
            add_product_to_store(new_store.id, prod_data, user_name=data.get("owner_name", "Retail Owner"))

    return jsonify({
        "success": True,
        "message": "Store registered successfully! " + ("Verified by Administrator." if is_admin else "Your listing is pending admin verification."),
        "store": new_store.to_dict(include_products=True)
    }), 201


@store_bp.route("/my-stores", methods=["GET"])
@login_required
def get_my_stores():
    """Returns all stores owned by the currently logged-in user."""
    user = get_current_user()
    stores = Store.query.filter_by(owner_id=user.id).all()
    
    # If admin or no stores owned, check if they have demo store or show all
    if not stores and user.role == "admin":
        stores = Store.query.limit(10).all()

    return jsonify({
        "success": True,
        "stores": [s.to_dict(include_products=True) for s in stores]
    })


@store_bp.route("/<int:store_id>/products", methods=["POST"])
@login_required
def add_product(store_id):
    """Adds a new agricultural product to a store inventory."""
    user = get_current_user()
    store = Store.query.get(store_id)
    if not store:
        return jsonify({"success": False, "message": "Store not found."}), 404

    # Permission check: must be owner or admin
    if store.owner_id and store.owner_id != user.id and user.role != "admin":
        return jsonify({"success": False, "message": "Unauthorized to manage this store's inventory."}), 403

    data = request.get_json() or {}
    if not data.get("product_name") or not data.get("active_ingredient"):
        return jsonify({"success": False, "message": "Product name and active ingredient are required."}), 400

    product = add_product_to_store(store_id, data, user_name=user.full_name)
    return jsonify({
        "success": True,
        "message": f"Product '{product.product_name}' added to inventory.",
        "product": product.to_dict()
    }), 201


@store_bp.route("/<int:store_id>/products/<int:prod_id>", methods=["PUT"])
@login_required
def update_product(store_id, prod_id):
    """Updates product stock status, price, pack size, etc."""
    user = get_current_user()
    store = Store.query.get(store_id)
    if not store:
        return jsonify({"success": False, "message": "Store not found."}), 404

    if store.owner_id and store.owner_id != user.id and user.role != "admin":
        return jsonify({"success": False, "message": "Unauthorized to manage this store."}), 403

    product = Product.query.filter_by(id=prod_id, store_id=store_id).first()
    if not product:
        return jsonify({"success": False, "message": "Product not found in this store."}), 404

    data = request.get_json() or {}
    updated = update_product_inventory(prod_id, data, user_name=user.full_name)

    return jsonify({
        "success": True,
        "message": f"Inventory updated for '{updated.product_name}'. Stock Status: {updated.stock_status.upper()}",
        "product": updated.to_dict()
    })


@store_bp.route("/<int:store_id>/products/<int:prod_id>", methods=["DELETE"])
@login_required
def delete_product(store_id, prod_id):
    """Removes a product from store inventory."""
    user = get_current_user()
    store = Store.query.get(store_id)
    if not store:
        return jsonify({"success": False, "message": "Store not found."}), 404

    if store.owner_id and store.owner_id != user.id and user.role != "admin":
        return jsonify({"success": False, "message": "Unauthorized."}), 403

    product = Product.query.filter_by(id=prod_id, store_id=store_id).first()
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "message": "Product removed from inventory."})


# ------------------------------------------------------------------------------
# 4. Administrator Governance & Verification Endpoints
# ------------------------------------------------------------------------------

@store_bp.route("/admin/all", methods=["GET"])
@admin_required
def admin_get_all_stores():
    """Administrator view of all registered stores with verification statuses."""
    stores = Store.query.order_by(Store.created_at.desc()).all()
    
    total_stores = len(stores)
    verified_count = sum(1 for s in stores if s.verification_status == "verified")
    pending_count = sum(1 for s in stores if s.verification_status == "pending")
    total_products = Product.query.count()
    total_requests = StoreRequest.query.count()

    return jsonify({
        "success": True,
        "total_stores": total_stores,
        "verified_count": verified_count,
        "pending_count": pending_count,
        "total_products": total_products,
        "total_requests": total_requests,
        "stores": [s.to_dict(include_products=True) for s in stores]
    })


@store_bp.route("/admin/<int:store_id>/status", methods=["PUT"])
@admin_required
def admin_update_store_status(store_id):
    """Admin endpoint to verify (✓), reject, or suspend a store."""
    admin_user = get_current_user()
    store = Store.query.get(store_id)
    if not store:
        return jsonify({"success": False, "message": "Store not found."}), 404

    data = request.get_json() or {}
    new_status = data.get("status", "verified")  # 'verified', 'pending', 'rejected', 'suspended'
    if new_status not in ["verified", "pending", "rejected", "suspended"]:
        return jsonify({"success": False, "message": "Invalid status."}), 400

    old_status = store.verification_status
    store.verification_status = new_status
    
    log = AdminLog(
        admin_id=admin_user.id,
        action="UPDATE_STORE_STATUS",
        target=f"Store:{store.store_name} (ID: {store.id})",
        details=f"Status changed from {old_status} to {new_status}"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Store '{store.store_name}' status updated to {new_status.title()}.",
        "store": store.to_dict()
    })

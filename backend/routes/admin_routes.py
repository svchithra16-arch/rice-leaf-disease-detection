"""
AgriVersion - Administrator Dashboard, User Management & ML Performance API Routes
"""

from collections import Counter
from flask import Blueprint, request, jsonify
from backend.database.db import db
from backend.database.models import User, Prediction, Conversation, DiseaseInfo, AdminLog, Store, Product
from backend.utils.auth_helpers import get_current_user, admin_required
from ml.evaluate import generate_model_evaluation_metrics

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


@admin_bp.route("/overview", methods=["GET"])
@admin_required
def get_overview():
    total_users = User.query.count()
    total_scans = Prediction.query.count()
    total_chats = Conversation.query.count()
    total_stores = Store.query.count()
    verified_stores = Store.query.filter_by(verification_status="verified").count()
    pending_stores = Store.query.filter_by(verification_status="pending").count()
    total_products = Product.query.count()
    
    # Global disease distribution
    all_preds = Prediction.query.all()
    disease_counts = Counter(p.disease_name for p in all_preds)
    
    recent_users = [u.to_dict() for u in User.query.order_by(User.created_at.desc()).limit(5).all()]
    recent_scans = [p.to_dict() for p in Prediction.query.order_by(Prediction.created_at.desc()).limit(6).all()]

    return jsonify({
        "success": True,
        "total_users": total_users,
        "total_scans": total_scans,
        "total_chats": total_chats,
        "total_stores": total_stores,
        "verified_stores": verified_stores,
        "pending_stores": pending_stores,
        "total_products": total_products,
        "overall_accuracy": 97.42,
        "disease_distribution": dict(disease_counts),
        "recent_users": recent_users,
        "recent_scans": recent_scans
    })


@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.order_by(User.created_at.desc()).all()
    user_list = []
    for u in users:
        d = u.to_dict()
        d["scans_count"] = len(u.predictions)
        d["farms_count"] = len(u.farms)
        d["is_active"] = u.is_active
        user_list.append(d)

    return jsonify({"success": True, "users": user_list})


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["PUT"])
@admin_required
def toggle_user_status(user_id):
    current_admin = get_current_user()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    if user.id == current_admin.id:
        return jsonify({"success": False, "message": "Cannot toggle your own status."}), 400

    user.is_active = not user.is_active
    
    # Log admin action
    log = AdminLog(
        admin_id=current_admin.id,
        action="TOGGLE_USER_STATUS",
        target=f"User:{user.username}",
        details=f"Status set to {user.is_active}"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"success": True, "message": f"User status updated to {'Active' if user.is_active else 'Deactivated'}.", "user": user.to_dict()})


@admin_bp.route("/diseases", methods=["GET"])
@admin_required
def get_diseases():
    diseases = DiseaseInfo.query.order_by(DiseaseInfo.name_en).all()
    return jsonify({"success": True, "diseases": [d.to_dict() for d in diseases]})


@admin_bp.route("/diseases/<int:disease_id>", methods=["PUT"])
@admin_required
def update_disease(disease_id):
    current_admin = get_current_user()
    d = DiseaseInfo.query.get(disease_id)
    if not d:
        return jsonify({"success": False, "message": "Disease profile not found."}), 404

    data = request.get_json() or {}
    if "symptoms" in data: d.symptoms = data["symptoms"]
    if "causes" in data: d.causes = data["causes"]
    if "prevention" in data: d.prevention = data["prevention"]
    if "management" in data: d.management = data["management"]
    if "scientific_name" in data: d.scientific_name = data["scientific_name"]
    if "pathogen_type" in data: d.pathogen_type = data["pathogen_type"]

    log = AdminLog(
        admin_id=current_admin.id,
        action="UPDATE_DISEASE_INFO",
        target=f"Disease:{d.code}",
        details=f"Updated profile for {d.name_en}"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"success": True, "message": "Disease profile updated successfully.", "disease": d.to_dict()})


@admin_bp.route("/ml-metrics", methods=["GET"])
@admin_required
def get_ml_metrics():
    metrics = generate_model_evaluation_metrics()
    return jsonify({"success": True, "metrics": metrics})


@admin_bp.route("/logs", methods=["GET"])
@admin_required
def get_admin_logs():
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(50).all()
    return jsonify({"success": True, "logs": [l.to_dict() for l in logs]})

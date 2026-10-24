"""
AgriVersion - Farm & Field Management API Routes
"""

from flask import Blueprint, request, jsonify
from backend.database.db import db
from backend.database.models import Farm, Field, Prediction
from backend.utils.auth_helpers import get_current_user, login_required

farm_bp = Blueprint("farm_bp", __name__, url_prefix="/api/farms")


@farm_bp.route("", methods=["GET"])
@login_required
def get_farms():
    user = get_current_user()
    farms = Farm.query.filter_by(user_id=user.id).order_by(Farm.created_at.desc()).all()
    
    result = []
    for farm in farms:
        f_dict = farm.to_dict()
        f_dict["fields"] = [f.to_dict() for f in farm.fields]
        result.append(f_dict)

    return jsonify({"success": True, "farms": result})


@farm_bp.route("", methods=["POST"])
@login_required
def create_farm():
    user = get_current_user()
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    location = data.get("location", "").strip()
    total_area = float(data.get("total_area", 1.0))
    soil_type = data.get("soil_type", "Alluvial / Clayey Loam").strip()

    if not name or not location:
        return jsonify({"success": False, "message": "Farm name and location are required."}), 400

    farm = Farm(
        user_id=user.id,
        name=name,
        location=location,
        total_area=total_area,
        soil_type=soil_type
    )
    db.session.add(farm)
    db.session.commit()

    return jsonify({"success": True, "message": "Farm created successfully.", "farm": farm.to_dict()}), 201


@farm_bp.route("/<int:farm_id>", methods=["DELETE"])
@login_required
def delete_farm(farm_id):
    user = get_current_user()
    farm = Farm.query.filter_by(id=farm_id, user_id=user.id).first()
    if not farm:
        return jsonify({"success": False, "message": "Farm not found."}), 404

    db.session.delete(farm)
    db.session.commit()
    return jsonify({"success": True, "message": "Farm deleted successfully."})


@farm_bp.route("/<int:farm_id>/fields", methods=["POST"])
@login_required
def create_field(farm_id):
    user = get_current_user()
    farm = Farm.query.filter_by(id=farm_id, user_id=user.id).first()
    if not farm:
        return jsonify({"success": False, "message": "Farm not found."}), 404

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    crop_variety = data.get("crop_variety", "IR64 / Sona Masoori").strip()
    sowing_date = data.get("sowing_date", "")
    notes = data.get("notes", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Field name is required."}), 400

    field = Field(
        farm_id=farm.id,
        name=name,
        crop_variety=crop_variety,
        sowing_date=sowing_date,
        notes=notes
    )
    db.session.add(field)
    db.session.commit()

    return jsonify({"success": True, "message": "Field added successfully.", "field": field.to_dict()}), 201


@farm_bp.route("/fields/<int:field_id>", methods=["DELETE"])
@login_required
def delete_field(field_id):
    user = get_current_user()
    field = Field.query.join(Farm).filter(Field.id == field_id, Farm.user_id == user.id).first()
    if not field:
        return jsonify({"success": False, "message": "Field not found."}), 404

    db.session.delete(field)
    db.session.commit()
    return jsonify({"success": True, "message": "Field deleted successfully."})


@farm_bp.route("/fields", methods=["GET"])
@login_required
def get_all_user_fields():
    """Returns a flat list of fields for dropdowns in disease detection."""
    user = get_current_user()
    fields = Field.query.join(Farm).filter(Farm.user_id == user.id).all()
    return jsonify({
        "success": True,
        "fields": [f.to_dict() for f in fields]
    })

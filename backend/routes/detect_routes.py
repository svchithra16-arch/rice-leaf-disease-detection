"""
AgriVersion - Disease Detection, Camera Scan, Diagnostic Reports & Model Validation API Routes
"""

import os
import json
import numpy as np
from flask import Blueprint, request, jsonify, send_file
from backend.database.db import db
from backend.database.models import Prediction, Field, Farm, User
from backend.services.ai_service import run_rice_leaf_diagnosis
from backend.services.pdf_service import generate_diagnostic_pdf_report
from backend.utils.auth_helpers import get_current_user, login_required
from backend.utils.file_validators import save_uploaded_image, save_base64_image
from ml.dataset_info import DISEASE_CLASSES, DISEASE_DETAILS
from ml.predict import predict_rice_disease

from backend.config import Config, BASE_DIR
from backend.utils.location_helpers import resolve_upload_location
from backend.services.weather_service import get_weather_and_disease_risk
from backend.services.store_service import search_stores

detect_bp = Blueprint("detect_bp", __name__, url_prefix="/api/detect")


@detect_bp.route("/upload", methods=["POST"])
@login_required
def detect_upload():
    user = get_current_user()
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image file provided in request."}), 400

    file_storage = request.files["image"]
    field_id = request.form.get("field_id")
    req_lat = request.form.get("latitude")
    req_lng = request.form.get("longitude")
    req_loc_hint = request.form.get("location_name")

    field = None
    if field_id:
        try:
            field_id = int(field_id)
            field = Field.query.get(field_id)
        except ValueError:
            field_id = None

    # Save and validate image
    saved, filename, err = save_uploaded_image(file_storage)
    if not saved:
        return jsonify({"success": False, "message": err, "error_type": "upload_error"}), 400

    image_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    # 1. Resolve Location from EXIF Metadata / Device Geolocation / Farm / User Profile
    loc_info = resolve_upload_location(
        lat=req_lat,
        lng=req_lng,
        location_hint=req_loc_hint,
        user=user,
        field=field,
        image_path=image_path
    )

    # 2. Execute AI Diagnosis
    diag_result = run_rice_leaf_diagnosis(filename)
    if not diag_result.get("success"):
        return jsonify(diag_result), 422

    # 3. Fetch Location-Aware Weather & Disease Outbreak Risk
    weather_risk = get_weather_and_disease_risk(
        latitude=loc_info["latitude"],
        longitude=loc_info["longitude"],
        location_name=loc_info["location_name"]
    )

    # 4. Fetch Nearby Registered Stores stocking treatment for this disease within 25 km of upload location
    disease_name = diag_result["primary_disease"]
    search_res = search_stores(
        user_lat=loc_info["latitude"],
        user_lng=loc_info["longitude"],
        disease=disease_name,
        max_distance_km=25.0,
        is_gps=True
    )
    nearby_stores = search_res.get("stores", [])[:3]

    # Save to Database
    prediction = Prediction(
        user_id=user.id,
        field_id=field_id,
        image_filename=filename,
        gradcam_filename=diag_result.get("gradcam_overlay_filename") or diag_result.get("gradcam_filename"),
        severity_mask_filename=diag_result.get("severity_mask_filename"),
        disease_name=disease_name,
        confidence=diag_result["confidence"],
        severity_level=diag_result["severity"]["severity_level"],
        healthy_area_pct=diag_result["severity"]["healthy_area_pct"],
        affected_area_pct=diag_result["severity"]["affected_area_pct"],
        lesion_count=diag_result["severity"]["lesion_count"],
        top_predictions_json=json.dumps(diag_result["top_predictions"]),
        is_low_confidence=diag_result.get("is_uncertain", False),
        location_name=loc_info["location_name"],
        latitude=loc_info["latitude"],
        longitude=loc_info["longitude"],
        location_source=loc_info["location_source"]
    )
    db.session.add(prediction)
    db.session.commit()

    # Generate Diagnostic PDF Report with Location Context
    farm_info = None
    if field:
        farm_info = {
            "farm_name": field.farm.name if field.farm else "",
            "field_name": field.name,
            "crop_variety": field.crop_variety
        }

    # Pass location info to PDF report
    pdf_user_data = user.to_dict()
    pdf_user_data["location"] = f"{loc_info['location_name']} ({loc_info['location_source']})"

    pdf_ok, pdf_name, _ = generate_diagnostic_pdf_report(
        prediction_data=diag_result,
        user_data=pdf_user_data,
        farm_data=farm_info
    )
    if pdf_ok:
        prediction.report_pdf_filename = pdf_name
        db.session.commit()
        diag_result["report_pdf_url"] = f"/static_reports/{pdf_name}"

    diag_result["prediction_id"] = prediction.id
    diag_result["location_info"] = loc_info
    diag_result["weather_risk"] = weather_risk
    diag_result["nearby_stores"] = nearby_stores

    return jsonify(diag_result)


@detect_bp.route("/camera", methods=["POST"])
@login_required
def detect_camera():
    user = get_current_user()
    data = request.get_json() or {}
    image_data = data.get("image_data")
    field_id = data.get("field_id")
    req_lat = data.get("latitude")
    req_lng = data.get("longitude")
    req_loc_hint = data.get("location_name")

    if not image_data:
        return jsonify({"success": False, "message": "No camera snapshot data provided."}), 400

    field = None
    if field_id:
        try:
            field_id = int(field_id)
            field = Field.query.get(field_id)
        except ValueError:
            field_id = None

    saved, filename, err = save_base64_image(image_data)
    if not saved:
        return jsonify({"success": False, "message": err, "error_type": "upload_error"}), 400

    image_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    loc_info = resolve_upload_location(
        lat=req_lat,
        lng=req_lng,
        location_hint=req_loc_hint,
        user=user,
        field=field,
        image_path=image_path
    )

    diag_result = run_rice_leaf_diagnosis(filename)
    if not diag_result.get("success"):
        return jsonify(diag_result), 422

    disease_name = diag_result["primary_disease"]

    weather_risk = get_weather_and_disease_risk(
        latitude=loc_info["latitude"],
        longitude=loc_info["longitude"],
        location_name=loc_info["location_name"]
    )

    search_res = search_stores(
        user_lat=loc_info["latitude"],
        user_lng=loc_info["longitude"],
        disease=disease_name,
        max_distance_km=25.0,
        is_gps=True
    )
    nearby_stores = search_res.get("stores", [])[:3]

    prediction = Prediction(
        user_id=user.id,
        field_id=field_id,
        image_filename=filename,
        gradcam_filename=diag_result.get("gradcam_overlay_filename") or diag_result.get("gradcam_filename"),
        severity_mask_filename=diag_result.get("severity_mask_filename"),
        disease_name=disease_name,
        confidence=diag_result["confidence"],
        severity_level=diag_result["severity"]["severity_level"],
        healthy_area_pct=diag_result["severity"]["healthy_area_pct"],
        affected_area_pct=diag_result["severity"]["affected_area_pct"],
        lesion_count=diag_result["severity"]["lesion_count"],
        top_predictions_json=json.dumps(diag_result["top_predictions"]),
        is_low_confidence=diag_result.get("is_uncertain", False),
        location_name=loc_info["location_name"],
        latitude=loc_info["latitude"],
        longitude=loc_info["longitude"],
        location_source=loc_info["location_source"]
    )
    db.session.add(prediction)
    db.session.commit()

    pdf_user_data = user.to_dict()
    pdf_user_data["location"] = f"{loc_info['location_name']} ({loc_info['location_source']})"

    pdf_ok, pdf_name, _ = generate_diagnostic_pdf_report(
        prediction_data=diag_result,
        user_data=pdf_user_data
    )
    if pdf_ok:
        prediction.report_pdf_filename = pdf_name
        db.session.commit()
        diag_result["report_pdf_url"] = f"/static_reports/{pdf_name}"

    diag_result["prediction_id"] = prediction.id
    diag_result["location_info"] = loc_info
    diag_result["weather_risk"] = weather_risk
    diag_result["nearby_stores"] = nearby_stores

    return jsonify(diag_result)


@detect_bp.route("/history", methods=["GET"])
@login_required
def get_history():
    user = get_current_user()
    disease_filter = request.args.get("disease")
    severity_filter = request.args.get("severity")
    field_id = request.args.get("field_id")

    query = Prediction.query.filter_by(user_id=user.id)
    if disease_filter:
        query = query.filter(Prediction.disease_name.ilike(f"%{disease_filter}%"))
    if severity_filter:
        query = query.filter(Prediction.severity_level == severity_filter)
    if field_id:
        query = query.filter(Prediction.field_id == field_id)

    predictions = query.order_by(Prediction.created_at.desc()).all()
    return jsonify({
        "success": True,
        "count": len(predictions),
        "history": [p.to_dict() for p in predictions]
    })


@detect_bp.route("/<int:pred_id>", methods=["GET"])
@login_required
def get_prediction_detail(pred_id):
    user = get_current_user()
    pred = Prediction.query.filter_by(id=pred_id, user_id=user.id).first()
    if not pred:
        return jsonify({"success": False, "message": "Prediction record not found."}), 404
    return jsonify({"success": True, "prediction": pred.to_dict()})


@detect_bp.route("/<int:pred_id>/save-field", methods=["POST"])
@login_required
def associate_field(pred_id):
    user = get_current_user()
    pred = Prediction.query.filter_by(id=pred_id, user_id=user.id).first()
    if not pred:
        return jsonify({"success": False, "message": "Record not found."}), 404

    data = request.get_json() or {}
    field_id = data.get("field_id")
    pred.field_id = field_id
    db.session.commit()
    return jsonify({"success": True, "message": "Associated with field successfully.", "prediction": pred.to_dict()})


@detect_bp.route("/<int:pred_id>", methods=["DELETE"])
@login_required
def delete_prediction(pred_id):
    user = get_current_user()
    pred = Prediction.query.filter_by(id=pred_id, user_id=user.id).first()
    if not pred:
        return jsonify({"success": False, "message": "Record not found."}), 404

    db.session.delete(pred)
    db.session.commit()
    return jsonify({"success": True, "message": "Scan record deleted successfully."})


@detect_bp.route("/<int:pred_id>/pdf", methods=["GET"])
@login_required
def download_pdf_report(pred_id):
    user = get_current_user()
    pred = Prediction.query.filter_by(id=pred_id, user_id=user.id).first()
    if not pred:
        return jsonify({"success": False, "message": "Record not found."}), 404

    if not pred.report_pdf_filename:
        pdf_ok, pdf_name, _ = generate_diagnostic_pdf_report(
            prediction_data=pred.to_dict(),
            user_data=user.to_dict()
        )
        if pdf_ok:
            pred.report_pdf_filename = pdf_name
            db.session.commit()

    return jsonify({
        "success": True,
        "report_url": f"/static_reports/{pred.report_pdf_filename}"
    })


@detect_bp.route("/sample-leaves", methods=["GET"])
def get_sample_leaves_list():
    """Returns metadata and download URLs for all 20 rice leaf disease sample images."""
    sample_dir = os.path.abspath(os.path.join(BASE_DIR, "frontend", "assets", "sample_leaves"))
    if not os.path.exists(sample_dir):
        return jsonify({"success": False, "message": "Sample directory not found."}), 404

    samples = []
    for idx, disease in enumerate(DISEASE_CLASSES):
        clean_name = disease.lower().replace(" ", "_").replace("(", "").replace(")", "")
        filename = f"{idx:02d}_{clean_name}.jpg"
        file_path = os.path.join(sample_dir, filename)
        if os.path.exists(file_path):
            samples.append({
                "class_index": idx,
                "disease_name": disease,
                "filename": filename,
                "download_url": f"/api/detect/sample-leaves/{filename}",
                "view_url": f"/assets/sample_leaves/{filename}"
            })

    return jsonify({"success": True, "count": len(samples), "samples": samples})


@detect_bp.route("/sample-leaves/<filename>", methods=["GET"])
def download_sample_leaf(filename):
    """Serves sample leaf image file for testing."""
    sample_dir = os.path.abspath(os.path.join(BASE_DIR, "frontend", "assets", "sample_leaves"))
    file_path = os.path.join(sample_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "Sample image file not found."}), 404

    return send_file(file_path, mimetype="image/jpeg", as_attachment=True, download_name=filename)


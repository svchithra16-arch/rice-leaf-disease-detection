"""
AgriVersion - Personal User Analytics & Diagnostic Insights API Routes
"""

from collections import Counter
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from sqlalchemy import func
from backend.database.db import db
from backend.database.models import Prediction, Farm
from backend.utils.auth_helpers import get_current_user, login_required

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/user-stats", methods=["GET"])
@login_required
def get_user_stats():
    user = get_current_user()
    predictions = Prediction.query.filter_by(user_id=user.id).all()
    
    total_scans = len(predictions)
    if total_scans == 0:
        return jsonify({
            "success": True,
            "total_scans": 0,
            "healthy_scans": 0,
            "diseased_scans": 0,
            "avg_confidence": 0.0,
            "top_detected_disease": "None",
            "disease_distribution": {},
            "severity_distribution": {"Healthy": 0, "Low": 0, "Mild": 0, "Moderate": 0, "Severe": 0},
            "recent_activity": []
        })

    def clean_disease_name(name):
        if not name:
            return "Healthy"
        return name.replace("_", " ").title().strip()

    def clean_severity(sev):
        if not sev:
            return "Healthy"
        s = sev.strip().title()
        if s in ["Healthy", "Low", "Mild", "Moderate", "Severe"]:
            return s
        return "Moderate"

    healthy_count = sum(
        1 for p in predictions
        if p.disease_name and p.disease_name.lower().strip() in ["healthy", "healthy crop", "normal"]
    )
    diseased_count = max(0, total_scans - healthy_count)

    valid_confidences = [p.confidence for p in predictions if p.confidence is not None]
    if valid_confidences:
        avg_conf = sum(valid_confidences) / len(valid_confidences)
        # Normalize if stored as fraction 0-1
        if avg_conf <= 1.0:
            avg_conf *= 100.0
    else:
        avg_conf = 0.0

    # Disease frequency
    disease_list = [clean_disease_name(p.disease_name) for p in predictions]
    disease_counts = Counter(disease_list)
    top_disease = disease_counts.most_common(1)[0][0] if disease_counts else "None"

    # Severity frequency
    sev_list = [clean_severity(p.severity_level) for p in predictions]
    sev_counts = Counter(sev_list)
    severity_distribution = {
        "Healthy": sev_counts.get("Healthy", 0),
        "Low": sev_counts.get("Low", 0),
        "Mild": sev_counts.get("Mild", 0),
        "Moderate": sev_counts.get("Moderate", 0),
        "Severe": sev_counts.get("Severe", 0)
    }

    # Recent scans (most recent first)
    sorted_preds = sorted(
        predictions,
        key=lambda x: x.created_at or datetime.min,
        reverse=True
    )[:8]

    recent = []
    for p in sorted_preds:
        p_dict = p.to_dict()
        p_dict["disease_name"] = clean_disease_name(p.disease_name)
        p_dict["severity_level"] = clean_severity(p.severity_level)
        p_dict["confidence"] = round(p_dict.get("confidence") or 0.0, 1)
        recent.append(p_dict)

    return jsonify({
        "success": True,
        "total_scans": total_scans,
        "healthy_scans": healthy_count,
        "diseased_scans": diseased_count,
        "avg_confidence": round(avg_conf, 1),
        "top_detected_disease": top_disease,
        "disease_distribution": dict(disease_counts),
        "severity_distribution": severity_distribution,
        "recent_activity": recent
    })


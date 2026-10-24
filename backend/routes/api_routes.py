"""
AgriVersion - Public API, Translations & Disease Encyclopedia Search
"""

import os
import json
from flask import Blueprint, jsonify, send_from_directory
from backend.config import Config
from backend.database.models import DiseaseInfo
from ml.dataset_info import DISEASE_DETAILS

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AgriVersion Rice Pathology Platform",
        "version": "2.4.0",
        "ml_engine": "RiceNet PyTorch + OpenCV Grad-CAM"
    })


@api_bp.route("/translations/<lang>", methods=["GET"])
def get_translation(lang):
    supported = ["en", "kn", "te", "hi", "ta", "ml", "mr", "bn"]
    if lang not in supported:
        lang = "en"

    file_path = os.path.join(Config.TRANSLATIONS_FOLDER, f"{lang}.json")
    if not os.path.exists(file_path):
        file_path = os.path.join(Config.TRANSLATIONS_FOLDER, "en.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/diseases", methods=["GET"])
def get_public_diseases():
    diseases = DiseaseInfo.query.order_by(DiseaseInfo.name_en).all()
    if not diseases:
        # Fallback to in-memory details
        res = []
        for name, d in DISEASE_DETAILS.items():
            res.append({
                "code": d["code"],
                "name_en": name,
                "scientific_name": d["scientific_name"],
                "pathogen_type": d["pathogen_type"],
                "description": d["description"],
                "symptoms": d["symptoms"],
                "causes": d["causes"],
                "prevention": d["prevention"],
                "management": d["management"],
                "severity_info": d["severity_guide"]
            })
        return jsonify({"success": True, "diseases": res})

    return jsonify({"success": True, "diseases": [d.to_dict() for d in diseases]})

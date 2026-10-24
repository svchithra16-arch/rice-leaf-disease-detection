"""
AgriVersion - AI Inference & Botanical Diagnostics Service
Coordinates image validation, Deep CNN prediction, Grad-CAM attention map saving, and quantitative severity estimation.
"""

import os
import uuid
import cv2
from PIL import Image

from backend.config import Config
from ml.predict import predict_rice_disease


def run_rice_leaf_diagnosis(image_filename, confidence_threshold=None, blur_threshold=None):
    """
    Executes full diagnosis on an uploaded/captured leaf image file.
    
    Returns:
        dict with prediction results, generated Grad-CAM filenames, and severity mask filename.
    """
    if confidence_threshold is None:
        confidence_threshold = Config.CONFIDENCE_THRESHOLD
    if blur_threshold is None:
        blur_threshold = Config.BLUR_THRESHOLD

    image_path = os.path.join(Config.UPLOAD_FOLDER, image_filename)
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error_type": "file_not_found",
            "message": "Uploaded image file could not be located on server."
        }

    # Run ML diagnosis pipeline
    results = predict_rice_disease(
        image_path=image_path,
        confidence_threshold=confidence_threshold,
        blur_threshold=blur_threshold
    )

    if not results.get("success"):
        return results

    uid_tag = uuid.uuid4().hex[:10]

    # 1. Save Pure Heatmap (AI Attention Map)
    gradcam_pure_filename = f"gradcam_pure_{uid_tag}.jpg"
    gradcam_pure_path = os.path.join(Config.UPLOAD_FOLDER, gradcam_pure_filename)
    pure_rgb = results["pure_heatmap_rgb"]
    pure_bgr = cv2.cvtColor(pure_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(gradcam_pure_path, pure_bgr)

    # 2. Save Blended Overlay (Grad-CAM Overlay)
    gradcam_overlay_filename = f"gradcam_overlay_{uid_tag}.jpg"
    gradcam_overlay_path = os.path.join(Config.UPLOAD_FOLDER, gradcam_overlay_filename)
    blended_rgb = results["blended_gradcam_rgb"]
    blended_bgr = cv2.cvtColor(blended_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(gradcam_overlay_path, blended_bgr)

    # 3. Save Severity Segmented Mask to upload folder
    severity_mask_filename = f"severity_{uid_tag}.jpg"
    severity_mask_path = os.path.join(Config.UPLOAD_FOLDER, severity_mask_filename)
    seg_rgb = results["segmented_mask_rgb"]
    seg_bgr = cv2.cvtColor(seg_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(severity_mask_path, seg_bgr)

    # Clean up non-serializable numpy arrays before returning
    results_cleaned = {
        "success": True,
        "image_filename": image_filename,
        "gradcam_pure_filename": gradcam_pure_filename,
        "gradcam_overlay_filename": gradcam_overlay_filename,
        "severity_mask_filename": severity_mask_filename,
        "image_url": f"/uploads/{image_filename}",
        "gradcam_pure_url": f"/uploads/{gradcam_pure_filename}",
        "gradcam_overlay_url": f"/uploads/{gradcam_overlay_filename}",
        "gradcam_url": f"/uploads/{gradcam_overlay_filename}",  # Backwards compatibility
        "severity_mask_url": f"/uploads/{severity_mask_filename}",
        "primary_disease": results["primary_disease"],
        "actual_classified_disease": results["actual_classified_disease"],
        "confidence": results["confidence"],
        "confidence_level": results["confidence_level"],
        "confidence_badge_class": results["confidence_badge_class"],
        "confidence_color": results["confidence_color"],
        "scientific_name": results["scientific_name"],
        "pathogen_type": results["pathogen_type"],
        "code": results["code"],
        "description": results["description"],
        "symptoms": results["symptoms"],
        "typical_botanical_symptoms": results.get("typical_botanical_symptoms", ""),
        "favorable_conditions": results["favorable_conditions"],
        "contributing_factors": results["contributing_factors"],
        "prevention": results["prevention"],
        "management": results["management"],
        "expert_consultation": results["expert_consultation"],
        "top_predictions": results["top_predictions"],
        "severity": results["severity"],
        "is_uncertain": results["is_uncertain"],
        "is_closely_matched": results["is_closely_matched"],
        "closely_matched_message": results["closely_matched_message"],
        "validation": results["validation"]
    }

    return results_cleaned

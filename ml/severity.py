"""
AgriVersion - Rice Leaf Disease Lesion Segmentation & Quantitative Area Analysis
Calculates estimated visible healthy vs diseased lesion area percentages and spot counts.
"""

import cv2
import numpy as np
from PIL import Image


def estimate_disease_severity(image_path_or_np, is_predicted_healthy=False):
    """
    Analyzes visible leaf pigmentation and lesion area to estimate disease severity.
    
    Returns:
        dict containing:
            healthy_area_pct: float (Estimated Visible Healthy Area)
            affected_area_pct: float (Estimated Visible Lesion Area)
            severity_level: str ("Healthy", "Low", "Mild", "Moderate", "Severe")
            severity_color: str (Hex color code)
            lesion_count: int (Estimated Visible Lesion Count)
            segmented_mask_rgb: np.ndarray (Visualized segmentation map)
    """
    if isinstance(image_path_or_np, str):
        cv_img = cv2.imread(image_path_or_np)
        if cv_img is None:
            cv_img = np.zeros((224, 224, 3), dtype=np.uint8)
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    elif isinstance(image_path_or_np, Image.Image):
        img_rgb = np.array(image_path_or_np.convert("RGB"))
        cv_img = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = image_path_or_np
        cv_img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    h, w = cv_img.shape[:2]
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

    # 1. Segment Foliage & Green Chlorophyll Mask
    b_ch = cv_img[:, :, 0].astype(np.float32)
    g_ch = cv_img[:, :, 1].astype(np.float32)
    r_ch = cv_img[:, :, 2].astype(np.float32)
    h_ch = hsv[:, :, 0].astype(np.float32)
    s_ch = hsv[:, :, 1].astype(np.float32)
    v_ch = hsv[:, :, 2].astype(np.float32)

    # Green chlorophyll mask (including shaded green tillers)
    green_mask = (((h_ch >= 24) & (h_ch <= 95) & (v_ch >= 6) & ((g_ch >= r_ch * 0.82) | (g_ch >= b_ch * 0.82))) |
                  ((g_ch > r_ch * 1.02) & (g_ch > b_ch * 1.02) & (v_ch >= 8))).astype(np.uint8) * 255

    # Chlorotic yellow
    yellow_mask = (((h_ch >= 10) & (h_ch <= 26) & (s_ch >= 38) & (v_ch >= 55) & (r_ch >= 75)) & (r_ch >= b_ch * 1.15)).astype(np.uint8) * 255

    # Necrotic brown
    brown_mask = (((h_ch >= 4) & (h_ch <= 24) & (s_ch >= 45) & (v_ch >= 55) & (v_ch <= 220) & (r_ch >= 75)) & (r_ch > g_ch) & (r_ch > b_ch * 1.2)).astype(np.uint8) * 255

    # Pale blast center
    pale_blast_center = ((s_ch <= 55) & (v_ch >= 80) & (v_ch <= 235) & (g_ch >= 60) & (r_ch >= 60)).astype(np.uint8) * 255

    # Plant canopy mask
    plant_raw = cv2.bitwise_or(green_mask, yellow_mask)
    plant_raw = cv2.bitwise_or(plant_raw, brown_mask)

    kernel_lg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    plant_mask = cv2.morphologyEx(plant_raw, cv2.MORPH_CLOSE, kernel_lg)
    total_leaf_pixels = max(cv2.countNonZero(plant_mask), int(h * w * 0.05))

    # Lesion mask within plant canopy
    lesion_raw = cv2.bitwise_and(plant_mask, cv2.bitwise_not(green_mask))
    kernel_sm = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    lesion_mask = cv2.morphologyEx(lesion_raw, cv2.MORPH_OPEN, kernel_sm)

    # Exclude outer border clutter
    border_mask = np.ones((h, w), dtype=np.uint8) * 255
    bx = max(4, int(w * 0.03))
    by = max(4, int(h * 0.03))
    border_mask[by:h-by, bx:w-bx] = 0

    contours, _ = cv2.findContours(lesion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area_thresh = max(35, int(total_leaf_pixels * 0.0004))
    significant_contours = []
    valid_lesion_pixels = 0

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area_thresh:
            continue
        x, y_box, cw, ch = cv2.boundingRect(c)
        c_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(c_mask, [c], -1, 255, -1)
        border_overlap = cv2.countNonZero(cv2.bitwise_and(c_mask, border_mask))
        if border_overlap > area * 0.65 and (x == 0 or y_box == 0 or (x + cw) >= w or (y_box + ch) >= h):
            continue
        significant_contours.append(c)
        valid_lesion_pixels += area

    lesion_count = len(significant_contours)

    # Calculate percentages
    if is_predicted_healthy:
        affected_pct = float((valid_lesion_pixels / max(total_leaf_pixels, 1)) * 100.0)
        affected_pct = min(affected_pct, 1.2)
        healthy_pct = 100.0 - affected_pct
        severity_level = "Healthy"
        severity_color = "#10b981"
        lesion_count = 0

        # Visualized Segmentation: Emerald green overlay on healthy foliage
        segmented_mask_rgb = img_rgb.copy()
        green_overlay = np.zeros_like(img_rgb)
        green_overlay[:, :] = [16, 185, 129]
        segmented_mask_rgb[green_mask > 0] = cv2.addWeighted(
            img_rgb[green_mask > 0], 0.78, green_overlay[green_mask > 0], 0.22, 0
        )
    else:
        raw_affected = float((valid_lesion_pixels / max(total_leaf_pixels, 1)) * 100.0)
        affected_pct = max(0.6, min(95.0, raw_affected))
        healthy_pct = 100.0 - affected_pct
        lesion_count = max(1, len(significant_contours))

        if affected_pct < 5.0:
            severity_level = "Low"
            severity_color = "#3b82f6"  # Blue
        elif affected_pct < 20.0:
            severity_level = "Mild"
            severity_color = "#f59e0b"  # Amber
        elif affected_pct < 40.0:
            severity_level = "Moderate"
            severity_color = "#f97316"  # Orange
        else:
            severity_level = "Severe"
            severity_color = "#ef4444"  # Red

        # Visualized Segmentation
        segmented_mask_rgb = img_rgb.copy()

        green_tint = np.zeros_like(img_rgb)
        green_tint[:, :] = [34, 197, 94]
        if np.any(green_mask > 0):
            segmented_mask_rgb[green_mask > 0] = cv2.addWeighted(
                img_rgb[green_mask > 0], 0.75, green_tint[green_mask > 0], 0.25, 0.0
            )

        red_tint = np.zeros_like(img_rgb)
        red_tint[:, :] = [239, 68, 68]
        if np.any(lesion_mask > 0):
            segmented_mask_rgb[lesion_mask > 0] = cv2.addWeighted(
                img_rgb[lesion_mask > 0], 0.35, red_tint[lesion_mask > 0], 0.65, 0.0
            )
        if significant_contours:
            cv2.drawContours(segmented_mask_rgb, significant_contours, -1, (255, 230, 0), 2)

    return {
        "healthy_area_pct": round(healthy_pct, 1),
        "affected_area_pct": round(affected_pct, 1),
        "severity_level": severity_level,
        "severity_color": severity_color,
        "lesion_count": lesion_count,
        "segmented_mask_rgb": segmented_mask_rgb
    }

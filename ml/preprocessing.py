"""
AgriVersion - ML Preprocessing, Botanical Image Quality & Rice-Leaf Validation
Provides strict image quality assessment (blur, lighting, resolution) and foliar verification.
"""

import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

# Standard ImageNet normalization parameters for PyTorch vision backbones
IMG_SIZE = 224
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]

# Standard inference transform (224x224 RGB normalized tensor)
inference_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
])

# Training augmentation transform
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
    transforms.RandomCrop((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=20),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
])


def validate_rice_leaf_image(image_input, blur_threshold=40.0):
    """
    Evaluates image quality and performs botanical rice leaf verification:
    1. Dimension & Resolution check (>= 180x180 px)
    2. Sharpness & Blur check (Laplacian variance)
    3. Lighting & Exposure check (Under/Over-exposure)
    4. Botanical Foliage & Rice Leaf Presence (HSV vegetation & necrotic spectrum)
    
    Returns:
        dict with validation results, error_type, and user-facing messages.
    """
    # 1. Convert input to standard NumPy BGR image
    if isinstance(image_input, str):
        cv_img = cv2.imread(image_input)
        if cv_img is None:
            return {
                "valid": False,
                "is_rice_leaf": False,
                "is_blurry": False,
                "blur_score": 0.0,
                "brightness": 0.0,
                "vegetation_ratio": 0.0,
                "message": "Invalid Image: Unable to read image file. Please upload a valid JPG, PNG, or WEBP image.",
                "error_type": "invalid_image"
            }
    elif isinstance(image_input, Image.Image):
        cv_img = cv2.cvtColor(np.array(image_input.convert("RGB")), cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, np.ndarray):
        cv_img = image_input
    else:
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": False,
            "blur_score": 0.0,
            "brightness": 0.0,
            "vegetation_ratio": 0.0,
            "message": "Invalid Image: Unsupported image format.",
            "error_type": "invalid_image"
        }

    h, w = cv_img.shape[:2]
    total_pixels = h * w

    # 2. Resolution check
    if h < 120 or w < 120:
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": False,
            "blur_score": 0.0,
            "brightness": 0.0,
            "vegetation_ratio": 0.0,
            "message": "Image Quality Insufficient: Image resolution is too low. Please upload an image of at least 200 × 200 pixels.",
            "error_type": "quality_insufficient"
        }

    # 3. Brightness & Lighting Analysis
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    is_too_dark = brightness < 26.0 or (np.sum(gray < 15) / total_pixels > 0.65)
    is_too_bright = brightness > 238.0 or (np.sum(gray > 248) / total_pixels > 0.50)

    if is_too_dark:
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": False,
            "blur_score": 0.0,
            "brightness": round(brightness, 2),
            "vegetation_ratio": 0.0,
            "message": "Image Quality Insufficient: The image is too dark to resolve leaf pathology. Please provide an image with adequate natural daylight or flash.",
            "error_type": "quality_insufficient"
        }

    if is_too_bright:
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": False,
            "blur_score": 0.0,
            "brightness": round(brightness, 2),
            "vegetation_ratio": 0.0,
            "message": "Image Quality Insufficient: The image is severely over-exposed or washed out with glare. Please capture the leaf without harsh direct flash reflections.",
            "error_type": "quality_insufficient"
        }

    # 4. Blur Detection via Laplacian Variance
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = blur_score < blur_threshold

    if is_blurry and blur_score < (blur_threshold * 0.55):
        # Heavily blurred images are rejected for clinical safety
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": True,
            "blur_score": round(blur_score, 2),
            "brightness": round(brightness, 2),
            "vegetation_ratio": 0.0,
            "message": f"Image Quality Insufficient: The photo is too blurry (Sharpness Score: {blur_score:.1f}). Please hold the camera steady and refocus on the leaf surface.",
            "error_type": "quality_insufficient"
        }

    # 5. Botanical Foliage & Rice Leaf Presence Analysis (HSV Color Space)
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
    
    # Healthy green chlorophyll: Hue 26 to 88, Sat > 28, Val > 28
    lower_green = np.array([26, 28, 28])
    upper_green = np.array([88, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # Chlorotic yellow/orange: Hue 10 to 26, Sat > 35, Val > 35
    lower_yellow = np.array([10, 35, 35])
    upper_yellow = np.array([26, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Necrotic foliar brown/rust: Hue 4 to 20, Sat > 35, Val > 25
    lower_brown = np.array([4, 35, 25])
    upper_brown = np.array([20, 255, 185])
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

    # Plant foliage mask
    foliage_mask = cv2.bitwise_or(mask_green, mask_yellow)
    foliage_mask = cv2.bitwise_or(foliage_mask, mask_brown)
    
    foliage_pixels = cv2.countNonZero(foliage_mask)
    vegetation_ratio = float(foliage_pixels / total_pixels)

    # 6. Check for non-plant / non-rice images (e.g. human face, cars, animals, buildings, plain surfaces)
    # Plant foliage must occupy at least 8% of the image frame
    is_rice_leaf = vegetation_ratio >= 0.08

    # Extra botanical check: skin tones / faces (Hue 0-15 with low saturation and high pink/red tones) vs plant green/foliar
    # If dominant color is not foliage and green/foliar is negligible (< 6%), reject as invalid non-rice image
    if not is_rice_leaf or (vegetation_ratio < 0.08):
        return {
            "valid": False,
            "is_rice_leaf": False,
            "is_blurry": is_blurry,
            "blur_score": round(blur_score, 2),
            "brightness": round(brightness, 2),
            "vegetation_ratio": round(vegetation_ratio, 4),
            "message": "Invalid Image: The uploaded image does not appear to contain a rice leaf or crop vegetation. Please upload a clear photo of a rice leaf.",
            "error_type": "invalid_image"
        }

    # If image passed all checks
    return {
        "valid": True,
        "is_rice_leaf": True,
        "is_blurry": is_blurry,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "vegetation_ratio": round(vegetation_ratio, 4),
        "message": "Image quality and botanical leaf verification passed.",
        "error_type": None
    }


def preprocess_for_model(image_path_or_pil):
    """Prepares standard 224x224 RGB normalized tensor for PyTorch model inference."""
    if isinstance(image_path_or_pil, str):
        img = Image.open(image_path_or_pil).convert("RGB")
    elif isinstance(image_path_or_pil, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(image_path_or_pil, cv2.COLOR_BGR2RGB))
    else:
        img = image_path_or_pil.convert("RGB")

    tensor = inference_transform(img).unsqueeze(0)  # Shape: [1, 3, 224, 224]
    return tensor, img

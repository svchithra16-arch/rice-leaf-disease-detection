"""
AgriVersion - File Upload Security & Image Validation
Validates MIME types, file extensions, size limits, and sanitizes storage paths.
"""

import os
import uuid
import base64
import re
from PIL import Image
from werkzeug.utils import secure_filename
from backend.config import Config


def is_allowed_file(filename: str) -> bool:
    """Checks if file has a permissible image extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage) -> tuple[bool, str, str]:
    """
    Validates and saves an uploaded Werkzeug FileStorage object.
    
    Returns:
        (success: bool, filename: str, error_message: str)
    """
    if not file_storage or file_storage.filename == "":
        return False, "", "No file selected for upload."

    original_name = secure_filename(file_storage.filename)
    if not is_allowed_file(original_name):
        return False, "", f"Unsupported file type. Allowed formats: {', '.join(Config.ALLOWED_EXTENSIONS).upper()}"

    ext = original_name.rsplit(".", 1)[1].lower()
    unique_filename = f"leaf_{uuid.uuid4().hex[:12]}.{ext}"
    save_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

    try:
        file_storage.save(save_path)
        
        # Verify that file is indeed a valid readable image using Pillow
        with Image.open(save_path) as img:
            img.verify()

        return True, unique_filename, ""
    except Exception as e:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        return False, "", f"Invalid or corrupted image file: {str(e)}"


def save_base64_image(base64_data_url: str) -> tuple[bool, str, str]:
    """
    Decodes and saves a base64 DataURL image (e.g. from camera viewfinder snapshot).
    
    Returns:
        (success: bool, filename: str, error_message: str)
    """
    if not base64_data_url:
        return False, "", "Empty camera image data received."

    try:
        # Match data:image/png;base64,... or data:image/jpeg;base64,...
        match = re.match(r"^data:image/(\w+);base64,(.+)$", base64_data_url)
        if match:
            ext = match.group(1).lower()
            if ext == "jpeg":
                ext = "jpg"
            b64_content = match.group(2)
        else:
            ext = "jpg"
            b64_content = base64_data_url

        if ext not in Config.ALLOWED_EXTENSIONS:
            ext = "jpg"

        image_bytes = base64.b64decode(b64_content)
        unique_filename = f"cam_{uuid.uuid4().hex[:12]}.{ext}"
        save_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

        with open(save_path, "wb") as f:
            f.write(image_bytes)

        # Verify image
        with Image.open(save_path) as img:
            img.verify()

        return True, unique_filename, ""
    except Exception as e:
        return False, "", f"Failed to process camera snapshot: {str(e)}"

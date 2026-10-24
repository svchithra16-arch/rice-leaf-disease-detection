"""
AgriVersion - Image Upload Location & Geolocation Resolution Helper
Extracts embedded EXIF GPS tags from leaf images and resolves human-readable paddy belt locations.
"""

import os
import math
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from backend.services.store_service import KNOWN_LOCATIONS


def extract_image_exif_location(image_path):
    """
    Extracts GPS Latitude and Longitude from image EXIF metadata if present.
    Returns (latitude: float, longitude: float) or (None, None).
    """
    try:
        if not image_path or not os.path.exists(image_path):
            return None, None

        img = Image.open(image_path)
        exif = img._getexif()
        if not exif:
            return None, None

        gps_info = {}
        for key, val in exif.items():
            tag = TAGS.get(key)
            if tag == "GPSInfo":
                for gps_key in val:
                    sub_tag = GPSTAGS.get(gps_key, gps_key)
                    gps_info[sub_tag] = val[gps_key]

        if not gps_info:
            return None, None

        def convert_to_degrees(value):
            try:
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)
            except Exception:
                return None

        lat = None
        lng = None

        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            if gps_info["GPSLatitudeRef"] == "S":
                lat = -lat

        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
            lng = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info["GPSLongitudeRef"] == "W":
                lng = -lng

        if lat is not None and lng is not None:
            return round(lat, 5), round(lng, 5)

    except Exception as e:
        print(f"[EXIF Location Extractor]: Error parsing EXIF from {image_path}: {e}")

    return None, None


def resolve_upload_location(lat=None, lng=None, location_hint=None, user=None, field=None, image_path=None):
    """
    Determines latitude, longitude, and human-readable location label for uploaded images.
    Prioritizes:
    1. EXIF GPS embedded in photo metadata
    2. Device Geolocation coordinates passed from browser
    3. Selected Field / Farm location
    4. User profile location
    5. Regional Paddy Belt Default (Mandya, Karnataka)
    """
    source = "Regional Fallback (Mandya Paddy Belt)"
    final_lat = None
    final_lng = None
    location_name = None

    # 1. Try EXIF GPS from image file metadata
    if image_path:
        ex_lat, ex_lng = extract_image_exif_location(image_path)
        if ex_lat is not None and ex_lng is not None:
            final_lat, final_lng = ex_lat, ex_lng
            source = "Image EXIF GPS Metadata"

    # 2. Try Device Geolocation passed from browser
    if final_lat is None and lat is not None and lng is not None:
        try:
            l_lat = float(lat)
            l_lng = float(lng)
            if -90 <= l_lat <= 90 and -180 <= l_lng <= 180 and not (l_lat == 0 and l_lng == 0):
                final_lat = l_lat
                final_lng = l_lng
                source = "Device Live GPS Geolocation"
        except (ValueError, TypeError):
            pass

    # 3. Location Hint / Text provided by client
    if location_hint and str(location_hint).strip():
        location_name = str(location_hint).strip()
        if source.startswith("Regional Fallback"):
            source = "Selected Location"

    # 4. Field / Farm Location
    if final_lat is None and field and field.farm and field.farm.location:
        location_name = field.farm.location
        source = f"Farm Location ({field.farm.name})"

    # 5. User Profile Location
    if final_lat is None and not location_name and user and user.location:
        location_name = user.location
        source = "User Profile Location"

    # Match location_name against KNOWN_LOCATIONS
    if location_name and final_lat is None:
        loc_key = location_name.lower().strip()
        for k, info in KNOWN_LOCATIONS.items():
            if k in loc_key:
                final_lat = info["lat"]
                final_lng = info["lng"]
                location_name = f"{k.title()}, {info['state']}"
                break

    # Reverse geocode lat/lng to real town / district if name missing
    if final_lat is not None and not location_name:
        try:
            from backend.services.store_service import get_live_location_address_details
            info = get_live_location_address_details(final_lat, final_lng)
            if info and info.get("city") and info["city"] != "Local Agricultural Hub":
                location_name = f"{info['city']}, {info.get('state', 'Karnataka')}"
        except Exception:
            pass

    if final_lat is not None and not location_name:
        closest_dist = float("inf")
        best_name = "Bengaluru, Karnataka"
        for k, info in KNOWN_LOCATIONS.items():
            d = math.hypot(final_lat - info["lat"], final_lng - info["lng"])
            if d < closest_dist:
                closest_dist = d
                best_name = f"{k.title()}, {info['state']}"
        location_name = best_name

    # Ultimate fallback
    if final_lat is None or final_lng is None:
        final_lat = 13.2936
        final_lng = 77.5342
        if not location_name:
            location_name = "Doddaballapur, Bengaluru Rural"
        source = "Regional Fallback (Doddaballapur Paddy Belt)"

    return {
        "latitude": final_lat,
        "longitude": final_lng,
        "location_name": location_name,
        "location_source": source
    }

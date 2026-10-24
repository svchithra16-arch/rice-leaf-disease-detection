"""
AgriVersion - Weather & Microclimate Disease Risk API Routes
Supports location name, pincode, and lat/lon for weather queries.
"""

from flask import Blueprint, request, jsonify
from backend.services.weather_service import get_weather_and_disease_risk, geocode_location
from backend.utils.auth_helpers import get_current_user

weather_bp = Blueprint("weather_bp", __name__, url_prefix="/api/weather")


@weather_bp.route("", methods=["GET"])
def get_weather():
    user = get_current_user()

    # Accept explicit lat/lon, location name, or pincode
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    loc_name = request.args.get("location", "").strip()
    pincode = request.args.get("pincode", "").strip()

    # Priority: explicit lat/lon > pincode > location param > user's saved location > default
    resolved_name = loc_name or "Karnataka Paddy Belt"

    if lat is not None and lon is not None:
        # Explicit coordinates provided
        if not loc_name:
            try:
                from backend.services.store_service import get_live_location_address_details
                addr_info = get_live_location_address_details(lat, lon)
                resolved_name = addr_info.get("label") or f"{addr_info.get('city')}, {addr_info.get('state')}"
            except Exception:
                resolved_name = f"Lat {lat:.2f}, Lon {lon:.2f}"
    elif pincode:
        # Geocode from pincode
        geo = geocode_location(pincode)
        if geo:
            lat, lon, resolved_name = geo
        else:
            return jsonify({
                "success": False,
                "message": f"Could not find location for pincode '{pincode}'. Please enter a valid Indian pincode or city name."
            }), 404
    elif loc_name:
        # Geocode from location name
        geo = geocode_location(loc_name)
        if geo:
            lat, lon, resolved_name = geo
        else:
            # Fall back to default coordinates but keep the name
            lat, lon = 13.2936, 77.5342
            resolved_name = loc_name
    else:
        # Use user's saved location if available
        if user and user.location:
            geo = geocode_location(user.location)
            if geo:
                lat, lon, resolved_name = geo
            else:
                lat, lon = 13.2936, 77.5342
                resolved_name = user.location
        else:
            lat, lon = 12.9753, 77.5910
            resolved_name = "Bengaluru, Karnataka"

    data = get_weather_and_disease_risk(latitude=lat, longitude=lon, location_name=resolved_name)
    return jsonify({"success": True, "weather": data})


@weather_bp.route("/geocode", methods=["GET"])
def geocode():
    """Utility endpoint to geocode a location name or pincode to lat/lon."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Please provide a location or pincode."}), 400

    result = geocode_location(query)
    if result:
        lat, lon, name = result
        return jsonify({
            "success": True,
            "latitude": lat,
            "longitude": lon,
            "resolved_name": name
        })
    else:
        return jsonify({
            "success": False,
            "message": f"Could not resolve '{query}' to a location. Try a city name or Indian pincode."
        }), 404

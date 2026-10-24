"""
AgriVersion - Real-Time Mobile GPS Location Sharing API Routes
Enables connecting a mobile phone's GPS to supply real-time coordinates
to the AgriVersion web application running on a laptop.
"""

import time
import uuid
import socket
from flask import Blueprint, request, jsonify
from backend.services.store_service import get_live_location_address_details

location_bp = Blueprint("location_bp", __name__, url_prefix="/api/location")

# In-memory thread-safe storage for active mobile GPS sessions
# session_id -> session dict
GPS_SESSIONS = {}

# Expiration constants
SESSION_EXPIRY_SECONDS = 3600 * 4  # 4 hours
DISCONNECT_TIMEOUT_SECONDS = 15.0  # If no update received in 15 seconds, mark disconnected


def get_lan_ip():
    """Determines the primary LAN IPv4 address of this machine on the local Wi-Fi/Ethernet network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable or send actual packets
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def cleanup_stale_sessions():
    """Prunes expired sessions to prevent memory accumulation."""
    now = time.time()
    stale_keys = [
        sid for sid, s in GPS_SESSIONS.items()
        if now - s.get("created_at", now) > SESSION_EXPIRY_SECONDS
    ]
    for sid in stale_keys:
        GPS_SESSIONS.pop(sid, None)


@location_bp.route("/network-info", methods=["GET"])
def get_network_info():
    """Returns detected local LAN IP and connection URLs."""
    lan_ip = get_lan_ip()
    host_header = request.host
    port = host_header.split(":")[-1] if ":" in host_header else "5000"
    
    return jsonify({
        "success": True,
        "lan_ip": lan_ip,
        "port": port,
        "base_url": f"http://{lan_ip}:{port}"
    })


@location_bp.route("/session/create", methods=["GET", "POST"])
def create_session():
    """
    Creates or initializes a unique mobile GPS session.
    Generates a shareable URL and connection data for QR code generation.
    """
    cleanup_stale_sessions()
    
    req_data = request.get_json(silent=True) or {}
    custom_sid = req_data.get("session_id") or request.args.get("session_id")
    
    session_id = custom_sid if custom_sid else f"gps-{uuid.uuid4().hex[:8]}"
    now = time.time()
    
    lan_ip = get_lan_ip()
    host_header = request.host
    port = host_header.split(":")[-1] if ":" in host_header else "5000"
    mobile_url = f"http://{lan_ip}:{port}/mobile-gps.html?session={session_id}"
    
    if session_id not in GPS_SESSIONS:
        GPS_SESSIONS[session_id] = {
            "session_id": session_id,
            "created_at": now,
            "last_seen": now,
            "status": "waiting",  # "waiting", "connected", "disconnected", "denied"
            "lat": None,
            "lng": None,
            "accuracy": None,
            "altitude": None,
            "heading": None,
            "speed": None,
            "label": None,
            "city": None,
            "district": None,
            "state": None,
            "pincode": None,
            "device_info": None,
            "updates_count": 0,
            "error_message": None
        }
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "lan_ip": lan_ip,
        "port": port,
        "mobile_url": mobile_url,
        "status": GPS_SESSIONS[session_id]["status"]
    })


@location_bp.route("/session/update", methods=["POST"])
def update_mobile_location():
    """
    Endpoint called by the mobile browser to stream real-time GPS coordinates.
    """
    data = request.get_json() or {}
    session_id = data.get("session_id")
    
    if not session_id:
        return jsonify({"success": False, "message": "Missing session_id"}), 400
    
    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid latitude or longitude"}), 400
    
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return jsonify({"success": False, "message": "Coordinates out of bounds"}), 400
    
    now = time.time()
    
    if session_id not in GPS_SESSIONS:
        GPS_SESSIONS[session_id] = {
            "session_id": session_id,
            "created_at": now,
            "updates_count": 0
        }
    
    sess = GPS_SESSIONS[session_id]
    sess["last_seen"] = now
    sess["status"] = "connected"
    sess["lat"] = lat
    sess["lng"] = lng
    sess["accuracy"] = data.get("accuracy")
    sess["altitude"] = data.get("altitude")
    sess["heading"] = data.get("heading")
    sess["speed"] = data.get("speed")
    sess["device_info"] = data.get("device_info", request.headers.get("User-Agent", "Mobile Browser"))
    sess["updates_count"] = sess.get("updates_count", 0) + 1
    sess["error_message"] = None
    
    # Perform reverse geocoding if new or coordinates shifted noticeably (> 100m)
    prev_lat = sess.get("geocoded_lat")
    prev_lng = sess.get("geocoded_lng")
    needs_geocode = (
        sess.get("label") is None or
        prev_lat is None or
        abs(lat - prev_lat) > 0.001 or
        abs(lng - prev_lng) > 0.001
    )
    
    if needs_geocode:
        try:
            addr = get_live_location_address_details(lat, lng)
            sess["label"] = addr.get("label", f"{lat:.4f}° N, {lng:.4f}° E")
            sess["city"] = addr.get("city", "Current Area")
            sess["district"] = addr.get("district", "Current Area")
            sess["state"] = addr.get("state", "India")
            sess["pincode"] = addr.get("pincode", "")
            sess["geocoded_lat"] = lat
            sess["geocoded_lng"] = lng
        except Exception:
            sess["label"] = f"{lat:.4f}° N, {lng:.4f}° E"
            sess["city"] = "Live Mobile GPS"
            sess["district"] = "Live Mobile GPS"
            sess["state"] = ""
    
    return jsonify({
        "success": True,
        "status": "connected",
        "updates_count": sess["updates_count"]
    })


@location_bp.route("/session/status-update", methods=["POST"])
def update_session_status():
    """
    Called by mobile browser when location permissions are denied or an error occurs.
    """
    data = request.get_json() or {}
    session_id = data.get("session_id")
    status = data.get("status", "error")
    msg = data.get("message", "")
    
    if not session_id:
        return jsonify({"success": False, "message": "Missing session_id"}), 400
    
    if session_id not in GPS_SESSIONS:
        GPS_SESSIONS[session_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "updates_count": 0
        }
    
    sess = GPS_SESSIONS[session_id]
    sess["status"] = status
    sess["error_message"] = msg
    sess["last_seen"] = time.time()
    
    return jsonify({"success": True, "status": sess["status"]})


@location_bp.route("/session/<session_id>/status", methods=["GET"])
def get_session_status(session_id):
    """
    Polled by laptop browser to check mobile connection status and fetch coordinates.
    """
    if session_id not in GPS_SESSIONS:
        now = time.time()
        GPS_SESSIONS[session_id] = {
            "session_id": session_id,
            "created_at": now,
            "last_seen": now,
            "status": "waiting",
            "lat": None,
            "lng": None,
            "accuracy": None,
            "altitude": None,
            "heading": None,
            "speed": None,
            "label": None,
            "city": None,
            "district": None,
            "state": None,
            "pincode": None,
            "device_info": None,
            "updates_count": 0,
            "error_message": None
        }
    
    sess = GPS_SESSIONS[session_id]
    now = time.time()
    last_seen = sess.get("last_seen", now)
    seconds_ago = now - last_seen
    
    # If the mobile hasn't transmitted coordinates within DISCONNECT_TIMEOUT_SECONDS, mark disconnected
    current_status = sess.get("status", "waiting")
    if current_status == "connected" and seconds_ago > DISCONNECT_TIMEOUT_SECONDS:
        current_status = "disconnected"
        sess["status"] = "disconnected"
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "status": current_status,
        "lat": sess.get("lat"),
        "lng": sess.get("lng"),
        "accuracy": sess.get("accuracy"),
        "altitude": sess.get("altitude"),
        "heading": sess.get("heading"),
        "speed": sess.get("speed"),
        "label": sess.get("label"),
        "city": sess.get("city"),
        "district": sess.get("district"),
        "state": sess.get("state"),
        "pincode": sess.get("pincode"),
        "updates_count": sess.get("updates_count", 0),
        "last_seen_seconds_ago": round(seconds_ago, 1),
        "device_info": sess.get("device_info"),
        "error_message": sess.get("error_message")
    })


@location_bp.route("/session/<session_id>/disconnect", methods=["POST"])
def disconnect_session(session_id):
    """Marks session as disconnected and resets active coordinates."""
    if session_id in GPS_SESSIONS:
        GPS_SESSIONS[session_id]["status"] = "disconnected"
        GPS_SESSIONS[session_id]["last_seen"] = time.time()
    return jsonify({"success": True, "status": "disconnected"})

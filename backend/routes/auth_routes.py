"""
AgriVersion - Authentication & User Management API Routes
"""

from flask import Blueprint, request, jsonify, session
from backend.database.db import db
from backend.database.models import User, Farm, Field
from backend.utils.auth_helpers import (
    hash_password,
    verify_password,
    evaluate_password_strength,
    get_current_user,
    login_required
)

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    location = data.get("location", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    preferred_lang = data.get("preferred_lang", "en")

    # Validations
    if not full_name or not username or not email or not password:
        return jsonify({"success": False, "message": "Please fill in all required fields."}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400

    strength = evaluate_password_strength(password)
    if not strength["is_valid"]:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

    # Duplicate checks
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists. Please choose another."}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email address is already registered."}), 409

    # Create new User
    new_user = User(
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        location=location,
        password_hash=hash_password(password),
        role="user",
        preferred_lang=preferred_lang
    )
    db.session.add(new_user)
    db.session.commit()

    # Automatically initialize a default Farm and Field for the user
    default_farm = Farm(
        user_id=new_user.id,
        name=f"{full_name}'s Farm",
        location=location or "Karnataka Paddy Belt",
        total_area=2.5,
        soil_type="Clayey Loam"
    )
    db.session.add(default_farm)
    db.session.commit()

    default_field = Field(
        farm_id=default_farm.id,
        name="Field A (Main Plot)",
        crop_variety="IR64 / Samba Mahsuri",
        sowing_date="2026-06-15",
        notes="High-yield irrigated paddy plot"
    )
    db.session.add(default_field)
    db.session.commit()

    # Set session
    session["user_id"] = new_user.id
    session["username"] = new_user.username
    session["role"] = new_user.role

    return jsonify({
        "success": True,
        "message": "Registration successful! Welcome to AgriVersion.",
        "user": new_user.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip().lower()  # username or email
    password = data.get("password", "")
    remember_me = bool(data.get("remember_me", False))

    if not identifier or not password:
        return jsonify({"success": False, "message": "Please provide username/email and password."}), 400

    # Lookup user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    if not user.is_active:
        return jsonify({"success": False, "message": "Your account has been deactivated. Please contact administrator."}), 403

    # Set session
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role
    session.permanent = remember_me

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user.full_name}!",
        "user": user.to_dict()
    })


@auth_bp.route("/demo-login", methods=["POST"])
def demo_login():
    """Quick demo authentication endpoint for viva / evaluations."""
    data = request.get_json() or {}
    role = data.get("role", "admin").lower()

    user = User.query.filter_by(role=role).first()
    if not user:
        # Fallback to any user
        user = User.query.first()

    if not user:
        return jsonify({"success": False, "message": "No demo users initialized."}), 404

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "success": True,
        "message": f"Logged in as Demo {user.role.title()}: {user.full_name}",
        "user": user.to_dict()
    })


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "You have been logged out successfully."})


@auth_bp.route("/me", methods=["GET"])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False, "user": None})
    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    })


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}

    if "full_name" in data and data["full_name"].strip():
        user.full_name = data["full_name"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "location" in data:
        user.location = data["location"].strip()
    if "preferred_lang" in data:
        user.preferred_lang = data["preferred_lang"]
    if "voice_pref" in data:
        user.voice_pref = data["voice_pref"]

    db.session.commit()
    return jsonify({"success": True, "message": "Profile updated successfully.", "user": user.to_dict()})


@auth_bp.route("/password", methods=["PUT"])
@login_required
def change_password():
    user = get_current_user()
    data = request.get_json() or {}
    old_pwd = data.get("old_password", "")
    new_pwd = data.get("new_password", "")
    confirm_pwd = data.get("confirm_password", "")

    if not verify_password(old_pwd, user.password_hash):
        return jsonify({"success": False, "message": "Incorrect existing password."}), 400

    if new_pwd != confirm_pwd:
        return jsonify({"success": False, "message": "New passwords do not match."}), 400

    if len(new_pwd) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters long."}), 400

    user.password_hash = hash_password(new_pwd)
    db.session.commit()
    return jsonify({"success": True, "message": "Password changed successfully."})

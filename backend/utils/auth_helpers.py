"""
AgriVersion - Authentication & Authorization Helpers
Provides password hashing, strength scoring, session management, and RBAC route decorators.
"""

from functools import wraps
import re
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import db
from backend.database.models import User


def hash_password(password: str) -> str:
    """Generates secure salted hash for user password."""
    return generate_password_hash(password, method="scrypt")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifies cleartext password against stored hash."""
    return check_password_hash(password_hash, password)


def evaluate_password_strength(password: str) -> dict:
    """
    Evaluates password complexity and returns strength level.
    Score: 0 to 4 (Weak, Medium, Strong)
    """
    if not password:
        return {"score": 0, "level": "weak", "message": "Password cannot be empty"}

    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters required.")

    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Include at least one uppercase letter.")

    if re.search(r"[0-9]", password):
        score += 1
    else:
        feedback.append("Include at least one numeric digit.")

    if re.search(r"[@$!%*?&#^_\-+=~]", password):
        score += 1
    else:
        feedback.append("Include at least one special character.")

    if score <= 1:
        level = "weak"
    elif score in (2, 3):
        level = "medium"
    else:
        level = "strong"

    return {
        "score": score,
        "level": level,
        "is_valid": len(password) >= 6,
        "feedback": feedback
    }


def get_current_user():
    """Retrieves currently logged-in user from session, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    """Decorator ensuring request is made by authenticated user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": "Please sign in to access this feature.",
                "redirect": "/login.html"
            }), 401
        
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            session.clear()
            return jsonify({
                "success": False,
                "error": "Session expired",
                "message": "User session is invalid or disabled.",
                "redirect": "/login.html"
            }), 401

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator ensuring request is made by user with 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": "Please sign in as Administrator.",
                "redirect": "/login.html"
            }), 401
        
        user = db.session.get(User, user_id)
        if not user or user.role != "admin":
            return jsonify({
                "success": False,
                "error": "Access denied",
                "message": "Administrator privileges required to access this endpoint."
            }), 403

        return f(*args, **kwargs)
    return decorated_function

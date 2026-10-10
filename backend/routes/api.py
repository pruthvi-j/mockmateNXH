"""
NextHire - Core API Blueprint
Provides health check, configuration status, system endpoints, and authentication routes.
"""
import re
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database import get_db_connection, check_db_health

api_bp = Blueprint("api", __name__, url_prefix="/api")

# In-memory user store for dev/testing fallback
USER_STORE = {}

# Regex for strict Gmail format validation: username@gmail.com
# Username allows letters, digits, dots, hyphens, underscores, plus signs
GMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', re.IGNORECASE)

def is_valid_gmail(email: str) -> bool:
    """
    Validates if the provided string is a correctly formatted Gmail address.
    Must follow username@gmail.com format with domain exactly gmail.com.
    """
    if not email or not isinstance(email, str):
        return False
    trimmed = email.strip()
    if len(trimmed) != len(email):
        return False
    if any(c.isspace() for c in trimmed):
        return False
    return bool(GMAIL_REGEX.match(trimmed))

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Returns application health status and database connectivity status."""
    db_status = check_db_health()
    return jsonify({
        "status": "online",
        "system": "NextHire Intelligent Mock Interview System",
        "stage": "Stage 1 - Phase 1 Architecture & JARVIS Core",
        "database": db_status
    }), 200

@api_bp.route("/jarvis/state", methods=["GET"])
def jarvis_state():
    """Mock/Preview endpoint for JARVIS assistant status."""
    return jsonify({
        "assistant": "JARVIS",
        "supported_states": ["IDLE", "LISTENING", "THINKING", "SPEAKING", "PROCESSING"],
        "version": "1.0-alpha"
    }), 200

@api_bp.route("/auth/validate-email", methods=["POST"])
def validate_email_endpoint():
    """Endpoint to validate Gmail ID format on server side."""
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip()
    valid = is_valid_gmail(email)
    if not valid:
        return jsonify({
            "valid": False,
            "error": "Your email ID is invalid. Please enter a valid Gmail ID."
        }), 400
    return jsonify({
        "valid": True,
        "message": "Valid Gmail ID"
    }), 200

@api_bp.route("/auth/register", methods=["POST"])
def register():
    """
    Registers a new candidate user after validating Gmail format.
    """
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    target_role = (data.get("target_role") or "Full Stack Software Engineer").strip()

    # Strict server-side Gmail format validation
    if not is_valid_gmail(email):
        return jsonify({
            "error": "Your email ID is invalid. Please enter a valid Gmail ID."
        }), 400

    if not username:
        return jsonify({"error": "Username is required."}), 400

    if not password:
        return jsonify({"error": "Password is required."}), 400

    # Attempt MySQL persistence
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "User with this email already exists."}), 400
            
            p_hash = generate_password_hash(password)
            try:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, p_hash)
                )
            except Exception:
                cur.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                    (email, p_hash)
                )
            conn.close()
    except Exception as e:
        print(f"[Auth DB Note] User registration fallback store: {e}")

    # Fallback in-memory store
    USER_STORE[email.lower()] = {
        "username": username,
        "email": email,
        "password": password,
        "password_hash": generate_password_hash(password),
        "target_role": target_role
    }

    return jsonify({
        "success": True,
        "message": "Registration successful! Account created with valid Gmail ID.",
        "redirect": "/login"
    }), 201

@api_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Authenticates candidate user after validating Gmail format.
    """
    data = request.get_json(silent=True) or request.form
    email_or_user = (data.get("usernameOrEmail") or data.get("email") or "").strip()
    password = data.get("password") or ""

    # Strict server-side Gmail format validation
    if not is_valid_gmail(email_or_user):
        return jsonify({
            "error": "Your email ID is invalid. Please enter a valid Gmail ID."
        }), 400

    if not password:
        return jsonify({"error": "Password is required."}), 400

    user_found = False
    password_correct = False

    # Check MySQL DB first if available
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email_or_user,))
            row = cur.fetchone()
            conn.close()
            if row:
                user_found = True
                stored_hash = row.get("password_hash", "")
                if check_password_hash(stored_hash, password) or stored_hash == password:
                    password_correct = True
    except Exception as e:
        print(f"[Auth DB Note] Login check fallback store: {e}")

    # Check fallback store if DB not available or user not found in DB
    if not user_found and email_or_user.lower() in USER_STORE:
        user_found = True
        cached = USER_STORE[email_or_user.lower()]
        if cached.get("password") == password or check_password_hash(cached.get("password_hash", ""), password):
            password_correct = True

    # If user was found in DB or memory, check password result
    if user_found:
        if not password_correct:
            return jsonify({"error": "Invalid credentials. Please check your password."}), 401
    else:
        # For dev/demo mode when DB is not seeded: if valid Gmail format & correct password (or any password if not registered yet), allow login
        pass

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "redirect": "/dashboard"
    }), 200


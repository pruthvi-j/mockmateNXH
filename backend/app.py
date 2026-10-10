"""
NextHire - Main Flask Application
Serves REST API endpoints and frontend interface pages.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.routes.api import api_bp
from backend.routes.interview import interview_bp

def create_app():
    """Application factory for NextHire."""
    Config.init_app()
    app = Flask(
        __name__,
        static_folder=None
    )
    app.config.from_object(Config)

    # Enable CORS for flexible integration
    CORS(app)

    # Register API blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(interview_bp)

    # Static and Page Serving Routes
    @app.route("/")
    def index():
        return send_from_directory(Config.FRONTEND_DIR, "index.html")

    @app.route("/login")
    def login():
        return send_from_directory(Config.FRONTEND_DIR, "login.html")

    @app.route("/register")
    def register():
        return send_from_directory(Config.FRONTEND_DIR, "register.html")

    @app.route("/dashboard")
    def dashboard():
        return send_from_directory(Config.FRONTEND_DIR, "dashboard.html")

    @app.route("/interview")
    def interview():
        return send_from_directory(Config.FRONTEND_DIR, "interview.html")

    @app.route("/feedback")
    def feedback():
        return send_from_directory(Config.FRONTEND_DIR, "feedback.html")

    @app.route("/history")
    def history():
        return send_from_directory(Config.FRONTEND_DIR, "history.html")

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(Config.FRONTEND_DIR / "css", filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(Config.FRONTEND_DIR / "js", filename)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource could not be found."
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

    return app

if __name__ == "__main__":
    app = create_app()
    print(f"[*] NextHire Server starting on http://127.0.0.1:{Config.PORT}")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

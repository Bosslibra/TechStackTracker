from flask import Blueprint, jsonify

health_check_bp = Blueprint("health_check", __name__)

# Health check route
@health_check_bp.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint to verify that the server is running."""


    # Here I should app services health checks, as db and similar
    # Overkill for now

    return jsonify({"status": "ok"}), 200

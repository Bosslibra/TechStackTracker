import secrets
import time
from flask import Blueprint, jsonify, request

from .auth import (
    clear_failed_logins,
    csrf_protect,
    get_csrf_token,
    is_authenticated,
    is_rate_limited,
    login_required,
    login_user,
    logout_user,
    record_failed_login,
    verify_credentials,
)


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Authenticate a user with username and password.

    Request Body (JSON):
        - username (str): Login username.
        - password (str): Login password.

    Behavior:
        - Enforces rate limiting on repeated failed attempts.
        - Records failed logins for invalid credentials.
        - Small delay on failed attempts to mitigate brute-force attacks.
        - On success, creates an authenticated session and returns a CSRF token.

    Returns:
        200 OK with JSON:
            - authenticated (bool): Always True on success.
            - csrfToken (str): Token required for CSRF-protected endpoints.
        401 Unauthorized with JSON:
            - error (str): Invalid credentials.
        429 Too Many Requests with JSON:
            - error (str): Too many failed attempts.
    """
    if is_rate_limited():
        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429

    payload = request.get_json(silent=True) or {}
    username = str(payload.get('username', '')).strip()
    password = str(payload.get('password', ''))

    if not verify_credentials(username, password):
        record_failed_login()
        time.sleep(0.2 + secrets.randbelow(300) / 1000)  # Basic protection against brute-force attacks
        return jsonify({'error': 'Invalid credentials'}), 401

    clear_failed_logins()
    login_user()
    return jsonify({'authenticated': True, 'csrfToken': get_csrf_token()})


@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
@csrf_protect
def logout():
    """
    Log out the currently authenticated user.

    Security:
        - Requires an authenticated session.
        - Requires a valid CSRF token.

    Returns:
        204 No Content on successful logout.
    """
    logout_user()
    return '', 204


@auth_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    """
        Check whether the current session is authenticated.

        If authenticated, returns a fresh CSRF token to be used for protected write requests.

        Returns:
            200 OK with JSON:
                - authenticated (bool): True when session is logged in.
                - csrfToken (str, optional): Present only when authenticated.
    """
    if is_authenticated():
        return jsonify({'authenticated': True, 'csrfToken': get_csrf_token()})
    return jsonify({'authenticated': False})
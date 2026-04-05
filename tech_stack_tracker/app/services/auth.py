import hmac
import os
import secrets
import time
from functools import lru_cache
from functools import wraps

from flask import jsonify, request, session
from werkzeug.security import check_password_hash
from config import Config

MAX_ATTEMPTS = Config.MAX_LOGIN_ATTEMPTS
WINDOW_SECONDS = Config.LOGIN_ATTEMPT_WINDOW_SECONDS
LOCK_SECONDS = Config.LOGIN_LOCKOUT_SECONDS

_FAILED_ATTEMPTS = {} # TODO: In-memory store for failed login attempts. Needs to be replaced with a persistent store for production.
_DUMMY_HASH = 'scrypt:32768:8:1$dummy$57ea7677ea2ed85df8e4caec2864fd6f73f4af5ca78f2d3f0bf93013f4f58cfdf59f2704ec6ef42e6db77f5d50f8fcb4f68543c18f20ce44392f4d8f07f80f43'


def _get_client_ip():
    """
    Extract the client's IP address from the request.

    Takes into account proxied requests by checking the X-Forwarded-For header
    before falling back to the direct remote address.
    
    Returns:
        str: Client IP address, or 'unknown' if unavailable.
    """
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _prune_attempts(ip, now):
    """
    Clean up old failed login attempts outside the tracking window.

    Removes attempt timestamps older than WINDOW_SECONDS to keep the tracking
    bucket current.
    
    Args:
        ip (str): Client IP address.
        now (float): Current Unix timestamp.
    
    Returns:
        dict: Bucket containing pruned 'attempts' list and 'blocked_until' timestamp.
    """
    bucket = _FAILED_ATTEMPTS.get(ip)
    if not bucket:
        return {'attempts': [], 'blocked_until': 0}

    attempts = [t for t in bucket['attempts'] if now - t <= WINDOW_SECONDS]
    bucket['attempts'] = attempts
    return bucket


def is_rate_limited():
    """
    Check whether a client is currently rate-limited.

    Returns True if the client has reached MAX_ATTEMPTS failed logins
    within WINDOW_SECONDS and is still within the LOCK_SECONDS lockout period.
    
    Returns:
        bool: True if rate-limited, False otherwise.
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = _prune_attempts(ip, now)

    return now < bucket.get('blocked_until', 0)


def record_failed_login():
    """
    Record a failed login attempt for the current client.
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = _FAILED_ATTEMPTS.setdefault(ip, {'attempts': [], 'blocked_until': 0})
    bucket = _prune_attempts(ip, now)

    bucket['attempts'].append(now)
    if len(bucket['attempts']) >= MAX_ATTEMPTS:
        bucket['blocked_until'] = now + LOCK_SECONDS


def clear_failed_logins():
    """
    Clear all failed login records for the current client.

    Called after a successful login to reset the rate limit counter.
    """
    ip = _get_client_ip()
    _FAILED_ATTEMPTS.pop(ip, None)


def _admin_username():
    """
    Retrieve the admin username from environment variables.
    
    Defaults to 'admin' if TRACK_ADMIN_USERNAME is not set.
    
    Returns:
        str: Admin username.
    """
    return os.getenv('TRACK_ADMIN_USERNAME', 'admin')


@lru_cache(maxsize=1)
def _admin_hash():
    """
    Retrieve the admin password hash from environment variables.
    
    Priority:
        1. TRACK_ADMIN_PASSWORD_HASH (recommended, pre-hashed)
        2. TRACK_ADMIN_PASSWORD (hashed on first call)
    
    Result is cached after first retrieval.
    
    Returns:
        str: Werkzeug scrypt password hash.
    
    Raises:
        RuntimeError: If neither environment variable is set.
    """
    hash_from_env = os.getenv('TRACK_ADMIN_PASSWORD_HASH')
    if hash_from_env:
        return hash_from_env

    plain = os.getenv('TRACK_ADMIN_PASSWORD')
    if plain:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(plain)

    raise RuntimeError(
        'Missing credentials. Set TRACK_ADMIN_PASSWORD_HASH (recommended) '
        'or TRACK_ADMIN_PASSWORD environment variable.'
    )


def validate_auth_config():
    """
    Validate that required authentication configuration is present.
    
    Triggers initialization of admin username and password hash.
    Called at application startup to fail fast if credentials are missing.
    
    Raises:
        RuntimeError: If credentials are not configured.
    """
    _ = _admin_username()
    _ = _admin_hash()


def verify_credentials(username, password):
    """
    Verify that provided credentials match the admin account.
    
    Uses constant-time comparison (hmac.compare_digest) for username
    and werkzeug's check_password_hash for password to prevent timing attacks.
    Always hashes the password even on username mismatch (via dummy hash).
    
    Args:
        username (str): Submitted username.
        password (str): Submitted password (plaintext).
    
    Returns:
        bool: True if both username and password are correct.
    """
    admin_user = _admin_username()
    admin_hash = _admin_hash()

    user_ok = hmac.compare_digest(username or '', admin_user)
    pass_ok = check_password_hash(admin_hash, password or '') if user_ok else check_password_hash(_DUMMY_HASH, password or '')
    return user_ok and pass_ok


def login_user():
    """
    Create an authenticated session for the user.
    
    Initializes session with authenticated flag, username, and CSRF token.
    Marks the session as permanent (persists across browser restarts).
    """
    session.clear()
    session['authenticated'] = True
    session['username'] = _admin_username()
    session['csrf_token'] = secrets.token_urlsafe(32)
    session.permanent = True


def logout_user():
    """
    Destroy the current session.
    
    Clears all session data including authentication status and CSRF token.
    """
    session.clear()


def is_authenticated():
    """
    Check if the current session is authenticated.
    
    Returns:
        bool: True if session contains authenticated flag, False otherwise.
    """
    return bool(session.get('authenticated'))


def get_csrf_token():
    """
    Retrieve the CSRF token from the current session.
    
    Returns:
        str: Session CSRF token, or empty string if not present.
    """
    return session.get('csrf_token', '')


def login_required(view_func):
    """
    Decorator to enforce authenticated session on an endpoint.
    
    Returns 401 Unauthorized if the user is not authenticated.
    
    Args:
        view_func: Flask route handler to protect.
    
    Returns:
        function: Wrapper that checks authentication before executing view_func.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        return view_func(*args, **kwargs)

    return wrapper


def csrf_protect(view_func):
    """
    Decorator to enforce CSRF token validation on an endpoint.
    
    Compares the X-CSRF-Token request header against the session token
    using constant-time comparison to prevent token forgery.
    
    Returns 403 Forbidden if the token is missing or invalid.
    
    Args:
        view_func: Flask route handler to protect.
    
    Returns:
        function: Wrapper that validates CSRF token before executing view_func.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        csrf_header = request.headers.get('X-CSRF-Token', '')
        csrf_session = get_csrf_token()

        if not csrf_session or not hmac.compare_digest(csrf_header, csrf_session):
            return jsonify({'error': 'Invalid CSRF token'}), 403

        return view_func(*args, **kwargs)

    return wrapper

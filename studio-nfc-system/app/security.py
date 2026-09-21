from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import timedelta
from typing import Optional

# Databases created before login sessions moved into SQLite were seeded with
# this password. init_db warns when an admin is still using it.
LEGACY_DEFAULT_PASSWORD = "change-me-now"


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, encoded: Optional[str]) -> bool:
    if not encoded:
        return False
    try:
        _, salt, digest = encoded.split("$", 2)
        return hmac.compare_digest(hash_password(password, salt), encoded)
    except ValueError:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """Sessions are stored by digest so a database copy cannot be replayed."""
    return hashlib.sha256(token.encode()).hexdigest()


def session_lifetime() -> timedelta:
    try:
        hours = int(os.getenv("SESSION_HOURS", "12"))
    except ValueError:
        hours = 12
    return timedelta(hours=max(1, hours))


def default_admin_password() -> tuple[str, bool]:
    """Return (password, generated). A generated one is printed once at startup."""
    configured = os.getenv("ADMIN_PASSWORD")
    if configured:
        return configured, False
    return secrets.token_urlsafe(12), True

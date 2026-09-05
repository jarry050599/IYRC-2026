from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Optional

TOKENS: dict[str, int] = {}


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


def new_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    TOKENS[token] = user_id
    return token


def default_admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "change-me-now")

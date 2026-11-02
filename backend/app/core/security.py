from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHashError,
)
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.config import settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2id.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return password_hasher.verify(
            hashed_password,
            plain_password,
        )

    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(hashed_password: str) -> bool:
    return password_hasher.check_needs_rehash(hashed_password)

def create_access_token(user_id: str, role: str) -> str:
    """
    Create a signed JWT access token.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "jti": str(uuid4()),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


def verify_access_token(token: str) -> dict | None:
    """
    Verify a JWT access token and return its payload.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "jti", "type"]},
        )

        if payload.get("type") != "access":
            return None

        return payload

    except jwt.InvalidTokenError:
        return None
    
# ==========================================
# Refresh Token
# ==========================================

def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Generate a SHA-256 hash of the refresh token.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
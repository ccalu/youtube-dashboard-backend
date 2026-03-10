"""
JWT Authentication module for YouTube Dashboard.
Handles token creation/validation, password hashing, and FastAPI dependencies.
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("JWT_SECRET_KEY not set — using random key (tokens won't survive restart)")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30


# ---------- Password hashing ----------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------- JWT tokens ----------

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# ---------- FastAPI dependencies ----------

def get_current_user(request: Request) -> dict:
    """Extract and validate JWT from Authorization header. Raises 401 if invalid."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Token invalido")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado ou invalido")


# ---------- User authentication ----------

def authenticate_user(supabase_client, username: str, password: str):
    """Query auth_users by username (case-insensitive) and verify password.
    Returns user dict or None.
    """
    try:
        result = supabase_client.table("auth_users").select("*").eq(
            "username_lower", username.lower()
        ).eq("is_active", True).execute()

        if not result.data:
            return None

        user = result.data[0]
        if not verify_password(password, user["password_hash"]):
            return None

        return user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None

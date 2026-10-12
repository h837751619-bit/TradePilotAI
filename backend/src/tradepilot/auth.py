from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, iterations: int = 210_000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), _decode(salt), int(iterations))
        return hmac.compare_digest(_encode(digest), expected)
    except (TypeError, ValueError):
        return False


def issue_token(subject: str, secret: str, ttl_seconds: int, role: str = "approver") -> str:
    header = _encode(b'{"alg":"HS256","typ":"TPA"}')
    payload = _encode(json.dumps({"sub": subject, "role": role, "exp": int(time.time()) + ttl_seconds}, separators=(",", ":")).encode())
    unsigned = f"{header}.{payload}".encode()
    signature = _encode(hmac.new(secret.encode(), unsigned, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def verify_token_claims(token: str, secret: str) -> dict | None:
    try:
        header, payload, signature = token.split(".")
        unsigned = f"{header}.{payload}".encode()
        expected = _encode(hmac.new(secret.encode(), unsigned, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(_decode(payload))
        if int(claims["exp"]) <= int(time.time()):
            return None
        subject = str(claims["sub"]).strip()
        role = str(claims.get("role", "")).strip()
        return {"sub": subject, "role": role} if subject else None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def verify_token(token: str, secret: str) -> str | None:
    claims = verify_token_claims(token, secret)
    return claims["sub"] if claims else None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def seed_auth_user(session: Session, username: str, password_hash: str, role: str) -> None:
    if not username or not password_hash:
        return
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        session.add(User(username=username, password_hash=password_hash, role=role, is_active=True))
        session.commit()

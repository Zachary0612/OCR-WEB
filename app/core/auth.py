import base64
import hashlib
import hmac
import json
import time
from secrets import compare_digest
from typing import Any

from fastapi import HTTPException, Request, Response, status

from config import (
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_SECURE,
    AUTH_ENABLED,
    AUTH_PASSWORD,
    AUTH_SECRET,
    AUTH_SESSION_TTL,
    AUTH_USERNAME,
)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def validate_credentials(username: str, password: str) -> bool:
    if not AUTH_ENABLED:
        return True
    return compare_digest(username, AUTH_USERNAME) and compare_digest(password, AUTH_PASSWORD)


def create_session_token(username: str, ttl: int = AUTH_SESSION_TTL) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + ttl,
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_encoded = _b64encode(payload_raw)
    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_encoded}.{signature}"


def verify_session_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        payload_encoded, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not compare_digest(signature, expected):
        return None

    try:
        payload = json.loads(_b64decode(payload_encoded).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


def _extract_basic_credentials(request: Request) -> tuple[str, str] | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return None
    return username, password


def get_authenticated_user(request: Request) -> dict[str, str] | None:
    if not AUTH_ENABLED:
        return {"username": AUTH_USERNAME}

    payload = verify_session_token(request.cookies.get(AUTH_COOKIE_NAME))
    if payload:
        return {"username": str(payload["sub"])}

    basic = _extract_basic_credentials(request)
    if basic and validate_credentials(*basic):
        return {"username": basic[0]}
    return None


def require_auth(request: Request) -> dict[str, str]:
    user = get_authenticated_user(request)
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


def set_auth_cookie(response: Response, username: str) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME,
        create_session_token(username),
        max_age=AUTH_SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=AUTH_COOKIE_SECURE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")

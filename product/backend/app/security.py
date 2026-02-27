import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional


TOKEN_SECRET = os.getenv("DMM_TOKEN_SECRET", "change_me_in_production")
TOKEN_TTL_SECONDS = int(os.getenv("DMM_TOKEN_TTL_SECONDS", "43200"))  # 12h


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("=")
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 150000)
    digest = base64.urlsafe_b64encode(derived).decode("utf-8").rstrip("=")
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if "$" not in password_hash:
        return False
    salt, expected = password_hash.split("$", 1)
    actual = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual, expected)


def create_token(payload: Dict[str, object], ttl_seconds: int = TOKEN_TTL_SECONDS) -> str:
    body = dict(payload)
    body["exp"] = int(time.time()) + ttl_seconds
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    data = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = hmac.new(TOKEN_SECRET.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{data}.{sig_b64}"


def decode_token(token: str) -> Dict[str, object]:
    if "." not in token:
        raise ValueError("invalid token format")
    data, sig = token.split(".", 1)
    expected = hmac.new(TOKEN_SECRET.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    expected_b64 = base64.urlsafe_b64encode(expected).decode("utf-8").rstrip("=")
    if not hmac.compare_digest(sig, expected_b64):
        raise ValueError("invalid token signature")
    padded = data + "=" * (-len(data) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise ValueError("token expired")
    return payload


def parse_bearer_token(authorization_header: str) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.strip().split(" ", 1)
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None

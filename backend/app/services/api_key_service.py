import os
import secrets
import hashlib
import hmac

def generate_api_key() -> str:
    # ag_ + 40 cryptographically random URL-safe characters
    random_part = secrets.token_urlsafe(30) # ~40 chars base64
    return f"ag_{random_part}"

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    attempt_hash = hash_api_key(raw_key)
    return hmac.compare_digest(attempt_hash, stored_hash)

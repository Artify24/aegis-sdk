from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import jwt
from app.config import settings
from app.services.api_key_service import hash_api_key

def build_sdk_token(project_id: str, workspace_id: str, key_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "project_id": project_id,
        "workspace_id": workspace_id,
        "key_id": key_id,
        "exp": expire,
        "type": "sdk"
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_sdk_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "sdk":
            raise Exception("Invalid token type")
        return payload
    except Exception as e:
        raise e

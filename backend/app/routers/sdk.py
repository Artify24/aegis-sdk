from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.database import get_database
from app.services.api_key_service import hash_api_key
from app.services.sdk_auth_service import build_sdk_token

router = APIRouter(prefix="/api/sdk", tags=["sdk"])

@router.post("/auth")
async def sdk_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Log auth failure
        db = get_database()
        await db.audit_log.insert_one({
            "event_type": "SDK_AUTH_FAILED",
            "reason": "Missing or invalid Authorization header",
            "ip_address": request.client.host if request.client else "unknown",
            "timestamp": datetime.now(timezone.utc)
        })
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
        
    raw_key = auth_header.split(" ")[1]
    key_hash = hash_api_key(raw_key)
    
    db = get_database()
    key_doc = await db.api_keys.find_one({"key_hash": key_hash})
    
    if not key_doc:
        await db.audit_log.insert_one({
            "event_type": "SDK_AUTH_FAILED",
            "reason": "Invalid API key",
            "ip_address": request.client.host if request.client else "unknown",
            "timestamp": datetime.now(timezone.utc)
        })
        raise HTTPException(status_code=401, detail={"error": "INVALID_KEY"})
        
    if not key_doc.get("is_active", True):
        await db.audit_log.insert_one({
            "event_type": "SDK_AUTH_FAILED",
            "reason": "API key disabled",
            "key_id": key_doc["key_id"],
            "ip_address": request.client.host if request.client else "unknown",
            "timestamp": datetime.now(timezone.utc)
        })
        raise HTTPException(status_code=401, detail={"error": "KEY_DISABLED"})
        
    if key_doc.get("expires_at") and key_doc["expires_at"] < datetime.now(timezone.utc):
        await db.audit_log.insert_one({
            "event_type": "SDK_AUTH_FAILED",
            "reason": "API key expired",
            "key_id": key_doc["key_id"],
            "ip_address": request.client.host if request.client else "unknown",
            "timestamp": datetime.now(timezone.utc)
        })
        raise HTTPException(status_code=401, detail={"error": "KEY_EXPIRED"})
        
    project = await db.projects.find_one({"_id": key_doc["project_id"]})
    if not project or not project.get("is_active", True):
        raise HTTPException(status_code=401, detail={"error": "PROJECT_NOT_FOUND_OR_INACTIVE"})
        
    # Update last_used_at
    await db.api_keys.update_one(
        {"key_id": key_doc["key_id"]},
        {"$set": {"last_used_at": datetime.now(timezone.utc)}}
    )
    
    sdk_token = build_sdk_token(
        project_id=project["_id"],
        workspace_id=project["workspace_id"],
        key_id=key_doc["key_id"]
    )
    
    return {
        "sdk_token": sdk_token,
        "project_id": project["_id"],
        "workspace_id": project["workspace_id"],
        "environment": project.get("environment", "development"),
        "sdk_version": project.get("sdk_version", "1.0.0"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    }

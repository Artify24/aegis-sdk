from fastapi import APIRouter, Depends, HTTPException, status
from app.models import APIKey, APIKeyCreate, APIKeyResponse, APIKeyFullResponse
from app.database import get_database
from app.services.auth_service import get_current_user
from app.services.api_key_service import generate_api_key, hash_api_key
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/projects/{project_id}/keys", tags=["api_keys"])

async def verify_project_access(project_id: str, user: dict) -> dict:
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "is_active": True})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    return project

@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(project_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    await verify_project_access(project_id, user)
    
    cursor = db.api_keys.find({"project_id": project_id})
    keys = []
    async for doc in cursor:
        keys.append(APIKeyResponse(**doc))
    return keys

@router.post("", response_model=APIKeyFullResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(project_id: str, key_in: APIKeyCreate, user: dict = Depends(get_current_user)):
    db = get_database()
    project = await verify_project_access(project_id, user)
    
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    
    key_id = str(uuid.uuid4())
    
    key_doc = {
        "_id": key_id,
        "key_id": key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "name": key_in.name,
        "key_prefix": raw_key[:10],
        "key_hash": key_hash,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "expires_at": key_in.expires_at,
        "last_used_at": None,
        "created_by": user["user_id"]
    }
    
    await db.api_keys.insert_one(key_doc)
    
    # Audit log
    await db.audit_log.insert_one({
        "event_type": "API_KEY_CREATED",
        "key_id": key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "performed_by": user["user_id"],
        "timestamp": datetime.now(timezone.utc)
    })
    
    return APIKeyFullResponse(**key_doc, raw_key=raw_key)

@router.put("/{key_id}/disable", response_model=APIKeyResponse)
async def disable_api_key(project_id: str, key_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    project = await verify_project_access(project_id, user)
    
    key_doc = await db.api_keys.find_one({"key_id": key_id, "project_id": project_id})
    if not key_doc:
        raise HTTPException(status_code=404, detail="API key not found")
        
    await db.api_keys.update_one({"key_id": key_id}, {"$set": {"is_active": False}})
    
    # Audit log
    await db.audit_log.insert_one({
        "event_type": "API_KEY_DISABLED",
        "key_id": key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "performed_by": user["user_id"],
        "timestamp": datetime.now(timezone.utc)
    })
    
    key_doc["is_active"] = False
    return APIKeyResponse(**key_doc)

@router.put("/{key_id}/enable", response_model=APIKeyResponse)
async def enable_api_key(project_id: str, key_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    project = await verify_project_access(project_id, user)
    
    key_doc = await db.api_keys.find_one({"key_id": key_id, "project_id": project_id})
    if not key_doc:
        raise HTTPException(status_code=404, detail="API key not found")
        
    await db.api_keys.update_one({"key_id": key_id}, {"$set": {"is_active": True}})
    
    key_doc["is_active"] = True
    return APIKeyResponse(**key_doc)

@router.delete("/{key_id}")
async def delete_api_key(project_id: str, key_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    project = await verify_project_access(project_id, user)
    
    result = await db.api_keys.delete_one({"key_id": key_id, "project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
        
    # Audit log
    await db.audit_log.insert_one({
        "event_type": "API_KEY_DELETED",
        "key_id": key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "performed_by": user["user_id"],
        "timestamp": datetime.now(timezone.utc)
    })
    
    return {"message": "API key successfully deleted."}

@router.post("/{key_id}/rotate", response_model=APIKeyFullResponse)
async def rotate_api_key(project_id: str, key_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    project = await verify_project_access(project_id, user)
    
    old_key = await db.api_keys.find_one({"key_id": key_id, "project_id": project_id})
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")
        
    # Delete old key
    await db.api_keys.delete_one({"key_id": key_id})
    
    # Create new key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    
    new_key_id = str(uuid.uuid4())
    
    key_doc = {
        "_id": new_key_id,
        "key_id": new_key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "name": old_key["name"],
        "key_prefix": raw_key[:10],
        "key_hash": key_hash,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "expires_at": old_key.get("expires_at"),
        "last_used_at": None,
        "created_by": user["user_id"]
    }
    
    await db.api_keys.insert_one(key_doc)
    
    # Audit log
    await db.audit_log.insert_one({
        "event_type": "API_KEY_ROTATED",
        "key_id": new_key_id,
        "old_key_id": key_id,
        "project_id": project_id,
        "workspace_id": project["workspace_id"],
        "performed_by": user["user_id"],
        "timestamp": datetime.now(timezone.utc)
    })
    
    return APIKeyFullResponse(**key_doc, raw_key=raw_key)

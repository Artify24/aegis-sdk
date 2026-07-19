from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Project, ProjectCreate, ProjectUpdate, ProjectCreateResponse
from app.database import get_database
from app.services.auth_service import get_current_user
from app.services.api_key_service import generate_api_key, hash_api_key
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=list[Project])
async def list_projects(workspace_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Verify user owns the workspace
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id})
    if not workspace or workspace["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    cursor = db.projects.find({"workspace_id": workspace_id, "is_active": True})
    projects = []
    async for doc in cursor:
        projects.append(Project(**doc))
    return projects

@router.post("", response_model=ProjectCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_in: ProjectCreate, user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Verify user owns the workspace
    workspace = await db.workspaces.find_one({"workspace_id": project_in.workspace_id})
    if not workspace or workspace["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    project_id = str(uuid.uuid4())
        
    project_doc = {
        "_id": project_id,
        "workspace_id": project_in.workspace_id,
        "owner_id": user["user_id"],
        "name": project_in.name,
        "description": project_in.description,
        "provider": project_in.provider or "OpenAI",
        "sdk_version": project_in.sdk_version or "1.0.0",
        "environment": project_in.environment or "development",
        "status": "healthy",
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    # Generate default API key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    key_id = str(uuid.uuid4())
    
    key_doc = {
        "_id": key_id,
        "key_id": key_id,
        "project_id": project_id,
        "workspace_id": project_in.workspace_id,
        "name": "Default API Key",
        "key_prefix": raw_key[:10],
        "key_hash": key_hash,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "last_used_at": None,
        "created_by": user["user_id"]
    }
    
    await db.projects.insert_one(project_doc)
    await db.api_keys.insert_one(key_doc)
    
    return ProjectCreateResponse(
        project=Project(**project_doc),
        default_api_key=raw_key
    )

@router.get("/{id}", response_model=Project)
async def get_project(id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.projects.find_one({"_id": id, "is_active": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Verify ownership
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    return Project(**doc)

@router.put("/{id}", response_model=Project)
async def update_project(id: str, project_in: ProjectUpdate, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.projects.find_one({"_id": id, "is_active": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Verify ownership
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
        
    update_data = {k: v for k, v in project_in.model_dump(exclude_unset=True).items()}
    if update_data:
        await db.projects.update_one({"_id": id}, {"$set": update_data})
        doc = await db.projects.find_one({"_id": id})
        
    return Project(**doc)

@router.delete("/{id}")
async def delete_project(id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.projects.find_one({"_id": id, "is_active": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
        
    # Soft delete
    await db.projects.update_one({"_id": id}, {"$set": {"is_active": False}})
    
    # Phase 4 API Keys will be soft deleted here as well, if we had them yet.
    # We will implement API Key cascading deletion in Phase 4.
    
    return {"message": "Project successfully deleted."}

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Workspace, WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.database import get_database
from app.services.auth_service import get_current_user
from datetime import datetime, timezone
import uuid
import re

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

def generate_slug(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug

@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.workspaces.find({"owner_id": user["user_id"]})
    workspaces = []
    async for doc in cursor:
        workspaces.append(WorkspaceResponse(**doc))
    return workspaces

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(workspace_in: WorkspaceCreate, user: dict = Depends(get_current_user)):
    db = get_database()
    
    workspace_id = str(uuid.uuid4())
    slug = generate_slug(workspace_in.name)
    
    # check unique slug
    base_slug = slug
    counter = 1
    while await db.workspaces.find_one({"slug": slug}):
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    workspace_doc = {
        "workspace_id": workspace_id,
        "owner_id": user["user_id"],
        "name": workspace_in.name,
        "slug": slug,
        "plan": "free",
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.workspaces.insert_one(workspace_doc)
    return WorkspaceResponse(**workspace_doc)

# NOTE: Specific sub-routes must appear BEFORE the wildcard /{id} route
@router.get("/{id}/summary")
async def get_workspace_summary(id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.workspaces.find_one({"workspace_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    project_count = await db.projects.count_documents({"workspace_id": id, "is_active": True})
    
    pipeline = [
        {"$match": {"context.workspace_id": id}},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "blocked": {"$sum": {"$cond": [{"$eq": ["$status", "BLOCKED"]}, 1, 0]}},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}},
            "avg_duration": {"$avg": "$summary.duration_ms"}
        }}
    ]
    cursor = db.execution_reports.aggregate(pipeline)
    agg = await cursor.to_list(length=1)
    stats = agg[0] if agg else {}
    total = stats.get("total", 0)
    success_rate = round((stats.get("success", 0) / total) * 100, 1) if total > 0 else 0
    
    return {
        "total_projects": project_count,
        "total_executions": total,
        "blocked_executions": stats.get("blocked", 0),
        "success_rate": success_rate,
        "avg_duration_ms": round(stats.get("avg_duration") or 0)
    }

@router.get("/{id}", response_model=WorkspaceResponse)
async def get_workspace(id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.workspaces.find_one({"workspace_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    return WorkspaceResponse(**doc)

@router.put("/{id}", response_model=WorkspaceResponse)
async def update_workspace(id: str, workspace_in: WorkspaceUpdate, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.workspaces.find_one({"workspace_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this workspace")
        
    update_data = {k: v for k, v in workspace_in.model_dump(exclude_unset=True).items()}
    if update_data:
        await db.workspaces.update_one({"workspace_id": id}, {"$set": update_data})
        doc = await db.workspaces.find_one({"workspace_id": id})
        
    return WorkspaceResponse(**doc)

@router.delete("/{id}")
async def delete_workspace(id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.workspaces.find_one({"workspace_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if doc["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this workspace")
        
    # Soft delete
    await db.workspaces.update_one({"workspace_id": id}, {"$set": {"is_active": False}})
    return {"message": "Workspace successfully deleted."}

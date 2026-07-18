from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from app.database import get_database
from app.services.auth_service import get_current_user
from app.middleware.sdk_auth_middleware import get_sdk_context
from app.services.execution_service import validate_report, store_report, get_report_summary
from datetime import datetime, timezone

router = APIRouter(prefix="/api/executions", tags=["executions"])
sdk_router = APIRouter(prefix="/api/sdk/executions", tags=["sdk_executions"])

# --- SDK Endpoints ---

@sdk_router.post("", status_code=status.HTTP_201_CREATED)
async def upload_execution_report(report: dict, sdk_context: dict = Depends(get_sdk_context)):
    project_id = sdk_context["project_id"]
    workspace_id = sdk_context["workspace_id"]
    key_id = sdk_context["key_id"]
    
    validate_report(report, project_id)
    
    execution_id = await store_report(report, workspace_id, key_id)
    
    # Broadcast to dashboard via websocket (Phase 9 integration)
    from app.routers.websocket import manager
    summary = get_report_summary(report)
    await manager.broadcast_to_project(project_id, {
        "type": "new_execution",
        "execution": summary
    })
    
    return {"execution_id": execution_id, "stored_at": datetime.now(timezone.utc).isoformat() + "Z"}

# --- Dashboard Endpoints ---

@router.get("")
async def list_executions(
    project_id: str,
    filter_status: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    db = get_database()
    
    # Verify project access
    project = await db.projects.find_one({"_id": project_id, "is_active": True})
    if not project or project["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    query = {"context.project_id": project_id}
    if filter_status:
        query["status"] = filter_status
    if risk_level:
        query["summary.risk_level"] = risk_level
        
    skip = (page - 1) * limit
    cursor = db.execution_reports.find(query).sort("audit.created_at", -1).skip(skip).limit(limit)
    
    total = await db.execution_reports.count_documents(query)
    
    executions = []
    async for doc in cursor:
        executions.append(get_report_summary(doc))
        
    return {
        "data": executions,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": (skip + limit) < total
        }
    }

@router.get("/{execution_id}")
async def get_execution_detail(execution_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Fetch report
    report = await db.execution_reports.find_one({"context.execution_id": execution_id})
    if not report:
        raise HTTPException(status_code=404, detail="Execution report not found")
        
    # Verify access
    project = await db.projects.find_one({"_id": report["context"]["project_id"]})
    if not project or project["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this execution")
        
    # Remove mongodb _id
    report.pop("_id", None)
    return report

@router.get("/{execution_id}/timeline")
async def get_execution_timeline(execution_id: str, user: dict = Depends(get_current_user)):
    report = await get_execution_detail(execution_id, user)
    return report.get("timeline", [])

@router.get("/{execution_id}/tool_calls")
async def get_execution_tool_calls(execution_id: str, user: dict = Depends(get_current_user)):
    report = await get_execution_detail(execution_id, user)
    return report.get("tool_calls", [])

@router.get("/{execution_id}/governance")
async def get_execution_governance(execution_id: str, user: dict = Depends(get_current_user)):
    report = await get_execution_detail(execution_id, user)
    return report.get("governance", {})

@router.get("/{execution_id}/metrics")
async def get_execution_metrics(execution_id: str, user: dict = Depends(get_current_user)):
    report = await get_execution_detail(execution_id, user)
    return report.get("metrics", {})

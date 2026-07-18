from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_database
from app.services.auth_service import get_current_user
from app.services.execution_service import get_report_summary

router = APIRouter(prefix="/api/risk", tags=["risk"])

@router.get("")
async def list_risk_feed(
    workspace_id: str,
    project_id: str | None = None,
    severity: str | None = None, # maps to risk_level: LOW, MEDIUM, HIGH, CRITICAL
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    db = get_database()
    
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id})
    if not workspace or workspace["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    query = {
        "context.workspace_id": workspace_id,
        "$or": [
            {"status": "BLOCKED"},
            {"summary.risk_level": {"$in": ["HIGH", "CRITICAL"]}}
        ]
    }
    
    if project_id:
        query["context.project_id"] = project_id
    if severity:
        # replace the generic $or with specific severity match
        query["summary.risk_level"] = severity
        # remove the $or to strictly match
        query.pop("$or")
        
    cursor = db.execution_reports.find(query).sort("audit.created_at", -1).limit(limit)
    
    feed = []
    async for doc in cursor:
        feed.append(get_report_summary(doc))
        
    return {"data": feed}

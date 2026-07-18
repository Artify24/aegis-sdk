from fastapi import HTTPException
from app.database import get_database
from datetime import datetime, timezone
import uuid

def validate_report(report: dict, project_id: str) -> None:
    context = report.get("context", {})
    if context.get("project_id") != project_id:
        raise HTTPException(status_code=403, detail="Project ID in report does not match token context")
        
    execution_id = context.get("execution_id")
    if not execution_id:
        raise HTTPException(status_code=422, detail="Missing execution_id in report context")
        
    summary = report.get("summary", {})
    status = summary.get("status")
    if status not in ["SUCCESS", "FAILED", "BLOCKED", "CANCELLED"]:
        raise HTTPException(status_code=422, detail=f"Invalid status: {status}")

async def store_report(report: dict, workspace_id: str, key_id: str) -> str:
    db = get_database()
    execution_id = report["context"]["execution_id"]
    
    # Check for duplicates
    existing = await db.execution_reports.find_one({"context.execution_id": execution_id})
    if existing:
        raise HTTPException(status_code=409, detail="Execution report already exists")
        
    # Inject backend metadata
    report["_ingested_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    report["_ingested_by"] = key_id
    report["_schema_version"] = "3.0"
    report["context"]["workspace_id"] = workspace_id
    report["status"] = report.get("summary", {}).get("status", "FAILED")
    
    # Store
    await db.execution_reports.insert_one(report)
    
    return execution_id

def get_report_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    context = report.get("context", {})
    audit = report.get("audit", {})
    
    return {
        "execution_id": context.get("execution_id"),
        "status": summary.get("status"),
        "risk_level": summary.get("risk_level"),
        "governance": summary.get("governance"),
        "duration_ms": summary.get("duration_ms"),
        "tools_used": summary.get("tools_used"),
        "created_at": audit.get("created_at")
    }

from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models import LogEntry, LogCreate
from app.database import get_database
from app.services.auth_service import get_current_user_email
from datetime import datetime, timezone
import uuid
from typing import Optional

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("", response_model=list[LogEntry])
async def list_logs(
    level: Optional[str] = None,
    source: Optional[str] = None,
    sessionId: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    email: str = Depends(get_current_user_email)
):
    db = get_database()
    query = {}
    
    if level:
        query["level"] = level
    if source:
        query["source"] = source
    if sessionId:
        query["meta.sessionId"] = sessionId
        
    cursor = db.logs.find(query).sort("ts", -1).limit(limit)
    logs = []
    async for doc in cursor:
        logs.append(LogEntry(**doc))
    return logs

@router.post("", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
async def create_log(log_in: LogCreate, email: str = Depends(get_current_user_email)):
    db = get_database()
    
    log_id = f"log_{uuid.uuid4().hex[:12]}"
    log_doc = {
        "_id": log_id,
        "ts": datetime.now(timezone.utc).isoformat() + "Z",
        "level": log_in.level,
        "source": log_in.source,
        "message": log_in.message,
        "meta": log_in.meta
    }
    
    await db.logs.insert_one(log_doc)
    return LogEntry(**log_doc)

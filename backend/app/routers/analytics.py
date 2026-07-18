from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_database
from app.services.auth_service import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

async def verify_workspace_access(workspace_id: str, user: dict) -> dict:
    db = get_database()
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id})
    if not workspace or workspace["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
    return workspace

@router.get("/kpis")
async def get_kpis(workspace_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    await verify_workspace_access(workspace_id, user)
    
    # KPIs: active projects, running sessions (we don't track running sessions anymore, so this is total executions), etc.
    active_projects = await db.projects.count_documents({"workspace_id": workspace_id, "is_active": True})
    
    pipeline = [
        {
            "$match": {
                "context.workspace_id": workspace_id
            }
        },
        {
            "$group": {
                "_id": None,
                "total_tokens": {"$sum": "$metrics.cost.total_tokens"},
                "total_cost": {"$sum": "$metrics.cost.estimated_cost_usd"},
                "avg_latency": {"$avg": "$summary.duration_ms"},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}},
                "errored": {"$sum": {"$cond": [{"$eq": ["$status", "FAILED"]}, 1, 0]}},
                "blocked": {"$sum": {"$cond": [{"$eq": ["$status", "BLOCKED"]}, 1, 0]}},
                "total": {"$sum": 1},
                "total_tools": {"$sum": "$summary.tools_used"}
            }
        }
    ]
    
    cursor = db.execution_reports.aggregate(pipeline)
    agg = await cursor.to_list(length=1)
    
    if agg:
        res = agg[0]
        token_usage = res.get("total_tokens", 0)
        total_cost = res.get("total_cost", 0.0)
        avg_latency = round(res.get("avg_latency") or 0.0)
        completed = res.get("completed", 0)
        total = res.get("total", 0)
        blocked = res.get("blocked", 0)
        total_tools = res.get("total_tools", 0)
        
        success_rate = round((completed / total) * 100, 1) if total > 0 else 0
    else:
        token_usage = 0
        total_cost = 0.0
        avg_latency = 0
        success_rate = 0
        total = 0
        blocked = 0
        total_tools = 0
        
    return {
        "activeProjects": active_projects,
        "totalExecutions": total,
        "totalToolCalls": total_tools,
        "tokenUsage": token_usage,
        "totalCost": round(total_cost, 2),
        "avgLatency": avg_latency,
        "successRate": success_rate,
        "blockedExecutions": blocked
    }

@router.get("/charts")
async def get_charts(workspace_id: str, days: int = 14, user: dict = Depends(get_current_user)):
    db = get_database()
    await verify_workspace_access(workspace_id, user)
    
    now = datetime.utcnow()
    date_list = [(now - timedelta(days=i)).strftime("%m-%d") for i in range(days - 1, -1, -1)]
    start_date = now - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "context.workspace_id": workspace_id,
                "audit.created_at": {"$gte": start_date.isoformat()}
            }
        },
        {
            "$project": {
                "day": {"$substr": ["$audit.created_at", 5, 5]},
                "tokens": {"$ifNull": ["$metrics.cost.total_tokens", 0]},
                "cost": {"$ifNull": ["$metrics.cost.estimated_cost_usd", 0.0]},
                "tools": {"$ifNull": ["$summary.tools_used", 0]}
            }
        },
        {
            "$group": {
                "_id": "$day",
                "tokens": {"$sum": "$tokens"},
                "cost": {"$sum": "$cost"},
                "sessions": {"$sum": 1},
                "tools": {"$sum": "$tools"}
            }
        }
    ]
    
    cursor = db.execution_reports.aggregate(pipeline)
    daily_results = {}
    async for doc in cursor:
        daily_results[doc["_id"]] = doc
        
    tokens_series = []
    cost_series = []
    sessions_series = []
    tools_series = []
    
    for d in date_list:
        metrics = daily_results.get(d, {})
        tokens_series.append({"date": d, "value": metrics.get("tokens", 0)})
        cost_series.append({"date": d, "value": metrics.get("cost", 0.0)})
        sessions_series.append({"date": d, "value": metrics.get("sessions", 0)})
        tools_series.append({"date": d, "value": metrics.get("tools", 0)})
        
    return {
        "tokens": tokens_series,
        "cost": cost_series,
        "sessions": sessions_series,
        "tools": tools_series
    }

@router.get("/tool-mix")
async def get_tool_mix(workspace_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    await verify_workspace_access(workspace_id, user)
    
    pipeline = [
        {
            "$match": {
                "context.workspace_id": workspace_id,
                "tool_calls": {"$exists": True, "$not": {"$size": 0}}
            }
        },
        {
            "$unwind": "$tool_calls"
        },
        {
            "$group": {
                "_id": "$tool_calls.tool",
                "value": {"$sum": 1}
            }
        },
        {
            "$sort": {"value": -1}
        },
        {
            "$limit": 10
        }
    ]
    
    cursor = db.execution_reports.aggregate(pipeline)
    db_mix = []
    async for doc in cursor:
        db_mix.append({"n": doc["_id"], "v": doc["value"]})
        
    return db_mix

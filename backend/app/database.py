from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None  # type: ignore[type-arg]
    db: Optional[AsyncIOMotorDatabase] = None  # type: ignore[type-arg]

db_helper = Database()

def get_database() -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Return the database instance. Raises if not connected."""
    assert db_helper.db is not None, "Database not connected. Call connect_to_mongo() first."
    return db_helper.db

def connect_to_mongo() -> None:
    db_helper.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_helper.db = db_helper.client[settings.DATABASE_NAME]

def close_mongo_connection() -> None:
    if db_helper.client:
        db_helper.client.close()

async def setup_indexes() -> None:
    import pymongo
    db = get_database()
    
    # Users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    
    # Workspaces
    await db.workspaces.create_index("owner_id")
    await db.workspaces.create_index("slug", unique=True)
    
    # Workspace Members
    await db.workspace_members.create_index([("workspace_id", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)], unique=True)
    await db.workspace_members.create_index("user_id")
    
    # Projects
    await db.projects.create_index("workspace_id")
    await db.projects.create_index("owner_id")
    await db.projects.create_index([("workspace_id", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
    
    # API Keys
    await db.api_keys.create_index("key_hash", unique=True)
    await db.api_keys.create_index("project_id")
    await db.api_keys.create_index("workspace_id")
    
    # Execution Reports
    await db.execution_reports.create_index("context.execution_id", unique=True)
    await db.execution_reports.create_index("context.project_id")
    await db.execution_reports.create_index("context.workspace_id")
    await db.execution_reports.create_index([("audit.created_at", pymongo.DESCENDING)])
    await db.execution_reports.create_index("status")
    await db.execution_reports.create_index([("context.project_id", pymongo.ASCENDING), ("audit.created_at", pymongo.DESCENDING)])
    
    # Audit Log
    await db.audit_log.create_index([("workspace_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
    await db.audit_log.create_index([("key_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
    await db.audit_log.create_index("event_type")
    # TTL index: 1 year (31536000 seconds)
    await db.audit_log.create_index("timestamp", expireAfterSeconds=31536000)
    
    # Policies
    await db.policies.create_index("workspace_id")
    await db.policies.create_index([("workspace_id", pymongo.ASCENDING), ("scope", pymongo.ASCENDING)])

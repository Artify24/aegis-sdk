from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

# --- Helper functions/classes for Mongo ID handling ---
class MongoBaseModel(BaseModel):
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# --- User Schemas ---
class User(MongoBaseModel):
    user_id: str
    username: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    is_verified: bool = False
    plan: str = "free"

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    created_at: datetime
    is_active: bool
    is_verified: bool
    plan: str

# --- Workspace Schemas ---
class Workspace(MongoBaseModel):
    workspace_id: str
    owner_id: str
    name: str
    slug: str
    plan: str = "free"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class WorkspaceCreate(BaseModel):
    name: str

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class WorkspaceResponse(BaseModel):
    workspace_id: str
    owner_id: str
    name: str
    slug: str
    plan: str
    created_at: datetime
    is_active: bool

# --- Project Schemas ---
class Project(MongoBaseModel):
    project_id: str = Field(alias="_id")
    workspace_id: str
    owner_id: str
    name: str
    description: str
    provider: str = "OpenAI"
    sdk_version: str = "1.0.0"
    environment: str = "development"
    status: str = "healthy"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    workspace_id: str
    name: str
    description: str
    provider: Optional[str] = "OpenAI"
    sdk_version: Optional[str] = "1.0.0"
    environment: Optional[str] = "development"

class ProjectCreateResponse(BaseModel):
    project: Project
    default_api_key: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    sdk_version: Optional[str] = None
    environment: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

# --- API Key Schemas ---
class APIKey(MongoBaseModel):
    key_id: str = Field(alias="_id")
    project_id: str
    workspace_id: str
    name: str
    key_prefix: str
    key_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_by: str

class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    key_id: str
    project_id: str
    workspace_id: str
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_by: str

class APIKeyFullResponse(APIKeyResponse):
    raw_key: str

# --- Session Schemas ---
class Session(MongoBaseModel):
    id: str = Field(alias="_id")
    projectId: str
    name: str
    status: str = "running"
    tokens: int = 0
    cost: float = 0.0
    latency: int = 0
    createdAt: str

class SessionCreate(BaseModel):
    projectId: str
    name: str
    status: Optional[str] = "running"

# --- Stage Event Schemas (Inside Session Trace) ---
class StageEvent(BaseModel):
    key: str  # e.g. "input", "intent", "policy", "risk", "planner", "tool", "memory", "llm", "final"
    label: str
    desc: str
    status: str  # "pending", "running", "done"
    startedAt: int  # ms timestamp
    finishedAt: Optional[int] = None  # ms timestamp
    logs: List[str] = []

class SessionDetail(Session):
    events: List[StageEvent] = []

# --- Policy Schemas ---
class Policy(MongoBaseModel):
    id: str = Field(alias="_id")
    name: str
    enabled: bool = True
    scope: str = "global"  # "global" | "project" | "tool"
    description: str
    triggers: int = 0

class PolicyCreate(BaseModel):
    name: str
    scope: str = "global"
    description: str
    enabled: Optional[bool] = True

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    scope: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    triggers: Optional[int] = None

# --- Log Schemas ---
class LogEntry(MongoBaseModel):
    id: str = Field(alias="_id")
    ts: str
    level: str  # "INFO" | "WARNING" | "ERROR" | "DEBUG"
    source: str
    message: str
    meta: Dict[str, Any] = {}

class LogCreate(BaseModel):
    level: str
    source: str
    message: str
    meta: Dict[str, Any] = {}

# --- Risk Event Schemas ---
class RiskEvent(MongoBaseModel):
    id: str = Field(alias="_id")
    kind: str
    severity: str  # "low" | "medium" | "high" | "critical"
    when: str
    project: str  # project name
    detail: str

class RiskCreate(BaseModel):
    kind: str
    severity: str
    project: str
    detail: str

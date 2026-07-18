import asyncio
from datetime import datetime, timedelta, timezone
import random
import argparse
from app.database import connect_to_mongo, close_mongo_connection, get_database
import os
# Seed datasets mirroring frontend's data.ts
PROJECT_NAMES = [
    "Aegis Support Agent",
]

PROVIDERS = ["OpenAI"]
RUNTIMES = ["kernel-v1"]
STATUSES = ["healthy"]

POLICIES = [
    { "_id": "pol_1", "name": "No API Key Leakage", "enabled": True, "scope": "global", "description": "Regex + entropy detector on outbound tokens.", "triggers": 41 },
    { "_id": "pol_2", "name": "Block Dangerous Prompts", "enabled": True, "scope": "global", "description": "Prompt-shield model with jailbreak classifier.", "triggers": 128 },
    { "_id": "pol_3", "name": "Restrict File Access", "enabled": True, "scope": "tool", "description": "Filesystem tool limited to /workspace subtree.", "triggers": 7 },
    { "_id": "pol_4", "name": "Limit Tool Usage", "enabled": False, "scope": "project", "description": "Rate-limit expensive tools per session.", "triggers": 0 },
    { "_id": "pol_5", "name": "PII Redaction", "enabled": True, "scope": "global", "description": "Automatic redaction of emails, phones, CC numbers.", "triggers": 356 },
    { "_id": "pol_6", "name": "Egress Domain Allowlist", "enabled": True, "scope": "global", "description": "HTTP tool restricted to approved domains.", "triggers": 12 }
]

RISK_KINDS = ["Prompt Injection", "Blocked Request", "Policy Violation", "High-Risk Session", "Sensitive Data", "Tool Abuse"]
SEVERITIES = ["low", "medium", "high", "critical"]

STAGE_METADATA = [
    {"key": "input", "label": "User Prompt", "desc": "Prompt received and normalized", "logs": ["received prompt", "sanitized whitespace", "tokenized 87 tokens"]},
    {"key": "intent", "label": "Intent Analysis", "desc": "Classifying user intent + entities", "logs": ["classifier: information_lookup (0.94)", "extracted 2 entities"]},
    {"key": "policy", "label": "Policy Check", "desc": "Evaluating policies against context", "logs": ["evaluating 6 active policies", "no violations detected"]},
    {"key": "risk", "label": "Risk Analysis", "desc": "Prompt-shield + jailbreak scoring", "logs": ["jailbreak score: 0.03", "prompt-shield: pass"]},
    {"key": "planner", "label": "Planner", "desc": "Building tool-use plan", "logs": ["plan built: 3 steps", "tools selected: [search_docs, http.get]"]},
    {"key": "tool", "label": "Tool Execution", "desc": "Invoking selected tool with args", "logs": ["invoking search_docs ...", "match found in kb_v2 (score 0.88)"]},
    {"key": "memory", "label": "Memory Update", "desc": "Persisting facts + episodic memory", "logs": ["upserted 1 fact into episodic memory"]},
    {"key": "llm", "label": "LLM Response", "desc": "Streaming completion from provider", "logs": ["streaming from anthropic:claude-sonnet", "chunk 1 of ~12"]},
    {"key": "final", "label": "Final Output", "desc": "Rendered response returned to caller", "logs": ["response formatted", "returned 412 tokens in 842ms"]}
]

async def seed_database(force=False):
    db = get_database()
    
    # Check if database is already seeded
    project_count = await db.projects.count_documents({})
    if project_count > 0 and not force:
        print("Database already contains data. Skipping seeding.")
        return
        
    print("Database empty or force seeding enabled. Starting seeding...")
    
    # 1. Clean existing collections if force
    if force:
        await db.users.delete_many({})
        await db.workspaces.delete_many({})
        await db.projects.delete_many({})
        await db.sessions.delete_many({})
        await db.events.delete_many({})
        await db.policies.delete_many({})
        await db.logs.delete_many({})
        await db.risk_events.delete_many({})
        
    # 2. Insert Policies
    for policy in POLICIES:
        await db.policies.update_one({"_id": policy["_id"]}, {"$set": policy}, upsert=True)
        
    # 3. Create default user
    from app.services.auth_service import get_password_hash
    import uuid
    admin_user = {
        "user_id": str(uuid.uuid4()),
        "username": "admin",
        "email": "admin@guardian.ai",
        "hashed_password": get_password_hash("admin123"),
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
        "is_verified": True,
        "plan": "free"
    }
    await db.users.update_one({"email": admin_user["email"]}, {"$set": admin_user}, upsert=True)
    
    # 3.5 Create default workspace
    workspace_id = f"ws_{str(uuid.uuid4())[:8]}"
    workspace_doc = {
        "workspace_id": workspace_id,
        "name": "Admin's Workspace",
        "owner_id": admin_user["user_id"],
        "created_at": datetime.now(timezone.utc)
    }
    await db.workspaces.update_one({"owner_id": admin_user["user_id"]}, {"$set": workspace_doc}, upsert=True)
    
    # 4. Generate projects & sessions (history of last 30 days)
    now = datetime.now(timezone.utc)
    
    for i, name in enumerate(PROJECT_NAMES):
        project_id = f"prj_{(1000 + i)}"
        
        # Calculate random stats
        proj_sessions_count = random.randint(120, 300)
        proj_tokens_count = proj_sessions_count * random.randint(1500, 3000)
        
        project_doc = {
            "_id": project_id,
            "workspace_id": workspace_id,
            "name": name,
            "description": "Live demo project connected to app.py.",
            "createdAt": now.isoformat() + "Z",
            "runtime": RUNTIMES[0],
            "provider": PROVIDERS[0],
            "status": STATUSES[0],
            "sessions": 0,
            "tokens": 0
        }
        await db.projects.update_one({"_id": project_id}, {"$set": project_doc}, upsert=True)
                        
    print("Database seeding completed instantly!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Aegis Cloud database.")
    parser.add_argument("--force", action="store_true", help="Force clear the database before seeding.")
    args = parser.parse_args()

    # Load environment variables if necessary
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    load_dotenv(env_path)

    connect_to_mongo()
    asyncio.run(seed_database(force=args.force))
    close_mongo_connection()

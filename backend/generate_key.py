import asyncio
from datetime import datetime, timezone
import uuid
import secrets
import hashlib
import os
from pymongo import MongoClient
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

def generate_key():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = MongoClient(mongo_url)
    db = client["aegis_cloud"]
    
    admin_user = db.users.find_one({"email": "admin@guardian.ai"})
    if not admin_user:
        print("Admin user not found. Did you run the seed script?")
        return
        
    admin_workspace = db.workspaces.find_one({"owner_id": admin_user["user_id"]})
    if not admin_workspace:
        print("Admin workspace not found.")
        return
        
    admin_project = db.projects.find_one({"workspace_id": admin_workspace["workspace_id"]})
    if not admin_project:
        print("Admin project not found.")
        return
        
    raw_key = f"ag_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:7] + "..." + raw_key[-4:]
    
    key_doc = {
        "_id": str(uuid.uuid4()),
        "project_id": admin_project["_id"],
        "workspace_id": admin_workspace["workspace_id"],
        "name": "Demo App Key",
        "key_prefix": key_prefix,
        "key_hash": key_hash,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "last_used_at": None,
        "created_by": admin_user["user_id"]
    }
    
    # Use key_id instead of _id because that's what the backend schema uses
    key_doc["key_id"] = key_doc.pop("_id")
    # Actually MongoDB requires _id, so we'll just use key_id for both or just use key_id in the doc.
    key_doc["_id"] = key_doc["key_id"]
    
    db.api_keys.insert_one(key_doc)
    
    print(f"Generated API Key: {raw_key}")
    
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\nAEGIS_PROJECT_KEY=\"{raw_key}\"\n")
        
    print(f"Successfully added AEGIS_PROJECT_KEY to {os.path.abspath(env_path)}!")

if __name__ == "__main__":
    generate_key()

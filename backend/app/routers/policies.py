from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Policy, PolicyCreate, PolicyUpdate
from app.database import get_database
from app.services.auth_service import get_current_user_email
import random
from typing import Optional

router = APIRouter(prefix="/api/policies", tags=["policies"])

def generate_policy_id() -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    suffix = "".join(random.choice(chars) for _ in range(5))
    return f"pol_{suffix}"

@router.get("", response_model=list[Policy])
async def list_policies(email: str = Depends(get_current_user_email)):
    db = get_database()
    cursor = db.policies.find({})
    policies = []
    async for doc in cursor:
        policies.append(Policy(**doc))
    return policies

@router.post("", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(policy_in: PolicyCreate, email: str = Depends(get_current_user_email)):
    db = get_database()
    
    policy_id = generate_policy_id()
    while await db.policies.find_one({"_id": policy_id}):
        policy_id = generate_policy_id()
        
    policy_doc = {
        "_id": policy_id,
        "name": policy_in.name,
        "enabled": policy_in.enabled if policy_in.enabled is not None else True,
        "scope": policy_in.scope,
        "description": policy_in.description,
        "triggers": 0
    }
    
    await db.policies.insert_one(policy_doc)
    return Policy(**policy_doc)

@router.put("/{id}", response_model=Policy)
async def update_policy(id: str, policy_in: PolicyUpdate, email: str = Depends(get_current_user_email)):
    db = get_database()
    doc = await db.policies.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    update_data = {k: v for k, v in policy_in.model_dump(exclude_unset=True).items()}
    if update_data:
        await db.policies.update_one({"_id": id}, {"$set": update_data})
        doc = await db.policies.find_one({"_id": id})
        
    return Policy(**doc)

@router.delete("/{id}")
async def delete_policy(id: str, email: str = Depends(get_current_user_email)):
    db = get_database()
    result = await db.policies.delete_one({"_id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy successfully deleted."}

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.models import UserRegister, UserLogin, UserResponse
from app.database import get_database
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_email,
    oauth2_scheme
)
from datetime import datetime, timedelta, timezone
import uuid
import jwt
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserRegister):
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_in.email},
            {"username": user_in.username}
        ]
    })
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
        
    hashed_password = get_password_hash(user_in.password)
    user_doc = {
        "user_id": str(uuid.uuid4()),
        "username": user_in.username,
        "email": user_in.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
        "is_verified": False,
        "plan": "free"
    }
    
    await db.users.insert_one(user_doc)
    
    # Create default workspace
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', f"{user_in.username}-workspace".lower()).strip('-')
    workspace_doc = {
        "workspace_id": str(uuid.uuid4()),
        "owner_id": user_doc["user_id"],
        "name": f"{user_in.username}'s Workspace",
        "slug": slug,
        "plan": "free",
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    await db.workspaces.insert_one(workspace_doc)
    
    return UserResponse(
        user_id=user_doc["user_id"],
        username=user_in.username,
        email=user_in.email,
        created_at=user_doc["created_at"],
        is_active=user_doc["is_active"],
        is_verified=user_doc["is_verified"],
        plan=user_doc["plan"]
    )

@router.post("/login")
async def login(user_in: UserLogin):
    db = get_database()
    user = await db.users.find_one({"email": user_in.email})
    if not user or not verify_password(user_in.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = user.get("user_id", "")
    access_token = create_access_token(data={"sub": user["email"], "user_id": user_id})
    refresh_token = create_access_token(
        data={"sub": user["email"], "user_id": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "username": user["username"],
            "email": user["email"]
        }
    }

@router.post("/refresh")
async def refresh_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Refresh token required")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if not email or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        access_token = create_access_token(data={"sub": email, "user_id": user_id})
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(email: str = Depends(get_current_user_email)):
    db = get_database()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user.get("user_id", ""),
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
        is_active=user.get("is_active", True),
        is_verified=user.get("is_verified", False),
        plan=user.get("plan", "free")
    )

@router.get("/verify-token")
async def verify_token(email: str = Depends(get_current_user_email)):
    return {"status": "valid", "email": email}

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.sdk_auth_service import verify_sdk_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/sdk/auth", auto_error=False)

async def get_sdk_context(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate SDK credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        payload = verify_sdk_token(token)
        return {
            "project_id": payload.get("project_id"),
            "workspace_id": payload.get("workspace_id"),
            "key_id": payload.get("key_id")
        }
    except Exception:
        raise credentials_exception

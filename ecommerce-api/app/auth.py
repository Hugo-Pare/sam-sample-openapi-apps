from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime
import secrets
from app.database import get_db
from app.models import APIKey, ScopeEnum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_api_key(key: str) -> str:
    """Hash an API key for storage"""
    return pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return pwd_context.verify(plain_key, hashed_key)


def generate_api_key() -> str:
    """Generate a new API key"""
    return secrets.token_urlsafe(32)


async def get_api_key(
    x_api_key: str = Header(..., description="API Key for authentication"),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Validate API key and return the APIKey object.
    Raises 401 if key is invalid or inactive.
    """
    # Query all API keys to check against the provided key
    api_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    
    for api_key in api_keys:
        if verify_api_key(x_api_key, api_key.key_hash):
            # Check if key is expired
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )
            return api_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or inactive API key"
    )


def require_scope(*required_scopes: ScopeEnum):
    """
    Dependency factory to check if API key has required scope.
    Scopes are hierarchical: admin > write > read
    """
    async def scope_checker(api_key: APIKey = Depends(get_api_key)) -> APIKey:
        scope_hierarchy = {
            ScopeEnum.READ: 1,
            ScopeEnum.WRITE: 2,
            ScopeEnum.ADMIN: 3
        }
        
        user_scope_level = scope_hierarchy.get(api_key.scope, 0)
        required_level = max(scope_hierarchy.get(scope, 0) for scope in required_scopes)
        
        if user_scope_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scopes}, your scope: {api_key.scope}"
            )
        
        return api_key
    
    return scope_checker

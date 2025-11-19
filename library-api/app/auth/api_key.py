from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets

from app.database import get_db
from app import models
from app.models import ScopeEnum

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a random API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """Hash an API key"""
    return pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return pwd_context.verify(plain_key, hashed_key)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> models.APIKey:
    """Dependency to validate API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check all API keys in database
    api_keys = db.query(models.APIKey).filter(models.APIKey.is_active == True).all()
    
    for db_key in api_keys:
        if verify_api_key(api_key, db_key.key_hash):
            return db_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_scope(*required_scopes: ScopeEnum):
    """Dependency factory to check if API key has required scope"""
    async def check_scope(
        api_key: models.APIKey = Depends(get_api_key)
    ) -> models.APIKey:
        # Admin scope has access to everything
        if api_key.scope == ScopeEnum.ADMIN:
            return api_key
        
        # Check if key has one of the required scopes
        if api_key.scope not in required_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[s.value for s in required_scopes]}, Have: {api_key.scope.value}"
            )
        
        return api_key
    
    return check_scope

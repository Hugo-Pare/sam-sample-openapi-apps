from fastapi import HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import APIKey
from app.auth.jwt_handler import verify_key

# Define API Key security scheme
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key_header: str = Depends(api_key_scheme),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Validate API key from X-API-Key header.
    Returns the APIKey object if valid.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Query all active API keys
    api_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    
    for api_key in api_keys:
        if verify_key(api_key_header, api_key.key_hash):
            return api_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or inactive API key"
    )

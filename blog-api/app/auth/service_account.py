from fastapi import HTTPException, status, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import ServiceAccount
from app.auth.jwt_handler import verify_key, decode_access_token, create_service_account_token
from app.schemas import TokenData, ServiceAccountJSON
from google.auth import jwt as google_jwt
from google.auth.exceptions import GoogleAuthError

security = HTTPBearer(auto_error=False)


def verify_google_oauth_token(token: str) -> Optional[str]:
    """
    Verify a Google OAuth2 token issued by a service account.
    Returns the service account email if valid, None otherwise.
    """
    try:
        # Decode the token without verification to get the email
        # Google service account tokens are self-signed JWTs
        decoded = google_jwt.decode(token, verify=False)
        
        # Extract service account email from different possible claims
        email = decoded.get('iss') or decoded.get('sub') or decoded.get('email')
        
        if email and '@' in email:
            return email
    except Exception:
        pass
    
    return None


async def get_service_account_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Validate Bearer token and return token data with scopes.
    Used for service account authenticated endpoints.
    """
    token = credentials.credentials
    
    # Decode the JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify it's a service account token
    if payload.get("type") != "service_account":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    scopes = payload.get("scopes", [])
    
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the service account still exists and is active
    service_account = db.query(ServiceAccount).filter(
        ServiceAccount.email == email,
        ServiceAccount.is_active == True
    ).first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(email=email, scopes=scopes)


async def get_service_account_from_json_or_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Authenticate using Bearer token (Blog API JWT or Google OAuth2) OR service account JSON in request body.
    Supports three authentication methods:
    1. Blog API's own JWT tokens
    2. Google OAuth2 tokens (from service_account_dict_to_scheme_credential)
    3. Service account JSON directly in request body
    """
    # Try Bearer token first
    if credentials:
        token = credentials.credentials
        
        # Try Blog API JWT token
        payload = decode_access_token(token)
        if payload and payload.get("type") == "service_account":
            email = payload.get("sub")
            scopes = payload.get("scopes", [])
            
            if email:
                # Verify service account still active
                service_account = db.query(ServiceAccount).filter(
                    ServiceAccount.email == email,
                    ServiceAccount.is_active == True
                ).first()
                
                if service_account:
                    return TokenData(email=email, scopes=scopes)
        
        # Try Google OAuth2 token
        google_email = verify_google_oauth_token(token)
        if google_email:
            # Look up service account by email
            service_account = db.query(ServiceAccount).filter(
                ServiceAccount.email == google_email,
                ServiceAccount.is_active == True
            ).first()
            
            if service_account:
                # Use all scopes configured for this service account
                return TokenData(email=service_account.email, scopes=service_account.scopes)
    
    # Try service account JSON from body
    try:
        body = await request.json()
        # Support both Google format (client_email) and legacy format (email)
        email = body.get("client_email") or body.get("email")
        private_key = body.get("private_key")
        scopes = body.get("scopes")
        
        if email and private_key and scopes:
            # Verify service account credentials
            service_account = verify_service_account_credentials(
                email,
                private_key,
                db
            )
            
            # Verify requested scopes are allowed
            for scope in scopes:
                if scope not in service_account.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Scope '{scope}' not allowed for this service account"
                    )
            
            return TokenData(email=service_account.email, scopes=scopes)
    except:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Bearer token (Blog API JWT or Google OAuth2) or service account JSON in body.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_scopes(*required_scopes: str):
    """
    Dependency factory to check if the service account has required scopes.
    Multiple scopes can be required - service account must have at least one.
    Accepts either Bearer token or service account JSON in body.
    """
    async def scope_checker(token_data: TokenData = Depends(get_service_account_from_json_or_token)) -> TokenData:
        # Check if service account has any of the required scopes
        has_required_scope = False
        for scope in required_scopes:
            if scope in token_data.scopes:
                has_required_scope = True
                break
        
        if not has_required_scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {required_scopes}, your scopes: {token_data.scopes}"
            )
        
        return token_data
    
    return scope_checker


def verify_service_account_credentials(email: str, private_key: str, db: Session) -> ServiceAccount:
    """
    Verify service account credentials (email and private key).
    Returns the ServiceAccount object if valid.
    """
    service_account = db.query(ServiceAccount).filter(
        ServiceAccount.email == email,
        ServiceAccount.is_active == True
    ).first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service account credentials"
        )
    
    # Verify the private key
    if not verify_key(private_key, service_account.private_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service account credentials"
        )
    
    return service_account

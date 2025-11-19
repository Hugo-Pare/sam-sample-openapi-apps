from datetime import datetime, timedelta
from typing import Optional
import secrets
import json
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app import models, schemas
from app.auth.jwt_handler import create_access_token

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
AUTHORIZATION_CODE_EXPIRE_MINUTES = 10
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def generate_client_id() -> str:
    """Generate a random client ID"""
    return secrets.token_urlsafe(16)


def generate_client_secret() -> str:
    """Generate a random client secret"""
    return secrets.token_urlsafe(32)


def generate_authorization_code() -> str:
    """Generate a random authorization code"""
    return secrets.token_urlsafe(32)


def generate_refresh_token() -> str:
    """Generate a random refresh token"""
    return secrets.token_urlsafe(48)


def hash_secret(secret: str) -> str:
    """Hash a client secret"""
    return pwd_context.hash(secret)


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Verify a client secret"""
    return pwd_context.verify(plain_secret, hashed_secret)


def create_oauth2_client(
    client_name: str,
    redirect_uris: list,
    db: Session
) -> tuple[models.OAuth2Client, str]:
    """
    Create a new OAuth2 client
    Returns: (client, plain_client_secret)
    """
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    
    # Store redirect URIs as JSON
    redirect_uris_json = json.dumps(redirect_uris)
    
    db_client = models.OAuth2Client(
        client_id=client_id,
        client_secret_hash=hash_secret(client_secret),
        client_name=client_name,
        redirect_uris=redirect_uris_json,
        is_active=True
    )
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    return db_client, client_secret


def validate_client(
    client_id: str,
    client_secret: str,
    db: Session
) -> models.OAuth2Client:
    """Validate OAuth2 client credentials"""
    client = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_id,
        models.OAuth2Client.is_active == True
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    if not verify_secret(client_secret, client.client_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    return client


def validate_redirect_uri(client: models.OAuth2Client, redirect_uri: str) -> bool:
    """Check if redirect URI is registered for the client"""
    registered_uris = json.loads(client.redirect_uris)
    return redirect_uri in registered_uris


def create_authorization_code(
    client_id: str,
    user_id: int,
    redirect_uri: str,
    scope: Optional[str],
    db: Session
) -> str:
    """Create an authorization code"""
    code = generate_authorization_code()
    expires_at = datetime.utcnow() + timedelta(minutes=AUTHORIZATION_CODE_EXPIRE_MINUTES)
    
    db_code = models.OAuth2AuthCode(
        code=code,
        client_id=client_id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        expires_at=expires_at,
        used=False
    )
    
    db.add(db_code)
    db.commit()
    
    return code


def exchange_code_for_token(
    code: str,
    client_id: str,
    redirect_uri: str,
    db: Session
) -> dict:
    """Exchange authorization code for access token"""
    # Find the authorization code
    db_code = db.query(models.OAuth2AuthCode).filter(
        models.OAuth2AuthCode.code == code,
        models.OAuth2AuthCode.client_id == client_id,
        models.OAuth2AuthCode.used == False
    ).first()
    
    if not db_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code"
        )
    
    # Check if code is expired
    if datetime.utcnow() > db_code.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code expired"
        )
    
    # Verify redirect URI matches
    if db_code.redirect_uri != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redirect URI mismatch"
        )
    
    # Mark code as used
    db_code.used = True
    db.commit()
    
    # Get user info
    user = db.query(models.User).filter(models.User.id == db_code.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Create access token
    scopes = db_code.scope.split() if db_code.scope else []
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "scopes": scopes},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Create refresh token
    refresh_token = generate_refresh_token()
    refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store token in database
    db_token = models.OAuth2Token(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        user_id=user.id,
        scope=db_code.scope,
        expires_at=refresh_expires_at
    )
    
    db.add(db_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "scope": db_code.scope
    }


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    db: Session
) -> dict:
    """Refresh an access token using refresh token"""
    # Find the token
    db_token = db.query(models.OAuth2Token).filter(
        models.OAuth2Token.refresh_token == refresh_token,
        models.OAuth2Token.client_id == client_id
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token is expired
    if datetime.utcnow() > db_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token expired"
        )
    
    # Get user info
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Create new access token
    scopes = db_token.scope.split() if db_token.scope else []
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "scopes": scopes},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Update token in database
    db_token.access_token = new_access_token
    db.commit()
    
    return {
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "scope": db_token.scope
    }

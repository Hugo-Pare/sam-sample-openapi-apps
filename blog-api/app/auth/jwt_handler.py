from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext

# Secret key for JWT - in production, use environment variable
SECRET_KEY = "your-secret-key-keep-this-safe-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_key(key: str) -> str:
    """Hash an API key or private key for storage"""
    return pwd_context.hash(key)


def verify_key(plain_key: str, hashed_key: str) -> bool:
    """Verify a key against its hash"""
    return pwd_context.verify(plain_key, hashed_key)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_service_account_token(email: str, scopes: List[str]) -> str:
    """Create a JWT token for a service account"""
    token_data = {
        "sub": email,
        "scopes": scopes,
        "type": "service_account"
    }
    return create_access_token(token_data)

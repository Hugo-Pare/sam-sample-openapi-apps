from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List


# Post Schemas
class PostBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    author: str = Field(..., max_length=100)
    is_published: bool = False


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    is_published: Optional[bool] = None


class Post(PostBase):
    id: int
    published_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Comment Schemas
class CommentBase(BaseModel):
    content: str
    author_name: str = Field(..., max_length=100)


class CommentCreate(CommentBase):
    post_id: int


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=100)


class Comment(CommentBase):
    id: int
    post_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API Key Schemas
class APIKeyInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Service Account Schemas
class ServiceAccountJSON(BaseModel):
    """Schema for service account JSON file (Google-style)"""
    type: str = Field(..., pattern="^service_account$")
    project_id: str
    private_key_id: Optional[str] = None
    private_key: str
    client_email: EmailStr
    client_id: Optional[str] = None
    auth_uri: Optional[str] = None
    token_uri: Optional[str] = None
    auth_provider_x509_cert_url: Optional[str] = None
    client_x509_cert_url: Optional[str] = None
    universe_domain: Optional[str] = None
    scopes: List[str] = Field(..., min_items=1)
    
    # Support legacy format with 'email' field
    email: Optional[EmailStr] = None
    
    @property
    def service_account_email(self) -> str:
        """Get the service account email from either client_email or email field"""
        return self.client_email or self.email


class ServiceAccountInfo(BaseModel):
    id: int
    email: str
    project_id: str
    scopes: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Authentication Token Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour in seconds
    scopes: List[str]


class TokenData(BaseModel):
    email: Optional[str] = None
    scopes: List[str] = []

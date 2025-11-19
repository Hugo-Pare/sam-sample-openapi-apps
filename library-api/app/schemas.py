from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional, List
from app.models import ScopeEnum


# API Key schemas
class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: ScopeEnum = ScopeEnum.READ


class APIKeyInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]
    scope: ScopeEnum
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyResponse(APIKeyInfo):
    key: Optional[str] = None  # Only included when creating new key


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    member_since: datetime
    
    class Config:
        from_attributes = True


# Token schemas for JWT
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: List[str] = []


# OAuth2 schemas
class OAuth2ClientCreate(BaseModel):
    client_name: str
    redirect_uris: List[str]


class OAuth2Client(BaseModel):
    id: int
    client_id: str
    client_name: str
    redirect_uris: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class OAuth2ClientResponse(OAuth2Client):
    client_secret: Optional[str] = None  # Only shown once on creation


class OAuth2AuthorizeRequest(BaseModel):
    response_type: str = "code"
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None


class OAuth2TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: str
    refresh_token: Optional[str] = None


class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# Author schemas
class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None
    birth_year: Optional[int] = None
    nationality: Optional[str] = None


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    birth_year: Optional[int] = None
    nationality: Optional[str] = None


class Author(AuthorBase):
    id: int
    
    class Config:
        from_attributes = True


# Book schemas
class BookBase(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=13)
    title: str
    description: Optional[str] = None
    author_id: int
    genre: Optional[str] = None
    published_year: Optional[int] = None
    total_copies: int = 1
    available_copies: int = 1


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    published_year: Optional[int] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None


class Book(BookBase):
    id: int
    author: Author
    
    class Config:
        from_attributes = True


# Loan schemas
class LoanBase(BaseModel):
    book_id: int
    due_date: date


class LoanCreate(LoanBase):
    pass


class LoanUpdate(BaseModel):
    due_date: Optional[date] = None
    return_date: Optional[date] = None
    is_returned: Optional[bool] = None


class Loan(LoanBase):
    id: int
    user_id: int
    loan_date: date
    return_date: Optional[date]
    is_returned: bool
    book: Book
    
    class Config:
        from_attributes = True


# Login schemas
class LoginRequest(BaseModel):
    username: str
    password: str

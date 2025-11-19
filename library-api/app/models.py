from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ScopeEnum(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# API Key model for API key authentication
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    key_hash = Column(String(255), unique=True, nullable=False)
    scope = Column(SQLEnum(ScopeEnum), nullable=False, default=ScopeEnum.READ)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# User/Member model for Basic Auth and OAuth2
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    member_since = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    loans = relationship("Loan", back_populates="user")


# OAuth2 Client model
class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    client_name = Column(String(100), nullable=False)
    redirect_uris = Column(Text, nullable=False)  # JSON array stored as text
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth2 Authorization Code model
class OAuth2AuthCode(Base):
    __tablename__ = "oauth2_auth_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth2 Access Token model
class OAuth2Token(Base):
    __tablename__ = "oauth2_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True, index=True)
    client_id = Column(String(100), ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Author model
class Author(Base):
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    bio = Column(Text)
    birth_year = Column(Integer)
    nationality = Column(String(50))
    
    # Relationships
    books = relationship("Book", back_populates="author")


# Book model
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(13), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    genre = Column(String(50))
    published_year = Column(Integer)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    # Relationships
    author = relationship("Author", back_populates="books")
    loans = relationship("Loan", back_populates="book")


# Loan model
class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loan_date = Column(Date, nullable=False, default=datetime.utcnow)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    is_returned = Column(Boolean, default=False)
    
    # Relationships
    book = relationship("Book", back_populates="loans")
    user = relationship("User", back_populates="loans")

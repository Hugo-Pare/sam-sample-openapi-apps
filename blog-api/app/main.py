from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from app.database import engine, get_db, Base
from app import models, schemas
from app.auth.jwt_handler import hash_key, create_service_account_token
from app.auth.api_key import get_api_key
from app.auth.service_account import (
    get_service_account_from_token,
    require_scopes,
    verify_service_account_credentials
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Blog API",
    description="A blog API with mixed authentication: public endpoints, API key auth, and service account auth",
    version="1.0.0"
)

# Sample data
SAMPLE_POSTS = [
    {"title": "Getting Started with FastAPI", "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+...", "author": "John Doe", "is_published": True},
    {"title": "Introduction to PostgreSQL", "content": "PostgreSQL is a powerful, open source object-relational database system...", "author": "Jane Smith", "is_published": True},
    {"title": "Understanding JWT Tokens", "content": "JSON Web Tokens are an open, industry standard RFC 7519 method...", "author": "Bob Wilson", "is_published": True},
    {"title": "Draft: Upcoming Features", "content": "We're working on some exciting new features...", "author": "Admin", "is_published": False},
    {"title": "Best Practices for API Design", "content": "When designing APIs, consider these best practices...", "author": "Alice Johnson", "is_published": True},
]

SAMPLE_COMMENTS = [
    {"post_index": 0, "content": "Great article! Very helpful.", "author_name": "Reader1"},
    {"post_index": 0, "content": "Thanks for sharing this.", "author_name": "Reader2"},
    {"post_index": 1, "content": "I love PostgreSQL!", "author_name": "DBFan"},
    {"post_index": 1, "content": "Very informative post.", "author_name": "Learner"},
    {"post_index": 2, "content": "JWT is awesome for authentication.", "author_name": "DevGuy"},
    {"post_index": 2, "content": "Clear explanation, thanks!", "author_name": "Student"},
    {"post_index": 4, "content": "Excellent best practices!", "author_name": "APIDesigner"},
]

SAMPLE_API_KEYS = [
    {"name": "Comment API Key", "description": "For posting and managing comments", "key": "comment-key-12345"},
    {"name": "Reader API Key", "description": "Read-only access", "key": "reader-key-12345"},
]

# Load service account private keys from files
def load_service_account_key(filename):
    """Load private key from file"""
    key_path = os.path.join(os.path.dirname(__file__), "..", "service-accounts", filename)
    with open(key_path, 'r') as f:
        return f.read()

SAMPLE_SERVICE_ACCOUNTS = [
    {
        "client_email": "admin@blog-api-project.iam.gserviceaccount.com",
        "project_id": "blog-api-project",
        "private_key": load_service_account_key("admin-private-key.pem"),
        "scopes": ["posts.admin", "comments.admin", "admin.manage"]
    },
    {
        "client_email": "moderator@blog-api-project.iam.gserviceaccount.com",
        "project_id": "blog-api-project",
        "private_key": load_service_account_key("moderator-private-key.pem"),
        "scopes": ["posts.write", "comments.admin"]
    },
]


@app.on_event("startup")
async def startup_event():
    """Load sample data on startup if database is empty"""
    db = next(get_db())
    try:
        existing_posts = db.query(models.Post).count()
        if existing_posts == 0:
            # Create posts
            created_posts = []
            for post_data in SAMPLE_POSTS:
                post = models.Post(**post_data)
                if post.is_published:
                    post.published_date = datetime.utcnow()
                db.add(post)
                db.flush()
                created_posts.append(post)
            
            db.commit()
            
            # Create comments
            for comment_data in SAMPLE_COMMENTS:
                post_index = comment_data.pop("post_index")
                if post_index < len(created_posts):
                    comment = models.Comment(
                        post_id=created_posts[post_index].id,
                        content=comment_data["content"],
                        author_name=comment_data["author_name"]
                    )
                    db.add(comment)
            
            db.commit()
            
            # Create API keys
            for key_data in SAMPLE_API_KEYS:
                plain_key = key_data["key"]
                api_key = models.APIKey(
                    name=key_data["name"],
                    description=key_data["description"],
                    key_hash=hash_key(plain_key)
                )
                db.add(api_key)
            
            db.commit()
            
            # Create service accounts
            for sa_data in SAMPLE_SERVICE_ACCOUNTS:
                private_key = sa_data["private_key"]
                service_account = models.ServiceAccount(
                    email=sa_data["client_email"],
                    project_id=sa_data["project_id"],
                    private_key_hash=hash_key(private_key),
                    scopes=sa_data["scopes"]
                )
                db.add(service_account)
            
            db.commit()
            
            print("\n" + "="*60)
            print("SAMPLE DATA LOADED")
            print("="*60)
            print("\n📝 API Keys (use in X-API-Key header):")
            print("  comment-key-12345")
            print("  reader-key-12345")
            print("\n🔐 Service Accounts (see service-accounts/ folder for JSON files)")
            print("  admin@blog-api-project.iam.gserviceaccount.com")
            print("  moderator@blog-api-project.iam.gserviceaccount.com")
            print("\n" + "="*60 + "\n")
            
    finally:
        db.close()


# PUBLIC ENDPOINTS (No authentication required)

@app.get("/", tags=["General"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Blog API with Mixed Authentication",
        "version": "1.0.0",
        "authentication": {
            "public": "No auth required for GET /posts",
            "api_key": "X-API-Key header for comments",
            "service_account": "Bearer token for admin operations"
        },
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/posts", response_model=List[schemas.Post], tags=["Posts (Public)"])
def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all published posts (public, no auth required)"""
    posts = db.query(models.Post).filter(
        models.Post.is_published == True
    ).offset(skip).limit(limit).all()
    return posts


@app.get("/posts/{post_id}", response_model=schemas.Post, tags=["Posts (Public)"])
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific published post (public, no auth required)"""
    post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.is_published == True
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


# API KEY AUTHENTICATED ENDPOINTS (Comments)

@app.get("/posts/{post_id}/comments", response_model=List[schemas.Comment], tags=["Comments (API Key)"])
def get_post_comments(
    post_id: int,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(get_api_key)
):
    """Get comments for a post (requires API key)"""
    # Verify post exists
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = db.query(models.Comment).filter(
        models.Comment.post_id == post_id
    ).all()
    return comments


@app.post("/comments", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED, tags=["Comments (API Key)"])
def create_comment(
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(get_api_key)
):
    """Create a comment (requires API key)"""
    # Verify post exists
    post = db.query(models.Post).filter(models.Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_comment = models.Comment(**comment.dict())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@app.put("/comments/{comment_id}", response_model=schemas.Comment, tags=["Comments (API Key)"])
def update_comment(
    comment_id: int,
    comment: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(get_api_key)
):
    """Update a comment (requires API key)"""
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    update_data = comment.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_comment, field, value)
    
    db.commit()
    db.refresh(db_comment)
    return db_comment


@app.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Comments (API Key)"])
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(get_api_key)
):
    """Delete a comment (requires API key)"""
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(db_comment)
    db.commit()
    return None


# SERVICE ACCOUNT AUTHENTICATED ENDPOINTS (Admin operations)

@app.post("/auth/token", response_model=schemas.TokenResponse, tags=["Authentication"])
def create_token(
    sa_json: schemas.ServiceAccountJSON,
    db: Session = Depends(get_db)
):
    """
    Exchange service account JSON for JWT token (public endpoint).
    Use the token as Bearer token for admin endpoints.
    Accepts standard Google service account JSON format.
    """
    # Get email from either client_email or email field
    email = sa_json.client_email or sa_json.email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service account JSON must include 'client_email' or 'email' field"
        )
    
    # Verify service account credentials
    service_account = verify_service_account_credentials(
        email,
        sa_json.private_key,
        db
    )
    
    # Verify requested scopes are allowed for this service account
    for scope in sa_json.scopes:
        if scope not in service_account.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{scope}' not allowed for this service account"
            )
    
    # Create JWT token with the requested scopes
    token = create_service_account_token(service_account.email, sa_json.scopes)
    
    return schemas.TokenResponse(
        access_token=token,
        scopes=sa_json.scopes
    )


@app.post("/posts", response_model=schemas.Post, status_code=status.HTTP_201_CREATED, tags=["Posts (Service Account)"])
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("posts.write", "posts.admin"))
):
    """Create a post (requires service account with posts.write or posts.admin scope)"""
    db_post = models.Post(**post.dict())
    if db_post.is_published:
        db_post.published_date = datetime.utcnow()
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.put("/posts/{post_id}", response_model=schemas.Post, tags=["Posts (Service Account)"])
def update_post(
    post_id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("posts.write", "posts.admin"))
):
    """Update a post (requires service account with posts.write or posts.admin scope)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    update_data = post.dict(exclude_unset=True)
    
    # Update published_date if changing to published
    if "is_published" in update_data and update_data["is_published"] and not db_post.is_published:
        db_post.published_date = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_post, field, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Posts (Service Account)"])
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("posts.admin"))
):
    """Delete a post (requires service account with posts.admin scope)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(db_post)
    db.commit()
    return None


@app.delete("/admin/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin (Service Account)"])
def admin_delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("comments.admin"))
):
    """Delete any comment as admin (requires service account with comments.admin scope)"""
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(db_comment)
    db.commit()
    return None


@app.get("/admin/service-accounts", response_model=List[schemas.ServiceAccountInfo], tags=["Admin (Service Account)"])
def list_service_accounts(
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("admin.manage"))
):
    """List all service accounts (requires service account with admin.manage scope)"""
    service_accounts = db.query(models.ServiceAccount).all()
    return service_accounts


@app.get("/admin/api-keys", response_model=List[schemas.APIKeyInfo], tags=["Admin (Service Account)"])
def list_api_keys(
    db: Session = Depends(get_db),
    token_data: schemas.TokenData = Depends(require_scopes("admin.manage"))
):
    """List all API keys (requires service account with admin.manage scope)"""
    api_keys = db.query(models.APIKey).all()
    return api_keys


# Run with: uvicorn app.main:app --reload
# Default port is 8002, or set PORT environment variable
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

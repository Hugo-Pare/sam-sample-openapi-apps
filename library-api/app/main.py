from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from contextlib import asynccontextmanager
import os

from app.database import engine, get_db, Base
from app import models, schemas
from app.models import ScopeEnum
from app.auth.api_key import require_scope, hash_api_key
from app.auth.basic_auth import (
    get_current_active_user,
    get_current_admin_user,
    hash_password,
    verify_password
)
from app.auth.jwt_handler import (
    create_access_token,
    get_current_active_user_jwt
)
from app.auth.oauth2_server import (
    create_oauth2_client,
    validate_client,
    validate_redirect_uri,
    create_authorization_code,
    exchange_code_for_token,
    refresh_access_token
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Sample data (defined before lifespan function)
SAMPLE_AUTHORS = [
    {"name": "George Orwell", "bio": "English novelist and essayist", "birth_year": 1903, "nationality": "British"},
    {"name": "Jane Austen", "bio": "English novelist known for romantic fiction", "birth_year": 1775, "nationality": "British"},
    {"name": "Mark Twain", "bio": "American writer and humorist", "birth_year": 1835, "nationality": "American"},
    {"name": "Agatha Christie", "bio": "English writer known for detective novels", "birth_year": 1890, "nationality": "British"},
    {"name": "Ernest Hemingway", "bio": "American novelist and short-story writer", "birth_year": 1899, "nationality": "American"},
]

SAMPLE_BOOKS = [
    {"isbn": "9780451524935", "title": "1984", "description": "Dystopian social science fiction novel", "author_name": "George Orwell", "genre": "Fiction", "published_year": 1949, "total_copies": 5, "available_copies": 3},
    {"isbn": "9780141439518", "title": "Pride and Prejudice", "description": "Romantic novel of manners", "author_name": "Jane Austen", "genre": "Romance", "published_year": 1813, "total_copies": 4, "available_copies": 2},
    {"isbn": "9780486280615", "title": "The Adventures of Tom Sawyer", "description": "Novel about a boy growing up along the Mississippi River", "author_name": "Mark Twain", "genre": "Adventure", "published_year": 1876, "total_copies": 3, "available_copies": 3},
    {"isbn": "9780062073488", "title": "Murder on the Orient Express", "description": "Detective novel featuring Hercule Poirot", "author_name": "Agatha Christie", "genre": "Mystery", "published_year": 1934, "total_copies": 4, "available_copies": 1},
    {"isbn": "9780684801223", "title": "The Old Man and the Sea", "description": "Short novel about an aging fisherman", "author_name": "Ernest Hemingway", "genre": "Fiction", "published_year": 1952, "total_copies": 3, "available_copies": 2},
]

SAMPLE_USERS = [
    {"username": "john_doe", "email": "john@example.com", "password": "password123", "full_name": "John Doe", "is_admin": False},
    {"username": "jane_smith", "email": "jane@example.com", "password": "password123", "full_name": "Jane Smith", "is_admin": False},
    {"username": "admin", "email": "admin@example.com", "password": "admin123", "full_name": "Library Admin", "is_admin": True},
]

SAMPLE_API_KEYS = [
    {"name": "Public Read Key", "description": "For public read access", "key": "library-read-key-123", "scope": ScopeEnum.READ},
    {"name": "Application Write Key", "description": "For application write access", "key": "library-write-key-456", "scope": ScopeEnum.WRITE},
    {"name": "Admin Master Key", "description": "Full administrative access", "key": "library-admin-key-789", "scope": ScopeEnum.ADMIN},
]

# Lifespan function to load sample data
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load sample data
    try:
        db = next(get_db())
        existing_authors = db.query(models.Author).count()
        if existing_authors == 0:
            # Create authors
            author_map = {}
            for author_data in SAMPLE_AUTHORS:
                author = models.Author(**author_data)
                db.add(author)
                db.flush()
                author_map[author_data["name"]] = author.id

            db.commit()

            # Create books
            for book_data in SAMPLE_BOOKS:
                author_name = book_data.pop("author_name")
                author_id = author_map.get(author_name)
                if author_id:
                    book = models.Book(**book_data, author_id=author_id)
                    db.add(book)

            db.commit()

            # Create users
            for user_data in SAMPLE_USERS:
                password = user_data.pop("password")
                user = models.User(**user_data, hashed_password=hash_password(password))
                db.add(user)

            db.commit()

            # Create API keys
            for key_data in SAMPLE_API_KEYS:
                plain_key = key_data.pop("key")
                api_key = models.APIKey(**key_data, key_hash=hash_api_key(plain_key))
                db.add(api_key)

            db.commit()

            print("\n" + "="*80)
            print("SAMPLE DATA LOADED - AUTHENTICATION CREDENTIALS")
            print("="*80)
            print("\n📝 API Keys (X-API-Key header):")
            print("  Read:  library-read-key-123")
            print("  Write: library-write-key-456")
            print("  Admin: library-admin-key-789")
            print("\n👤 User Accounts (Basic Auth or JWT):")
            print("  Username: john_doe  | Password: password123")
            print("  Username: jane_smith | Password: password123")
            print("  Username: admin      | Password: admin123 (admin user)")
            print("\n" + "="*80 + "\n")

        db.close()
    except Exception as e:
        print(f"ERROR in startup: {e}")
        import traceback
        traceback.print_exc()

    yield  # Application runs here
    # Shutdown: cleanup if needed

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Library Management API",
    description="A comprehensive library API demonstrating multiple authentication methods: API Key, Basic Auth, JWT Bearer, and OAuth2",
    version="1.0.0",
    lifespan=lifespan
)

# ========================================
# PUBLIC ENDPOINTS (No Authentication)
# ========================================

@app.get("/", tags=["General"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Library Management API",
        "version": "1.0.0",
        "authentication_methods": {
            "none": "Public endpoints (GET /books, /authors)",
            "api_key": "X-API-Key header with scopes: read, write, admin",
            "basic": "HTTP Basic Auth (username:password)",
            "bearer": "JWT Bearer token (get from /auth/login)",
            "oauth2": "OAuth2 authorization code flow (/oauth/*)"
        },
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/books", response_model=List[schemas.Book], tags=["Books (Public)"])
def get_books_public(
    skip: int = 0,
    limit: int = 100,
    genre: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all books (public, no authentication required)"""
    query = db.query(models.Book)
    if genre:
        query = query.filter(models.Book.genre == genre)
    books = query.offset(skip).limit(limit).all()
    return books


@app.get("/books/{book_id}", response_model=schemas.Book, tags=["Books (Public)"])
def get_book_public(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book (public, no authentication required)"""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.get("/authors", response_model=List[schemas.Author], tags=["Authors (Public)"])
def get_authors_public(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all authors (public, no authentication required)"""
    authors = db.query(models.Author).offset(skip).limit(limit).all()
    return authors


# ========================================
# API KEY AUTHENTICATED ENDPOINTS
# ========================================

@app.post("/books", response_model=schemas.Book, status_code=status.HTTP_201_CREATED, tags=["Books (API Key)"])
def create_book_apikey(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(require_scope(ScopeEnum.WRITE, ScopeEnum.ADMIN))
):
    """Create a book (requires API key with write or admin scope)"""
    # Check if ISBN already exists
    existing = db.query(models.Book).filter(models.Book.isbn == book.isbn).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Books (API Key)"])
def delete_book_apikey(
    book_id: int,
    db: Session = Depends(get_db),
    api_key: models.APIKey = Depends(require_scope(ScopeEnum.ADMIN))
):
    """Delete a book (requires API key with admin scope)"""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return None


# ========================================
# BASIC AUTH ENDPOINTS
# ========================================

@app.get("/me", response_model=schemas.User, tags=["Users (Basic Auth)"])
def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current user information (requires Basic Auth)"""
    return current_user


@app.get("/my-loans", response_model=List[schemas.Loan], tags=["Loans (Basic Auth)"])
def get_my_loans(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's loans (requires Basic Auth)"""
    loans = db.query(models.Loan).filter(
        models.Loan.user_id == current_user.id
    ).all()
    return loans


@app.post("/loans", response_model=schemas.Loan, status_code=status.HTTP_201_CREATED, tags=["Loans (Basic Auth)"])
def create_loan(
    loan: schemas.LoanCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Borrow a book (requires Basic Auth)"""
    # Check if book exists and is available
    book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No copies available")
    
    # Create loan
    db_loan = models.Loan(
        book_id=loan.book_id,
        user_id=current_user.id,
        loan_date=date.today(),
        due_date=loan.due_date,
        is_returned=False
    )
    
    # Update available copies
    book.available_copies -= 1
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


# ========================================
# JWT/BEARER TOKEN ENDPOINTS
# ========================================

@app.post("/auth/login", response_model=schemas.Token, tags=["Authentication (JWT)"])
def login_for_jwt(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """Login with username/password to get JWT token"""
    user = db.query(models.User).filter(
        models.User.username == login_data.username
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "scopes": []}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/jwt/me", response_model=schemas.User, tags=["Users (JWT Bearer)"])
def get_current_user_jwt_endpoint(
    current_user: models.User = Depends(get_current_active_user_jwt)
):
    """Get current user information (requires JWT Bearer token)"""
    return current_user


@app.get("/jwt/my-loans", response_model=List[schemas.Loan], tags=["Loans (JWT Bearer)"])
def get_my_loans_jwt(
    current_user: models.User = Depends(get_current_active_user_jwt),
    db: Session = Depends(get_db)
):
    """Get current user's loans (requires JWT Bearer token)"""
    loans = db.query(models.Loan).filter(
        models.Loan.user_id == current_user.id
    ).all()
    return loans


# ========================================
# OAUTH2 ENDPOINTS
# ========================================

@app.post("/oauth/clients", response_model=schemas.OAuth2ClientResponse, tags=["OAuth2"])
def create_oauth_client(
    client_data: schemas.OAuth2ClientCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Create OAuth2 client (requires admin Basic Auth)"""
    client, client_secret = create_oauth2_client(
        client_data.client_name,
        client_data.redirect_uris,
        db
    )
    
    response = schemas.OAuth2ClientResponse.from_orm(client)
    response.client_secret = client_secret
    return response


@app.get("/oauth/authorize", response_class=HTMLResponse, tags=["OAuth2"])
async def oauth_authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """OAuth2 authorization endpoint (shows login form)"""
    # Validate client
    client = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_id,
        models.OAuth2Client.is_active
    ).first()
    
    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    if not validate_redirect_uri(client, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # Simple HTML login form
    html_content = f"""
    <html>
        <head><title>Authorize Application</title></head>
        <body style="font-family: Arial; max-width: 500px; margin: 50px auto; padding: 20px;">
            <h2>Authorize {client.client_name}</h2>
            <p>This application wants to access your library account.</p>
            <form method="post" action="/oauth/authorize">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <input type="hidden" name="state" value="{state or ''}">
                <div style="margin: 10px 0;">
                    <label>Username:</label><br>
                    <input type="text" name="username" required style="width: 100%; padding: 5px;">
                </div>
                <div style="margin: 10px 0;">
                    <label>Password:</label><br>
                    <input type="password" name="password" required style="width: 100%; padding: 5px;">
                </div>
                <button type="submit" style="background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                    Authorize
                </button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/oauth/authorize", tags=["OAuth2"])
async def oauth_authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    scope: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Process OAuth2 authorization (handles login)"""
    # Validate user
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create authorization code
    code = create_authorization_code(client_id, user.id, redirect_uri, scope, db)
    
    # Redirect back to client with code
    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"
    
    # Use 303 to force GET method on redirect (prevents "Method Not Allowed" errors)
    return RedirectResponse(url=redirect_url, status_code=303)


@app.post("/oauth/token", response_model=schemas.OAuth2TokenResponse, tags=["OAuth2"])
async def oauth_token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    refresh_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """OAuth2 token endpoint (exchange code for access token)"""
    # Validate client
    validate_client(client_id, client_secret, db)
    
    if grant_type == "authorization_code":
        if not code or not redirect_uri:
            raise HTTPException(status_code=400, detail="code and redirect_uri required")
        
        token_data = exchange_code_for_token(code, client_id, redirect_uri, db)
        return token_data
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token required")
        
        token_data = refresh_access_token(refresh_token, client_id, db)
        return token_data
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant_type")


# Run with: uvicorn app.main:app --reload
# Default port is 8003, or set PORT environment variable
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

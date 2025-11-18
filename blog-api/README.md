# Blog API with Mixed Authentication

A sample blog REST API demonstrating three different authentication methods: public endpoints, API key authentication, and Google-style service account authentication with JWT tokens.

## Features

- ✅ **Mixed Authentication** - Three authentication layers
  - Public endpoints (no auth)
  - API key authentication (X-API-Key header)
  - Service account authentication (Bearer JWT tokens)
- ✅ **Scope-based permissions** for service accounts
- ✅ **Google-style service account JSON** files
- ✅ **JWT tokens** with 1-hour expiration
- ✅ **Full CRUD operations** for posts and comments
- ✅ **Automatic OpenAPI 3.0** documentation
- ✅ **PostgreSQL database** with SQLAlchemy ORM
- ✅ **Sample data preloaded** on startup

## Prerequisites

- Python 3.9+
- Podman (or Docker)
- pip

## Quick Start

### 1. Start the PostgreSQL Database

```bash
podman run -d --name blog-db \
  -e POSTGRES_USER=bloguser \
  -e POSTGRES_PASSWORD=blogpass \
  -e POSTGRES_DB=blog \
  -p 5435:5432 \
  docker.io/library/postgres:15-alpine
```

This starts PostgreSQL on port **5435** (to avoid conflicts with other databases).

### 2. Create Virtual Environment and Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the API Server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

The server will start on **port 8002** by default.

**Custom port:**
```bash
uvicorn app.main:app --reload --port 3000
```

Or set via environment variable:
```bash
PORT=3000 uvicorn app.main:app --reload
```

### 4. Access the API

- **API Base URL**: http://localhost:8002
- **Interactive Documentation (Swagger UI)**: http://localhost:8002/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8002/redoc
- **OpenAPI Specification**: http://localhost:8002/openapi.json

## Authentication Methods

This API uses three different authentication methods depending on the endpoint:

### 1. Public Endpoints (No Authentication)

These endpoints are accessible without any authentication:
- `GET /` - API information
- `GET /health` - Health check
- `GET /posts` - List all published posts
- `GET /posts/{id}` - Get a specific published post

**Example:**
```bash
curl http://localhost:8002/posts
```

### 2. API Key Authentication

Comment-related endpoints require an API key in the `X-API-Key` header.

**Hardcoded API Keys:**
- `comment-key-12345` - For managing comments
- `reader-key-12345` - Alternative key

**Endpoints:**
- `GET /posts/{post_id}/comments` - List comments on a post
- `POST /comments` - Create a comment
- `PUT /comments/{id}` - Update a comment
- `DELETE /comments/{id}` - Delete a comment

**Example:**
```bash
# Get comments for a post
curl -H "X-API-Key: comment-key-12345" \
  http://localhost:8002/posts/1/comments

# Create a comment
curl -X POST http://localhost:8002/comments \
  -H "X-API-Key: comment-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "content": "Great post!",
    "author_name": "John Doe"
  }'
```

### 3. Service Account Authentication (Google-Style)

Admin endpoints require a Bearer token obtained from a service account JSON file.

#### Step 1: Get a Token

Use a service account JSON file to get a JWT token:

```bash
curl -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d @service-accounts/admin-sa.json
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scopes": ["posts.admin", "comments.admin", "admin.manage"]
}
```

#### Step 2: Use the Token

Include the token as a Bearer token in the Authorization header:

```bash
# Create a post
curl -X POST http://localhost:8002/posts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Blog Post",
    "content": "This is the content...",
    "author": "Admin",
    "is_published": true
  }'
```

## Service Account Scopes

Service accounts can have different permission scopes:

| Scope | Description |
|-------|-------------|
| `posts.read` | Read posts (redundant, posts are public) |
| `posts.write` | Create and update posts |
| `posts.admin` | Full control over posts (includes write + delete) |
| `comments.admin` | Moderate/delete any comments |
| `admin.manage` | Manage service accounts and API keys |

## Sample Service Accounts

Two service account JSON files are provided in the `service-accounts/` folder:

### 1. Admin Service Account
**File:** `service-accounts/admin-sa.json`

```json
{
  "type": "service_account",
  "project_id": "blog-api-project",
  "email": "admin@blog-api-project.iam.gserviceaccount.com",
  "private_key": "admin-private-key-12345",
  "scopes": ["posts.admin", "comments.admin", "admin.manage"]
}
```

**Permissions:** Full administrative access

### 2. Moderator Service Account
**File:** `service-accounts/moderator-sa.json`

```json
{
  "type": "service_account",
  "project_id": "blog-api-project",
  "email": "moderator@blog-api-project.iam.gserviceaccount.com",
  "private_key": "moderator-private-key-12345",
  "scopes": ["posts.write", "comments.admin"]
}
```

**Permissions:** Can create/update posts and moderate comments

## API Endpoints

### Public (No Auth)
- `GET /` - API information
- `GET /health` - Health check
- `GET /posts` - List published posts
- `GET /posts/{id}` - Get a published post

### API Key Required (X-API-Key header)
- `GET /posts/{post_id}/comments` - List comments
- `POST /comments` - Create comment
- `PUT /comments/{id}` - Update comment
- `DELETE /comments/{id}` - Delete comment

### Service Account Required (Bearer token)

**Posts Management:**
- `POST /posts` - Create post (scope: `posts.write` or `posts.admin`)
- `PUT /posts/{id}` - Update post (scope: `posts.write` or `posts.admin`)
- `DELETE /posts/{id}` - Delete post (scope: `posts.admin`)

**Admin Operations:**
- `DELETE /admin/comments/{id}` - Delete any comment (scope: `comments.admin`)
- `GET /admin/service-accounts` - List service accounts (scope: `admin.manage`)
- `GET /admin/api-keys` - List API keys (scope: `admin.manage`)

**Authentication:**
- `POST /auth/token` - Get JWT token from service account JSON (public)

## Example Workflows

### Workflow 1: View Public Blog Posts

```bash
# No authentication required
curl http://localhost:8002/posts
```

### Workflow 2: Add Comments (API Key)

```bash
# Get comments on a post
curl -H "X-API-Key: comment-key-12345" \
  http://localhost:8002/posts/1/comments

# Add a new comment
curl -X POST http://localhost:8002/comments \
  -H "X-API-Key: comment-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "content": "Interesting perspective!",
    "author_name": "Jane Doe"
  }'
```

### Workflow 3: Manage Posts (Service Account)

```bash
# Step 1: Get a token
TOKEN=$(curl -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d @service-accounts/admin-sa.json | jq -r '.access_token')

# Step 2: Create a new post
curl -X POST http://localhost:8002/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Advanced FastAPI Techniques",
    "content": "In this post, we explore advanced FastAPI features...",
    "author": "Tech Blogger",
    "is_published": true
  }'

# Step 3: Update a post
curl -X PUT http://localhost:8002/posts/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_published": false
  }'

# Step 4: Delete a post (requires posts.admin scope)
curl -X DELETE http://localhost:8002/posts/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 4: Moderate Comments (Service Account)

```bash
# Get token with moderator service account
TOKEN=$(curl -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d @service-accounts/moderator-sa.json | jq -r '.access_token')

# Delete a comment as moderator
curl -X DELETE http://localhost:8002/admin/comments/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Sample Data

The API automatically loads sample data on first startup:

- **5 Blog Posts** (4 published, 1 draft)
- **7 Comments** across different posts
- **2 API Keys** for comment management
- **2 Service Accounts** (admin and moderator)

## Testing with Swagger UI

1. Navigate to http://localhost:8002/docs

**For API Key endpoints:**
2. Click the **Authorize** button (lock icon)
3. Enter `comment-key-12345` in the `X-API-Key` field
4. Click **Authorize**

**For Service Account endpoints:**
2. First, get a token using `/auth/token` endpoint with a service account JSON
3. Click the **Authorize** button next to HTTPBearer
4. Enter `Bearer YOUR_TOKEN_HERE`
5. Click **Authorize**

## Database Configuration

The database connection is hardcoded in `app/database.py`:

```
postgresql://bloguser:blogpass@localhost:5435/blog
```

Note: Port **5435** is used to avoid conflicts with other PostgreSQL instances.

## Stopping the Application

Stop the API server: Press `Ctrl+C`

**Stop the PostgreSQL container:**
```bash
podman stop blog-db
podman rm blog-db
```

**To remove all data:**
```bash
podman stop blog-db
podman rm blog-db
podman volume prune
```

## Project Structure

```
blog-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   └── auth/
│       ├── __init__.py
│       ├── jwt_handler.py   # JWT token creation/validation
│       ├── api_key.py       # API key authentication
│       └── service_account.py  # Service account authentication
├── service-accounts/
│   ├── admin-sa.json        # Admin service account
│   └── moderator-sa.json    # Moderator service account
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Technologies Used

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **PostgreSQL** - Relational database
- **python-jose** - JWT token handling
- **Passlib** - Password/key hashing library
- **Uvicorn** - ASGI server
- **Podman/Docker** - Containerization

## Security Notes

- API keys are hashed using bcrypt before storage
- Service account private keys are hashed before storage
- JWT tokens expire after 1 hour
- Tokens include scope validation
- Service accounts can only request scopes they're authorized for

## License

This is a sample project for demonstration purposes.

# Library Management API

A comprehensive REST API demonstrating **multiple authentication methods** for learning and development purposes. This API manages books, authors, users, and library loans while showcasing various authentication strategies.

## 🔐 Authentication Methods

This API implements **4 different authentication methods** (excluding service accounts):

1. **No Authentication** - Public endpoints
2. **API Key** - Header-based with scopes (read/write/admin)
3. **HTTP Basic Auth** - Username and password
4. **JWT Bearer Token** - Token-based authentication
5. **OAuth2** - Authorization code flow with custom server

## 🚀 Quick Start

### 1. Start the Database

```bash
podman run -d --name library-db --replace \
  -e POSTGRES_USER=libraryuser \
  -e POSTGRES_PASSWORD=librarypass \
  -e POSTGRES_DB=library \
  -p 5436:5432 \
  docker.io/library/postgres:15-alpine
```

This starts PostgreSQL on port **5436** (to avoid conflicts with other databases).

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.main:app --reload --port 8003
```

The API will be available at: http://localhost:8003

- **Interactive API Docs**: http://localhost:8003/docs
- **OpenAPI Spec**: http://localhost:8003/openapi.json

## 📝 Sample Credentials

The API loads sample data on first startup:

### API Keys (X-API-Key header)

```
Read Scope:  library-read-key-123
Write Scope: library-write-key-456
Admin Scope: library-admin-key-789
```

### User Accounts (for Basic Auth & JWT)

```
Username: john_doe   | Password: password123
Username: jane_smith | Password: password123
Username: admin      | Password: admin123 (admin user)
```

## 🔑 Authentication Examples

### 1. No Authentication (Public Endpoints)

Browse books and authors without authentication:

```bash
# Get all books
curl http://localhost:8003/books

# Get specific book
curl http://localhost:8003/books/1

# Get all authors
curl http://localhost:8003/authors
```

### 2. API Key Authentication

Use the `X-API-Key` header with different scopes:

```bash
# Read books (read scope)
curl -H "X-API-Key: library-read-key-123" \
  http://localhost:8003/books

# Create a book (write or admin scope required)
curl -X POST http://localhost:8003/books \
  -H "X-API-Key: library-write-key-456" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "9781234567890",
    "title": "New Book",
    "description": "A great book",
    "author_id": 1,
    "genre": "Fiction",
    "published_year": 2024,
    "total_copies": 5,
    "available_copies": 5
  }'

# Delete a book (admin scope required)
curl -X DELETE http://localhost:8003/books/1 \
  -H "X-API-Key: library-admin-key-789"
```

### 3. HTTP Basic Authentication

Use username:password for member-specific operations:

```bash
# Get current user info
curl -u john_doe:password123 \
  http://localhost:8003/me

# Get my loans
curl -u john_doe:password123 \
  http://localhost:8003/my-loans

# Borrow a book
curl -X POST http://localhost:8003/loans \
  -u john_doe:password123 \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "due_date": "2024-12-31"
  }'
```

### 4. JWT Bearer Token

First, login to get a token, then use it:

```bash
# Login to get JWT token
TOKEN=$(curl -X POST http://localhost:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "password123"
  }' | jq -r '.access_token')

# Use the token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8003/jwt/me

# Get my loans with JWT
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8003/jwt/my-loans
```

### 5. OAuth2 Authorization Code Flow

#### Step 1: Create an OAuth2 Client (requires admin)

```bash
curl -X POST http://localhost:8003/oauth/clients \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "My Library App",
    "redirect_uris": ["http://localhost:3000/callback"]
  }'
```

Save the `client_id` and `client_secret` from the response.

#### Step 2: Authorization Request

Open in browser (replace `CLIENT_ID`):

```
http://localhost:8003/oauth/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=http://localhost:3000/callback&state=random_state
```

Login with username/password, and you'll be redirected with an authorization code.

#### Step 3: Exchange Code for Token

```bash
curl -X POST http://localhost:8003/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTH_CODE" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

#### Step 4: Use Access Token

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8003/jwt/me
```

#### Step 5: Refresh Token (optional)

```bash
curl -X POST http://localhost:8003/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

## 📚 API Endpoints Overview

### Public Endpoints (No Auth)
- `GET /` - API information
- `GET /health` - Health check
- `GET /books` - List all books
- `GET /books/{id}` - Get specific book
- `GET /authors` - List all authors

### API Key Protected
- `POST /books` - Create book (write/admin)
- `DELETE /books/{id}` - Delete book (admin)

### Basic Auth Protected
- `GET /me` - Get current user info
- `GET /my-loans` - Get user's loans
- `POST /loans` - Borrow a book

### JWT Bearer Protected
- `POST /auth/login` - Login to get JWT
- `GET /jwt/me` - Get current user (JWT)
- `GET /jwt/my-loans` - Get loans (JWT)

### OAuth2 Endpoints
- `POST /oauth/clients` - Create OAuth2 client (admin)
- `GET /oauth/authorize` - Authorization endpoint
- `POST /oauth/authorize` - Process authorization
- `POST /oauth/token` - Token endpoint

## 🗄️ Database Schema

### Models
- **User** - Library members with username/password
- **Author** - Book authors
- **Book** - Books with ISBN, copies, etc.
- **Loan** - Book loans by users
- **APIKey** - API keys with scopes
- **OAuth2Client** - OAuth2 registered clients
- **OAuth2AuthCode** - Authorization codes
- **OAuth2Token** - Access/refresh tokens

## 🛠️ Development

### Reset Database

```bash
podman stop library-db
podman rm library-db
podman run -d --name library-db \
  -e POSTGRES_USER=libraryuser \
  -e POSTGRES_PASSWORD=librarypass \
  -e POSTGRES_DB=library \
  -p 5436:5432 \
  docker.io/library/postgres:15-alpine
# Restart the API to reload sample data
```

### View Database

```bash
podman exec -it library-db psql -U libraryuser -d library
```

### Stop the Application

Stop the API server: Press `Ctrl+C`

**Stop and remove the PostgreSQL container:**
```bash
podman stop library-db
podman rm library-db
```

### Run Tests

```bash
pytest  # Add your tests
```

## 📖 Documentation

Visit http://localhost:8003/docs for the interactive Swagger UI documentation.

## 🔒 Security Notes

⚠️ **This is a demo/learning API. DO NOT use in production without:**

1. Changing all secret keys and tokens
2. Using environment variables for sensitive data
3. Implementing proper HTTPS
4. Adding rate limiting
5. Implementing proper password policies
6. Using secure session management
7. Adding CORS protection
8. Implementing proper logging and monitoring

## 📝 License

MIT License - Free to use for learning and development.

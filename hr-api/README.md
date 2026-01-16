# HR Management API

OAuth2-based REST API for managing employees and departments with **RFC 8414 Discovery** and **RFC 7591 Dynamic Client Registration**.

## 🔐 Authentication

This API uses **OAuth2 authorization code flow only**. No API keys or Basic Auth (except for the OAuth2 flow itself).

### Key Features

- **RFC 8414 Discovery**: Programmatically discover OAuth2 endpoints via `/.well-known/oauth-authorization-server`
- **RFC 7591 Dynamic Client Registration**: Self-service client registration via `/oauth/register`
- **Scope-based Authorization**: Fine-grained access control with HR-specific scopes
- **Sensitive Field Protection**: Salary and budget fields require elevated scopes

## 🚀 Quick Start

### 1. Start the Database

Choose either docker-compose or Podman:

**Using docker-compose:**
```bash
docker-compose up -d
```

**Using Podman:**
```bash
podman run -d --name hr-db --replace \
  -e POSTGRES_USER=hruser \
  -e POSTGRES_PASSWORD=hrpass \
  -e POSTGRES_DB=hr \
  -p 5438:5432 \
  docker.io/library/postgres:15-alpine
```

This starts PostgreSQL on port **5438** (to avoid conflicts with other databases).

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.main:app --reload --port 8005
```

The API will be available at: http://localhost:8005

- **Interactive API Docs**: http://localhost:8005/docs
- **OpenAPI Spec**: http://localhost:8005/openapi.json
- **Discovery Endpoint**: http://localhost:8005/.well-known/oauth-authorization-server

## 🔑 OAuth2 Setup Guide

### Step 1: Discover OAuth2 Endpoints

```bash
curl http://localhost:8005/.well-known/oauth-authorization-server
```

This returns RFC 8414 metadata including:
- `authorization_endpoint`
- `token_endpoint`
- `registration_endpoint`
- `scopes_supported`
- `grant_types_supported`

### Step 2: Register an OAuth2 Client

```bash
curl -X POST http://localhost:8005/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["http://localhost:8080/callback"],
    "client_name": "My HR App",
    "scope": "employees:read departments:read"
  }'
```

**Response:**
```json
{
  "client_id": "abc123...",
  "client_secret": "xyz789...",
  "client_id_issued_at": 1705248000,
  "client_secret_expires_at": 0,
  "redirect_uris": ["http://localhost:8080/callback"],
  "client_name": "My HR App",
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "employees:read departments:read",
  "token_endpoint_auth_method": "client_secret_post"
}
```

**⚠️ Important**: Save the `client_secret` - it's only shown once!

### Step 3: Authorization Code Flow

**3a. Direct user to authorization endpoint:**

```
http://localhost:8005/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&scope=employees:read%20departments:read
```

User will see a login form. Test credentials:
- Username: `sarah.johnson`, Password: `password123`
- Username: `michael.chen`, Password: `password123`
- Username: `admin`, Password: `admin123`

**3b. User authorizes, receives authorization code:**

After successful login, redirected to:
```
http://localhost:8080/callback?code=AUTH_CODE_HERE
```

**3c. Exchange code for access token:**

```bash
curl -X POST http://localhost:8005/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTH_CODE_HERE" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "scope": "employees:read departments:read"
}
```

### Step 4: Use Access Token

```bash
curl http://localhost:8005/employees \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 5: Refresh Access Token (Optional)

When the access token expires, use the refresh token:

```bash
curl -X POST http://localhost:8005/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

## 📊 API Endpoints

### Public Endpoints (No Auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/departments` | List departments (basic info only) |

### OAuth2 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/.well-known/oauth-authorization-server` | RFC 8414 discovery |
| POST | `/oauth/register` | RFC 7591 client registration |
| GET | `/oauth/authorize` | Authorization page (shows login form) |
| POST | `/oauth/authorize` | Process authorization |
| POST | `/oauth/token` | Token endpoint (exchange code or refresh) |

### Employee Endpoints (OAuth2 Required)

| Method | Path | Scopes | Description |
|--------|------|--------|-------------|
| GET | `/employees` | `employees:read` | List employees (no salary) |
| GET | `/employees/{id}` | `employees:read` | Get employee details |
| POST | `/employees` | `employees:write` | Create employee |
| PATCH | `/employees/{id}` | `employees:write` | Update employee |
| DELETE | `/employees/{id}` | `employees:write` | Soft delete employee |

**Note**: Salary information requires `employees:read:sensitive` scope.

### Department Endpoints (OAuth2 Required)

| Method | Path | Scopes | Description |
|--------|------|--------|-------------|
| GET | `/departments/{id}` | `departments:read` | Get department details |
| POST | `/departments` | `departments:write` | Create department |
| PATCH | `/departments/{id}` | `departments:write` | Update department |
| DELETE | `/departments/{id}` | `departments:manage` | Soft delete department |
| GET | `/departments/{id}/employees` | `departments:read` + `employees:read` | List dept employees |

**Note**: Budget information requires `departments:manage` scope.

## 🔒 OAuth2 Scopes

| Scope | Description |
|-------|-------------|
| `employees:read` | View employee basic information (no salary) |
| `employees:write` | Create and update employees |
| `employees:read:sensitive` | View salary information |
| `departments:read` | View department information (no budget) |
| `departments:write` | Create and update departments |
| `departments:manage` | Full department access including budget |

## 📝 Sample Data

On first startup, the API loads sample data:

### Departments (5)
- **ENG** - Engineering (San Francisco, CA) - Manager: Sarah Johnson
- **SALES** - Sales (Austin, TX) - Manager: David Kim
- **HR** - Human Resources (New York, NY) - Manager: Emily Rodriguez
- **FIN** - Finance (New York, NY) - Manager: Robert Davis
- **OPS** - Operations (Chicago, IL) - Manager: James Wilson

### Employees (8)
- Sarah Johnson - VP of Engineering
- Michael Chen - Senior Software Engineer
- Emily Rodriguez - HR Manager
- David Kim - Sales Director
- Jennifer White - Senior Accountant
- Robert Davis - Financial Controller
- Lisa Thompson - Software Engineer
- James Wilson - Operations Manager

### Test Users (3)
- **admin** / admin123 (admin privileges)
- **sarah.johnson** / password123
- **michael.chen** / password123

## 🛠️ Development

### Reset Database

```bash
# With docker-compose
docker-compose down -v
docker-compose up -d

# With Podman
podman stop hr-db
podman rm hr-db
podman volume prune
podman run -d --name hr-db --replace \
  -e POSTGRES_USER=hruser \
  -e POSTGRES_PASSWORD=hrpass \
  -e POSTGRES_DB=hr \
  -p 5438:5432 \
  docker.io/library/postgres:15-alpine
```

### View Database

```bash
# With docker-compose
docker exec -it hr-db psql -U hruser -d hr

# With Podman
podman exec -it hr-db psql -U hruser -d hr
```

### Run Tests

```bash
pytest  # If tests are added
```

## 🔧 Configuration

Environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8005` | API server port |
| `DATABASE_URL` | `postgresql://hruser:hrpass@localhost:5438/hr` | Database connection |
| `SECRET_KEY` | ⚠️ Change in production | JWT signing key |

## 🏗️ Architecture

### Technology Stack
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation
- **python-jose** - JWT token handling
- **bcrypt** - Password hashing

### Project Structure
```
hr-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with endpoints
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic validation schemas
│   ├── database.py      # Database configuration
│   ├── oauth2.py        # OAuth2 implementation
│   └── scopes.py        # Scope definitions
├── docker-compose.yml   # PostgreSQL container
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## ⚠️ Security Notes

**This is a demo/learning API - NOT production ready!**

For production use:
1. ✅ Use environment variables for `SECRET_KEY` and `DATABASE_URL`
2. ✅ Enable HTTPS/TLS for all endpoints
3. ✅ Implement rate limiting on `/oauth/register`
4. ✅ Add audit logging for all operations
5. ✅ Implement client approval workflow for registration
6. ✅ Use strong passwords and rotate secrets regularly
7. ✅ Comply with data privacy regulations (GDPR, CCPA, etc.)
8. ✅ Enable database backups and disaster recovery
9. ✅ Implement proper monitoring and alerting

## 📚 Resources

- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 📄 License

This is a sample/educational project. Use at your own risk.

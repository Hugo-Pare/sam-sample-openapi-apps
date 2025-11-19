# E-commerce Product Catalog API

A sample e-commerce REST API with API key authentication and scope-based permissions. Built with FastAPI and PostgreSQL, featuring automatic OpenAPI 3.0 specification generation.

## Features

- ✅ **API Key Authentication** with three permission scopes (read, write, admin)
- ✅ **Scope-based Access Control** - hierarchical permissions system
- ✅ **Full CRUD operations** for products and categories
- ✅ **Nested categories** support
- ✅ **Stock quantity tracking**
- ✅ **Automatic OpenAPI 3.0 documentation** with security schemes
- ✅ **PostgreSQL database** with SQLAlchemy ORM
- ✅ **Sample data preloaded** on startup
- ✅ **Input validation** with Pydantic

## Prerequisites

- Python 3.9+
- Podman (or Docker)
- pip

## Quick Start

### 1. Start the PostgreSQL Database

```bash
podman run -d --name ecommerce-db \
  -e POSTGRES_USER=ecomuser \
  -e POSTGRES_PASSWORD=ecompass \
  -e POSTGRES_DB=ecommerce \
  -p 5434:5432 \
  docker.io/library/postgres:15-alpine
```

This starts PostgreSQL on port **5434** (to avoid conflicts with other databases).

### 2. Create Virtual Environment and Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the API Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate
uvicorn app.main:app --reload --port 8004
```

The API will start on port **8004** by default.

**Custom port:**
```bash
uvicorn app.main:app --reload --port 3000
```

The API uses three hardcoded API keys that are always the same, making testing easy:

```
Read-Only Key (scope: read):
  X-API-Key: read-key-12345

Write Key (scope: write):
  X-API-Key: write-key-12345

Admin Key (scope: admin):
  X-API-Key: admin-key-12345
```

These keys are displayed in the console when the server starts, but they never change.

### 4. Access the API

- **API Base URL**: http://localhost:8004
- **Interactive Documentation (Swagger UI)**: http://localhost:8004/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8004/redoc
- **OpenAPI Specification**: http://localhost:8004/openapi.json

## Authentication

All endpoints (except `/` and `/health`) require API key authentication via the `X-API-Key` header.

### Permission Scopes

The API uses three hierarchical permission scopes:

1. **read** - Can view products and categories (GET requests)
2. **write** - Can read + create/update products and categories (GET, POST, PUT)
3. **admin** - Full access including delete operations and API key management (GET, POST, PUT, DELETE)

Higher scopes inherit lower scope permissions (admin > write > read).

### Using API Keys

Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" http://localhost:8004/products
```

## API Endpoints

### General
- `GET /` - API information (no auth required)
- `GET /health` - Health check (no auth required)

### Categories
- `GET /categories` - List all categories (scope: **read**)
- `GET /categories/{id}` - Get specific category (scope: **read**)
- `POST /categories` - Create category (scope: **write**)
- `PUT /categories/{id}` - Update category (scope: **write**)
- `DELETE /categories/{id}` - Delete category (scope: **admin**)

### Products
- `GET /products` - List all products with optional filters (scope: **read**)
- `GET /products/{id}` - Get specific product (scope: **read**)
- `GET /products/sku/{sku}` - Get product by SKU (scope: **read**)
- `POST /products` - Create product (scope: **write**)
- `PUT /products/{id}` - Update product (scope: **write**)
- `DELETE /products/{id}` - Delete product (scope: **admin**)

### API Key Management
- `GET /api-keys` - List all API keys (scope: **admin**)
- `POST /api-keys` - Generate new API key (scope: **admin**)
- `DELETE /api-keys/{id}` - Revoke API key (scope: **admin**)

## Sample Data

The API automatically loads sample data on first startup:

**10 Categories** including:
- Electronics (with subcategories: Laptops, Smartphones, Tablets)
- Clothing (with subcategories: Men's, Women's)
- Home & Garden
- Books
- Sports & Outdoors

**16 Sample Products** across different categories with realistic prices and stock quantities.

**3 API Keys** with different scopes (shown in console on startup).

## Example Usage

### Using Read Scope

View all products (requires read scope or higher):

```bash
curl -H "X-API-Key: read-key-12345" http://localhost:8004/products
```

Get products by category:

```bash
curl -H "X-API-Key: read-key-12345" http://localhost:8004/products?category_id=2
```

Get a specific product:

```bash
curl -H "X-API-Key: read-key-12345" http://localhost:8004/products/1
```

### Using Write Scope

Create a new product (requires write scope or higher):

```bash
curl -X POST http://localhost:8004/products \
  -H "X-API-Key: write-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "stock_quantity": 50,
    "category_id": 1,
    "sku": "MOUSE-001",
    "is_active": true
  }'
```

Update a product:

```bash
curl -X PUT http://localhost:8004/products/1 \
  -H "X-API-Key: write-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 24.99,
    "stock_quantity": 75
  }'
```

### Using Admin Scope

Delete a product (requires admin scope):

```bash
curl -X DELETE http://localhost:8004/products/1 \
  -H "X-API-Key: admin-key-12345"
```

Generate a new API key (requires admin scope):

```bash
curl -X POST http://localhost:8004/api-keys \
  -H "X-API-Key: admin-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Application Key",
    "description": "For external application",
    "scope": "write"
  }'
```

List all API keys:

```bash
curl -H "X-API-Key: admin-key-12345" http://localhost:8004/api-keys
```

## Testing with Swagger UI

1. Navigate to http://localhost:8004/docs
2. Click the **Authorize** button (lock icon)
3. Enter your API key in the `X-API-Key` field
4. Click **Authorize**
5. Now you can test any endpoint with the appropriate scope

## Error Responses

### 401 Unauthorized
Missing or invalid API key:
```json
{
  "detail": "Invalid or inactive API key"
}
```

### 403 Forbidden
Insufficient permissions:
```json
{
  "detail": "Insufficient permissions. Required scope: (ScopeEnum.WRITE,), your scope: read"
}
```

### 404 Not Found
Resource not found:
```json
{
  "detail": "Product not found"
}
```

## Database Configuration

The database connection is hardcoded in `app/database.py`:

```
postgresql://ecomuser:ecompass@localhost:5434/ecommerce
```

Note: Port **5434** is used to avoid conflicts with other PostgreSQL instances.

## Stopping the Application

Stop the API server: Press `Ctrl+C`

**Stop the PostgreSQL container:**
```bash
podman stop ecommerce-db
podman rm ecommerce-db
```

**To remove all data:**
```bash
podman stop ecommerce-db
podman rm ecommerce-db
podman volume prune
```

## OpenAPI Specification

This API is fully compliant with OpenAPI 3.0 specification with security schemes documented. The specification includes:

- All endpoint definitions with required scopes
- Request/response schemas
- Authentication requirements
- Validation rules
- Example values

Access the spec at: http://localhost:8004/openapi.json

The security scheme is defined as:
```yaml
securitySchemes:
  APIKeyHeader:
    type: apiKey
    in: header
    name: X-API-Key
```

## Project Structure

```
ecommerce-api/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application and endpoints
│   ├── database.py         # Database configuration
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic validation schemas
│   └── auth.py             # API key authentication & authorization
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # PostgreSQL container setup
└── README.md              # This file
```

## Technologies Used

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **PostgreSQL** - Relational database
- **Passlib** - Password hashing library (for API key hashing)
- **Uvicorn** - ASGI server
- **Podman/Docker** - Containerization

## Security Notes

- API keys are hashed using bcrypt before storage
- Plain text keys are only shown once when created
- Keys can be revoked by deleting them (admin scope required)
- Expired keys are automatically rejected
- You cannot delete the API key you're currently using

## License

This is a sample project for demonstration purposes.

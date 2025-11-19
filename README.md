# SAM Sample OpenAPI Apps

This repository contains four sample OpenAPI applications demonstrating different authentication methods for use with AWS SAM (Serverless Application Model) and AI agents.

## Projects

### 📚 [Library Management API](./library-api/README.md)
A comprehensive library API demonstrating **all authentication methods**: public endpoints, API Key, Basic Auth, JWT Bearer tokens, and OAuth2 authorization code flow with custom server.

### 📝 [Blog API](./blog-api/README.md)
A blog management API with mixed authentication: public endpoints, API key authentication, and Google-style service account authentication.

### 🛒 [E-commerce API](./ecommerce-api/README.md)
An e-commerce product catalog API demonstrating API key authentication with scopes.

### 📈 [Stock Portfolio API](./stock-portfolio-api/README.md)
A stock portfolio tracking API with no authentication (open access).

## Authentication Methods Comparison

| API | No Auth | API Key | Basic Auth | JWT Bearer | Service Account | OAuth2 |
|-----|---------|---------|------------|------------|-----------------|--------|
| **Library API** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Blog API** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **E-commerce API** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Stock Portfolio API** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Authentication Method Details

- **No Auth**: Open access, no authentication required
- **API Key**: Simple authentication using API keys in headers with optional scopes
- **Basic Auth**: HTTP Basic Authentication using username and password
- **JWT Bearer**: Token-based authentication using JSON Web Tokens
- **Service Account**: Google-style service account authentication with JWT tokens
- **OAuth2**: Industry-standard OAuth2 authorization code flow

## Getting Started

Each project directory contains its own README with specific setup instructions, including:
- Installation requirements
- Running the application locally
- API documentation
- Authentication setup (where applicable)

Navigate to the individual project directories for detailed information.

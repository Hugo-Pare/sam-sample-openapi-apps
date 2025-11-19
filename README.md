# SAM Sample OpenAPI Apps

This repository contains four sample OpenAPI applications demonstrating different authentication methods for testing the OpenAPI tool in [Solace Agent Mesh (SAM)](https://github.com/SolaceLabs/solace-agent-mesh).

> **Note:** The SAM OpenAPI tool does not yet support Basic Auth and OAuth2 authentication methods. These are implemented in the Library API for future compatibility and testing purposes.

## Projects

### 📝 [Blog API](./blog-api/README.md)
A blog management API with mixed authentication: public endpoints, API key authentication, and Google-style service account authentication.

### 🛒 [E-commerce API](./ecommerce-api/README.md)
An e-commerce product catalog API demonstrating API key authentication with scopes.

### 📚 [Library Management API](./library-api/README.md)
A comprehensive library API demonstrating **all authentication methods**: public endpoints, API Key, Basic Auth, JWT Bearer tokens, and OAuth2 authorization code flow with custom server.

### 📈 [Stock Portfolio API](./stock-portfolio-api/README.md)
A stock portfolio tracking API with no authentication (open access).

## Authentication Methods Comparison

| API | No Auth | API Key | Basic Auth | JWT Bearer | Service Account | OAuth2 |
|-----|---------|---------|------------|------------|-----------------|--------|
| **Blog API** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **E-commerce API** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Library API** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
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

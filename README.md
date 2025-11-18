# SAM Sample OpenAPI Apps

This repository contains three sample OpenAPI applications demonstrating different authentication methods for use with AWS SAM (Serverless Application Model) and AI agents.

## Projects

### 📝 [Blog API](./blog-api/README.md)
A blog management API with advanced authentication options.

### 🛒 [E-commerce API](./ecommerce-api/README.md)
An e-commerce API demonstrating API key authentication.

### 📈 [Stock Portfolio API](./stock-portfolio-api/README.md)
A stock portfolio tracking API with no authentication (open access).

## Authentication Methods Comparison

| API | No Auth | API Key | Service Account | OAuth2 |
|-----|---------|---------|-----------------|--------|
| **Blog API** | ✅ | ✅ | ✅ | ❌ |
| **E-commerce API** | ✅ | ✅ | ❌ | ❌ |
| **Stock Portfolio API** | ✅ | ❌ | ❌ | ❌ |

### Authentication Method Details

- **No Auth**: Open access, no authentication required
- **API Key**: Simple authentication using API keys in headers
- **Service Account**: JWT-based authentication using service account credentials
- **OAuth2**: Industry-standard authorization framework (not implemented in these examples)

## Getting Started

Each project directory contains its own README with specific setup instructions, including:
- Installation requirements
- Running the application locally
- API documentation
- Authentication setup (where applicable)

Navigate to the individual project directories for detailed information.

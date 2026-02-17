# Kubernetes Deployment Guide

This guide explains how to build Docker images and deploy the E-commerce, Stock Portfolio, and Library APIs to Kubernetes.

## Architecture

All services run in a **single pod** named `api-servers`:
- **ecommerce-db**: PostgreSQL database on port 5434
- **stock-db**: PostgreSQL database on port 5432
- **library-db**: PostgreSQL database on port 5436
- **ecommerce-api**: FastAPI application on port 8004
- **stock-api**: FastAPI application on port 8001
- **library-api**: FastAPI application on port 8003

## Prerequisites

- Docker installed and running
- Kubernetes cluster access (kubectl configured)
- Existing namespace where you want to deploy

## Step 1: Build Docker Images

Build the Docker images for all three APIs:

```bash
# Build E-commerce API image
cd ecommerce-api
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t 868978040651.dkr.ecr.us-east-1.amazonaws.com/sample-ecommerce-api:0.0.3 \
  --push \
  .
cd ..

# Build Stock Portfolio API image
cd stock-portfolio-api
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t 868978040651.dkr.ecr.us-east-1.amazonaws.com/sample-stock-api:0.0.2 \
  --push \
  .
cd ..

# Build Library API image
cd library-api
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t 868978040651.dkr.ecr.us-east-1.amazonaws.com/sample-library-api:0.0.1 \
  --push \
  .
cd ..
```

## Step 2: Load Images to Kubernetes

If you're using a local Kubernetes cluster (like Minikube, Kind, or Docker Desktop):

### For Minikube:
```bash
minikube image load ecommerce-api:latest
minikube image load stock-api:latest
```

### For Kind:
```bash
kind load docker-image ecommerce-api:latest
kind load docker-image stock-api:latest
```

### For remote clusters:
Push images to a container registry and update the image names in `k8s-deployment.yaml`:
```bash
# Tag and push to your registry
docker tag ecommerce-api:latest your-registry/ecommerce-api:latest
docker tag stock-api:latest your-registry/stock-api:latest
docker push your-registry/ecommerce-api:latest
docker push your-registry/stock-api:latest
```

## Step 3: Deploy to Kubernetes

Deploy to your existing namespace:

```bash
# Switch to your namespace
kubectl config set-context --current --namespace=your-namespace

# Apply the deployment
kubectl apply -f k8s-deployment.yaml
```

## Step 4: Verify Deployment

Check that the pod is running:

```bash
# Check pod status
kubectl get pods

# Check all containers in the pod
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].name}'

# View pod logs for specific container
kubectl logs api-servers-<pod-id> -c ecommerce-api
kubectl logs api-servers-<pod-id> -c stock-api
kubectl logs api-servers-<pod-id> -c ecommerce-db
kubectl logs api-servers-<pod-id> -c stock-db

# Check services
kubectl get services
```

## Step 5: Access the APIs

### Within the cluster:
- E-commerce API: `http://ecommerce-api:8004`
- Stock Portfolio API: `http://stock-api:8001`

### From outside the cluster (port-forward):

```bash
# Port forward E-commerce API
kubectl port-forward service/ecommerce-api 8004:8004

# Port forward Stock Portfolio API (in another terminal)
kubectl port-forward service/stock-api 8001:8001
```

Then access:
- E-commerce API docs: http://localhost:8004/docs
- Stock Portfolio API docs: http://localhost:8001/docs

## API Endpoints

### E-commerce API (port 8004)
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /products` - List products (requires API key)
- `GET /categories` - List categories (requires API key)

**Default API Keys:**
- Read-Only: `read-key-12345`
- Write: `write-key-12345`
- Admin: `admin-key-12345`

### Stock Portfolio API (port 8001)
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /stocks` - List stocks
- `GET /portfolio` - View portfolio
- `GET /portfolio/summary/total` - Portfolio summary

## Troubleshooting

### Pod not starting:
```bash
kubectl describe pod api-servers-<pod-id>
kubectl logs api-servers-<pod-id> -c <container-name>
```

### Database connection issues:
The APIs use `localhost` to connect to databases since they're in the same pod. Check that:
- Database containers are ready: `kubectl get pods -w`
- Environment variables are correct: `kubectl describe pod api-servers-<pod-id>`

### Image pull errors:
Ensure images are available in the cluster:
```bash
# List loaded images (Minikube)
minikube ssh docker images

# For other clusters, check imagePullPolicy
kubectl describe pod api-servers-<pod-id>
```

## Cleanup

To remove the deployment:

```bash
kubectl delete -f k8s-deployment.yaml
```

## Notes

- This configuration is optimized for **testing/development** with low traffic
- All containers share the pod's network namespace (localhost communication)
- Databases use separate subdirectories on the same PVC
- Resource limits are set conservatively for testing purposes
- For production, consider separate pods with proper scaling and redundancy

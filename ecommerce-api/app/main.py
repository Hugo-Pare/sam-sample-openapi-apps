from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import engine, get_db, Base
from app import models, schemas
from app.auth import generate_api_key, hash_api_key, require_scope
from app.models import ScopeEnum

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce Product Catalog API",
    description="A sample e-commerce API with API key authentication and scope-based permissions",
    version="1.0.0"
)

# Sample data
SAMPLE_CATEGORIES = [
    {"name": "Electronics", "description": "Electronic devices and gadgets"},
    {"name": "Laptops", "description": "Laptop computers", "parent_name": "Electronics"},
    {"name": "Smartphones", "description": "Mobile phones", "parent_name": "Electronics"},
    {"name": "Tablets", "description": "Tablet devices", "parent_name": "Electronics"},
    {"name": "Clothing", "description": "Apparel and fashion"},
    {"name": "Men's Clothing", "description": "Men's apparel", "parent_name": "Clothing"},
    {"name": "Women's Clothing", "description": "Women's apparel", "parent_name": "Clothing"},
    {"name": "Home & Garden", "description": "Home and garden products"},
    {"name": "Books", "description": "Books and literature"},
    {"name": "Sports & Outdoors", "description": "Sports equipment and outdoor gear"},
]

SAMPLE_PRODUCTS = [
    {"name": "MacBook Pro 16", "description": "High-performance laptop", "price": 2499.99, "stock_quantity": 15, "category_name": "Laptops", "sku": "LAPTOP-001"},
    {"name": "Dell XPS 15", "description": "Premium Windows laptop", "price": 1899.99, "stock_quantity": 20, "category_name": "Laptops", "sku": "LAPTOP-002"},
    {"name": "iPhone 15 Pro", "description": "Latest iPhone model", "price": 999.99, "stock_quantity": 50, "category_name": "Smartphones", "sku": "PHONE-001"},
    {"name": "Samsung Galaxy S24", "description": "Flagship Android phone", "price": 899.99, "stock_quantity": 45, "category_name": "Smartphones", "sku": "PHONE-002"},
    {"name": "iPad Pro", "description": "Professional tablet", "price": 799.99, "stock_quantity": 30, "category_name": "Tablets", "sku": "TABLET-001"},
    {"name": "Samsung Galaxy Tab S9", "description": "Premium Android tablet", "price": 649.99, "stock_quantity": 25, "category_name": "Tablets", "sku": "TABLET-002"},
    {"name": "Men's Casual Shirt", "description": "Comfortable cotton shirt", "price": 39.99, "stock_quantity": 100, "category_name": "Men's Clothing", "sku": "MCLOTH-001"},
    {"name": "Men's Jeans", "description": "Classic denim jeans", "price": 59.99, "stock_quantity": 80, "category_name": "Men's Clothing", "sku": "MCLOTH-002"},
    {"name": "Women's Dress", "description": "Elegant summer dress", "price": 79.99, "stock_quantity": 60, "category_name": "Women's Clothing", "sku": "WCLOTH-001"},
    {"name": "Women's Handbag", "description": "Designer handbag", "price": 149.99, "stock_quantity": 40, "category_name": "Women's Clothing", "sku": "WCLOTH-002"},
    {"name": "Coffee Maker", "description": "Automatic drip coffee maker", "price": 89.99, "stock_quantity": 35, "category_name": "Home & Garden", "sku": "HOME-001"},
    {"name": "Garden Tools Set", "description": "Complete gardening toolkit", "price": 49.99, "stock_quantity": 50, "category_name": "Home & Garden", "sku": "HOME-002"},
    {"name": "The Great Gatsby", "description": "Classic American novel", "price": 14.99, "stock_quantity": 200, "category_name": "Books", "sku": "BOOK-001"},
    {"name": "Python Programming", "description": "Learn Python from scratch", "price": 44.99, "stock_quantity": 75, "category_name": "Books", "sku": "BOOK-002"},
    {"name": "Yoga Mat", "description": "Non-slip exercise mat", "price": 29.99, "stock_quantity": 100, "category_name": "Sports & Outdoors", "sku": "SPORT-001"},
    {"name": "Running Shoes", "description": "Lightweight running shoes", "price": 89.99, "stock_quantity": 60, "category_name": "Sports & Outdoors", "sku": "SPORT-002"},
]

SAMPLE_API_KEYS = [
    {"name": "Read-Only Key", "description": "Public read-only access", "scope": ScopeEnum.READ, "key": "read-key-12345"},
    {"name": "Application Key", "description": "For application write access", "scope": ScopeEnum.WRITE, "key": "write-key-12345"},
    {"name": "Admin Master Key", "description": "Full administrative access", "scope": ScopeEnum.ADMIN, "key": "admin-key-12345"},
]


@app.on_event("startup")
async def startup_event():
    """Load sample data on startup if database is empty"""
    db = next(get_db())
    try:
        # Check if data already exists
        existing_categories = db.query(models.Category).count()
        if existing_categories == 0:
            # Create categories
            category_map = {}
            for cat_data in SAMPLE_CATEGORIES:
                _parent_name = cat_data.pop("parent_name", None)
                category = models.Category(**cat_data)
                db.add(category)
                db.flush()
                category_map[cat_data["name"]] = category.id
                
            db.commit()
            
            # Update parent IDs
            for cat_data in SAMPLE_CATEGORIES:
                if "parent_name" in cat_data:
                    category = db.query(models.Category).filter(
                        models.Category.name == cat_data["name"]
                    ).first()
                    if category:
                        parent_id = category_map.get(cat_data["parent_name"])
                        if parent_id:
                            category.parent_id = parent_id
            db.commit()
            
            # Refresh category map
            categories = db.query(models.Category).all()
            category_map = {cat.name: cat.id for cat in categories}
            
            # Create products
            for prod_data in SAMPLE_PRODUCTS:
                category_name = prod_data.pop("category_name")
                category_id = category_map.get(category_name)
                if category_id:
                    product = models.Product(
                        **prod_data,
                        category_id=category_id
                    )
                    db.add(product)
            
            db.commit()
            
            # Create sample API keys with hardcoded values
            for key_data in SAMPLE_API_KEYS:
                plain_key = key_data.pop("key")  # Extract the hardcoded key
                api_key = models.APIKey(
                    name=key_data["name"],
                    description=key_data["description"],
                    scope=key_data["scope"],
                    key_hash=hash_api_key(plain_key)
                )
                db.add(api_key)
            
            db.commit()
            
            # Print hardcoded keys for reference
            print("\n" + "="*60)
            print("HARDCODED API KEYS (always the same):")
            print("="*60)
            print("\nRead-Only Key (scope: read):")
            print("  X-API-Key: read-key-12345")
            print("\nWrite Key (scope: write):")
            print("  X-API-Key: write-key-12345")
            print("\nAdmin Key (scope: admin):")
            print("  X-API-Key: admin-key-12345")
            print("\n" + "="*60 + "\n")
            
    finally:
        db.close()


# Root endpoint
@app.get("/", tags=["General"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "E-commerce Product Catalog API",
        "version": "1.0.0",
        "authentication": "API Key (X-API-Key header)",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


# Health check endpoint
@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Category endpoints
@app.get("/categories", response_model=List[schemas.Category], tags=["Categories"], dependencies=[Depends(require_scope(ScopeEnum.READ))])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all categories (requires read scope)"""
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories


@app.get("/categories/{category_id}", response_model=schemas.Category, tags=["Categories"], dependencies=[Depends(require_scope(ScopeEnum.READ))])
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific category (requires read scope)"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.post("/categories", response_model=schemas.Category, status_code=status.HTTP_201_CREATED, tags=["Categories"], dependencies=[Depends(require_scope(ScopeEnum.WRITE))])
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new category (requires write scope)"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.put("/categories/{category_id}", response_model=schemas.Category, tags=["Categories"], dependencies=[Depends(require_scope(ScopeEnum.WRITE))])
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a category (requires write scope)"""
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"], dependencies=[Depends(require_scope(ScopeEnum.ADMIN))])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Delete a category (requires admin scope)"""
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()
    return None


# Product endpoints
@app.get("/products", response_model=List[schemas.Product], tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.READ))])
def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: int = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filters (requires read scope)"""
    query = db.query(models.Product)

    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)

    products = query.offset(skip).limit(limit).all()
    return products


@app.get("/products/{product_id}", response_model=schemas.Product, tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.READ))])
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific product (requires read scope)"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/sku/{sku}", response_model=schemas.Product, tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.READ))])
def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db)
):
    """Get a product by SKU (requires read scope)"""
    product = db.query(models.Product).filter(models.Product.sku == sku).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED, tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.WRITE))])
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product (requires write scope)"""
    # Check if category exists
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if SKU already exists
    existing = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.put("/products/{product_id}", response_model=schemas.Product, tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.WRITE))])
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product (requires write scope)"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product.dict(exclude_unset=True)

    # Check if updating SKU to one that already exists
    if "sku" in update_data:
        existing = db.query(models.Product).filter(
            models.Product.sku == update_data["sku"],
            models.Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"], dependencies=[Depends(require_scope(ScopeEnum.ADMIN))])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Delete a product (requires admin scope)"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return None


# API Key management endpoints
@app.get("/api-keys", response_model=List[schemas.APIKeyInfo], tags=["API Keys"], dependencies=[Depends(require_scope(ScopeEnum.ADMIN))])
def get_api_keys(
    db: Session = Depends(get_db)
):
    """List all API keys (requires admin scope)"""
    api_keys = db.query(models.APIKey).all()
    return api_keys


@app.post("/api-keys", response_model=schemas.APIKeyResponse, status_code=status.HTTP_201_CREATED, tags=["API Keys"], dependencies=[Depends(require_scope(ScopeEnum.ADMIN))])
def create_api_key(
    key_data: schemas.APIKeyCreate,
    db: Session = Depends(get_db)
):
    """Generate a new API key (requires admin scope)"""
    plain_key = generate_api_key()

    db_api_key = models.APIKey(
        **key_data.dict(),
        key_hash=hash_api_key(plain_key)
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    # Return the response with the plain key (only shown once!)
    response = schemas.APIKeyResponse.from_orm(db_api_key)
    response.key = plain_key
    return response


@app.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["API Keys"], dependencies=[Depends(require_scope(ScopeEnum.ADMIN))])
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db)
):
    """Revoke an API key (requires admin scope)"""
    db_api_key = db.query(models.APIKey).filter(models.APIKey.id == key_id).first()
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(db_api_key)
    db.commit()
    return None


# Run with: uvicorn app.main:app --reload --port <PORT>
# Default port is 8004, or set PORT environment variable
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)

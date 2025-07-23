import logging
from typing import List, Optional
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String, Numeric, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
import os

# Database URL from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "product_management")
DB_USERNAME = os.getenv("DB_USERNAME", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app configuration
API_CONFIG = {
    "title": "Product Management API",
    "description": "A RESTful API for managing products with CRUD operations",
    "version": "1.0.0"
}

app = FastAPI(**API_CONFIG)

# Database model
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)

# Pydantic models for request/response
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal

class ProductCreate(ProductBase):
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v

class ProductUpdate(BaseModel):
    description: Optional[str] = None
    price: Optional[Decimal] = None
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))  # Test the connection
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.get("/products", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        return [
            {"id": p.id, "name": p.name, "description": p.description, "price": float(p.price)}
            for p in products
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving products: {str(e)}"
        )

@app.get("/products/{product_id}", status_code=status.HTTP_200_OK)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        )

@app.get("/products/name/{product_name}", status_code=status.HTTP_200_OK)
def get_product_by_name(product_name: str, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with name '{product_name}' not found"
            )
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        )

@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        # Check if product with same name already exists
        existing = db.query(Product).filter(Product.name == product.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with name '{product.name}' already exists"
            )
        
        new_product = Product(
            name=product.name,
            description=product.description,
            price=float(product.price)
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return {
            "msg": "Product created successfully",
            "id": new_product.id,
            "name": new_product.name
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )

@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        db.delete(product)
        db.commit()
        return {
            "msg": "Product deleted successfully",
            "id": product_id,
            "name": product.name
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )

@app.put("/products/name/{product_name}", status_code=status.HTTP_200_OK)
def update_product_by_name(product_name: str, update: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product by name with partial updates supported"""
    try:
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with name '{product_name}' not found"
            )

        # Track what was updated
        updates = []
        if update.description is not None:
            product.description = update.description
            updates.append("description")
        if update.price is not None:
            product.price = float(update.price) if update.price is not None else product.price
            updates.append("price")

        if not updates:
            return {"msg": "No fields to update"}

        db.commit()
        return {
            "msg": "Product updated successfully",
            "id": product.id,
            "name": product.name,
            "updated_fields": updates
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for container health monitoring"""
    return {
        "status": "healthy",
        "version": API_CONFIG["version"],
        "timestamp": "2025-01-23T18:48:44Z"
    }

@app.get("/health/detailed", status_code=status.HTTP_200_OK)
def detailed_health_check():
    """Detailed health check endpoint that includes database connectivity"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": API_CONFIG["version"],
            "timestamp": "2025-01-23T18:48:44Z"
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


def run_app():
    """Entry point for the console script to run the application"""
    import uvicorn
    import os
    
    # Use environment variable for host, default to 0.0.0.0 for containers
    # nosec B104: Binding to 0.0.0.0 is required for containerized applications
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    uvicorn.run("src.main.python.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_app()
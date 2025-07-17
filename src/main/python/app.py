import os
import logging
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, validator, constr
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Import configuration
try:
    # Try absolute import first (for when running as a package)
    from config import get_db_config, API_CONFIG, TEST_MODE, LOG_LEVEL, LOG_FORMAT
except ImportError:
    # Fall back to relative import (for when running as a module)
    from src.main.python.config import get_db_config, API_CONFIG, TEST_MODE, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Get database configuration
db_config = get_db_config()
logger.info(f"Using database configuration: {db_config['url']}")

# Create engine with connection pooling
engine = create_engine(
    db_config.pop('url'),  # Extract URL and use remaining items as kwargs
    **db_config
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Initialize FastAPI with configuration
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"],
    docs_url=API_CONFIG["docs_url"],
    redoc_url=API_CONFIG["redoc_url"],
    openapi_url=API_CONFIG["openapi_url"],
    debug=API_CONFIG["debug"]
)

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(String(255))
    price = Column(Float, nullable=False)

class ProductCreate(BaseModel):
    name: constr(min_length=1, max_length=120)
    description: constr(max_length=255) = ""
    price: Decimal

    @validator('name')
    def validate_name(cls, v):
        if len(v) > 120:
            raise ValueError('Name must be 120 characters or less')
        return v

    @validator('description')
    def validate_description(cls, v):
        if len(v) > 255:
            raise ValueError('Description must be 255 characters or less')
        return v

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

class ProductUpdate(BaseModel):
    description: Optional[str] = None
    price: Optional[Decimal] = None

    @validator('description')
    def validate_description(cls, v):
        if v is not None and len(v) > 255:
            raise ValueError('Description must be 255 characters or less')
        return v

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
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": API_CONFIG["version"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


def run_app():
    """Entry point for the console script to run the application"""
    import uvicorn
    uvicorn.run("src.main.python.app:app", host="0.0.0.0", port=80, log_level="info")


if __name__ == "__main__":
    run_app()
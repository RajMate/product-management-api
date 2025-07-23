import sys
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test mode
os.environ['TEST_MODE'] = 'true'

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

# Add main python directory to path
main_python_dir = os.path.join(project_root, 'src', 'main', 'python')
sys.path.insert(0, main_python_dir)

# Import the app module
from app import app, Base, Product, ProductCreate, ProductUpdate, get_db

# Create test database
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # This ensures single connection for in-memory SQLite
)

# Create all tables in the engine
Base.metadata.create_all(bind=engine)

# Create session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        db.execute(text('SELECT 1'))  # Test connection
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

class TestProductAPI(unittest.TestCase):
    """Test suite for Product API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        # Create tables once for all tests
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        # Clear all tables before each test
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                # Use proper SQLAlchemy delete to avoid SQL injection
                conn.execute(table.delete())
        # VACUUM must be run outside transaction
        with engine.connect() as conn:
            conn.execute(text('VACUUM'))
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        # Drop all tables after all tests
        Base.metadata.drop_all(bind=engine)
    
    def test_create_product(self):
        """Test successful product creation"""
        response = client.post("/products", json={
            "name": "Pen",
            "description": "Blue ink pen",
            "price": 10.50
        })
        self.assertEqual(response.status_code, 201)
        json_data = response.json()
        self.assertEqual(json_data["msg"], "Product created successfully")
        self.assertIsInstance(json_data["id"], int)
        self.assertEqual(json_data["name"], "Pen")
        
        # Verify product was actually created
        get_response = client.get(f"/products/{json_data['id']}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["name"], "Pen")
        self.assertEqual(get_response.json()["price"], 10.50)
    
    def test_get_all_products(self):
        client.post("/products", json={"name": "Pencil", "description": "HB", "price": 5.0})
        response = client.get("/products")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)
    
    def test_get_product_by_id(self):
        client.post("/products", json={"name": "Eraser", "description": "Rubber", "price": 2.0})
        response = client.get("/products/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Eraser")
    
    def test_get_product_by_name(self):
        client.post("/products", json={"name": "Sharpener", "description": "Steel", "price": 3.0})
        response = client.get("/products/name/Sharpener")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Sharpener")
    
    def test_update_product_by_name(self):
        """Test successful product update"""
        # Create a product first
        client.post("/products", json={
            "name": "Notebook",
            "description": "Lined paper",
            "price": 15.0
        })
        
        # Update the product
        update_response = client.put("/products/name/Notebook", json={
            "description": "Updated description",
            "price": 20.0
        })
        
        self.assertEqual(update_response.status_code, 200)
        json_data = update_response.json()
        self.assertEqual(json_data["msg"], "Product updated successfully")
        self.assertEqual(json_data["name"], "Notebook")
        self.assertIn("description", json_data["updated_fields"])
        self.assertIn("price", json_data["updated_fields"])
        
        # Verify product was actually updated
        get_response = client.get("/products/name/Notebook")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["description"], "Updated description")
        self.assertEqual(get_response.json()["price"], 20.0)
    
    def test_delete_product(self):
        """Test successful product deletion"""
        # Create a product first
        create_response = client.post("/products", json={
            "name": "ToDelete",
            "description": "Will be deleted",
            "price": 5.0
        })
        product_id = create_response.json()["id"]
        
        # Delete the product
        delete_response = client.delete(f"/products/{product_id}")
        self.assertEqual(delete_response.status_code, 200)
        json_data = delete_response.json()
        self.assertEqual(json_data["msg"], "Product deleted successfully")
        self.assertEqual(json_data["id"], product_id)
        self.assertEqual(json_data["name"], "ToDelete")
        
        # Verify product was actually deleted
        get_response = client.get(f"/products/{product_id}")
        self.assertEqual(get_response.status_code, 404)
    
    def test_get_nonexistent_product(self):
        response = client.get("/products/999")
        self.assertEqual(response.status_code, 404)
    
    def test_create_duplicate_product(self):
        client.post("/products", json={"name": "Duplicate", "description": "First", "price": 10.0})
        response = client.post("/products", json={"name": "Duplicate", "description": "Second", "price": 20.0})
        self.assertEqual(response.status_code, 409)  # Conflict
    
    def test_create_product_missing_fields(self):
        response = client.post("/products", json={"description": "Missing name and price"})
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
    
    def test_update_nonexistent_product(self):
        response = client.put("/products/name/NonExistent", json={"description": "New", "price": 10.0})
        self.assertEqual(response.status_code, 404)
    
    def test_get_product_by_nonexistent_name(self):
        response = client.get("/products/name/NonExistent")
        self.assertEqual(response.status_code, 404)
    
    def test_partial_update_product(self):
        """Test partial updates with individual fields"""
        # Create a product first
        client.post("/products", json={
            "name": "PartialUpdate",
            "description": "Original description",
            "price": 25.0
        })
        
        # Update only the description
        desc_update_response = client.put("/products/name/PartialUpdate", json={
            "description": "Updated description only"
        })
        
        self.assertEqual(desc_update_response.status_code, 200)
        json_data = desc_update_response.json()
        self.assertEqual(json_data["msg"], "Product updated successfully")
        self.assertEqual(json_data["updated_fields"], ["description"])
        
        # Verify only description was updated
        get_response = client.get("/products/name/PartialUpdate")
        self.assertEqual(get_response.status_code, 200)
        product_data = get_response.json()
        self.assertEqual(product_data["description"], "Updated description only")
        self.assertEqual(product_data["price"], 25.0)  # Price unchanged
        
        # Update only the price
        price_update_response = client.put("/products/name/PartialUpdate", json={
            "price": 30.0
        })
        
        self.assertEqual(price_update_response.status_code, 200)
        json_data = price_update_response.json()
        self.assertEqual(json_data["updated_fields"], ["price"])
        
        # Verify only price was updated
        get_response = client.get("/products/name/PartialUpdate")
        product_data = get_response.json()
        self.assertEqual(product_data["description"], "Updated description only")  # Description from previous update
        self.assertEqual(product_data["price"], 30.0)  # Updated price
    
    def test_delete_nonexistent_product(self):
        response = client.delete("/products/999")
        self.assertEqual(response.status_code, 404)
    
    def test_partial_update_price_only(self):
        # Create a product first
        client.post("/products", json={
            "name": "PriceUpdate",
            "description": "Original description",
            "price": 15.0
        })
        
        # Update only the price
        update_response = client.put("/products/name/PriceUpdate", json={"price": 25.0})
        self.assertEqual(update_response.status_code, 200)
        
        # Verify update
        get_response = client.get("/products/name/PriceUpdate")
        self.assertEqual(get_response.json()["price"], 25.0)
        self.assertEqual(get_response.json()["description"], "Original description")  # Unchanged


class TestModels(unittest.TestCase):
    
    def setUp(self):
        Base.metadata.create_all(bind=engine)
    
    def tearDown(self):
        Base.metadata.drop_all(bind=engine)
    
    def test_product_model_creation(self):
        # Create a session
        db = TestingSessionLocal()
        
        try:
            # Create a product
            product = Product(
                name="Test Product",
                description="Test Description",
                price=10.0
            )
            
            # Add to session and commit
            db.add(product)
            db.commit()
            db.refresh(product)
            
            # Verify product was created
            self.assertIsNotNone(product.id)
            self.assertEqual(product.name, "Test Product")
            self.assertEqual(product.description, "Test Description")
            self.assertEqual(product.price, 10.0)
            
            # Query the product
            queried_product = db.query(Product).filter(Product.id == product.id).first()
            self.assertEqual(queried_product.name, "Test Product")
            
        finally:
            db.close()
    
    def test_product_create_pydantic_model(self):
        """Test Pydantic model for creating products"""
        product = ProductCreate(name="Test", description="Test Description", price=10.0)
        self.assertEqual(product.name, "Test")
        self.assertEqual(product.description, "Test Description")
        self.assertEqual(product.price, 10.0)
        
        # Test validation
        with self.assertRaises(Exception):
            ProductCreate(name="", description="Invalid name", price=10.0)
    
    def test_product_update_pydantic_model(self):
        """Test Pydantic model for updating products"""
        update = ProductUpdate(description="Updated Description", price=20.0)
        self.assertEqual(update.description, "Updated Description")
        self.assertEqual(update.price, 20.0)
        
        # Test validation
        with self.assertRaises(Exception):
            ProductUpdate(description="Valid", price=-10.0)  # Negative price
    
    def test_product_update_pydantic_model_partial(self):
        """Test partial updates with Pydantic model"""
        # Only description
        update1 = ProductUpdate(description="Only Description")
        self.assertEqual(update1.description, "Only Description")
        self.assertIsNone(update1.price)
        
        # Only price
        update2 = ProductUpdate(price=30.0)
        self.assertIsNone(update2.description)
        self.assertEqual(update2.price, 30.0)
        
        # Empty update
        update3 = ProductUpdate()
        self.assertIsNone(update3.description)
        self.assertIsNone(update3.price)


class TestErrorHandling(unittest.TestCase):
    """Test suite for API error handling"""
    
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        # Clear all tables before each test
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                # Use proper SQLAlchemy delete to avoid SQL injection
                conn.execute(table.delete())
        # Create test data
        client.post("/products", json={"name": "ErrorTest", "description": "Test", "price": 10.0})

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
    
    def test_internal_server_error_handling(self):
        """Test 500 error handling with invalid SQL"""
        # This test is a bit tricky to implement without mocking
        # We'll check that our endpoints return proper error responses
        
        # Test with invalid product ID format
        response = client.get("/products/invalid")
        self.assertEqual(response.status_code, 422)  # Validation error
        
        # Test with invalid JSON
        response = client.post("/products", data="invalid json")
        self.assertEqual(response.status_code, 422)  # JSON parsing error
        
        # Test with invalid data types
        response = client.post("/products", json={
            "name": "Test",
            "description": "Test",
            "price": "invalid"
        })
        self.assertEqual(response.status_code, 422)
    
    def test_concurrent_updates(self):
        """Test handling concurrent updates to same product"""
        # Create initial product
        client.post("/products", json={
            "name": "Concurrent",
            "description": "Test",
            "price": 10.0
        })
        
        # Simulate concurrent updates
        response1 = client.put("/products/name/Concurrent", json={"price": 20.0})
        response2 = client.put("/products/name/Concurrent", json={"price": 30.0})
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Verify final state
        get_response = client.get("/products/name/Concurrent")
        self.assertEqual(get_response.json()["price"], 30.0)


class TestValidation(unittest.TestCase):
    """Test suite for input validation"""
    
    def test_product_name_required(self):
        # Test that product name is required
        with self.assertRaises(Exception):
            ProductCreate(description="No name", price=10.0)
    
    def test_product_name_length_validation(self):
        # Test name length validation
        with self.assertRaises(Exception):
            ProductCreate(name="a" * 121, description="Too long name", price=10.0)
    
    def test_product_description_length_validation(self):
        # Test description length validation
        with self.assertRaises(Exception):
            ProductCreate(name="Valid", description="a" * 256, price=10.0)
    
    def test_product_price_validation(self):
        # Test negative price validation
        with self.assertRaises(Exception):
            ProductCreate(name="Valid", description="Valid", price=-1.0)
    
    def test_product_update_validation(self):
        # Test update validation
        with self.assertRaises(Exception):
            ProductUpdate(description="a" * 256, price=10.0)
        
        with self.assertRaises(Exception):
            ProductUpdate(description="Valid", price=-1.0)


class TestDatabaseSession(unittest.TestCase):
    """Test database session management"""
    
    def setUp(self):
        # Create tables and clear data before each test
        Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                # Use proper SQLAlchemy delete to avoid SQL injection
                conn.execute(table.delete())
        with engine.connect() as conn:
            conn.execute(text('VACUUM'))
            conn.commit()
    
    def test_database_connection(self):
        """Test database connection works"""
        db = TestingSessionLocal()
        try:
            result = db.execute(text('SELECT 1'))
            self.assertIsNotNone(result)
        finally:
            db.close()
    
    def test_session_rollback_on_error(self):
        """Test that database sessions rollback on errors"""
        db = TestingSessionLocal()
        try:
            # Create a product
            product = Product(name="Test", description="Test", price=10.0)
            db.add(product)
            db.commit()
            
            # Try to create duplicate (should fail)
            duplicate = Product(name="Test", description="Duplicate", price=20.0)
            db.add(duplicate)
            
            with self.assertRaises(Exception):
                db.commit()
            
            # Session should be rolled back
            db.rollback()
            
            # Original product should still exist
            existing = db.query(Product).filter(Product.name == "Test").first()
            self.assertIsNotNone(existing)
            self.assertEqual(existing.description, "Test")
            
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
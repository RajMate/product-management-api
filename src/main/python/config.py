"""
Database and application configuration module.
Handles environment variables and configuration for different environments.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Environment types
ENV_LOCAL = "local"
ENV_DEV = "development"
ENV_TEST = "test"
ENV_PROD = "production"

# Load environment variables
load_dotenv()

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", ENV_LOCAL).lower()
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true" or ENVIRONMENT == ENV_TEST

# Database configuration
DB_CONFIG = {
    # Default SQLite configuration for local development
    "sqlite": {
        "url": "sqlite:///product_management.db",
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo": False,
    },
    # In-memory SQLite for testing
    "sqlite_memory": {
        "url": "sqlite:///:memory:",
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
        "echo": False,
    },
    # MySQL configuration for production
    "mysql": {
        "url": os.getenv("MYSQL_URI", "").replace("mysql://", "mysql+pymysql://"),
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "echo": os.getenv("DB_ECHO", "false").lower() == "true",
    },
    # PostgreSQL configuration (if needed)
    "postgresql": {
        "url": os.getenv("POSTGRES_URI", "").replace("postgresql://", "postgresql+psycopg2://"),
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "echo": os.getenv("DB_ECHO", "false").lower() == "true",
    }
}

def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration based on environment.
    
    Returns:
        Dict[str, Any]: Database configuration dictionary
    """
    if TEST_MODE:
        return DB_CONFIG["sqlite_memory"]
    
    db_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    if db_type not in DB_CONFIG:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    return DB_CONFIG[db_type]

# API configuration
API_CONFIG = {
    "title": "Product Management API",
    "description": "API for managing product information",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json",
    "debug": os.getenv("DEBUG", "false").lower() == "true",
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
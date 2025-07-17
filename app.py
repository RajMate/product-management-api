"""
Entry point for the product management API.
This module imports and re-exports the app and run_app function from the actual implementation.
"""
from src.main.python.app import app, run_app

# Re-export the FastAPI app instance and run_app function
__all__ = ['app', 'run_app']
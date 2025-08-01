#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    app.run() 
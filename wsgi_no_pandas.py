#!/usr/bin/env python3
"""
WSGI entry point for Render deployment (no pandas version)
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app_no_pandas import app

# Create the Flask application instance
application = app

if __name__ == "__main__":
    app.run() 
#!/usr/bin/env python3
"""
PythonAnywhere WSGI entry point
This file is specifically for PythonAnywhere deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for PythonAnywhere
os.environ['FLASK_ENV'] = 'production'

# Import and create the Flask application
from app import create_app

# Create the Flask application instance
application = create_app()

# PythonAnywhere expects the variable to be named 'application'
# This is the standard WSGI application object 
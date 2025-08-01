# PythonAnywhere Deployment Guide

This guide will help you deploy the School Resource Management System on PythonAnywhere using their Web tab and WSGI configuration.

## Prerequisites

1. A PythonAnywhere account (free or paid)
2. All project files uploaded to your PythonAnywhere account

## Step 1: Upload Your Project

1. **Download your project files** from your local machine
2. **Upload to PythonAnywhere**:
   - Go to the **Files** tab in PythonAnywhere
   - Navigate to your home directory
   - Create a new directory for your project (e.g., `school-resource-management`)
   - Upload all project files to this directory

## Step 2: Set Up Virtual Environment

1. **Open a Bash console** in PythonAnywhere
2. **Navigate to your project directory**:
   ```bash
   cd ~/school-resource-management
   ```

3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

5. **Install required packages** (use the PythonAnywhere-optimized requirements):
   ```bash
   pip install -r requirements_pythonanywhere.txt
   ```
   
   **Note**: If you encounter pandas installation issues, try:
   ```bash
   pip install --upgrade pip
   pip install pandas==1.5.3
   pip install -r requirements_pythonanywhere.txt
   ```

## Step 3: Configure Environment Variables

1. **Create a `.env` file** in your project directory:
   ```bash
   nano .env
   ```

2. **Add the following content** (adjust values as needed):
   ```env
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-key-change-this-in-production
   DATABASE_URL=sqlite:///resource_management.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   LOG_LEVEL=INFO
   LOG_FILE=app.log
   ```

3. **Save the file** (Ctrl+X, then Y, then Enter)

## Step 4: Configure the Web App

1. **Go to the Web tab** in PythonAnywhere
2. **Click "Add a new web app"**
3. **Choose your domain** (e.g., `yourusername.pythonanywhere.com`)
4. **Select "Manual configuration"** (not Flask)
5. **Choose Python version** (3.8 or higher)

## Step 5: Configure WSGI File

1. **Click on the WSGI configuration file** link in the Web tab
2. **Replace the entire content** with:

```python
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
```

3. **Save the file**

## Step 6: Configure Virtual Environment Path

1. **In the Web tab**, find the **Virtual environment** section
2. **Enter the path** to your virtual environment:
   ```
   /home/yourusername/school-resource-management/venv
   ```
   (Replace `yourusername` with your actual PythonAnywhere username)

## Step 7: Configure Static Files

1. **In the Web tab**, find the **Static files** section
2. **Add static file mappings**:
   - URL: `/static/`
   - Directory: `/home/yourusername/school-resource-management/static`

## Step 8: Create Required Directories

1. **Open a Bash console** and run:
   ```bash
   cd ~/school-resource-management
   mkdir -p logs uploads data
   ```

## Step 9: Initialize the Database

1. **Open a Python console** in PythonAnywhere
2. **Run the following commands**:
   ```python
   import os
   import sys
   sys.path.insert(0, '/home/yourusername/school-resource-management')
   
   from app import create_app, db
   
   app = create_app()
   with app.app_context():
       db.create_all()
       print("Database initialized successfully!")
   ```

## Step 10: Reload the Web App

1. **Go back to the Web tab**
2. **Click the green "Reload" button** to restart your application

## Step 11: Test Your Application

1. **Visit your web app URL** (e.g., `https://yourusername.pythonanywhere.com`)
2. **Test the login** with default admin credentials:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

### Common Issues and Solutions

1. **Import Error: No module named 'app'**
   - **Solution**: Make sure your project files are in the correct directory
   - Check that `app.py` exists in your project root

2. **Database Error**
   - **Solution**: Ensure the database file has write permissions
   - Run: `chmod 666 resource_management.db`

3. **Static Files Not Loading**
   - **Solution**: Check the static files configuration in the Web tab
   - Verify the directory path is correct

4. **Email Not Working**
   - **Solution**: Configure your email settings in the `.env` file
   - Use Gmail App Passwords for Gmail accounts

5. **500 Internal Server Error**
   - **Solution**: Check the error logs in the Web tab
   - Look for specific error messages in the logs

### Checking Logs

1. **In the Web tab**, click on **Error log** to view recent errors
2. **In the Web tab**, click on **Server log** to view general server logs

### File Permissions

If you encounter permission issues:
```bash
chmod 755 ~/school-resource-management
chmod 644 ~/school-resource-management/*.py
chmod 644 ~/school-resource-management/*.txt
chmod 644 ~/school-resource-management/*.md
```

## Security Considerations

1. **Change the default admin password** after first login
2. **Use a strong SECRET_KEY** in your `.env` file
3. **Configure proper email settings** for notifications
4. **Regularly backup your database**

## Maintenance

### Updating Your Application

1. **Upload new files** to PythonAnywhere
2. **Reload the web app** from the Web tab
3. **Test the application** to ensure everything works

### Database Management

- The application automatically handles database switching when size limits are reached
- Monitor database size through the admin interface
- Backup your database regularly

## Support

If you encounter issues:
1. Check the error logs in the Web tab
2. Verify all file paths are correct
3. Ensure all required packages are installed
4. Test the application locally before deploying

## Default Credentials

After deployment, you can log in with:
- **Username**: `admin`
- **Password**: `admin123`

**Important**: Change these credentials immediately after first login! 
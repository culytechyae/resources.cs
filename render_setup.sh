#!/bin/bash

# Render Deployment Setup Script for School Resource Management System
# This script helps prepare your project for Render deployment

echo "🚀 Setting up School Resource Management System for Render deployment..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from your project root directory."
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "📋 Files found:"
ls -la

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "🔧 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Add all files
echo "📝 Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Initial commit - School Resource Management System"
    echo "✅ Changes committed"
fi

echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com"
echo "   - Click '+' → 'New repository'"
echo "   - Name it: school-resource-management"
echo "   - Make it PUBLIC"
echo "   - Don't initialize with README"
echo ""
echo "2. Push to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/school-resource-management.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Render:"
echo "   - Go to https://render.com"
echo "   - Sign up with GitHub"
echo "   - Click 'New +' → 'Web Service'"
echo "   - Connect your repository"
echo "   - Configure environment variables"
echo "   - Deploy!"
echo ""
echo "📖 For detailed instructions, see: RENDER_DEPLOYMENT.md"
echo ""
echo "🔗 Useful URLs:"
echo "   - GitHub: https://github.com"
echo "   - Render: https://render.com"
echo "   - Render Dashboard: https://dashboard.render.com"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "⚠️  WARNING: .env file found. Make sure to:"
    echo "   - Add .env to .gitignore"
    echo "   - Set environment variables in Render dashboard"
    echo "   - Never commit sensitive data to GitHub"
else
    echo "ℹ️  No .env file found. You'll need to set environment variables in Render."
fi

echo ""
echo "✅ Setup complete! Follow the steps above to deploy to Render." 
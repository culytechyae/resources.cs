#!/bin/bash

# School Resource Management System - Production Deployment Script
# This script sets up the application for production deployment

set -e

echo "🚀 Starting School Resource Management System deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs uploads data ssl

# Generate SSL certificates (self-signed for development)
echo "🔐 Generating SSL certificates..."
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ SSL certificates generated"
else
    echo "✅ SSL certificates already exist"
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your production settings before starting the application"
    echo "   - Update SECRET_KEY with a strong secret"
    echo "   - Configure email settings"
    echo "   - Set proper database URL if using external database"
fi

# Build and start the application
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting the application..."
docker-compose up -d

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 30

# Check if the application is running
if curl -f http://localhost/health &> /dev/null; then
    echo "✅ Application is running successfully!"
    echo ""
    echo "🌐 Access your application at:"
    echo "   - HTTP:  http://localhost (redirects to HTTPS)"
    echo "   - HTTPS: https://localhost"
    echo ""
    echo "📊 Default admin credentials:"
    echo "   - Username: admin"
    echo "   - Password: admin123"
    echo ""
    echo "⚠️  IMPORTANT: Change the default admin password after first login!"
    echo ""
    echo "📋 Useful commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop app: docker-compose down"
    echo "   - Restart app: docker-compose restart"
    echo "   - Update app: docker-compose pull && docker-compose up -d"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi 
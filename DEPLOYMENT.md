# School Resource Management System - Deployment Guide

## 🚀 Production Deployment

This guide will help you deploy the School Resource Management System to production.

## Prerequisites

- **Docker & Docker Compose**: Required for containerized deployment
- **Git**: For cloning the repository
- **SSL Certificate**: For HTTPS (optional, self-signed will be generated)

## Quick Deployment

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Resource
```

### 2. Run the Deployment Script
```bash
# On Linux/Mac
chmod +x deploy.sh
./deploy.sh

# On Windows (PowerShell)
.\deploy.sh
```

### 3. Access the Application
- **URL**: https://localhost
- **Default Admin**: `admin` / `admin123`

## Manual Deployment

### Step 1: Environment Setup

1. **Create environment file**
   ```bash
   cp env.example .env
   ```

2. **Edit configuration**
   ```bash
   # Edit .env file with your settings
   nano .env
   ```

   **Required settings:**
   ```bash
   SECRET_KEY=your-super-secret-key-change-this
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

### Step 2: SSL Certificate Setup

1. **Generate self-signed certificate (development)**
   ```bash
   mkdir -p ssl
   openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
   ```

2. **Use Let's Encrypt (production)**
   ```bash
   # Install certbot
   sudo apt-get install certbot

   # Generate certificate
   sudo certbot certonly --standalone -d yourdomain.com

   # Copy certificates
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
   ```

### Step 3: Docker Deployment

1. **Build and start**
   ```bash
   docker-compose up -d
   ```

2. **Check status**
   ```bash
   docker-compose ps
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Application secret key | `your-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///resource_management.db` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS for email | `true` |
| `MAIL_USERNAME` | Email username | - |
| `MAIL_PASSWORD` | Email password | - |
| `MAIL_DEFAULT_SENDER` | Default sender email | - |

### Database Configuration

The application supports multiple database backends:

#### SQLite (Default)
```bash
DATABASE_URL=sqlite:///resource_management.db
```

#### PostgreSQL
```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
```

#### MySQL
```bash
DATABASE_URL=mysql://user:password@localhost/dbname
```

### Email Configuration

#### Gmail Setup
1. Enable 2-factor authentication
2. Generate App Password
3. Use App Password in `MAIL_PASSWORD`

#### Custom SMTP
```bash
MAIL_SERVER=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
```

## Security Considerations

### 1. Change Default Credentials
- **Default Admin**: `admin` / `admin123`
- Change immediately after first login

### 2. Strong Secret Key
```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. HTTPS Only
- Application redirects HTTP to HTTPS
- SSL certificates required for production

### 4. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Monitoring & Maintenance

### Health Checks
```bash
# Check application health
curl https://yourdomain.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "database": "connected"
}
```

### Log Monitoring
```bash
# View application logs
docker-compose logs -f web

# View nginx logs
docker-compose logs -f nginx

# View all logs
docker-compose logs -f
```

### Database Backup
```bash
# Backup database
docker-compose exec web cp data/resource_management.db backup/

# Restore database
docker-compose exec web cp backup/resource_management.db data/
```

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Kill the process or change ports in docker-compose.yml
```

#### 2. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Regenerate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

#### 3. Database Connection Issues
```bash
# Check database files
ls -la data/

# Recreate database if needed
rm data/resource_management.db
docker-compose restart
```

#### 4. Email Not Working
- Check email credentials in `.env`
- Verify SMTP settings
- Check firewall settings
- Test with a simple email client

### Performance Optimization

#### 1. Database Optimization
```bash
# Optimize database (runs automatically)
docker-compose exec web python -c "from app import optimize_database; optimize_database()"
```

#### 2. Nginx Configuration
- Adjust worker processes in `nginx.conf`
- Configure caching for static files
- Enable gzip compression

#### 3. Docker Resources
```yaml
# In docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## Scaling Considerations

### Horizontal Scaling
```bash
# Scale web service
docker-compose up -d --scale web=3
```

### Load Balancer
```nginx
# Add to nginx.conf
upstream flask_app {
    server web1:8000;
    server web2:8000;
    server web3:8000;
}
```

### Database Scaling
- Consider PostgreSQL for larger deployments
- Implement read replicas
- Use connection pooling

## Backup Strategy

### Automated Backups
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz data/ logs/ uploads/
```

### Cron Job
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

## Support

For deployment issues:
1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Contact the development team

---

**© 2025 Taaleem charter schools. All rights reserved.** 
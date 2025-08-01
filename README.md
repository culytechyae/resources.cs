# School Resource Management System

A comprehensive web application for managing school resources, inventory, and requests with role-based access control and modern UI.

## 🌟 Features

### User Management
- **Super Admin**: Full system control, user management, database administration
- **School Admin**: Request approval, inventory management, reports
- **School Manager**: Approval workflow for high-value requests
- **Regular User**: Resource requests, cart functionality, status tracking

### Inventory Management
- E-commerce style inventory browsing
- Search and category filtering
- Real-time stock tracking
- Bulk upload via Excel files
- Automatic inventory reduction on request approval

### Request System
- Shopping cart functionality
- Multi-step approval workflow
- Status tracking (pending, approved, rejected, delivered)
- Conversational comment system
- Email notifications

### Reporting & Analytics
- Comprehensive reporting dashboard
- Export functionality (CSV, Excel)
- Analytics and trends
- Stock reports and sales summaries
- User activity tracking

### Security & Performance
- Session timeout (5 minutes inactivity)
- Database redundancy (5 backup files, 5GB each)
- Rate limiting and security headers
- Optimized for large datasets
- Modern, responsive UI

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Production Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Resource
   ```

2. **Run the deployment script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Access the application**
   - URL: https://localhost
   - Default admin: `admin` / `admin123`

### Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - URL: http://localhost:5001
   - Default admin: `admin` / `admin123`

## 📁 Project Structure

```
Resource/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── wsgi.py               # WSGI entry point
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── nginx.conf          # Nginx reverse proxy
├── deploy.sh           # Deployment script
├── env.example         # Environment template
├── templates/          # HTML templates
├── static/            # Static files (CSS, JS)
├── logs/              # Application logs
├── uploads/           # File uploads
└── data/              # Database files
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Database Configuration
DATABASE_URL=sqlite:///resource_management.db
```

### Email Setup

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in `MAIL_PASSWORD`

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

### Manual Docker Build

```bash
# Build image
docker build -t resource-management .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data resource-management
```

## 🔒 Security Features

- **HTTPS/SSL**: Automatic SSL termination with Nginx
- **Rate Limiting**: Protection against brute force attacks
- **Security Headers**: XSS protection, CSRF protection
- **Session Management**: Secure session handling
- **Input Validation**: Form validation and sanitization
- **SQL Injection Protection**: Parameterized queries

## 📊 Database Management

### Database Redundancy
- 5 SQLite database files (5GB each)
- Automatic switching when database is full
- Backup and restore functionality

### Database Optimization
- Connection pooling
- Indexed queries for performance
- WAL mode for better concurrency
- Regular cleanup of old data

## 📈 Monitoring & Logging

### Application Logs
- Rotating log files
- Structured logging
- Error tracking

### Health Checks
- Application health endpoint
- Database connectivity checks
- Email service monitoring

## 🔄 Backup & Recovery

### Database Backup
```bash
# Backup current database
cp data/resource_management.db backup/

# Restore from backup
cp backup/resource_management.db data/
```

### Full System Backup
```bash
# Backup entire application
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ uploads/
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   # Kill the process or change port in docker-compose.yml
   ```

2. **Database connection issues**
   ```bash
   # Check database files
   ls -la data/
   # Recreate database if needed
   rm data/resource_management.db
   docker-compose restart
   ```

3. **Email not working**
   - Check email credentials in `.env`
   - Verify SMTP settings
   - Check firewall settings

### Logs
```bash
# Application logs
docker-compose logs web

# Nginx logs
docker-compose logs nginx

# All logs
docker-compose logs -f
```

## 🔧 Development

### Adding New Features

1. **Create new routes in `app.py`**
2. **Add templates in `templates/`**
3. **Update navigation in `base.html`**
4. **Test thoroughly**

### Database Migrations

```python
# Add new model
class NewModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ... other fields

# Create tables
with app.app_context():
    db.create_all()
```

## 📝 API Documentation

### Authentication Endpoints
- `POST /login` - User login
- `GET /logout` - User logout
- `GET /check-session` - Session validation

### Inventory Endpoints
- `GET /inventory` - List inventory items
- `POST /add-to-cart` - Add item to cart
- `GET /cart` - View cart

### Request Endpoints
- `POST /submit-request` - Submit request
- `GET /admin/requests` - Admin view requests
- `POST /admin/request/<id>/<action>` - Update request status

### Report Endpoints
- `GET /reports` - Main reports page
- `GET /reports/export/requests` - Export requests
- `GET /reports/export/inventory` - Export inventory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section

## 🔄 Updates

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added school manager role and approval workflow
- **v1.2.0**: Enhanced UI and added comprehensive reporting
- **v1.3.0**: Production deployment support and security improvements

---

**© 2025 Taaleem charter schools. All rights reserved.** 
# Deployment Guides for School Resource Management System

This document provides step-by-step deployment instructions for various hosting platforms.

## 🚀 **Render Deployment** (Recommended)

### Prerequisites
- GitHub account
- Render account (free)

### Steps

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/school-resource-management.git
   git push -u origin main
   ```

2. **Create Render account and new Web Service**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the service**
   - **Name**: `school-resource-management`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Plan**: Free

4. **Add Environment Variables**
   ```
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-key
   DATABASE_URL=sqlite:///resource_management.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete
   - Access your app at the provided URL

## 🚂 **Railway Deployment**

### Steps

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set environment variables**
   ```bash
   railway variables set FLASK_ENV=production
   railway variables set SECRET_KEY=your-super-secret-key
   # Add other variables as needed
   ```

4. **Access your app**
   ```bash
   railway open
   ```

## ☁️ **Google Cloud Run Deployment**

### Prerequisites
- Google Cloud account
- Google Cloud CLI installed

### Steps

1. **Create Dockerfile** (already exists in your project)

2. **Build and deploy**
   ```bash
   # Set your project ID
   gcloud config set project YOUR_PROJECT_ID
   
   # Build the container
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/school-resource-management
   
   # Deploy to Cloud Run
   gcloud run deploy school-resource-management \
     --image gcr.io/YOUR_PROJECT_ID/school-resource-management \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Set environment variables**
   ```bash
   gcloud run services update school-resource-management \
     --set-env-vars FLASK_ENV=production,SECRET_KEY=your-secret-key
   ```

## 🐳 **DigitalOcean App Platform**

### Steps

1. **Create DigitalOcean account**

2. **Deploy from GitHub**
   - Go to DigitalOcean App Platform
   - Click "Create App"
   - Connect GitHub repository
   - Select branch

3. **Configure app**
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn wsgi:app`
   - **HTTP Port**: `8000`

4. **Add environment variables**
   - Add all required environment variables in the UI

5. **Deploy**
   - Click "Launch Basic App"
   - Wait for deployment

## 🐙 **Heroku Deployment**

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

3. **Add buildpacks**
   ```bash
   heroku buildpacks:set heroku/python
   ```

4. **Set environment variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-super-secret-key
   heroku config:set DATABASE_URL=sqlite:///resource_management.db
   # Add other variables
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Open app**
   ```bash
   heroku open
   ```

## 🖥️ **VPS Deployment (DigitalOcean/Linode)**

### Prerequisites
- VPS with Ubuntu 20.04+
- Domain name (optional)

### Steps

1. **Connect to your server**
   ```bash
   ssh root@your-server-ip
   ```

2. **Update system**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Install dependencies**
   ```bash
   apt install python3 python3-pip python3-venv nginx -y
   ```

4. **Create application user**
   ```bash
   adduser app
   usermod -aG sudo app
   ```

5. **Clone your repository**
   ```bash
   cd /home/app
   git clone https://github.com/yourusername/school-resource-management.git
   cd school-resource-management
   ```

6. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

7. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/school-resource-management.service
   ```

   Add this content:
   ```ini
   [Unit]
   Description=School Resource Management
   After=network.target

   [Service]
   User=app
   WorkingDirectory=/home/app/school-resource-management
   Environment="PATH=/home/app/school-resource-management/venv/bin"
   ExecStart=/home/app/school-resource-management/venv/bin/gunicorn wsgi:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

8. **Start the service**
   ```bash
   sudo systemctl enable school-resource-management
   sudo systemctl start school-resource-management
   ```

9. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/school-resource-management
   ```

   Add this content:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /home/app/school-resource-management/static/;
       }
   }
   ```

10. **Enable the site**
    ```bash
    sudo ln -s /etc/nginx/sites-available/school-resource-management /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. **Set up SSL (optional)**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d your-domain.com
    ```

## 🔧 **Environment Variables for All Platforms**

Create a `.env` file or set these environment variables:

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

## 📊 **Platform Comparison**

| Platform | Free Tier | Ease of Use | Performance | Cost (Paid) |
|----------|-----------|-------------|-------------|-------------|
| **Render** | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $7/month |
| **Railway** | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Pay-per-use |
| **Heroku** | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $7/month |
| **Google Cloud Run** | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Pay-per-use |
| **DigitalOcean App** | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $5/month |
| **VPS (DO/Linode)** | ❌ | ⭐⭐ | ⭐⭐⭐⭐⭐ | $4-5/month |

## 🎯 **Recommendations**

### **For Beginners**
1. **Render** - Easiest to deploy, good free tier
2. **Railway** - Simple, fast deployment
3. **Heroku** - Excellent documentation, but no free tier

### **For Production**
1. **Google Cloud Run** - Best performance, cost-effective
2. **DigitalOcean App Platform** - Reliable, predictable pricing
3. **VPS** - Full control, best performance

### **For Learning**
1. **VPS** - Learn server management
2. **Google Cloud Run** - Learn cloud-native deployment
3. **Render** - Quick deployment for testing

## 🚨 **Important Notes**

1. **Database**: For production, consider using PostgreSQL instead of SQLite
2. **Static Files**: Ensure static files are properly served
3. **SSL**: Always use HTTPS in production
4. **Backups**: Set up regular database backups
5. **Monitoring**: Use platform monitoring tools

## 🔗 **Quick Links**

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Heroku Documentation](https://devcenter.heroku.com)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [DigitalOcean App Platform](https://docs.digitalocean.com/products/app-platform) 
# Render Deployment Guide for School Resource Management System

This guide will walk you through deploying your School Resource Management Flask application on Render step by step.

## 🚀 **Prerequisites**

1. **GitHub account** - You'll need to push your code to GitHub
2. **Render account** - Sign up at [render.com](https://render.com)
3. **Your project files** - All the files from your School Resource Management app

## 📋 **Step 1: Prepare Your Code for GitHub**

### 1.1 Initialize Git Repository (if not already done)
```bash
# Navigate to your project directory
cd /path/to/your/school-resource-management

# Initialize git repository
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit - School Resource Management System"
```

### 1.2 Create GitHub Repository
1. Go to [github.com](https://github.com)
2. Click the "+" icon → "New repository"
3. Name it: `school-resource-management`
4. Make it **Public** (Render works better with public repos)
5. Don't initialize with README (you already have files)
6. Click "Create repository"

### 1.3 Push Code to GitHub
```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/school-resource-management.git

# Push to GitHub
git push -u origin main
```

## 🌐 **Step 2: Set Up Render Account**

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started"
3. Sign up with your GitHub account (recommended)
4. Complete the signup process

### 2.2 Connect GitHub (if not done during signup)
1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub account if prompted

## 🔧 **Step 3: Create Web Service on Render**

### 3.1 Start New Web Service
1. In Render dashboard, click **"New +"**
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click "Connect" next to your `school-resource-management` repository
   - Or search for your repository name

### 3.2 Configure the Web Service

Fill in the configuration details:

**Basic Settings:**
- **Name**: `school-resource-management` (or any name you prefer)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users (e.g., US East for US users)

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`
- **Plan**: `Free` (for testing)

**Advanced Settings:**
- **Auto-Deploy**: ✅ Yes (automatically deploys when you push to GitHub)
- **Branch**: `main` (or `master` if that's your default branch)

### 3.3 Add Environment Variables

Click on **"Environment"** tab and add these variables:

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

**Important Notes:**
- Replace `your-super-secret-key-change-this-in-production` with a strong secret key
- Replace `your-email@gmail.com` and `your-app-password` with your actual email credentials
- For Gmail, use an App Password (not your regular password)

### 3.4 Create the Service
1. Review all settings
2. Click **"Create Web Service"**
3. Wait for the build to complete (usually 2-5 minutes)

## ⏳ **Step 4: Monitor the Deployment**

### 4.1 Check Build Logs
During deployment, you can monitor the process:
1. Click on your service name
2. Go to **"Logs"** tab
3. Watch for any errors

**Common Build Issues & Solutions:**

**Issue**: `ModuleNotFoundError: No module named 'pandas'`
**Solution**: The build should work with your current `requirements.txt`, but if it fails, Render will show the error in logs.

**Issue**: `ImportError: No module named 'app'`
**Solution**: Make sure your `wsgi.py` file is in the root directory and properly configured.

### 4.2 Verify Deployment
Once the build completes successfully:
1. You'll see a green checkmark ✅
2. Your app URL will be displayed (e.g., `https://school-resource-management.onrender.com`)
3. Click the URL to test your application

## 🧪 **Step 5: Test Your Application**

### 5.1 Initial Testing
1. Visit your Render URL
2. You should see the login page
3. Test with default credentials:
   - **Username**: `admin`
   - **Password**: `admin123`

### 5.2 Test Key Features
- ✅ Login functionality
- ✅ Dashboard access
- ✅ Inventory browsing
- ✅ Cart functionality
- ✅ Admin features

### 5.3 Check for Issues
If you encounter issues:
1. Check the **"Logs"** tab in Render dashboard
2. Look for error messages
3. Common issues and solutions are listed below

## 🔧 **Step 6: Troubleshooting Common Issues**

### Issue 1: Application Not Loading
**Symptoms**: White page or 500 error
**Solutions**:
1. Check **"Logs"** tab for error messages
2. Verify environment variables are set correctly
3. Ensure `wsgi.py` file exists and is properly configured

### Issue 2: Database Errors
**Symptoms**: Database-related errors in logs
**Solutions**:
1. SQLite databases on Render are ephemeral (they reset on each deploy)
2. For production, consider using PostgreSQL
3. Check if database file has proper permissions

### Issue 3: Static Files Not Loading
**Symptoms**: CSS/JS files not loading, broken styling
**Solutions**:
1. Ensure static files are in the `static/` directory
2. Check that `wsgi.py` is properly configured
3. Verify file paths in templates

### Issue 4: Email Not Working
**Symptoms**: Email notifications not sending
**Solutions**:
1. Check email credentials in environment variables
2. For Gmail, use App Passwords
3. Verify SMTP settings

## 📊 **Step 7: Monitor and Maintain**

### 7.1 View Application Logs
1. Go to your service in Render dashboard
2. Click **"Logs"** tab
3. Monitor for errors or issues

### 7.2 Update Your Application
To update your application:
1. Make changes to your code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. Render will automatically redeploy

### 7.3 Check Service Status
- **Green**: Service is running
- **Yellow**: Service is building/deploying
- **Red**: Service has an error

## 🔒 **Step 8: Security Considerations**

### 8.1 Change Default Credentials
After successful deployment:
1. Log in with default credentials (`admin` / `admin123`)
2. Go to Admin Settings
3. Change the admin password immediately

### 8.2 Environment Variables Security
- Never commit sensitive data to GitHub
- Use Render's environment variables for secrets
- Regularly rotate your `SECRET_KEY`

### 8.3 SSL/HTTPS
- Render automatically provides SSL certificates
- Your app will be accessible via HTTPS
- No additional configuration needed

## 💰 **Step 9: Upgrade to Paid Plan (Optional)**

### When to Upgrade
- When you exceed 750 hours/month (free tier limit)
- When you need more resources
- For production applications

### Upgrade Process
1. Go to your service in Render dashboard
2. Click **"Settings"** tab
3. Click **"Change Plan"**
4. Select a paid plan (starts at $7/month)

## 📱 **Step 10: Custom Domain (Optional)**

### Add Custom Domain
1. Go to your service settings
2. Click **"Custom Domains"**
3. Add your domain name
4. Configure DNS settings as instructed

## 🎯 **Quick Reference Commands**

### Local Development
```bash
# Run locally
python app.py

# Test before deploying
pip install -r requirements.txt
gunicorn wsgi:app
```

### Git Commands
```bash
# Update and deploy
git add .
git commit -m "Update description"
git push origin main
```

### Render Dashboard
- **URL**: [dashboard.render.com](https://dashboard.render.com)
- **Service Logs**: Available in service dashboard
- **Environment Variables**: Manage in service settings

## 🆘 **Getting Help**

### Render Support
- **Documentation**: [render.com/docs](https://render.com/docs)
- **Community**: [render.com/community](https://render.com/community)
- **Support**: Available in Render dashboard

### Common Render URLs
- **Dashboard**: [dashboard.render.com](https://dashboard.render.com)
- **Documentation**: [render.com/docs](https://render.com/docs)
- **Status**: [status.render.com](https://status.render.com)

## ✅ **Deployment Checklist**

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] Environment variables set
- [ ] Build completed successfully
- [ ] Application accessible via URL
- [ ] Login functionality working
- [ ] Default password changed
- [ ] All features tested
- [ ] Monitoring set up

## 🎉 **Congratulations!**

Your School Resource Management System is now live on Render! 

**Your app URL**: `https://your-app-name.onrender.com`

**Next Steps**:
1. Test all features thoroughly
2. Change default admin password
3. Configure email settings
4. Set up monitoring
5. Consider upgrading to paid plan for production use

---

**Need help?** Check the troubleshooting section above or refer to Render's documentation. 
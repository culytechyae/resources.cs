# This is a modified version of app.py that can work without pandas
# For Render deployment to avoid pandas compatibility issues

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange
import json
import csv
from io import StringIO, BytesIO
import zipfile
from sqlalchemy import func, text, Index
from sqlalchemy.sql import extract
import logging
from logging.handlers import RotatingFileHandler
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///resource_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # super_admin, admin, school_manager, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.relationship('Comment', backref='request', lazy=True)
    items = db.relationship('RequestItem', backref='request', lazy=True)

class RequestItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    inventory = db.relationship('Inventory', backref='request_items')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='comments')

class EmailSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(100), default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(100))
    smtp_password = db.Column(db.String(100))
    use_tls = db.Column(db.Boolean, default=True)

# Forms
class InventoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    cost = IntegerField('Cost', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description')

class EmailSettingsForm(FlaskForm):
    smtp_server = StringField('SMTP Server', validators=[DataRequired()])
    smtp_port = IntegerField('SMTP Port', validators=[DataRequired()])
    smtp_username = StringField('SMTP Username', validators=[DataRequired(), Email()])
    smtp_password = PasswordField('SMTP Password', validators=[DataRequired()])
    use_tls = SelectField('Use TLS', choices=[('true', 'Yes'), ('false', 'No')])

# Database Manager for redundancy
class DatabaseManager:
    def __init__(self, app):
        self.app = app
        self.current_db_index = 0
        self.max_db_size = app.config.get('DATABASE_SIZE_LIMIT', 5 * 1024 * 1024 * 1024)  # 5GB
        self.backup_count = app.config.get('DATABASE_BACKUP_COUNT', 5)
    
    def get_current_database(self):
        return f"resource_management{self.current_db_index}.db"
    
    def get_database_size(self):
        db_path = self.get_current_database()
        if os.path.exists(db_path):
            return os.path.getsize(db_path)
        return 0
    
    def switch_to_next_database(self):
        self.current_db_index = (self.current_db_index + 1) % self.backup_count
        new_db_uri = f"sqlite:///resource_management{self.current_db_index}.db"
        self.app.config['SQLALCHEMY_DATABASE_URI'] = new_db_uri
        with self.app.app_context():
            db.create_all()
        return new_db_uri

# Initialize database manager
db_manager = DatabaseManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            session.permanent = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'super_admin':
        return render_template('super_admin_dashboard.html')
    elif current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'school_manager':
        return render_template('school_manager_dashboard.html')
    else:
        return render_template('user_dashboard.html')

@app.route('/inventory')
@login_required
def inventory():
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    query = Inventory.query
    
    if search:
        query = query.filter(Inventory.name.contains(search))
    if category_filter:
        query = query.filter(Inventory.category == category_filter)
    
    items = query.all()
    categories = db.session.query(Inventory.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('inventory.html', items=items, categories=categories)

@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if item_id in session['cart']:
        session['cart'][item_id] += quantity
    else:
        session['cart'][item_id] = quantity
    
    session.modified = True
    
    # Update cart count for notification
    cart_count = sum(session['cart'].values())
    
    return jsonify({
        'success': True,
        'message': 'Item added to cart successfully!',
        'cart_count': cart_count
    })

@app.route('/cart')
@login_required
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', items=[], total=0)
    
    cart_items = []
    total = 0
    
    for item_id, quantity in session['cart'].items():
        item = Inventory.query.get(item_id)
        if item:
            cart_items.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity': quantity,
                'cost': item.cost,
                'total': item.cost * quantity
            })
            total += item.cost * quantity
    
    return render_template('cart.html', items=cart_items, total=total)

@app.route('/submit-request', methods=['POST'])
@login_required
def submit_request():
    if 'cart' not in session or not session['cart']:
        return jsonify({'success': False, 'message': 'Cart is empty'})
    
    # Create request
    new_request = Request(user_id=current_user.id)
    db.session.add(new_request)
    db.session.flush()  # Get the request ID
    
    # Add items to request
    for item_id, quantity in session['cart'].items():
        inventory_item = Inventory.query.get(item_id)
        if inventory_item and inventory_item.quantity >= quantity:
            request_item = RequestItem(
                request_id=new_request.id,
                inventory_id=item_id,
                quantity=quantity
            )
            db.session.add(request_item)
    
    db.session.commit()
    
    # Clear cart
    session.pop('cart', None)
    
    # Send email notification
    try:
        msg = Message(
            'New Resource Request Submitted',
            recipients=[current_user.email]
        )
        msg.body = f'Your request has been submitted successfully. Request ID: {new_request.id}'
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
    
    return jsonify({'success': True, 'message': 'Request submitted successfully!'})

@app.route('/admin/requests')
@login_required
def admin_requests():
    if current_user.role not in ['admin', 'super_admin', 'school_manager']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    requests = Request.query.order_by(Request.created_at.desc()).all()
    return render_template('admin_requests.html', requests=requests)

@app.route('/admin/request/<int:request_id>/items')
@login_required
def get_request_items(request_id):
    if current_user.role not in ['admin', 'super_admin', 'school_manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        request_obj = Request.query.get_or_404(request_id)
        items = []
        
        for item in request_obj.items:
            items.append({
                'id': item.id,
                'name': item.inventory.name,
                'quantity': item.quantity,
                'cost': item.inventory.cost,
                'total': item.quantity * item.inventory.cost
            })
        
        return jsonify({'items': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/request/<int:request_id>/update_quantity', methods=['POST'])
@login_required
def update_request_item_quantity(request_id):
    if current_user.role not in ['admin', 'super_admin', 'school_manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        new_quantity = data.get('quantity')
        
        request_item = RequestItem.query.get_or_404(item_id)
        request_item.quantity = new_quantity
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Quantity updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/request/<int:request_id>/<action>')
@login_required
def update_request_status(request_id, action):
    if current_user.role not in ['admin', 'super_admin', 'school_manager']:
        flash('Access denied', 'error')
        return redirect(url_for('admin_requests'))
    
    request_obj = Request.query.get_or_404(request_id)
    
    if action == 'approve':
        request_obj.status = 'approved'
        # Reduce inventory quantities
        for item in request_obj.items:
            inventory_item = item.inventory
            inventory_item.quantity -= item.quantity
        flash('Request approved successfully!', 'success')
    
    elif action == 'reject':
        request_obj.status = 'rejected'
        flash('Request rejected successfully!', 'success')
    
    elif action == 'deliver':
        request_obj.status = 'delivered'
        flash('Request marked as delivered!', 'success')
    
    db.session.commit()
    
    # Send email notification
    try:
        status_msg = {
            'approved': 'approved',
            'rejected': 'rejected',
            'delivered': 'delivered'
        }.get(action, action)
        
        msg = Message(
            f'Request {status_msg.title()}',
            recipients=[request_obj.user.email]
        )
        msg.body = f'Your request (ID: {request_obj.id}) has been {status_msg}.'
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
    
    return redirect(url_for('admin_requests'))

@app.route('/request/<int:request_id>/comment', methods=['POST'])
@login_required
def add_comment(request_id):
    request_obj = Request.query.get_or_404(request_id)
    
    # Check if user has permission to comment
    if current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    comment_text = request.form.get('comment')
    if comment_text:
        comment = Comment(
            request_id=request_id,
            user_id=current_user.id,
            comment=comment_text
        )
        db.session.add(comment)
        db.session.commit()
        
        # Send email notification
        try:
            msg = Message(
                'New Comment on Request',
                recipients=[request_obj.user.email]
            )
            msg.body = f'A new comment has been added to your request (ID: {request_id}).'
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
    
    return redirect(url_for('view_request', request_id=request_id))

@app.route('/request/<int:request_id>/view')
@login_required
def view_request(request_id):
    request_obj = Request.query.get_or_404(request_id)
    
    # Check if user has permission to view
    if current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('view_request.html', request=request_obj)

@app.route('/request/<int:request_id>/comments')
@login_required
def get_comments(request_id):
    request_obj = Request.query.get_or_404(request_id)
    
    # Check if user has permission to view comments
    if current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    comments = Comment.query.filter_by(request_id=request_id).order_by(Comment.created_at).all()
    comments_data = []
    
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'comment': comment.comment,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'comments': comments_data})

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'super_admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/new-user', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.role != 'super_admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('new_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('new_user.html')
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('new_user.html')

@app.route('/admin/inventory')
@login_required
def admin_inventory():
    if current_user.role not in ['admin', 'super_admin']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    items = Inventory.query.all()
    return render_template('admin_inventory.html', items=items)

@app.route('/admin/new-inventory', methods=['GET', 'POST'])
@login_required
def new_inventory():
    if current_user.role not in ['admin', 'super_admin']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    form = InventoryForm()
    if form.validate_on_submit():
        item = Inventory(
            name=form.name.data,
            category=form.category.data,
            quantity=form.quantity.data,
            cost=form.cost.data,
            description=form.description.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('admin_inventory'))
    
    return render_template('new_inventory.html', form=form)

@app.route('/admin/settings')
@login_required
def admin_settings():
    if current_user.role != 'super_admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    form = EmailSettingsForm()
    if form.validate_on_submit():
        # Update email settings
        app.config['MAIL_SERVER'] = form.smtp_server.data
        app.config['MAIL_PORT'] = form.smtp_port.data
        app.config['MAIL_USERNAME'] = form.smtp_username.data
        app.config['MAIL_PASSWORD'] = form.smtp_password.data
        app.config['MAIL_USE_TLS'] = form.use_tls.data == 'true'
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin_settings.html', form=form)

@app.route('/reports')
@login_required
def reports():
    if current_user.role not in ['admin', 'super_admin']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('reports.html')

@app.route('/reports/export/requests')
@login_required
def export_requests():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    requests = Request.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'User', 'Status', 'Created At', 'Updated At'])
    
    for req in requests:
        user = User.query.get(req.user_id)
        writer.writerow([
            req.id,
            user.username if user else 'Unknown',
            req.status,
            req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            req.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'requests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/reports/export/inventory')
@login_required
def export_inventory():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    items = Inventory.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Quantity', 'Cost', 'Description', 'Created At'])
    
    for item in items:
        writer.writerow([
            item.id,
            item.name,
            item.category,
            item.quantity,
            item.cost,
            item.description or '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/reports/export/all')
@login_required
def export_all_data():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    # Create ZIP file with all data
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        # Export users
        users = User.query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        users_output = StringIO()
        writer = csv.writer(users_output)
        writer.writerow(['ID', 'Username', 'Email', 'Role', 'Created At'])
        for user_data in users_data:
            writer.writerow([
                user_data['id'],
                user_data['username'],
                user_data['email'],
                user_data['role'],
                user_data['created_at']
            ])
        zf.writestr('users.csv', users_output.getvalue())
        
        # Export requests
        requests = Request.query.all()
        requests_data = []
        for req in requests:
            user = User.query.get(req.user_id)
            requests_data.append({
                'id': req.id,
                'user': user.username if user else 'Unknown',
                'status': req.status,
                'created_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': req.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        requests_output = StringIO()
        writer = csv.writer(requests_output)
        writer.writerow(['ID', 'User', 'Status', 'Created At', 'Updated At'])
        for req_data in requests_data:
            writer.writerow([
                req_data['id'],
                req_data['user'],
                req_data['status'],
                req_data['created_at'],
                req_data['updated_at']
            ])
        zf.writestr('requests.csv', requests_output.getvalue())
        
        # Export inventory
        items = Inventory.query.all()
        inventory_data = []
        for item in items:
            inventory_data.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity': item.quantity,
                'cost': item.cost,
                'description': item.description or '',
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        inventory_output = StringIO()
        writer = csv.writer(inventory_output)
        writer.writerow(['ID', 'Name', 'Category', 'Quantity', 'Cost', 'Description', 'Created At'])
        for item_data in inventory_data:
            writer.writerow([
                item_data['id'],
                item_data['name'],
                item_data['category'],
                item_data['quantity'],
                item_data['cost'],
                item_data['description'],
                item_data['created_at']
            ])
        zf.writestr('inventory.csv', inventory_output.getvalue())
        
        # Export request items
        request_items = RequestItem.query.all()
        request_items_data = []
        for item in request_items:
            request = Request.query.get(item.request_id)
            inventory = Inventory.query.get(item.inventory_id)
            request_items_data.append({
                'id': item.id,
                'request_id': item.request_id,
                'inventory_name': inventory.name if inventory else 'Unknown',
                'quantity': item.quantity
            })
        
        request_items_output = StringIO()
        writer = csv.writer(request_items_output)
        writer.writerow(['ID', 'Request ID', 'Inventory Name', 'Quantity'])
        for item_data in request_items_data:
            writer.writerow([
                item_data['id'],
                item_data['request_id'],
                item_data['inventory_name'],
                item_data['quantity']
            ])
        zf.writestr('request_items.csv', request_items_output.getvalue())
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    )

@app.route('/session-timeout')
def session_timeout():
    return render_template('session_timeout.html')

@app.route('/check-session')
@login_required
def check_session():
    return jsonify({'valid': True})

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create super admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True, port=5001) 
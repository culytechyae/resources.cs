from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import os
import io
import csv
from datetime import datetime, timedelta
from sqlalchemy import func, Index, text
from flask_mail import Mail, Message
import logging
from logging.handlers import RotatingFileHandler
import json

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Setup login manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Resource Management startup')
    
    # Register blueprints (if any)
    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint)
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all application routes"""
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Database Models
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False, index=True)
        email = db.Column(db.String(120), unique=True, nullable=False, index=True)
        password_hash = db.Column(db.String(255), nullable=False)
        role = db.Column(db.String(20), nullable=False, default='user', index=True)
        school = db.Column(db.String(100), nullable=True, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        is_active = db.Column(db.Boolean, default=True, index=True)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    class Inventory(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False, index=True)
        description = db.Column(db.Text)
        quantity = db.Column(db.Integer, default=0, index=True)
        cost = db.Column(db.Float, default=0.0, index=True)
        category = db.Column(db.String(50), index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    class Request(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        status = db.Column(db.String(20), default='pending', index=True)
        total_cost = db.Column(db.Float, default=0.0, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
        user = db.relationship('User', backref='requests')
        items = db.relationship('RequestItem', backref='request', lazy=True)

    class RequestItem(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False, index=True)
        inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False, index=True)
        quantity = db.Column(db.Integer, nullable=False, index=True)
        cost = db.Column(db.Float, default=0.0, index=True)
        inventory = db.relationship('Inventory')

    class Comment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        comment = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        request = db.relationship('Request', backref='comments')
        user = db.relationship('User', backref='comments')

    # Database Indexes
    db.Index('idx_request_user_status', Request.user_id, Request.status)
    db.Index('idx_request_created_status', Request.created_at, Request.status)
    db.Index('idx_inventory_category_quantity', Inventory.category, Inventory.quantity)
    db.Index('idx_inventory_cost_quantity', Inventory.cost, Inventory.quantity)
    db.Index('idx_requestitem_request_inventory', RequestItem.request_id, RequestItem.inventory_id)

    # Forms
    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    class UserForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
        email = StringField('Email', validators=[DataRequired(), Email()])
        password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
        role = SelectField('Role', choices=[
            ('user', 'User'),
            ('admin', 'School Admin'),
            ('school_manager', 'School Manager'),
            ('super_admin', 'Super Admin')
        ])
        school = StringField('School')
        submit = SubmitField('Create User')

    class CommentForm(FlaskForm):
        comment = TextAreaField('Comment', validators=[DataRequired()])
        submit = SubmitField('Add Comment')

    class InventoryForm(FlaskForm):
        name = StringField('Name', validators=[DataRequired()])
        description = TextAreaField('Description')
        quantity = IntegerField('Quantity', validators=[DataRequired()])
        cost = StringField('Cost', validators=[DataRequired()])
        category = StringField('Category')

    class EmailSettingsForm(FlaskForm):
        smtp_server = StringField('SMTP Server', validators=[DataRequired()])
        smtp_port = IntegerField('SMTP Port', validators=[DataRequired()])
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        use_tls = SelectField('Use TLS', choices=[(True, 'Yes'), (False, 'No')])

    class EmailSettings(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        smtp_server = db.Column(db.String(100), nullable=False)
        smtp_port = db.Column(db.Integer, nullable=False)
        username = db.Column(db.String(100), nullable=False)
        password = db.Column(db.String(100), nullable=False)
        use_tls = db.Column(db.Boolean, default=True)

    # Database Management
    class DatabaseManager:
        def __init__(self, app):
            self.app = app
            self.db_files = [
                'resource_management.db',
                'resource_management2.db',
                'resource_management3.db',
                'resource_management4.db',
                'resource_management5.db'
            ]
            self.current_db_index = 0
            self.size_limit = app.config['DATABASE_SIZE_LIMIT']

        def get_current_database(self):
            return self.db_files[self.current_db_index]

        def get_database_size(self, db_file):
            if os.path.exists(db_file):
                return os.path.getsize(db_file)
            return 0

        def check_and_switch_if_needed(self):
            current_db = self.get_current_database()
            current_size = self.get_database_size(current_db)
            
            if current_size >= self.size_limit:
                print(f"Database {current_db} is full ({current_size} bytes). Switching to next database...")
                self.switch_to_next_database()
                return True
            return False

        def switch_to_next_database(self):
            self.current_db_index = (self.current_db_index + 1) % len(self.db_files)
            new_db = self.get_current_database()
            print(f"Switched to database: {new_db}")
            
            # Update SQLAlchemy URI
            self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{new_db}'
            
            # Recreate tables in new database
            with self.app.app_context():
                db.create_all()

        def get_all_database_stats(self):
            stats = []
            for i, db_file in enumerate(self.db_files):
                size = self.get_database_size(db_file)
                is_current = (i == self.current_db_index)
                stats.append({
                    'name': db_file,
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'is_current': is_current,
                    'is_full': size >= self.size_limit
                })
            return stats

    # Initialize database manager
    db_manager = DatabaseManager(app)

    # Database optimization functions
    def optimize_database():
        with app.app_context():
            db.session.execute(text("PRAGMA journal_mode=WAL"))
            db.session.execute(text("PRAGMA cache_size=65536"))
            db.session.execute(text("PRAGMA temp_store=MEMORY"))
            db.session.execute(text("PRAGMA foreign_keys=ON"))
            db.session.execute(text("ANALYZE"))
            db.session.commit()

    def get_database_stats():
        with app.app_context():
            user_count = db.session.execute(text("SELECT COUNT(*) FROM user")).scalar()
            inventory_count = db.session.execute(text("SELECT COUNT(*) FROM inventory")).scalar()
            request_count = db.session.execute(text("SELECT COUNT(*) FROM request")).scalar()
            comment_count = db.session.execute(text("SELECT COUNT(*) FROM comment")).scalar()
            
            tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            
            return {
                'users': user_count,
                'inventory': inventory_count,
                'requests': request_count,
                'comments': comment_count,
                'tables': [table[0] for table in tables]
            }

    def bulk_insert_inventory(data):
        with app.app_context():
            inventory_items = []
            for _, row in data.iterrows():
                item = Inventory(
                    name=row['name'],
                    description=row.get('description', ''),
                    quantity=row['quantity'],
                    cost=row['cost'],
                    category=row.get('category', 'General')
                )
                inventory_items.append(item)
            
            db.session.bulk_save_objects(inventory_items)
            db.session.commit()

    def cleanup_old_data():
        with app.app_context():
            # Delete requests older than 1 year
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            old_requests = Request.query.filter(Request.created_at < one_year_ago).all()
            for req in old_requests:
                db.session.delete(req)
            
            # Delete comments older than 1 year
            old_comments = Comment.query.filter(Comment.created_at < one_year_ago).all()
            for comment in old_comments:
                db.session.delete(comment)
            
            db.session.commit()

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
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                session.permanent = True
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role == 'super_admin':
            return render_template('admin_dashboard.html')
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
        
        query = Inventory.query.filter(Inventory.quantity > 0)
        
        if search:
            query = query.filter(Inventory.name.ilike(f'%{search}%'))
        
        if category_filter:
            query = query.filter(Inventory.category == category_filter)
        
        items = query.all()
        categories = db.session.query(Inventory.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('inventory.html', items=items, categories=categories, search=search, category_filter=category_filter)

    @app.route('/cart')
    @login_required
    def cart():
        cart_data = request.cookies.get('cart', '{}')
        try:
            cart_items = json.loads(cart_data)
        except:
            cart_items = {}
        
        items = []
        total_cost = 0
        
        for item_id, quantity in cart_items.items():
            item = Inventory.query.get(item_id)
            if item and item.quantity >= quantity:
                items.append({
                    'id': item.id,
                    'name': item.name,
                    'quantity': quantity,
                    'cost': item.cost,
                    'total': item.cost * quantity
                })
                total_cost += item.cost * quantity
        
        return render_template('cart.html', items=items, total_cost=total_cost)

    @app.route('/add-to-cart', methods=['POST'])
    @login_required
    def add_to_cart():
        item_id = request.form.get('item_id')
        quantity = int(request.form.get('quantity', 1))
        
        item = Inventory.query.get(item_id)
        if not item or item.quantity < quantity:
            return jsonify({'success': False, 'message': 'Item not available'})
        
        # Get current cart
        cart_data = request.cookies.get('cart', '{}')
        try:
            cart_items = json.loads(cart_data)
        except:
            cart_items = {}
        
        # Update cart
        if item_id in cart_items:
            cart_items[item_id] += quantity
        else:
            cart_items[item_id] = quantity
        
        response = jsonify({'success': True, 'message': 'Added to cart'})
        response.set_cookie('cart', json.dumps(cart_items))
        return response

    @app.route('/submit-request', methods=['POST'])
    @login_required
    def submit_request():
        db_manager.check_and_switch_if_needed()
        
        cart_data = request.cookies.get('cart', '{}')
        try:
            cart_items = json.loads(cart_data)
        except:
            return jsonify({'success': False, 'message': 'Invalid cart data'})
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'})
        
        total_cost = 0
        request_items = []
        
        for item_id, quantity in cart_items.items():
            item = Inventory.query.get(item_id)
            if item and item.quantity >= quantity:
                total_cost += item.cost * quantity
                request_items.append({
                    'item': item,
                    'quantity': quantity,
                    'cost': item.cost
                })
        
        if not request_items:
            return jsonify({'success': False, 'message': 'No valid items in cart'})
        
        # Create request
        new_request = Request(
            user_id=current_user.id,
            status='pending',
            total_cost=total_cost
        )
        db.session.add(new_request)
        db.session.flush()  # Get the request ID
        
        # Create request items
        for item_data in request_items:
            request_item = RequestItem(
                request_id=new_request.id,
                inventory_id=item_data['item'].id,
                quantity=item_data['quantity'],
                cost=item_data['cost']
            )
            db.session.add(request_item)
            
            # Update inventory
            item_data['item'].quantity -= item_data['quantity']
        
        db.session.commit()
        
        # Send email notification
        try:
            msg = Message(
                'New Resource Request',
                recipients=[current_user.email],
                body=f'Your request for ${total_cost:.2f} has been submitted and is pending approval.'
            )
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
        
        return jsonify({'success': True, 'message': 'Request submitted successfully'})

    @app.route('/admin/requests')
    @login_required
    def admin_requests():
        if current_user.role not in ['admin', 'super_admin']:
            return redirect(url_for('dashboard'))
        
        requests = Request.query.all()
        return render_template('admin_requests.html', requests=requests)

    @app.route('/admin/request/<int:request_id>/<action>')
    @login_required
    def update_request_status(request_id, action):
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        request_obj = Request.query.get(request_id)
        if not request_obj:
            flash('Request not found')
            return redirect(url_for('admin_requests'))
        
        # Check if user has permission to modify this request
        if current_user.role == 'school_manager' and request_obj.status != 'pending_manager_approval':
            flash('You can only approve requests pending manager approval')
            return redirect(url_for('admin_requests'))
        
        if action == 'approve':
            if current_user.role == 'admin':
                # Admin can either approve directly or send to manager
                if request.args.get('send_to_manager') == 'true':
                    request_obj.status = 'pending_manager_approval'
                    flash('Request sent to school manager for approval')
                else:
                    request_obj.status = 'approved'
                    # Reduce inventory
                    for item in request_obj.items:
                        inventory_item = Inventory.query.get(item.inventory_id)
                        if inventory_item:
                            inventory_item.quantity -= item.quantity
                    flash('Request approved')
            elif current_user.role == 'school_manager':
                request_obj.status = 'approved'
                # Reduce inventory
                for item in request_obj.items:
                    inventory_item = Inventory.query.get(item.inventory_id)
                    if inventory_item:
                        inventory_item.quantity -= item.quantity
                flash('Request approved by school manager')
        
        elif action == 'reject':
            request_obj.status = 'rejected'
            flash('Request rejected')
        
        elif action == 'deliver':
            if current_user.role in ['admin', 'super_admin']:
                request_obj.status = 'delivered'
                flash('Request delivered')
            else:
                flash('Only admins can deliver requests')
                return redirect(url_for('admin_requests'))
        
        request_obj.admin_notes = request.args.get('notes', '')
        db.session.commit()
        
        # Send email notification
        user = User.query.get(request_obj.user_id)
        status_message = 'approved' if action == 'approve' else action
        try:
            msg = Message(
                f'Request {status_message.title()}',
                recipients=[user.email],
                body=f'Your request #{request_id} has been {status_message}.'
            )
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
        
        return redirect(url_for('admin_requests'))

    @app.route('/admin/request/<int:request_id>/items')
    @login_required
    def get_request_items(request_id):
        try:
            if current_user.role not in ['admin', 'super_admin', 'school_manager']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            request_obj = Request.query.get(request_id)
            if not request_obj:
                return jsonify({'error': 'Request not found'}), 404
            
            items = []
            for item in request_obj.items:
                inventory_item = Inventory.query.get(item.inventory_id)
                items.append({
                    'id': item.id,
                    'inventory_id': item.inventory_id,
                    'name': inventory_item.name if inventory_item else 'Unknown Item',
                    'description': inventory_item.description if inventory_item else '',
                    'quantity': item.quantity,
                    'cost': item.cost,
                    'total': item.quantity * item.cost,
                    'available_quantity': inventory_item.quantity if inventory_item else 0
                })
            
            return jsonify({
                'request_id': request_id,
                'user': request_obj.user.username,
                'status': request_obj.status,
                'total_cost': request_obj.total_cost,
                'created_at': request_obj.created_at.strftime('%Y-%m-%d %H:%M'),
                'notes': request_obj.notes,
                'admin_notes': request_obj.admin_notes,
                'items': items
            })
        except Exception as e:
            print(f"Error in get_request_items: {e}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/admin/request/<int:request_id>/update_quantity', methods=['POST'])
    @login_required
    def update_request_item_quantity(request_id):
        try:
            if current_user.role not in ['admin', 'super_admin']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            data = request.get_json()
            item_id = data.get('item_id')
            new_quantity = data.get('quantity')
            
            if not item_id or not new_quantity:
                return jsonify({'error': 'Missing required data'}), 400
            
            request_item = RequestItem.query.get(item_id)
            if not request_item or request_item.request_id != request_id:
                return jsonify({'error': 'Item not found'}), 404
            
            # Check if new quantity is available in inventory
            inventory_item = Inventory.query.get(request_item.inventory_id)
            if not inventory_item:
                return jsonify({'error': 'Inventory item not found'}), 404
            
            # Calculate available quantity (considering current request)
            current_request_quantity = request_item.quantity
            available_quantity = inventory_item.quantity + current_request_quantity
            
            if new_quantity > available_quantity:
                return jsonify({'error': f'Only {available_quantity} items available'}), 400
            
            # Update quantity
            old_quantity = request_item.quantity
            request_item.quantity = new_quantity
            request_item.cost = inventory_item.cost
            
            # Update request total cost
            request_obj = Request.query.get(request_id)
            total_cost = 0
            for item in request_obj.items:
                total_cost += item.quantity * item.cost
            request_obj.total_cost = total_cost
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Quantity updated from {old_quantity} to {new_quantity}',
                'new_total_cost': total_cost
            })
        except Exception as e:
            print(f"Error in update_request_item_quantity: {e}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/request/<int:request_id>/comments')
    @login_required
    def get_request_comments(request_id):
        request_obj = Request.query.get(request_id)
        if not request_obj:
            return jsonify({'error': 'Request not found'}), 404
        
        # Check if user has permission to view comments
        # Users can only view their own requests, but admins and school managers can view any request
        if current_user.role == 'user' and request_obj.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        elif current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        comments = Comment.query.filter_by(request_id=request_id).order_by(Comment.created_at).all()
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'user': comment.user.username,
                'comment': comment.comment,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({'comments': comments_data})

    @app.route('/request/<int:request_id>/add_comment', methods=['POST'])
    @login_required
    def add_comment(request_id):
        request_obj = Request.query.get(request_id)
        if not request_obj:
            return jsonify({'error': 'Request not found'}), 404
        
        # Check if user has permission to add comments
        # Users can only comment on their own requests, but admins and school managers can comment on any request
        if current_user.role == 'user' and request_obj.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        elif current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        comment_text = data.get('comment')
        
        if not comment_text:
            return jsonify({'error': 'Comment is required'}), 400
        
        new_comment = Comment(
            request_id=request_id,
            user_id=current_user.id,
            comment=comment_text
        )
        db.session.add(new_comment)
        db.session.commit()
        
        # Send email notification to request owner
        if current_user.id != request_obj.user_id:
            user = User.query.get(request_obj.user_id)
            try:
                msg = Message(
                    'New Comment on Request',
                    recipients=[user.email],
                    body=f'A new comment has been added to your request #{request_id}.'
                )
                mail.send(msg)
            except Exception as e:
                app.logger.error(f"Failed to send email: {e}")
        
        return jsonify({'success': True, 'message': 'Comment added successfully'})

    @app.route('/request/<int:request_id>/view')
    @login_required
    def view_request_comments(request_id):
        request_obj = Request.query.get(request_id)
        if not request_obj:
            flash('Request not found')
            return redirect(url_for('dashboard'))
        
        # Check if user has permission to view this request
        # Users can only view their own requests, but admins and school managers can view any request
        if current_user.role == 'user' and request_obj.user_id != current_user.id:
            flash('You can only view your own requests')
            return redirect(url_for('dashboard'))
        elif current_user.role not in ['admin', 'super_admin', 'school_manager'] and request_obj.user_id != current_user.id:
            flash('You can only view your own requests')
            return redirect(url_for('dashboard'))
        
        return render_template('request_comments.html', request=request_obj)

    @app.route('/school-manager/requests')
    @login_required
    def school_manager_requests():
        if current_user.role != 'school_manager':
            return redirect(url_for('dashboard'))
        
        # Get requests pending manager approval
        pending_requests = Request.query.filter_by(status='pending_manager_approval').all()
        return render_template('school_manager_requests.html', requests=pending_requests)

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/user/new', methods=['GET', 'POST'])
    @login_required
    def new_user():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        form = UserForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
                school=form.school.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User created successfully')
            return redirect(url_for('admin_users'))
        
        return render_template('new_user.html', form=form)

    @app.route('/admin/inventory')
    @login_required
    def admin_inventory():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        search = request.args.get('search', '')
        category_filter = request.args.get('category', '')
        
        # Base query - all items
        query = Inventory.query
        
        # Apply search filter if provided
        if search:
            query = query.filter(Inventory.name.ilike(f'%{search}%'))
        
        # Apply category filter if provided
        if category_filter:
            query = query.filter(Inventory.category == category_filter)
        
        items = query.all()
        
        # Get unique categories for filter dropdown
        categories = db.session.query(Inventory.category).filter(
            Inventory.category.isnot(None),
            Inventory.category != ''
        ).distinct().all()
        categories = [cat[0] for cat in categories]
        
        return render_template('admin_inventory.html', items=items, categories=categories, search=search, category_filter=category_filter)

    @app.route('/admin/inventory/new', methods=['GET', 'POST'])
    @login_required
    def new_inventory():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        form = InventoryForm()
        if form.validate_on_submit():
            item = Inventory(
                name=form.name.data,
                description=form.description.data,
                quantity=form.quantity.data,
                cost=float(form.cost.data),
                category=form.category.data
            )
            db.session.add(item)
            db.session.commit()
            flash('Inventory item created successfully')
            return redirect(url_for('admin_inventory'))
        
        return render_template('new_inventory.html', form=form)

    @app.route('/admin/inventory/upload', methods=['GET', 'POST'])
    @login_required
    def upload_inventory():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file selected')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            
            if file and file.filename.endswith('.xlsx'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                try:
                    df = pd.read_excel(filepath)
                    
                    # Convert DataFrame to list of dictionaries for bulk insert
                    items_data = []
                    for _, row in df.iterrows():
                        items_data.append({
                            'name': row['name'],
                            'description': row.get('description', ''),
                            'quantity': int(row['quantity']),
                            'cost': float(row['cost']),
                            'category': row.get('category', '')
                        })
                    
                    # Use bulk insert for better performance with large datasets
                    bulk_insert_inventory(df)
                    
                    flash(f'Inventory uploaded successfully: {len(items_data)} items')
                except Exception as e:
                    flash(f'Error uploading inventory: {str(e)}')
                
                os.remove(filepath)
        
        return render_template('upload_inventory.html')

    @app.route('/admin/settings')
    @login_required
    def admin_settings():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        settings = EmailSettings.query.first()
        form = EmailSettingsForm(obj=settings)
        
        if form.validate_on_submit():
            if settings:
                settings.smtp_server = form.smtp_server.data
                settings.smtp_port = form.smtp_port.data
                settings.username = form.username.data
                settings.password = form.password.data
                settings.use_tls = form.use_tls.data
            else:
                settings = EmailSettings(
                    smtp_server=form.smtp_server.data,
                    smtp_port=form.smtp_port.data,
                    username=form.username.data,
                    password=form.password.data,
                    use_tls=form.use_tls.data
                )
                db.session.add(settings)
            
            db.session.commit()
            flash('Settings updated successfully')
            return redirect(url_for('admin_settings'))
        
        return render_template('admin_settings.html', form=form)

    @app.route('/reports')
    @login_required
    def reports():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Generate reports
        total_requests = Request.query.count()
        pending_requests = Request.query.filter_by(status='pending').count()
        approved_requests = Request.query.filter_by(status='approved').count()
        delivered_requests = Request.query.filter_by(status='delivered').count()
        rejected_requests = Request.query.filter_by(status='rejected').count()
        
        # Monthly statistics
        current_month = datetime.now().month
        monthly_requests = Request.query.filter(
            db.extract('month', Request.created_at) == current_month
        ).count()
        
        # Analytics data
        # Get requests by month for the last 6 months
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = db.session.query(
            extract('month', Request.created_at).label('month'),
            func.count(Request.id).label('count')
        ).filter(Request.created_at >= six_months_ago).group_by(
            extract('month', Request.created_at)
        ).all()
        
        # Get top requested items with current inventory quantity
        top_items = db.session.query(
            Inventory.name,
            Inventory.quantity,
            func.sum(RequestItem.quantity).label('total_requested')
        ).join(RequestItem).group_by(Inventory.name, Inventory.quantity).order_by(
            func.sum(RequestItem.quantity).desc()
        ).limit(10).all()
        
        # Get total inventory value
        total_inventory_value = db.session.query(
            func.sum(Inventory.quantity * Inventory.cost)
        ).scalar() or 0
        
        return render_template('reports.html',
                             total_requests=total_requests,
                             pending_requests=pending_requests,
                             approved_requests=approved_requests,
                             delivered_requests=delivered_requests,
                             rejected_requests=rejected_requests,
                             monthly_requests=monthly_requests,
                             monthly_data=monthly_data,
                             top_items=top_items,
                             total_inventory_value=total_inventory_value)

    @app.route('/reports/export/requests')
    @login_required
    def export_requests():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get all requests with details
        requests = Request.query.all()
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Request ID', 'User', 'Status', 'Total Cost', 'Created Date', 'Notes', 'Admin Notes'])
        
        for req in requests:
            writer.writerow([
                req.id,
                req.user.username,
                req.status,
                f"${req.total_cost:.2f}",
                req.created_at.strftime('%Y-%m-%d %H:%M'),
                req.notes or '',
                req.admin_notes or ''
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'requests_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/reports/export/inventory')
    @login_required
    def export_inventory():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get all inventory items
        inventory_items = Inventory.query.all()
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Description', 'Quantity', 'Cost', 'Category', 'Total Value', 'Last Updated'])
        
        for item in inventory_items:
            total_value = item.quantity * item.cost
            writer.writerow([
                item.id,
                item.name,
                item.description or '',
                item.quantity,
                f"${item.cost:.2f}",
                item.category or '',
                f"${total_value:.2f}",
                item.updated_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'inventory_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/reports/export/all')
    @login_required
    def export_all_data():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Create Excel file with multiple sheets
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Users sheet
            users_data = []
            for user in User.query.all():
                users_data.append({
                    'ID': user.id,
                    'Username': user.username,
                    'Email': user.email,
                    'Role': user.role,
                    'School': user.school or '',
                    'Created At': user.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Is Active': user.is_active
                })
            pd.DataFrame(users_data).to_excel(writer, sheet_name='Users', index=False)
            
            # Requests sheet
            requests_data = []
            for req in Request.query.all():
                requests_data.append({
                    'ID': req.id,
                    'User': req.user.username,
                    'Status': req.status,
                    'Total Cost': req.total_cost,
                    'Created Date': req.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Notes': req.notes or '',
                    'Admin Notes': req.admin_notes or ''
                })
            pd.DataFrame(requests_data).to_excel(writer, sheet_name='Requests', index=False)
            
            # Inventory sheet
            inventory_data = []
            for item in Inventory.query.all():
                inventory_data.append({
                    'ID': item.id,
                    'Name': item.name,
                    'Description': item.description or '',
                    'Quantity': item.quantity,
                    'Cost': item.cost,
                    'Category': item.category or '',
                    'Total Value': item.quantity * item.cost,
                    'Created At': item.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Updated At': item.updated_at.strftime('%Y-%m-%d %H:%M')
                })
            pd.DataFrame(inventory_data).to_excel(writer, sheet_name='Inventory', index=False)
            
            # Request Items sheet
            request_items_data = []
            for item in RequestItem.query.all():
                request_items_data.append({
                    'ID': item.id,
                    'Request ID': item.request_id,
                    'User': item.request.user.username,
                    'Item Name': item.inventory.name,
                    'Quantity': item.quantity,
                    'Cost': item.cost,
                    'Total': item.quantity * item.cost
                })
            pd.DataFrame(request_items_data).to_excel(writer, sheet_name='Request Items', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'all_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    @app.route('/reports/analytics')
    @login_required
    def analytics_report():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get analytics data
        # Monthly trends for the last 6 months
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_trends = db.session.query(
            extract('month', Request.created_at).label('month'),
            func.count(Request.id).label('count'),
            func.sum(Request.total_cost).label('total_cost')
        ).filter(Request.created_at >= six_months_ago).group_by(
            extract('month', Request.created_at)
        ).all()
        
        # Status distribution
        status_distribution = db.session.query(
            Request.status,
            func.count(Request.id).label('count')
        ).group_by(Request.status).all()
        
        # Top requested items
        top_items = db.session.query(
            Inventory.name,
            func.sum(RequestItem.quantity).label('total_requested'),
            func.sum(RequestItem.quantity * RequestItem.cost).label('total_value')
        ).join(RequestItem).group_by(Inventory.name).order_by(
            func.sum(RequestItem.quantity).desc()
        ).limit(10).all()
        
        # User activity
        user_activity = db.session.query(
            User.username,
            func.count(Request.id).label('request_count'),
            func.sum(Request.total_cost).label('total_spent')
        ).join(Request).group_by(User.id).order_by(
            func.count(Request.id).desc()
        ).limit(10).all()
        
        return render_template('analytics.html',
                             monthly_trends=monthly_trends,
                             status_distribution=status_distribution,
                             top_items=top_items,
                             user_activity=user_activity)

    @app.route('/reports/summary')
    @login_required
    def summary_report():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Generate summary statistics
        total_users = User.query.count()
        total_inventory_items = Inventory.query.count()
        total_requests = Request.query.count()
        total_inventory_value = db.session.query(
            func.sum(Inventory.quantity * Inventory.cost)
        ).scalar() or 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_requests = Request.query.filter(Request.created_at >= week_ago).count()
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        
        # Low stock items (less than 10 items)
        low_stock_items = Inventory.query.filter(Inventory.quantity < 10).count()
        
        # Pending requests
        pending_requests = Request.query.filter_by(status='pending').count()
        
        return render_template('summary.html',
                             total_users=total_users,
                             total_inventory_items=total_inventory_items,
                             total_requests=total_requests,
                             total_inventory_value=total_inventory_value,
                             recent_requests=recent_requests,
                             recent_users=recent_users,
                             low_stock_items=low_stock_items,
                             pending_requests=pending_requests)

    @app.route('/reports/daily-transactions')
    @login_required
    def daily_transactions():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get daily transactions for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        daily_data = db.session.query(
            func.date(Request.created_at).label('date'),
            func.count(Request.id).label('requests'),
            func.sum(Request.total_cost).label('total_cost')
        ).filter(Request.created_at >= thirty_days_ago).group_by(
            func.date(Request.created_at)
        ).order_by(func.date(Request.created_at).desc()).all()
        
        return render_template('daily_transactions.html', daily_data=daily_data)

    @app.route('/reports/stock-report')
    @login_required
    def stock_report():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get stock information
        low_stock_items = Inventory.query.filter(Inventory.quantity < 10).order_by(Inventory.quantity.asc()).all()
        out_of_stock_items = Inventory.query.filter(Inventory.quantity == 0).all()
        high_value_items = Inventory.query.order_by((Inventory.quantity * Inventory.cost).desc()).limit(10).all()
        
        # Stock categories
        stock_by_category = db.session.query(
            Inventory.category,
            func.count(Inventory.id).label('item_count'),
            func.sum(Inventory.quantity).label('total_quantity'),
            func.sum(Inventory.quantity * Inventory.cost).label('total_value')
        ).group_by(Inventory.category).all()
        
        return render_template('stock_report.html',
                             low_stock_items=low_stock_items,
                             out_of_stock_items=out_of_stock_items,
                             high_value_items=high_value_items,
                             stock_by_category=stock_by_category)

    @app.route('/reports/sales-report')
    @login_required
    def sales_report():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get sales data (delivered requests)
        delivered_requests = Request.query.filter_by(status='delivered').all()
        
        # Sales by month
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_sales = db.session.query(
            extract('month', Request.created_at).label('month'),
            func.count(Request.id).label('orders'),
            func.sum(Request.total_cost).label('revenue')
        ).filter(Request.created_at >= six_months_ago, Request.status == 'delivered').group_by(
            extract('month', Request.created_at)
        ).all()
        
        # Top selling items
        top_selling_items = db.session.query(
            Inventory.name,
            func.sum(RequestItem.quantity).label('units_sold'),
            func.sum(RequestItem.quantity * RequestItem.cost).label('revenue')
        ).join(RequestItem).join(Request).filter(Request.status == 'delivered').group_by(
            Inventory.name
        ).order_by(func.sum(RequestItem.quantity * RequestItem.cost).desc()).limit(10).all()
        
        return render_template('sales_report.html',
                             delivered_requests=delivered_requests,
                             monthly_sales=monthly_sales,
                             top_selling_items=top_selling_items)

    @app.route('/reports/pending-report')
    @login_required
    def pending_report():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Get pending requests
        pending_requests = Request.query.filter_by(status='pending').order_by(Request.created_at.desc()).all()
        approved_requests = Request.query.filter_by(status='approved').order_by(Request.created_at.desc()).all()
        
        # Pending by user
        pending_by_user = db.session.query(
            User.username,
            func.count(Request.id).label('pending_count'),
            func.sum(Request.total_cost).label('total_value')
        ).join(Request).filter(Request.status == 'pending').group_by(User.id).order_by(
            func.count(Request.id).desc()
        ).all()
        
        return render_template('pending_report.html',
                             pending_requests=pending_requests,
                             approved_requests=approved_requests,
                             pending_by_user=pending_by_user)

    @app.route('/reports/user-summary')
    @login_required
    def user_summary():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # User activity summary
        user_activity = db.session.query(
            User.username,
            User.email,
            User.role,
            func.count(Request.id).label('total_requests'),
            func.sum(Request.total_cost).label('total_spent'),
            func.max(Request.created_at).label('last_request')
        ).outerjoin(Request).group_by(User.id).order_by(
            func.count(Request.id).desc()
        ).all()
        
        # Recent user registrations
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        return render_template('user_summary.html',
                             user_activity=user_activity,
                             recent_users=recent_users)

    @app.route('/reports/inventory-sales-summary')
    @login_required
    def inventory_sales_summary():
        if current_user.role not in ['admin', 'super_admin', 'school_manager']:
            return redirect(url_for('dashboard'))
        
        # Inventory sales summary
        inventory_sales = db.session.query(
            Inventory.name,
            Inventory.category,
            Inventory.quantity.label('current_stock'),
            func.coalesce(func.sum(RequestItem.quantity), 0).label('total_requested'),
            func.coalesce(func.sum(RequestItem.quantity * RequestItem.cost), 0).label('total_value'),
            func.coalesce(func.avg(RequestItem.cost), 0).label('avg_cost')
        ).outerjoin(RequestItem).group_by(Inventory.id).order_by(
            func.coalesce(func.sum(RequestItem.quantity), 0).desc()
        ).all()
        
        # Category summary
        category_summary = db.session.query(
            Inventory.category,
            func.count(Inventory.id).label('item_count'),
            func.coalesce(func.sum(Inventory.quantity), 0).label('total_stock'),
            func.coalesce(func.sum(Inventory.quantity * Inventory.cost), 0).label('total_value')
        ).group_by(Inventory.category).all()
        
        return render_template('inventory_sales_summary.html',
                             inventory_sales=inventory_sales,
                             category_summary=category_summary)

    @app.route('/admin/database/stats')
    @login_required
    def database_stats():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        # Get current database stats
        current_stats = get_database_stats()
        
        # Get all database stats
        all_db_stats = db_manager.get_all_database_stats()
        
        return render_template('database_stats.html', 
                             stats=current_stats, 
                             all_db_stats=all_db_stats,
                             current_db=db_manager.get_current_database())

    @app.route('/admin/database/optimize')
    @login_required
    def optimize_database_route():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        success = optimize_database()
        if success:
            flash('Database optimized successfully')
        else:
            flash('Database optimization failed')
        
        return redirect(url_for('database_stats'))

    @app.route('/admin/database/cleanup')
    @login_required
    def cleanup_database():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        success, message = cleanup_old_data()
        if success:
            flash(f'Database cleanup completed: {message}')
        else:
            flash(f'Database cleanup failed: {message}')
        
        return redirect(url_for('database_stats'))

    @app.route('/admin/database/switch')
    @login_required
    def switch_database():
        if current_user.role != 'super_admin':
            return redirect(url_for('dashboard'))
        
        success = db_manager.switch_to_next_database()
        if success:
            flash('Successfully switched to next database')
        else:
            flash('Failed to switch database')
        
        return redirect(url_for('database_stats'))

    @app.route('/session-timeout')
    def session_timeout():
        """Handle session timeout"""
        logout_user()
        flash('Your session has expired due to inactivity. Please login again.', 'warning')
        return redirect(url_for('login'))

    @app.route('/check-session')
    @login_required
    def check_session():
        """Check if session is still valid"""
        return jsonify({'valid': True, 'user': current_user.username})

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Check database connectivity
            db.session.execute(text("SELECT 1"))
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create super admin if not exists
        if not User.query.filter_by(role='super_admin').first():
            super_admin = User(
                username='admin',
                email='admin@school.com',
                role='super_admin',
                school='Main School'
            )
            super_admin.set_password('admin123')
            db.session.add(super_admin)
            db.session.commit()
        
        # Initialize database manager
        db_manager.load_current_database()
        
        # Optimize database
        optimize_database()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
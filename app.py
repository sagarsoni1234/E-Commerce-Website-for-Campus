from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

jwt = JWTManager(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'campus_marketplace'
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT role FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user and user['role'] == 'admin':
                return f(*args, **kwargs)
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('home'))
    return decorated_function

def init_db():
    """Initialize database with schema"""
    try:
        # First, connect without database to create it
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS campus_marketplace")
        cursor.close()
        conn.close()
        
        # Now connect to the database
        conn = get_db_connection()
        if not conn:
            print("Error: Could not connect to database")
            return
        
        cursor = conn.cursor()
        
        # Create tables one by one
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                address TEXT,
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                category VARCHAR(50),
                stock INT DEFAULT 0,
                image VARCHAR(255) DEFAULT 'default-product.jpg',
                seller_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS cart (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE KEY unique_cart_item (user_id, product_id)
            )""",
            """CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                payment_method VARCHAR(50),
                shipping_address TEXT,
                status ENUM('pending', 'processing', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS feedbacks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                rating INT DEFAULT 5,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                CHECK (rating >= 1 AND rating <= 5)
            )""",
            """CREATE TABLE IF NOT EXISTS general_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                subject VARCHAR(200),
                message TEXT NOT NULL,
                rating INT DEFAULT 5,
                status ENUM('new', 'read', 'replied') DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                CHECK (rating >= 1 AND rating <= 5)
            )""",
            """CREATE TABLE IF NOT EXISTS contact_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                subject VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                status ENUM('new', 'read', 'replied') DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )"""
        ]
        
        # Execute each table creation
        for table_sql in tables:
            try:
                cursor.execute(table_sql)
                conn.commit()
            except Error as e:
                # Ignore errors for existing tables
                if 'already exists' not in str(e).lower():
                    print(f"Warning creating table: {e}")
        
        # Create admin user if not exists
        try:
            cursor.execute("SELECT id FROM users WHERE email = 'admin@campus.com'")
            if not cursor.fetchone():
                admin_password = generate_password_hash('admin123')
                cursor.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'admin')",
                    ('Admin User', 'admin@campus.com', admin_password)
                )
                conn.commit()
                print("Admin user created: admin@campus.com / admin123")
        except Error as e:
            print(f"Warning creating admin user: {e}")
        
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
    except Error as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()

# Routes
@app.route('/')
def home():
    conn = get_db_connection()
    featured_products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT 6")
        featured_products = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('home.html', products=featured_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['user_role'] = user['role']
                
                # Create JWT token
                access_token = create_access_token(identity=user['id'])
                
                flash('Login successful!', 'success')
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered', 'danger')
                cursor.close()
                conn.close()
                return render_template('register.html')
            
            # Create new user
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, 'user')",
                (name, email, hashed_password, phone)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/products')
def products():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    products_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as seller_name FROM products p JOIN users u ON p.seller_id = u.id WHERE 1=1"
        params = []
        
        if search:
            query += " AND (p.name LIKE %s OR p.description LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category:
            query += " AND p.category = %s"
            params.append(category)
        
        query += " ORDER BY p.created_at DESC"
        cursor.execute(query, params)
        products_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('products.html', products=products_list, search=search, category=category)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    conn = get_db_connection()
    product = None
    feedbacks = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.*, u.name as seller_name, u.email as seller_email FROM products p JOIN users u ON p.seller_id = u.id WHERE p.id = %s",
            (product_id,)
        )
        product = cursor.fetchone()
        
        if product:
            cursor.execute(
                "SELECT f.*, u.name as user_name FROM feedbacks f JOIN users u ON f.user_id = u.id WHERE f.product_id = %s ORDER BY f.created_at DESC",
                (product_id,)
            )
            feedbacks = cursor.fetchall()
        
        cursor.close()
        conn.close()
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    
    return render_template('product_details.html', product=product, feedbacks=feedbacks)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Debug: Check session
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format'}), 400
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Check if item already in cart
        cursor.execute(
            "SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s",
            (session['user_id'], product_id)
        )
        cart_item = cursor.fetchone()
        
        if cart_item:
            # Update quantity
            new_quantity = cart_item[1] + quantity
            cursor.execute(
                "UPDATE cart SET quantity = %s WHERE id = %s",
                (new_quantity, cart_item[0])
            )
        else:
            # Add new item
            cursor.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                (session['user_id'], product_id, quantity)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Item added to cart'})
    
    return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cart_items = []
    total = 0
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Clean up cart items for deleted products
        cursor.execute(
            """DELETE FROM cart 
               WHERE user_id = %s 
               AND product_id NOT IN (SELECT id FROM products)""",
            (session['user_id'],)
        )
        removed_count = cursor.rowcount
        if removed_count > 0:
            conn.commit()
            flash(f'{removed_count} item(s) were removed from your cart because the products are no longer available.', 'warning')
        
        # Get valid cart items (INNER JOIN ensures only existing products)
        cursor.execute(
            """SELECT c.*, p.name, p.price, p.image, p.seller_id, p.stock, u.name as seller_name 
               FROM cart c 
               INNER JOIN products p ON c.product_id = p.id 
               INNER JOIN users u ON p.seller_id = u.id 
               WHERE c.user_id = %s""",
            (session['user_id'],)
        )
        cart_items = cursor.fetchall()
        
        # Check stock and adjust quantities if needed
        for item in cart_items:
            if item['stock'] < item['quantity']:
                if item['stock'] > 0:
                    # Adjust quantity to available stock
                    cursor.execute(
                        "UPDATE cart SET quantity = %s WHERE id = %s",
                        (item['stock'], item['id'])
                    )
                    item['quantity'] = item['stock']
                    flash(f'Quantity adjusted for {item["name"]} due to limited stock.', 'info')
                else:
                    # Remove out of stock items
                    cursor.execute("DELETE FROM cart WHERE id = %s", (item['id'],))
                    cart_items.remove(item)
                    flash(f'{item["name"]} is out of stock and removed from cart.', 'warning')
                    continue
            
            item['subtotal'] = item['price'] * item['quantity']
            total += item['subtotal']
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    cart_id = data.get('cart_id')
    quantity = int(data.get('quantity', 1))
    
    if quantity <= 0:
        # Remove item
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
            conn.commit()
            cursor.close()
            conn.close()
    else:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s",
                (quantity, cart_id, session['user_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
    
    return jsonify({'success': True})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        address = request.form.get('address')
        
        if not address or not address.strip():
            flash('Please provide a shipping address', 'danger')
            return redirect(url_for('checkout'))
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get cart items with product validation (only products that still exist)
            cursor.execute(
                """SELECT c.id as cart_id, c.product_id, c.quantity, p.price, p.name, p.stock 
                   FROM cart c 
                   INNER JOIN products p ON c.product_id = p.id 
                   WHERE c.user_id = %s""",
                (session['user_id'],)
            )
            cart_items = cursor.fetchall()
            
            # Remove cart items for products that no longer exist
            cursor.execute(
                """DELETE FROM cart 
                   WHERE user_id = %s 
                   AND product_id NOT IN (SELECT id FROM products)""",
                (session['user_id'],)
            )
            removed_items = cursor.rowcount
            
            if removed_items > 0:
                flash(f'{removed_items} item(s) were removed from your cart because the products are no longer available.', 'warning')
            
            if not cart_items:
                flash('Your cart is empty', 'warning')
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('cart'))
            
            # Validate stock and adjust quantities if needed
            valid_items = []
            for item in cart_items:
                if item['stock'] < item['quantity']:
                    if item['stock'] > 0:
                        flash(f'Only {item["stock"]} units available for {item["name"]}. Quantity adjusted.', 'warning')
                        item['quantity'] = item['stock']
                        # Update cart with adjusted quantity
                        cursor.execute(
                            "UPDATE cart SET quantity = %s WHERE id = %s",
                            (item['stock'], item['cart_id'])
                        )
                        valid_items.append(item)
                    else:
                        flash(f'{item["name"]} is out of stock and removed from cart.', 'warning')
                        cursor.execute("DELETE FROM cart WHERE id = %s", (item['cart_id'],))
                else:
                    valid_items.append(item)
            
            if not valid_items:
                flash('No valid items in cart after validation', 'warning')
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('cart'))
            
            # Calculate total
            total = sum(item['price'] * item['quantity'] for item in valid_items)
            
            # Create order
            cursor.execute(
                "INSERT INTO orders (user_id, total_amount, payment_method, shipping_address, status) VALUES (%s, %s, %s, %s, 'pending')",
                (session['user_id'], total, payment_method, address)
            )
            order_id = cursor.lastrowid
            
            # Create order items with validation
            for item in valid_items:
                try:
                    # Double-check product still exists
                    cursor.execute("SELECT id FROM products WHERE id = %s", (item['product_id'],))
                    if cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                            (order_id, item['product_id'], item['quantity'], item['price'])
                        )
                    else:
                        flash(f'Product {item["name"]} no longer exists and was skipped.', 'warning')
                except Error as e:
                    print(f"Error adding order item: {e}")
                    flash(f'Error adding {item["name"]} to order. Please try again.', 'danger')
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return redirect(url_for('cart'))
            
            # Clear cart only after successful order creation
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (session['user_id'],))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_details', order_id=order_id))
    
    # GET request - show checkout page
    conn = get_db_connection()
    cart_items = []
    total = 0
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Clean up cart items for deleted products
        cursor.execute(
            """DELETE FROM cart 
               WHERE user_id = %s 
               AND product_id NOT IN (SELECT id FROM products)""",
            (session['user_id'],)
        )
        removed_count = cursor.rowcount
        if removed_count > 0:
            conn.commit()
            flash(f'{removed_count} item(s) were removed from your cart because the products are no longer available.', 'warning')
        
        # Get valid cart items
        cursor.execute(
            """SELECT c.*, p.name, p.price, p.image, p.stock 
               FROM cart c 
               INNER JOIN products p ON c.product_id = p.id 
               WHERE c.user_id = %s""",
            (session['user_id'],)
        )
        cart_items = cursor.fetchall()
        
        # Validate and adjust quantities
        for item in cart_items:
            if item['stock'] < item['quantity']:
                if item['stock'] > 0:
                    item['quantity'] = item['stock']
                    cursor.execute(
                        "UPDATE cart SET quantity = %s WHERE id = %s",
                        (item['stock'], item['id'])
                    )
                else:
                    # Remove out of stock items
                    cursor.execute("DELETE FROM cart WHERE id = %s", (item['id'],))
                    cart_items.remove(item)
                    continue
            
            item['subtotal'] = item['price'] * item['quantity']
            total += item['subtotal']
        
        conn.commit()
        cursor.close()
        conn.close()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    orders_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        if session.get('user_role') == 'admin':
            cursor.execute(
                "SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC"
            )
        else:
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC",
                (session['user_id'],)
            )
        orders_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('orders.html', orders=orders_list)

@app.route('/order/<int:order_id>')
def order_details(order_id):
    if 'user_id' not in session:
        flash('Please login to view order details', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    order = None
    order_items = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        if session.get('user_role') == 'admin':
            cursor.execute(
                "SELECT o.*, u.name as user_name, u.email as user_email FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = %s",
                (order_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM orders WHERE id = %s AND user_id = %s",
                (order_id, session['user_id'])
            )
        order = cursor.fetchone()
        
        if order:
            cursor.execute(
                """SELECT oi.*, p.name, p.image 
                   FROM order_items oi 
                   JOIN products p ON oi.product_id = p.id 
                   WHERE oi.order_id = %s""",
                (order_id,)
            )
            order_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    
    return render_template('order_details.html', order=order, order_items=order_items)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to view profile', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = None
    user_orders = []
    user_products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        cursor.execute(
            "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
            (session['user_id'],)
        )
        user_orders = cursor.fetchall()
        
        cursor.execute(
            "SELECT * FROM products WHERE seller_id = %s ORDER BY created_at DESC",
            (session['user_id'],)
        )
        user_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
    
    return render_template('profile.html', user=user, orders=user_orders, products=user_products)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name = %s, phone = %s, address = %s WHERE id = %s",
            (name, phone, address, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        session['user_name'] = name
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    flash('Error updating profile', 'danger')
    return redirect(url_for('profile'))

@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedbacks (user_id, product_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (session['user_id'], product_id, rating, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Feedback added successfully'})
    
    return jsonify({'success': False, 'message': 'Database error'}), 500

# Admin Routes
@app.route('/feedback', methods=['GET', 'POST'])
def feedback_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject', '')
        message = request.form.get('message')
        rating = int(request.form.get('rating', 5))
        user_id = session.get('user_id')
        
        if not name or not email or not message:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('feedback_page'))
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO general_feedback (user_id, name, email, subject, message, rating, status) VALUES (%s, %s, %s, %s, %s, %s, 'new')",
                (user_id, name, email, subject, message, rating)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Thank you for your feedback! We appreciate your input.', 'success')
            return redirect(url_for('feedback_page'))
    
    return render_template('feedback.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        subject = request.form.get('subject')
        message = request.form.get('message')
        user_id = session.get('user_id')
        
        if not name or not email or not subject or not message:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('contact'))
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contact_messages (user_id, name, email, phone, subject, message, status) VALUES (%s, %s, %s, %s, %s, %s, 'new')",
                (user_id, name, email, phone, subject, message)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Thank you for contacting us! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    stats = {
        'total_users': 0,
        'total_products': 0,
        'total_orders': 0,
        'total_revenue': 0
    }
    recent_orders = []
    recent_feedbacks = []
    recent_general_feedback = []
    recent_contacts = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'user'")
        stats['total_users'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM products")
        stats['total_products'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        stats['total_orders'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE status = 'completed'")
        result = cursor.fetchone()
        stats['total_revenue'] = result['total'] or 0
        
        cursor.execute(
            "SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 5"
        )
        recent_orders = cursor.fetchall()
        
        cursor.execute(
            "SELECT f.*, u.name as user_name, p.name as product_name FROM feedbacks f JOIN users u ON f.user_id = u.id JOIN products p ON f.product_id = p.id ORDER BY f.created_at DESC LIMIT 5"
        )
        recent_feedbacks = cursor.fetchall()
        
        # Get recent general feedback
        try:
            cursor.execute(
                "SELECT * FROM general_feedback ORDER BY created_at DESC LIMIT 5"
            )
            recent_general_feedback = cursor.fetchall()
        except Error:
            recent_general_feedback = []
        
        # Get recent contact messages
        try:
            cursor.execute(
                "SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 5"
            )
            recent_contacts = cursor.fetchall()
        except Error:
            recent_contacts = []
        
        cursor.close()
        conn.close()
    
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, recent_feedbacks=recent_feedbacks, recent_general_feedback=recent_general_feedback, recent_contacts=recent_contacts)

@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        stock = int(request.form.get('stock', 0))
        
        # Handle file upload
        image = 'default-product.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(filepath)
                image = filename
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, description, price, category, stock, image, seller_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, description, price, category, stock, image, session['user_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Product added successfully', 'success')
            return redirect(url_for('admin_products'))
    
    # GET request
    conn = get_db_connection()
    products_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.*, u.name as seller_name FROM products p JOIN users u ON p.seller_id = u.id ORDER BY p.created_at DESC"
        )
        products_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/products.html', products=products_list)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        stock = int(request.form.get('stock', 0))
        
        if conn:
            cursor = conn.cursor()
            
            # Handle file upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(filepath)
                    cursor.execute(
                        "UPDATE products SET name = %s, description = %s, price = %s, category = %s, stock = %s, image = %s WHERE id = %s",
                        (name, description, price, category, stock, filename, product_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE products SET name = %s, description = %s, price = %s, category = %s, stock = %s WHERE id = %s",
                        (name, description, price, category, stock, product_id)
                    )
            else:
                cursor.execute(
                    "UPDATE products SET name = %s, description = %s, price = %s, category = %s, stock = %s WHERE id = %s",
                    (name, description, price, category, stock, product_id)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin_products'))
    
    # GET request
    product = None
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Product deleted successfully', 'success')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    users_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/users.html', users=users_list)

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('User deleted successfully', 'success')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/feedbacks')
@admin_required
def admin_feedbacks():
    conn = get_db_connection()
    feedbacks_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT f.*, u.name as user_name, p.name as product_name FROM feedbacks f JOIN users u ON f.user_id = u.id JOIN products p ON f.product_id = p.id ORDER BY f.created_at DESC"
        )
        feedbacks_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/feedbacks.html', feedbacks=feedbacks_list)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_db_connection()
    orders_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC"
        )
        orders_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/orders.html', orders=orders_list)

@app.route('/admin/order/update_status', methods=['POST'])
@admin_required
def admin_update_order_status():
    data = request.get_json()
    order_id = data.get('order_id')
    status = data.get('status')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            (status, order_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Order status updated'})
    
    return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/admin/general-feedback')
@admin_required
def admin_general_feedback():
    conn = get_db_connection()
    feedbacks_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT gf.*, u.name as user_name 
                   FROM general_feedback gf 
                   LEFT JOIN users u ON gf.user_id = u.id 
                   ORDER BY gf.created_at DESC"""
            )
            feedbacks_list = cursor.fetchall()
        except Error:
            feedbacks_list = []
        cursor.close()
        conn.close()
    
    return render_template('admin/general_feedback.html', feedbacks=feedbacks_list)

@app.route('/admin/contact-messages')
@admin_required
def admin_contact_messages():
    conn = get_db_connection()
    messages_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT cm.*, u.name as user_name 
                   FROM contact_messages cm 
                   LEFT JOIN users u ON cm.user_id = u.id 
                   ORDER BY cm.created_at DESC"""
            )
            messages_list = cursor.fetchall()
        except Error:
            messages_list = []
        cursor.close()
        conn.close()
    
    return render_template('admin/contact_messages.html', messages=messages_list)

@app.route('/admin/feedback/update_status', methods=['POST'])
@admin_required
def admin_update_feedback_status():
    data = request.get_json()
    feedback_id = data.get('feedback_id')
    status = data.get('status')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE general_feedback SET status = %s WHERE id = %s",
                (status, feedback_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Feedback status updated'})
        except Error:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Database error'}), 500
    
    return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/admin/contact/update_status', methods=['POST'])
@admin_required
def admin_update_contact_status():
    data = request.get_json()
    message_id = data.get('message_id')
    status = data.get('status')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE contact_messages SET status = %s WHERE id = %s",
                (status, message_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Contact message status updated'})
        except Error:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Database error'}), 500
    
    return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/init-db')
def init_db_route():
    """Manual database initialization route"""
    init_db()
    flash('Database initialized successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Initialize database on first run
    print("Initializing database...")
    init_db()
    # Create uploads directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print("Starting Flask application...")
    print("Open your browser at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)


# Campus Marketplace - Full-Stack Web Application

A complete e-commerce platform built with Python Flask and MySQL for campus students to buy and sell products within their campus community.

## 🚀 Features

### Frontend Pages
- **Home Page** - Featured products and welcome section
- **Products Page** - Browse all products with search and filter
- **Product Details Page** - View product details, add to cart, and feedback
- **Login/Register** - User authentication
- **Cart Page** - Manage shopping cart items
- **Checkout Page** - Place orders with payment options
- **Orders Page** - View order history
- **User Profile** - Manage profile and view orders/products
- **Admin Dashboard** - Complete admin panel for managing the marketplace

### Backend Functionalities
- ✅ JWT-based user authentication
- ✅ Product management (Add/Edit/Delete)
- ✅ Cart management API
- ✅ Order & Payment API
- ✅ Feedback system
- ✅ Admin protected routes
- ✅ MySQL database integration
- ✅ File upload for product images

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL (XAMPP or standalone)
- pip (Python package manager)

## 🛠️ Installation

### Quick Setup (Recommended)

We provide automated setup scripts that check prerequisites, verify MySQL connection, clean ports, and install dependencies:

#### Windows (Batch Script)
```batch
setup_windows.bat
```

#### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

#### macOS/Linux
```bash
chmod +x setup_mac.sh
./setup_mac.sh
```

### Manual Installation

#### 1. Clone or Download the Project

```bash
cd campus-project-python-flask-mysql
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Database Setup

1. Make sure MySQL is running in XAMPP (or your MySQL server)
2. The database will be created automatically when you run the application
3. Or manually create database:
   ```sql
   CREATE DATABASE campus_marketplace;
   ```

#### 4. Configure Database Connection

Edit `app.py` and update the database configuration if needed:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password (empty for XAMPP default)
    'database': 'campus_marketplace'
}
```

### Running the Application

#### Quick Start Scripts

**Windows (Batch):**
```batch
start_app.bat
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

**macOS/Linux:**
```bash
chmod +x start_app.sh
./start_app.sh
```

#### Manual Start

```bash
python app.py
```

The application will:
- Check MySQL connection
- Create the database if it doesn't exist
- Run the schema.sql to create all tables
- Create default admin user
- Start the Flask server on `http://localhost:5000`

## 🔑 Default Admin Credentials

- **Email:** admin@campus.com
- **Password:** admin123

**Note:** The admin user is created automatically when the database is initialized. You can change the password after first login.

## 📁 Project Structure

```
campus-project-python-flask-mysql/
│
├── app.py                 # Main Flask application
├── schema.sql             # Database schema
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── home.html         # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── products.html     # Products listing
│   ├── product_details.html  # Product details
│   ├── cart.html         # Shopping cart
│   ├── checkout.html     # Checkout page
│   ├── orders.html       # Orders list
│   ├── order_details.html # Order details
│   ├── profile.html      # User profile
│   └── admin/            # Admin templates
│       ├── dashboard.html
│       ├── products.html
│       ├── edit_product.html
│       ├── users.html
│       ├── feedbacks.html
│       └── orders.html
│
└── static/               # Static files
    ├── css/
    │   └── style.css     # Custom styles
    ├── js/
    │   └── main.js       # JavaScript functions
    └── uploads/          # Product images (created automatically)
```

## 🎯 Usage Guide

### For Users

1. **Register/Login** - Create an account or login
2. **Browse Products** - View all available products
3. **View Details** - Click on any product to see details
4. **Add to Cart** - Add products to your shopping cart
5. **Checkout** - Proceed to checkout and place orders
6. **View Orders** - Track your order history
7. **Leave Feedback** - Rate and review products

### For Admins

1. **Login** with admin credentials
2. **Dashboard** - View statistics and recent activity
3. **Manage Products** - Add, edit, or delete products
4. **Manage Users** - View and manage user accounts
5. **View Orders** - See all orders and update status
6. **View Feedbacks** - Monitor customer feedback

## 🔒 Security Features

- Password hashing using Werkzeug
- JWT token-based authentication
- Session management
- Admin route protection
- SQL injection prevention (parameterized queries)
- File upload validation

## 🗄️ Database Schema

The database includes the following tables:
- `users` - User accounts (customers and admins)
- `products` - Product listings
- `cart` - Shopping cart items
- `orders` - Order records
- `order_items` - Individual items in orders
- `feedbacks` - Product reviews and ratings

## 🎨 Technologies Used

- **Backend:** Python Flask
- **Database:** MySQL
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication:** Flask-JWT-Extended
- **Icons:** Font Awesome

## 🐛 Troubleshooting

### Database Connection Error
- Ensure MySQL is running in XAMPP
- Check database credentials in `app.py`
- Verify database exists or let the app create it

### Port Already in Use
- Change the port in `app.py`: `app.run(port=5001)`
- Or stop the process using port 5000

### Image Upload Issues
- Ensure `static/uploads/` directory exists
- Check file permissions
- Verify file size (max 16MB)

## 📝 Notes

- The application uses session-based authentication for web interface
- JWT tokens are generated but can be used for API access
- Product images are stored in `static/uploads/` directory
- Default product image is used if no image is uploaded

## 🔄 Future Enhancements

- Email notifications
- Payment gateway integration
- Advanced search and filters
- Product categories management
- Seller dashboard
- Order tracking
- Wishlist feature
- Product recommendations

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Support

For issues or questions, please check the code comments or create an issue in the repository.

---

**Happy Shopping! 🛒**


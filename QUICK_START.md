# Quick Start Guide

## 🚀 Fastest Way to Get Started

### For Windows Users

1. **Double-click** `setup_windows.bat` to run the setup script
   - It will check Python, pip, MySQL connection, and install dependencies
   - Or use PowerShell: `powershell -ExecutionPolicy Bypass -File setup_windows.ps1`

2. **Start MySQL** in XAMPP Control Panel

3. **Double-click** `start_app.bat` to start the application
   - Or use PowerShell: `powershell -ExecutionPolicy Bypass -File start_app.ps1`

4. **Open browser** at `http://localhost:5000`

### For macOS/Linux Users

1. **Make scripts executable:**
   ```bash
   chmod +x setup_mac.sh start_app.sh
   ```

2. **Run setup:**
   ```bash
   ./setup_mac.sh
   ```

3. **Start MySQL** service

4. **Start application:**
   ```bash
   ./start_app.sh
   ```

5. **Open browser** at `http://localhost:5000`

## 📋 What the Setup Scripts Do

### Setup Scripts (`setup_*.bat/ps1/sh`)

1. ✅ Check Python installation
2. ✅ Check pip installation
3. ✅ Test MySQL connection
4. ✅ Check if port 5000 is available
5. ✅ Clean port 5000 if needed (with user confirmation)
6. ✅ Install Python dependencies
7. ✅ Create necessary directories

### Start Scripts (`start_app.*`)

1. ✅ Verify Python is installed
2. ✅ Check MySQL connection
3. ✅ Check and clean port 5000 if needed
4. ✅ Start Flask application

## 🔧 Troubleshooting

### MySQL Connection Failed

**Windows (XAMPP):**
- Open XAMPP Control Panel
- Click "Start" next to MySQL
- Wait for green "Running" status

**macOS:**
```bash
brew services start mysql
# or
sudo /usr/local/mysql/support-files/mysql.server start
```

**Linux:**
```bash
sudo systemctl start mysql
# or
sudo service mysql start
```

### Port 5000 Already in Use

The scripts will detect this and ask if you want to kill the process. You can also:

**Windows:**
```batch
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

**macOS/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

### Python Not Found

- Make sure Python 3.8+ is installed
- Add Python to PATH during installation
- Restart terminal/command prompt after installation

## 📝 Default Credentials

- **Admin Email:** admin@campus.com
- **Admin Password:** admin123

## 🎯 Next Steps

After setup:
1. Register a new user account
2. Login as admin to add products
3. Browse products and add to cart
4. Place orders and test the system

---

**Need Help?** Check the main README.md for detailed documentation.


@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Campus Marketplace - Setup Script
echo ========================================
echo.

:: Check Python installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo [OK] Python is installed
echo.

:: Check pip installation
echo [2/6] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed!
    pause
    exit /b 1
)
echo [OK] pip is installed
echo.

:: Check MySQL connection
echo [3/6] Checking MySQL connection...
python -c "import mysql.connector; conn = mysql.connector.connect(host='localhost', user='root', password=''); conn.close(); print('MySQL connection successful!')" 2>nul
if errorlevel 1 (
    echo [WARNING] Cannot connect to MySQL!
    echo.
    echo Please ensure:
    echo   1. XAMPP MySQL is running
    echo   2. MySQL service is started in XAMPP Control Panel
    echo   3. MySQL credentials are correct (default: root / no password)
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "!continue!"=="y" (
        echo Setup cancelled.
        pause
        exit /b 1
    )
) else (
    echo [OK] MySQL connection successful
)
echo.

:: Check if port 5000 is in use
echo [4/6] Checking if port 5000 is available...
netstat -ano | findstr ":5000" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 5000 is already in use!
    echo.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do (
        echo Process using port 5000: PID %%a
        set /p kill="Kill process? (y/n): "
        if /i "!kill!"=="y" (
            taskkill /F /PID %%a >nul 2>&1
            echo Process killed.
        )
    )
) else (
    echo [OK] Port 5000 is available
)
echo.

:: Install Python dependencies
echo [5/6] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: Create uploads directory
echo [6/6] Creating necessary directories...
if not exist "static\uploads" mkdir "static\uploads"
echo [OK] Directories created
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To start the application, run:
echo   python app.py
echo.
echo Or use: start_app.bat
echo.
pause


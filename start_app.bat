@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Campus Marketplace - Starting...
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

:: Check MySQL connection
echo Checking MySQL connection...
python -c "import mysql.connector; conn = mysql.connector.connect(host='localhost', user='root', password=''); conn.close(); print('MySQL OK')" 2>nul
if errorlevel 1 (
    echo [WARNING] Cannot connect to MySQL!
    echo Please ensure XAMPP MySQL is running
    echo.
    pause
)

:: Check if port 5000 is in use
netstat -ano | findstr ":5000" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 5000 is already in use!
    echo.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do (
        echo Process using port 5000: PID %%a
        set /p kill="Kill process and continue? (y/n): "
        if /i "!kill!"=="y" (
            taskkill /F /PID %%a >nul 2>&1
            echo Process killed.
        ) else (
            echo Exiting...
            pause
            exit /b 1
        )
    )
)

:: Start the application
echo.
echo Starting Flask application...
echo Open your browser at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python app.py

pause


@echo off
echo Setting up Campus Marketplace...
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To run the application:
echo   python app.py
echo.
echo Make sure MySQL is running in XAMPP before starting the application.
echo.
pause


# Campus Marketplace - PowerShell Start Script
# Run with: powershell -ExecutionPolicy Bypass -File start_app.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Campus Marketplace - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $null = python --version 2>&1
} catch {
    Write-Host "[ERROR] Python is not installed!" -ForegroundColor Red
    Write-Host "Please run setup_windows.ps1 first" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check MySQL connection
Write-Host "Checking MySQL connection..." -ForegroundColor Yellow
$mysqlTestScript = @"
import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', connection_timeout=3)
    conn.close()
    print('MySQL OK')
except Exception as e:
    print(f'ERROR: {e}')
"@

$mysqlResult = $mysqlTestScript | python 2>&1
if ($mysqlResult -notmatch "MySQL OK") {
    Write-Host "[WARNING] Cannot connect to MySQL!" -ForegroundColor Yellow
    Write-Host "Please ensure XAMPP MySQL is running" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue anyway"
}

# Check if port 5000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[WARNING] Port 5000 is already in use!" -ForegroundColor Yellow
    Write-Host ""
    $processes = $portInUse | ForEach-Object {
        Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    } | Select-Object -Unique
    
    foreach ($proc in $processes) {
        Write-Host "Process using port 5000: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Yellow
        $kill = Read-Host "Kill process and continue? (y/n)"
        if ($kill -eq "y" -or $kill -eq "Y") {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "[OK] Process killed" -ForegroundColor Green
            } catch {
                Write-Host "[ERROR] Could not kill process" -ForegroundColor Red
                Read-Host "Press Enter to exit"
                exit 1
            }
        } else {
            Write-Host "Exiting..." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
}

# Start the application
Write-Host ""
Write-Host "Starting Flask application..." -ForegroundColor Green
Write-Host "Open your browser at: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python app.py

Read-Host "Press Enter to exit"


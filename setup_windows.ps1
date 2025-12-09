# Campus Marketplace - PowerShell Setup Script
# Run with: powershell -ExecutionPolicy Bypass -File setup_windows.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Campus Marketplace - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# [1/6] Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# [2/6] Check pip installation
Write-Host "[2/6] Checking pip installation..." -ForegroundColor Yellow
try {
    $pipVersion = python -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] pip is installed" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host "[ERROR] pip is not installed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# [3/6] Check MySQL connection
Write-Host "[3/6] Checking MySQL connection..." -ForegroundColor Yellow
$mysqlTestScript = @"
import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', connection_timeout=3)
    conn.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
"@

$mysqlTestScript | python 2>&1 | Out-Null
$mysqlResult = $mysqlTestScript | python 2>&1

if ($mysqlResult -match "SUCCESS") {
    Write-Host "[OK] MySQL connection successful" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Cannot connect to MySQL!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. XAMPP MySQL is running" -ForegroundColor Yellow
    Write-Host "  2. MySQL service is started in XAMPP Control Panel" -ForegroundColor Yellow
    Write-Host "  3. MySQL credentials are correct (default: root / no password)" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Setup cancelled." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host ""

# [4/6] Check if port 5000 is in use
Write-Host "[4/6] Checking if port 5000 is available..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[WARNING] Port 5000 is already in use!" -ForegroundColor Yellow
    Write-Host ""
    $processes = $portInUse | ForEach-Object {
        Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    } | Select-Object -Unique
    
    foreach ($proc in $processes) {
        Write-Host "Process using port 5000: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Yellow
        $kill = Read-Host "Kill process? (y/n)"
        if ($kill -eq "y" -or $kill -eq "Y") {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "[OK] Process killed" -ForegroundColor Green
            } catch {
                Write-Host "[ERROR] Could not kill process" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "[OK] Port 5000 is available" -ForegroundColor Green
}
Write-Host ""

# [5/6] Install Python dependencies
Write-Host "[5/6] Installing Python dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip | Out-Null
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    } else {
        throw "Installation failed"
    }
} catch {
    Write-Host "[ERROR] Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# [6/6] Create necessary directories
Write-Host "[6/6] Creating necessary directories..." -ForegroundColor Yellow
if (-not (Test-Path "static\uploads")) {
    New-Item -ItemType Directory -Path "static\uploads" -Force | Out-Null
}
Write-Host "[OK] Directories created" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""
Write-Host "Or use: .\start_app.ps1" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"


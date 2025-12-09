#!/bin/bash

# Campus Marketplace - macOS/Linux Setup Script
# Run with: chmod +x setup_mac.sh && ./setup_mac.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Campus Marketplace - Setup Script${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# [1/6] Check Python installation
echo -e "${YELLOW}[1/6] Checking Python installation...${NC}"
if command_exists python3; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command_exists python; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo -e "${RED}[ERROR] Python is not installed!${NC}"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}[OK] $PYTHON_VERSION${NC}"
echo ""

# [2/6] Check pip installation
echo -e "${YELLOW}[2/6] Checking pip installation...${NC}"
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] pip is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] pip is installed${NC}"
echo ""

# [3/6] Check MySQL connection
echo -e "${YELLOW}[3/6] Checking MySQL connection...${NC}"
MYSQL_TEST_SCRIPT="
import mysql.connector
import sys
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        connection_timeout=3
    )
    conn.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"

MYSQL_RESULT=$(echo "$MYSQL_TEST_SCRIPT" | $PYTHON_CMD 2>&1)

if echo "$MYSQL_RESULT" | grep -q "SUCCESS"; then
    echo -e "${GREEN}[OK] MySQL connection successful${NC}"
else
    echo -e "${YELLOW}[WARNING] Cannot connect to MySQL!${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. MySQL is installed and running"
    echo "  2. MySQL service is started"
    echo "  3. MySQL credentials are correct (default: root / no password)"
    echo ""
    read -p "Continue anyway? (y/n): " continue_choice
    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi
echo ""

# [4/6] Check if port 5000 is in use
echo -e "${YELLOW}[4/6] Checking if port 5000 is available...${NC}"
if command_exists lsof; then
    PORT_CHECK=$(lsof -ti:5000 2>/dev/null)
elif command_exists netstat; then
    PORT_CHECK=$(netstat -an | grep ":5000" | grep LISTEN)
else
    PORT_CHECK=""
fi

if [ -n "$PORT_CHECK" ]; then
    echo -e "${YELLOW}[WARNING] Port 5000 is already in use!${NC}"
    echo ""
    if command_exists lsof; then
        PROCESSES=$(lsof -ti:5000)
        for PID in $PROCESSES; do
            PROCESS_NAME=$(ps -p $PID -o comm= 2>/dev/null)
            echo "Process using port 5000: $PROCESS_NAME (PID: $PID)"
            read -p "Kill process? (y/n): " kill_choice
            if [[ "$kill_choice" =~ ^[Yy]$ ]]; then
                kill -9 $PID 2>/dev/null
                echo -e "${GREEN}[OK] Process killed${NC}"
            fi
        done
    else
        echo "Please manually stop the process using port 5000"
    fi
else
    echo -e "${GREEN}[OK] Port 5000 is available${NC}"
fi
echo ""

# [5/6] Install Python dependencies
echo -e "${YELLOW}[5/6] Installing Python dependencies...${NC}"
$PYTHON_CMD -m pip install --upgrade pip >/dev/null 2>&1
if $PYTHON_CMD -m pip install -r requirements.txt; then
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
else
    echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
    exit 1
fi
echo ""

# [6/6] Create necessary directories
echo -e "${YELLOW}[6/6] Creating necessary directories...${NC}"
mkdir -p static/uploads
echo -e "${GREEN}[OK] Directories created${NC}"
echo ""

echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}To start the application, run:${NC}"
echo -e "  $PYTHON_CMD app.py"
echo ""
echo -e "Or use: ./start_app.sh"
echo ""


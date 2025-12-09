#!/bin/bash

# Campus Marketplace - macOS/Linux Start Script
# Run with: chmod +x start_app.sh && ./start_app.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Campus Marketplace - Starting...${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Determine Python command
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[ERROR] Python is not installed!${NC}"
    echo "Please run ./setup_mac.sh first"
    exit 1
fi

# Check MySQL connection
echo -e "${YELLOW}Checking MySQL connection...${NC}"
MYSQL_TEST_SCRIPT="
import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', connection_timeout=3)
    conn.close()
    print('MySQL OK')
except Exception as e:
    print(f'ERROR: {e}')
"

MYSQL_RESULT=$(echo "$MYSQL_TEST_SCRIPT" | $PYTHON_CMD 2>&1)
if echo "$MYSQL_RESULT" | grep -q "MySQL OK"; then
    echo -e "${GREEN}MySQL connection OK${NC}"
else
    echo -e "${YELLOW}[WARNING] Cannot connect to MySQL!${NC}"
    echo "Please ensure MySQL is running"
    echo ""
    read -p "Press Enter to continue anyway..."
fi

# Check if port 5000 is in use
if command -v lsof >/dev/null 2>&1; then
    PORT_CHECK=$(lsof -ti:5000 2>/dev/null)
    if [ -n "$PORT_CHECK" ]; then
        echo -e "${YELLOW}[WARNING] Port 5000 is already in use!${NC}"
        echo ""
        PROCESSES=$(lsof -ti:5000)
        for PID in $PROCESSES; do
            PROCESS_NAME=$(ps -p $PID -o comm= 2>/dev/null)
            echo "Process using port 5000: $PROCESS_NAME (PID: $PID)"
            read -p "Kill process and continue? (y/n): " kill_choice
            if [[ "$kill_choice" =~ ^[Yy]$ ]]; then
                kill -9 $PID 2>/dev/null
                echo -e "${GREEN}[OK] Process killed${NC}"
            else
                echo "Exiting..."
                exit 1
            fi
        done
    fi
fi

# Start the application
echo ""
echo -e "${GREEN}Starting Flask application...${NC}"
echo -e "${CYAN}Open your browser at: http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

$PYTHON_CMD app.py


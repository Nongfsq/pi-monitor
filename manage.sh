#!/bin/bash

# ==========================================
# Pi-Monitor Management Script
# ==========================================

# Configuration & Paths
APP_DIR="/home/frank/Desktop/pi-monitor/backend"
VENV_PYTHON="$APP_DIR/venv/bin/python"
SCRIPT="$APP_DIR/run.py"
PID_FILE="$APP_DIR/monitor.pid"
LOG_FILE="$APP_DIR/monitor.log"

# Function to check if the application is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        # Check if the process ID is still alive
        if ps -p $PID > /dev/null 2>&1; then
            return 0 # Running
        else
            return 1 # Process died, but PID file exists
        fi
    else
        return 1 # Not running
    fi
}

# Function to start the application
start_app() {
    if is_running; then
        echo "⚠️  Service is already running! (PID: $(cat $PID_FILE))"
    else
        echo "🚀 Starting monitoring service in the background..."
        cd "$APP_DIR" || exit
        # Run in background via nohup and redirect output to log file
        nohup "$VENV_PYTHON" "$SCRIPT" > "$LOG_FILE" 2>&1 &
        # Save the process ID
        echo $! > "$PID_FILE"
        echo "✅ Service started successfully! (PID: $(cat $PID_FILE))"
        echo "📄 Logging to: $LOG_FILE"
    fi
}

# Function to stop the application
stop_app() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "🛑 Stopping service (PID: $PID)..."
        kill $PID
        rm -f "$PID_FILE"
        echo "✅ Service stopped. (Note: Hardware LED may retain its last state)"
    else
        echo "ℹ️  Service is not currently running."
        rm -f "$PID_FILE" # Clean up zombie PID file if exists
    fi
}

# Function to print current status
status_app() {
    if is_running; then
        LOCAL_IP=$(hostname -I | awk '{print $1}')
        echo -e "🟢 Current Status: [\033[32mRUNNING\033[0m] (PID: $(cat $PID_FILE))"
        echo -e "🌐 Web Dashboard : \033[36mhttp://${LOCAL_IP}:5000\033[0m"
    else
        echo -e "🔴 Current Status: [\033[31mSTOPPED\033[0m]"
    fi
}

# ==========================================
# Interactive CLI Menu
# ==========================================
clear
echo "====================================="
echo "   Pi-Monitor Management Dashboard"
echo "====================================="
status_app
echo "-------------------------------------"
echo "  1) Start Service (Background)"
echo "  2) Stop Service"
echo "  3) Refresh Status"
echo "  4) View Live Logs"
echo "  0) Exit Menu"
echo "====================================="
read -p "Please select an option [0-4]: " option

case $option in
    1) start_app ;;
    2) stop_app ;;
    3) status_app ;;
    4) 
       echo "Press [Ctrl+C] to exit log view..."
       sleep 1
       tail -f "$LOG_FILE" 
       ;;
    0) echo "Goodbye!"; exit 0 ;;
    *) echo "❌ Invalid option." ;;
esac
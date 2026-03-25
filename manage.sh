#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/backend"
SCRIPT="$APP_DIR/run.py"
PID_FILE="$APP_DIR/monitor.pid"
LOG_FILE="$APP_DIR/monitor.log"

if [ -x "$APP_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$APP_DIR/venv/bin/python"
else
    PYTHON_BIN="$(command -v python3 || true)"
fi

check_environment() {
    if [ ! -d "$APP_DIR" ]; then
        echo "Error: backend directory not found: $APP_DIR"
        exit 1
    fi

    if [ ! -f "$SCRIPT" ]; then
        echo "Error: run.py not found: $SCRIPT"
        exit 1
    fi

    if [ -z "${PYTHON_BIN:-}" ] || [ ! -x "$PYTHON_BIN" ]; then
        echo "Error: Python interpreter not found."
        exit 1
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID="$(cat "$PID_FILE")"
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

cleanup_stale_pid() {
    if [ -f "$PID_FILE" ] && ! is_running; then
        rm -f "$PID_FILE"
    fi
}

get_local_ip() {
    hostname -I 2>/dev/null | awk '{print $1}'
}

start_app() {
    check_environment
    cleanup_stale_pid

    if is_running; then
        echo "Service is already running. PID: $(cat "$PID_FILE")"
        return 0
    fi

    cd "$APP_DIR" || exit 1
    nohup "$PYTHON_BIN" "$SCRIPT" > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"

    sleep 1

    if ps -p "$NEW_PID" > /dev/null 2>&1; then
        echo "Service started. PID: $NEW_PID"
        echo "Log file: $LOG_FILE"

        LOCAL_IP="$(get_local_ip)"
        if [ -n "${LOCAL_IP:-}" ]; then
            echo "Dashboard: http://${LOCAL_IP}:5000"
            echo "Dev Console: http://${LOCAL_IP}:5000/dev"
        fi
    else
        echo "Failed to start service."
        echo "Last log output:"
        tail -n 20 "$LOG_FILE" 2>/dev/null || true
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_app() {
    cleanup_stale_pid

    if is_running; then
        PID="$(cat "$PID_FILE")"
        kill "$PID" 2>/dev/null || true
        sleep 1

        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID" 2>/dev/null || true
        fi

        rm -f "$PID_FILE"
        echo "Service stopped."
    else
        echo "Service is not running."
    fi
}

restart_app() {
    stop_app
    start_app
}

status_app() {
    cleanup_stale_pid

    if is_running; then
        PID="$(cat "$PID_FILE")"
        echo "Status: RUNNING"
        echo "PID: $PID"

        LOCAL_IP="$(get_local_ip)"
        if [ -n "${LOCAL_IP:-}" ]; then
            echo "Dashboard: http://${LOCAL_IP}:5000"
            echo "Dev Console: http://${LOCAL_IP}:5000/dev"
        fi
    else
        echo "Status: STOPPED"
    fi
}

logs_app() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Log file not found: $LOG_FILE"
    fi
}

run_foreground() {
    check_environment
    cd "$APP_DIR" || exit 1
    exec "$PYTHON_BIN" "$SCRIPT"
}

show_help() {
    cat <<EOF
Usage:
  ./manage.sh start
  ./manage.sh stop
  ./manage.sh restart
  ./manage.sh status
  ./manage.sh logs
  ./manage.sh run
  ./manage.sh help

Commands:
  start    Start the service in the background
  stop     Stop the background service
  restart  Restart the background service
  status   Show current service status
  logs     View live logs
  run      Run the app in the foreground
  help     Show this help message
EOF
}

COMMAND="${1:-help}"

case "$COMMAND" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        logs_app
        ;;
    run)
        run_foreground
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo
        show_help
        exit 1
        ;;
esac
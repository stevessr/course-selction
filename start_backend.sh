#!/bin/bash
## start_backend.sh - start/stop/restart/status for backend services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PIDS_FILE=".backend_pids"

# Load env vars from project root .env if present
load_root_env() {
    if [ -f ".env" ]; then
        echo_msg "${GREEN}Loading environment from ./.env${NC}"
        # Export all variables defined by sourcing .env
        set -a
        # shellcheck disable=SC1091
        . ./.env
        set +a
        # Optional: show a couple of important ones if set
        if [ -n "${INTERNAL_TOKEN:-}" ]; then echo_msg "INTERNAL_TOKEN is set"; fi
        if [ -n "${USE_SOCKETS:-}" ]; then echo_msg "USE_SOCKETS=${USE_SOCKETS}"; fi
        if [ -n "${SOCKET_DIR:-}" ]; then echo_msg "SOCKET_DIR=${SOCKET_DIR}"; fi
    else
        echo_msg "${YELLOW}No .env found in project root; using defaults${NC}"
    fi
}

echo_msg() { printf "%b\n" "$1"; }

create_envs() {
    for service in data_node auth_node teacher_node student_node queue_node; do
        if [ ! -f "backend/$service/.env" ]; then
            echo_msg "${YELLOW}Creating .env file for $service${NC}"
            cp "backend/$service/.env.example" "backend/$service/.env" 2>/dev/null || true
        fi
    done
}

start_services() {
    echo_msg "${GREEN}Starting Course Selection System Backend Services${NC}"
    load_root_env
    create_envs

    # Select Python interpreter robustly
    # Prefer project virtualenv only if it's healthy (can import encodings)
    PY_BIN="python3"
    if command -v python3 >/dev/null 2>&1; then
        PY_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PY_BIN="python"
    fi

    if [ -x ".venv/bin/python" ]; then
        if ".venv/bin/python" - <<'EOF'
import sys
try:
    import encodings  # minimal sanity check of venv
except Exception as e:
    sys.exit(1)
else:
    sys.exit(0)
EOF
        then
            PY_BIN=".venv/bin/python"
        else
            echo_msg "${YELLOW}Warning: .venv appears broken (cannot import encodings). Falling back to system Python (${PY_BIN}).${NC}"
        fi
    fi

    # Start services in background and record PIDs
    echo_msg "${GREEN}Starting Data Node (port 8001)...${NC}"
    $PY_BIN -m backend.data_node.main &
    DATA_PID=$!

    sleep 2

    echo_msg "${GREEN}Starting Auth Node (port 8002)...${NC}"
    $PY_BIN -m backend.auth_node.main &
    AUTH_PID=$!

    sleep 2

    echo_msg "${GREEN}Starting Teacher Node (port 8003)...${NC}"
    $PY_BIN -m backend.teacher_node.main &
    TEACHER_PID=$!

    sleep 2

    echo_msg "${GREEN}Starting Student Node (port 8004)...${NC}"
    $PY_BIN -m backend.student_node.main &
    STUDENT_PID=$!

    sleep 2

    echo_msg "${GREEN}Starting Queue Node (port 8005)...${NC}"
    $PY_BIN -m backend.queue_node.main &
    QUEUE_PID=$!

    # Save PIDs to file for relative stop
    cat > "$PIDS_FILE" <<EOF
DATA=$DATA_PID
AUTH=$AUTH_PID
TEACHER=$TEACHER_PID
STUDENT=$STUDENT_PID
QUEUE=$QUEUE_PID
EOF

    echo ""
    echo_msg "${GREEN}All services started!${NC}"
    echo "Data Node:    http://localhost:8001/docs"
    echo "Auth Node:    http://localhost:8002/docs"
    echo "Teacher Node: http://localhost:8003/docs"
    echo "Student Node: http://localhost:8004/docs"
    echo "Queue Node:   http://localhost:8005/docs"
    echo ""
    echo "Process IDs: DATA=$DATA_PID AUTH=$AUTH_PID TEACHER=$TEACHER_PID STUDENT=$STUDENT_PID QUEUE=$QUEUE_PID"
    echo ""
    echo_msg "Use './start_backend.sh stop' to stop these services"

    # Wait for all child processes so script doesn't exit immediately when used interactively
    wait
}

stop_services() {
    # If PID file exists, use it. Otherwise try to discover processes by pattern.
    if [ -f "$PIDS_FILE" ]; then
        # shellcheck disable=SC1090
        source "$PIDS_FILE"

        echo_msg "${YELLOW}Stopping all services (using $PIDS_FILE)...${NC}"
        kill ${DATA:-} ${AUTH:-} ${TEACHER:-} ${STUDENT:-} ${QUEUE:-} 2>/dev/null || true
        sleep 1
        # Ensure processes terminated, force kill if necessary
        for pid in ${DATA:-} ${AUTH:-} ${TEACHER:-} ${STUDENT:-} ${QUEUE:-}; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        done

        rm -f "$PIDS_FILE"
        echo_msg "${GREEN}All backend services stopped.${NC}"
    else
        echo_msg "${YELLOW}No PID file found ($PIDS_FILE). Attempting to discover running backend Python services...${NC}"
        services_patterns=("backend.data_node.main" "backend.auth_node.main" "backend.teacher_node.main" "backend.student_node.main" "backend.queue_node.main")
        found_any=0
        for pat in "${services_patterns[@]}"; do
            pids=$(pgrep -f "$pat" | tr '\n' ' ')
            if [ -n "$pids" ]; then
                found_any=1
                echo_msg "Stopping processes matching '$pat': $pids"
                kill $pids 2>/dev/null || true
                sleep 1
                # force kill if still alive
                for pid in $pids; do
                    if kill -0 "$pid" 2>/dev/null; then
                        kill -9 "$pid" 2>/dev/null || true
                    fi
                done
            fi
        done
        if [ "$found_any" -eq 0 ]; then
            echo_msg "${YELLOW}No matching backend processes found.${NC}"
            exit 1
        else
            echo_msg "${GREEN}Discovered backend services stopped.${NC}"
        fi
    fi
}

status_services() {
    if [ ! -f "$PIDS_FILE" ]; then
        echo_msg "${YELLOW}No PID file ($PIDS_FILE) — services may not be running.${NC}"
        exit 1
    fi
    source "$PIDS_FILE"
    printf "%-10s %-8s %s\n" "SERVICE" "PID" "STATUS"
    for name in DATA AUTH TEACHER STUDENT QUEUE; do
        pid=${!name}
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            stat="running"
        else
            stat="stopped"
        fi
        printf "%-10s %-8s %s\n" "$name" "${pid:--}" "$stat"
    done
}

case "$1" in
    start|"")
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services || true
        sleep 1
        start_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 2
        ;;
esac

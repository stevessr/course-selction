#!/bin/bash
# stop_backend.sh - stop backend services for course selection system
#
# Behavior:
#   - If `.backend_pids` exists, read PIDs and kill them (graceful then force).
#   - Otherwise, try to discover running Python processes by matching module
#     patterns (pgrep -f) and kill those.
#
# Usage:
#   ./stop_backend.sh
#
# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PIDS_FILE=".backend_pids"

echo_msg() { printf "%b\n" "$1"; }

if [ -f "$PIDS_FILE" ]; then
    # shellcheck disable=SC1090
    source "$PIDS_FILE"
    echo_msg "${YELLOW}Stopping all services (using $PIDS_FILE)...${NC}"
    kill ${DATA:-} ${AUTH:-} ${TEACHER:-} ${STUDENT:-} ${QUEUE:-} 2>/dev/null || true
    sleep 1
    for pid in ${DATA:-} ${AUTH:-} ${TEACHER:-} ${STUDENT:-} ${QUEUE:-}; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo_msg "Force killing PID $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    rm -f "$PIDS_FILE"
    echo_msg "${GREEN}All backend services stopped.${NC}"
    exit 0
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
            for pid in $pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    echo_msg "Force killing PID $pid"
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
        exit 0
    fi
fi

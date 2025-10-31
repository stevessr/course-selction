#!/bin/bash
# Start all backend services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Course Selection System Backend Services${NC}"

# Create .env files if they don't exist
for service in data_node auth_node teacher_node student_node queue_node; do
    if [ ! -f "backend/$service/.env" ]; then
        echo -e "${YELLOW}Creating .env file for $service${NC}"
        cp "backend/$service/.env.example" "backend/$service/.env"
    fi
done

# Start services in background
echo -e "${GREEN}Starting Data Node (port 8001)...${NC}"
python -m backend.data_node.main &
DATA_PID=$!

sleep 2

echo -e "${GREEN}Starting Auth Node (port 8002)...${NC}"
python -m backend.auth_node.main &
AUTH_PID=$!

sleep 2

echo -e "${GREEN}Starting Teacher Node (port 8003)...${NC}"
python -m backend.teacher_node.main &
TEACHER_PID=$!

sleep 2

echo -e "${GREEN}Starting Student Node (port 8004)...${NC}"
python -m backend.student_node.main &
STUDENT_PID=$!

sleep 2

echo -e "${GREEN}Starting Queue Node (port 8005)...${NC}"
python -m backend.queue_node.main &
QUEUE_PID=$!

echo ""
echo -e "${GREEN}All services started!${NC}"
echo "Data Node:    http://localhost:8001/docs"
echo "Auth Node:    http://localhost:8002/docs"
echo "Teacher Node: http://localhost:8003/docs"
echo "Student Node: http://localhost:8004/docs"
echo "Queue Node:   http://localhost:8005/docs"
echo ""
echo "Process IDs: DATA=$DATA_PID AUTH=$AUTH_PID TEACHER=$TEACHER_PID STUDENT=$STUDENT_PID QUEUE=$QUEUE_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to stop all services
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    kill $DATA_PID $AUTH_PID $TEACHER_PID $STUDENT_PID $QUEUE_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Wait for all processes
wait

#!/bin/bash

# Create logs and pids directory if they don't exist
mkdir -p .cluster/logs .cluster/pids

# Function to start a backend service
start_backend_service() {
  local service_name=$1
  local port=$2
  echo "Starting $service_name on port $port..."
  uv run backend/server.py $service_name --port $port > .cluster/logs/$service_name.log 2>&1 &
  echo $! > .cluster/pids/$service_name.pid
}

# Function to stop a backend service
stop_backend_service() {
  local service_name=$1
  if [ -f ".cluster/pids/$service_name.pid" ]; then
    local pid=$(cat .cluster/pids/$service_name.pid)
    echo "Stopping $service_name (PID: $pid)..."
    kill $pid
    rm .cluster/pids/$service_name.pid
  else
    echo "$service_name is not running."
  fi
}

# Function to start the frontend
start_frontend() {
  echo "Starting frontend development server..."
  (cd ui-of-course-selection && bun dev) > .cluster/logs/frontend.log 2>&1 &
  echo $! > .cluster/pids/frontend.pid
}

# Function to stop the frontend
stop_frontend() {
  if [ -f ".cluster/pids/frontend.pid" ]; then
    local pid=$(cat .cluster/pids/frontend.pid)
    echo "Stopping frontend (PID: $pid)..."
    kill $pid
    rm .cluster/pids/frontend.pid
  else
    echo "Frontend is not running."
  fi
}

if [ "$1" == "start" ]; then
  echo "Stopping existing cluster if any..."
  stop_backend_service "login"
  stop_backend_service "course_data"
  stop_backend_service "teacher"
  stop_backend_service "student"
  stop_backend_service "queue"
  stop_frontend
  echo "Starting new cluster..."
  start_backend_service "course_data" 8001
  start_backend_service "login" 8002
  start_backend_service "teacher" 8003
  start_backend_service "student" 8004
  start_backend_service "queue" 8005
  start_frontend
  echo "Development cluster started."
elif [ "$1" == "stop" ]; then
  stop_backend_service "login"
  stop_backend_service "course_data"
  stop_backend_service "teacher"
  stop_backend_service "student"
  stop_backend_service "queue"
  stop_frontend
  echo "Development cluster stopped."
else
  echo "Usage: $0 {start|stop}"
  exit 1
fi

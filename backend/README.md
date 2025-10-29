# Course Selection Backend

This is a multi-service backend for a course selection system built with FastAPI. It consists of five separate services that communicate with each other.

## Architecture

The system is divided into 5 services:

1. **Course Data Node** (Port 8001): Handles course information storage and retrieval
2. **Login Node** (Port 8002): Handles user authentication and JWT token management
3. **Teacher Processing Node** (Port 8003): Handles teacher-specific operations
4. **Student Processing Node** (Port 8004): Handles student-specific operations
5. **Queue Buffer Node** (Port 8005): Handles high-concurrency requests with message queuing

## Setup

### Prerequisites

- Python 3.9+
- Redis server (for queue buffering)

### Installation

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Set up environment variables (optional, defaults are in settings.py):
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. Initialize the database and create default admin accounts:
   ```bash
   python init_db.py
   # Or use the direct method if bcrypt is problematic:
   python create_admins.py
   ```

## Default Configuration

### Default Admin Accounts

The system comes with default admin accounts for initial access:

- Username: `admin`, Password: `admin123`
- Username: `super_admin`, Password: `super123`

**IMPORTANT: Change these default passwords immediately after first login for security reasons.**

### Default System Settings

The system includes various configurable settings for:
- Security (password policies, 2FA, session timeouts)
- Course management (limits, deadlines, conflict checking)
- Queue processing (priorities, retry logic, timeouts)
- Notifications (email, SMS)

## Running Services

Each service can be run independently:

```bash
# Course Data Node
python backend/server.py course_data

# Login Node
python backend/server.py login

# Teacher Processing Node
python backend/server.py teacher

# Student Processing Node
python backend/server.py student

# Queue Buffer Node
python backend/server.py queue
```

## Multi-Node Configuration

The system supports master-slave configuration for high availability:

- Each service can operate as a master or slave node
- Master-slave election is handled automatically using a consensus algorithm
- Node discovery is performed on startup

## API Protection

- Internal service communication is protected by tokens
- API endpoints may require protection tokens for access
- JWT tokens are used for user authentication

## Database

- SQLite is used as the primary database (can be configured to use PostgreSQL/MySQL)
- Each service has its own database schema as needed

## Redis Configuration

- Queue buffer service uses Redis for task queuing
- Session storage and caching (optional)

## API Documentation

API documentation is available at `/docs` endpoint for each service when running.
# Course Selection System

A comprehensive student course selection system built with FastAPI (Python) backend and Vue3 + Ant Design frontend.

## Features

### Backend (FastAPI Microservices)
- **Course Data Node**: Course and student data management with SQLite
- **Authentication Node**: User authentication with JWT tokens and 2FA
- **Teacher Service**: Course CRUD operations and student management
- **Student Service**: Course selection and schedule viewing
- **Queue Buffer Node**: Rate limiting with token bucket algorithm

### Frontend (Vue3 + Ant Design)
- **Student Interface**: Course selection with 2FA authentication
- **Teacher Interface**: Course management and student import
- **Admin Interface**: User management and registration code generation

### Key Features
- Dual rate limiting (frontend token pool + backend rate limiting)
- IP-based rate limiting with X-Forwarded-For support
- 2FA authentication for students
- Refresh token + access token mechanism
- SQLite database with master-slave replication support
- Role-based access control (Student, Teacher, Admin)

## Project Structure

```
.
├── backend/
│   ├── common/          # Shared utilities and models
│   ├── data_node/       # Course data management service
│   ├── auth_node/       # Authentication service
│   ├── teacher_node/    # Teacher service
│   ├── student_node/    # Student service
│   └── queue_node/      # Queue buffer and rate limiting service
├── frontend/
│   └── src/
│       ├── api/         # API client modules
│       ├── components/  # Vue components
│       ├── views/       # Page views
│       ├── router/      # Vue Router configuration
│       ├── store/       # Pinia store
│       └── utils/       # Utility functions
└── plan.md             # Detailed architecture plan

```

## Installation

### Backend

```bash
# Install Python dependencies
pip install -e .

# Or use uv (recommended)
uv sync
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Services

### Backend Services

Each microservice can be run independently:

```bash
# Course Data Node (default: port 8001)
python -m backend.data_node.main

# Authentication Node (default: port 8002)
python -m backend.auth_node.main

# Teacher Service (default: port 8003)
python -m backend.teacher_node.main

# Student Service (default: port 8004)
python -m backend.student_node.main

# Queue Buffer Node (default: port 8005)
python -m backend.queue_node.main
```

### Frontend

```bash
cd frontend
npm run dev
```

## Configuration

Each backend service uses environment variables for configuration. Create `.env` files in each service directory:

```env
# Example for data_node/.env
DATABASE_URL=sqlite:///./course_data.db
SECRET_TOKEN=your-secret-token-here
PORT=8001
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=backend --cov-report=html
```

## API Documentation

Once services are running, access the interactive API documentation:

- Data Node: http://localhost:8001/docs
- Auth Node: http://localhost:8002/docs
- Teacher Service: http://localhost:8003/docs
- Student Service: http://localhost:8004/docs
- Queue Node: http://localhost:8005/docs

## License

MIT

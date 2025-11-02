# Course Selection System - Project Overview

## Project Summary

The Course Selection System is a comprehensive student course management application built using a microservices architecture. It features a FastAPI backend with multiple service nodes and a Vue3 frontend with Ant Design UI components. The system supports student course selection, teacher course management, and administrator user management with dual-factor authentication and advanced rate limiting.

## Architecture

### Backend (FastAPI Microservices)

The backend is composed of five interconnected microservices:

1. **Data Node** (`/backend/data_node`): Manages course and student data with SQLite
2. **Auth Node** (`/backend/auth_node`): Handles user authentication with JWT tokens and 2FA
3. **Teacher Service** (`/backend/teacher_node`): Provides course CRUD operations and student management
4. **Student Service** (`/backend/student_node`): Manages course selection and schedule viewing
5. **Queue Buffer Node** (`/backend/queue_node`): Implements rate limiting with token bucket algorithm

### Frontend (Vue3 + Ant Design)

The frontend provides three distinct interfaces:
- **Student Interface**: Course selection with 2FA authentication
- **Teacher Interface**: Course management and student import
- **Admin Interface**: User management and registration code generation

## Key Features

- **Dual Rate Limiting**: Frontend token pool + backend rate limiting
- **2FA Authentication**: Required for students, using TOTP
- **Token Management**: Refresh token + access token mechanism
- **SQLite Database**: With master-slave replication support
- **Role-based Access Control**: Student, Teacher, Admin roles
- **Dual Communication**: HTTP and Socket communication modes
- **Separated APIs**: Role-specific API endpoints
- **CLI Tools**: For user management and database editing
- **CSV Import**: User bulk import functionality
- **Random User Generation**: For testing and development

## Building and Running

### Prerequisites
- Python 3.10+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
pip install -e .
```

Or using uv (recommended):
```bash
pip install uv
uv sync
```

### Environment Configuration
Each service needs a `.env` file:
```bash
cd backend/data_node && cp .env.example .env
cd ../auth_node && cp .env.example .env
cd ../teacher_node && cp .env.example .env
cd ../student_node && cp .env.example .env
cd ../queue_node && cp .env.example .env
cd ../..
```

### Start Backend Services
```bash
./start_backend.sh
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access Points
- Frontend: http://localhost:3000
- Data Node API: http://localhost:8001/docs
- Auth Node API: http://localhost:8002/docs
- Teacher Node API: http://localhost:8003/docs
- Student Node API: http://localhost:8004/docs
- Queue Node API: http://localhost:8005/docs

## Development Conventions

### Code Structure
- Python backend follows FastAPI conventions with Pydantic models
- Vue3 frontend uses Composition API with Pinia for state management
- Ant Design Vue components for UI consistency
- SQLAlchemy ORM for database operations

### Testing
The system includes comprehensive testing:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# System integration test
python test_system.py
```

### CLI Tools
Two main CLI tools are available:
1. `course-cli` - for user management and system operations
2. `course-db-edit` - for direct database manipulation

### Coding Style
- Python: Black and Ruff formatting
- JavaScript/Vue: Prettier and ESLint

### Authentication Flow
The system uses a two-phase authentication process:
1. Primary phase: username/password login
2. Secondary phase: 2FA verification (required for students)

## Deployment Notes

For production deployment:
1. Change default passwords and tokens
2. Use environment variables for sensitive data
3. Enable HTTPS for all services
4. Configure proper CORS origins
5. Use production-grade database (PostgreSQL)
6. Set up proper logging and monitoring
7. Use reverse proxy (nginx) for load balancing

## Database Models

The system uses several key models:
- `Course`: Course information with scheduling and capacity
- `Student`: Student profiles and enrolled courses
- `Teacher`: Teacher profiles and assigned courses
- `User`: Authentication information with 2FA support
- `Admin`: Administrative accounts
- `RefreshToken`: JWT refresh token management
- `RegistrationCode`: Admin-generated registration tokens
- `QueueTask`: Course selection queue tasks

## Environment Variables

Each service requires specific environment variables in its `.env` file:
- `INTERNAL_TOKEN`: Token for inter-service communication
- `JWT_SECRET_KEY`: Secret for JWT signing
- `PORT`: Service HTTP port
- `DATABASE_URL`: Database connection string
- Service-specific URLs for inter-service communication
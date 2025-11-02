# Developer Guide

Complete guide for developers working on the Course Selection System.

## Table of Contents

- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [Testing](#testing)
- [Utilities](#utilities)
- [Contributing](#contributing)

## Development Environment

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional, for DevContainer)

### Option 1: DevContainer (Recommended)

The easiest way to get started:

1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project in VS Code
3. Click "Reopen in Container" when prompted
4. Wait for the container to build and setup to complete
5. You're ready to develop!

All dependencies, tools, and services are pre-configured.

### Option 2: Local Setup

```bash
# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend
npm install

# Create environment files
cp backend/data_node/.env.example backend/data_node/.env
cp backend/auth_node/.env.example backend/auth_node/.env
cp backend/teacher_node/.env.example backend/teacher_node/.env
cp backend/student_node/.env.example backend/student_node/.env
cp backend/queue_node/.env.example backend/queue_node/.env

# Edit .env files with your configuration
```

## Project Structure

```
course-selction/
├── backend/
│   ├── common/              # Shared utilities
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── security.py      # Auth & crypto utils
│   │   ├── rate_limiter.py  # Token bucket implementation
│   │   ├── csv_import.py    # CSV user import
│   │   └── user_generator.py # Random user generator
│   │
│   ├── data_node/          # Course data service
│   ├── auth_node/          # Authentication service
│   ├── teacher_node/       # Teacher operations
│   ├── student_node/       # Student operations
│   └── queue_node/         # Queue & rate limiting
│
├── frontend/               # Vue3 + Ant Design
│   ├── src/
│   │   ├── api/           # API clients
│   │   ├── components/    # Reusable components
│   │   ├── views/         # Page views
│   │   ├── router/        # Vue Router
│   │   └── store/         # Pinia stores
│   └── package.json
│
├── tests/                 # Test suite
│   ├── test_basic.py      # Unit tests
│   └── test_integration.py # Integration tests
│
└── .devcontainer/         # Dev Container config
```

## Backend Development

### Running Services

Start all backend services:
```bash
./start_backend.sh
```

Or run individually for debugging:
```bash
# Data Node
python -m backend.data_node.main

# Auth Node
python -m backend.auth_node.main

# Teacher Node
python -m backend.teacher_node.main

# Student Node
python -m backend.student_node.main

# Queue Node
python -m backend.queue_node.main
```

### API Documentation

Each service provides interactive API docs (Swagger UI):
- Data Node: http://localhost:8001/docs
- Auth Node: http://localhost:8002/docs
- Teacher Node: http://localhost:8003/docs
- Student Node: http://localhost:8004/docs
- Queue Node: http://localhost:8005/docs

### Adding a New Endpoint

1. **Define the Pydantic schema** in `backend/common/schemas.py`:
```python
class NewFeatureRequest(BaseModel):
    field1: str
    field2: int
```

2. **Add the endpoint** to the appropriate service:
```python
@app.post("/new-feature")
async def new_feature(
    request: NewFeatureRequest,
    current_user: Dict = Depends(get_current_user)
):
    # Your logic here
    return {"success": True}
```

3. **Add tests** in `tests/`:
```python
@pytest.mark.asyncio
async def test_new_feature(client, access_token):
    response = await client.post(
        f"{SERVICE_URL}/new-feature",
        json={"field1": "value", "field2": 42},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
```

### Database Migrations

Currently using SQLite with auto-create. For production with PostgreSQL:

1. Install Alembic:
```bash
pip install alembic
```

2. Initialize migrations:
```bash
alembic init migrations
```

3. Create migration:
```bash
alembic revision --autogenerate -m "Description"
```

4. Apply migration:
```bash
alembic upgrade head
```

## Frontend Development

### Running Development Server

```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

### Project Structure

```
frontend/src/
├── api/           # API client modules
├── components/    # Reusable Vue components
├── views/         # Page components
│   ├── student/   # Student interface
│   ├── teacher/   # Teacher interface
│   └── admin/     # Admin interface
├── router/        # Vue Router configuration
├── store/         # Pinia state management
└── utils/         # Helper functions
```

### Adding a New View

1. **Create the view** in `frontend/src/views/`:
```vue
<template>
  <div>
    <h1>New Feature</h1>
    <!-- Your content -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
// Your logic
</script>
```

2. **Add route** in `frontend/src/router/index.js`:
```javascript
{
  path: '/new-feature',
  name: 'NewFeature',
  component: () => import('@/views/NewFeature.vue'),
  meta: { requiresAuth: true }
}
```

3. **Add API client** in `frontend/src/api/`:
```javascript
export default {
  newFeature(accessToken, data) {
    return api.post('/new-feature', data, {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  }
}
```

### State Management

Using Pinia for state management:

```javascript
// frontend/src/store/feature.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFeatureStore = defineStore('feature', () => {
  const data = ref([])
  
  function loadData() {
    // Load data
  }
  
  return { data, loadData }
})
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_integration.py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html

# Integration tests only
pytest tests/test_integration.py -v -s
```

### Writing Tests

**Unit Test Example:**
```python
def test_token_bucket():
    """Test token bucket rate limiting"""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)
    assert bucket.consume(5) == True
    assert bucket.get_available_tokens() == 5
```

**Integration Test Example:**
```python
@pytest.mark.asyncio
async def test_student_workflow(client, admin_token):
    """Test complete student workflow"""
    # Register student
    response = await client.post(...)
    assert response.status_code == 200
    
    # Login
    response = await client.post(...)
    assert response.status_code == 200
```

### Test Data

Generate test users:
```bash
# Generate 50 random students
python -m backend.common.user_generator 50 --output students.csv

# Generate teachers
python -m backend.common.user_generator 20 --type teacher --output teachers.csv
```

Import test users:
```bash
# Import from CSV
python -m backend.common.csv_import students.csv --type student

# Generate passwords automatically
python -m backend.common.csv_import users.csv --generate-passwords
```

## Utilities

### CSV User Import

Import users from CSV file:

**CSV Format:**
```csv
username,password,name,email
john.doe,pass123,John Doe,john@example.com
jane.smith,pass456,Jane Smith,jane@example.com
```

**Import:**
```bash
python -m backend.common.csv_import users.csv \
  --type student \
  --admin-user admin \
  --admin-pass admin123 \
  --output results.csv
```

**Options:**
- `--type`: User type (student/teacher)
- `--generate-passwords`: Generate random passwords
- `--output`: Save results to file
- `--auth-url`: Auth service URL
- `--data-url`: Data service URL

### Random User Generator

Generate random users for testing:

```bash
# Generate 50 students
python -m backend.common.user_generator 50 \
  --output students.csv

# Generate teachers without passwords
python -m backend.common.user_generator 20 \
  --type teacher \
  --no-passwords \
  --output teachers.csv
```

### System Test Script

Test all services:
```bash
python test_system.py
```

This will:
1. Check service health
2. Test admin login
3. Create test data
4. Generate registration codes

## Code Style

### Python

Using Black and Ruff for formatting:
```bash
# Format code
black backend/

# Lint code
ruff check backend/

# Fix lint issues
ruff check --fix backend/
```

### JavaScript/Vue

Using Prettier and ESLint:
```bash
cd frontend

# Format code
npm run format

# Lint code
npm run lint
```

## Debugging

### Backend Debugging

Add breakpoints and run in debug mode:
```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger:
1. Set breakpoints in code
2. Press F5
3. Select "Python: FastAPI"

### Frontend Debugging

Use Vue DevTools:
1. Install [Vue DevTools](https://devtools.vuejs.org/)
2. Open Chrome DevTools
3. Navigate to Vue tab

### Logging

Configure logging in services:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

## Common Tasks

### Add a New User Role

1. Update `User` model in `backend/common/models.py`
2. Add validation in `backend/common/schemas.py`
3. Update authentication logic in `backend/auth_node/main.py`
4. Add route guards in `frontend/src/router/index.js`
5. Create role-specific views

### Change Database Schema

1. Update models in `backend/common/models.py`
2. Delete existing `.db` files
3. Restart services (auto-create will run)
4. Or use Alembic for proper migrations

### Add Rate Limiting to Endpoint

```python
from backend.common import api_limiter, get_request_headers

@app.post("/endpoint")
async def endpoint(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    headers = get_request_headers(request)
    if not api_limiter.check_rate_limit(headers, current_user['user_id']):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Your logic here
```

## Contributing

### Workflow

1. Create a feature branch:
```bash
git checkout -b feature/my-feature
```

2. Make your changes

3. Run tests:
```bash
pytest tests/ -v
```

4. Format code:
```bash
black backend/
cd frontend && npm run lint
```

5. Commit changes:
```bash
git add .
git commit -m "feat: add new feature"
```

6. Push and create PR:
```bash
git push origin feature/my-feature
```

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `style:` Code style
- `chore:` Maintenance

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted
- [ ] No console.log/print statements
- [ ] Error handling implemented
- [ ] Security considerations addressed

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Ant Design Vue](https://antdv.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Troubleshooting

### Services Won't Start

Check if ports are in use:
```bash
lsof -i :8001
lsof -i :8002
# etc.
```

### Import Errors

Reinstall dependencies:
```bash
pip install -e .
cd frontend && npm install
```

### Database Errors

Delete and recreate:
```bash
rm *.db
# Restart services
```

### 2FA Not Working

1. Check system time is synchronized
2. Verify TOTP secret is correct
3. Try different authenticator app
4. Generate reset code as admin

## Getting Help

- Check existing issues on GitHub
- Review documentation in `/docs`
- Ask in project discussions
- Contact maintainers

---

Happy coding! 🚀

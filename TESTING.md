# Testing Guide

Complete guide for testing the Course Selection System.

## Quick Start

### Run All Tests

```bash
# Install test dependencies first
pip install pytest pytest-asyncio pytest-cov httpx pyotp

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

## Test Types

### 1. Unit Tests

Location: `tests/test_basic.py`

Tests individual components:
- Password hashing and verification
- TOTP secret generation
- Token bucket rate limiting
- Rate limiter functionality

**Run unit tests:**
```bash
pytest tests/test_basic.py -v
```

### 2. Integration Tests

Location: `tests/test_integration.py`

Tests complete workflows:
- Complete user registration with 2FA
- Student course selection workflow
- Rate limiting under load
- Teacher operations
- Queue processing

**Run integration tests:**
```bash
# Start all backend services first
./start_backend.sh

# In another terminal, run tests
pytest tests/test_integration.py -v -s
```

**Note:** Integration tests require services to be running!

### 3. System Tests

Location: `test_system.py`

Tests system health and basic operations:
- Service health checks
- Admin authentication
- Basic CRUD operations
- Registration code generation

**Run system test:**
```bash
# Start services first
./start_backend.sh

# Run system test
python test_system.py
```

## Test Data Management

### Generate Test Users

```bash
# Generate 50 random students
python -m backend.common.user_generator 50 --output students.csv

# Generate 20 teachers
python -m backend.common.user_generator 20 --type teacher --output teachers.csv
```

### Import Test Users

```bash
# Import from CSV
python -m backend.common.csv_import students.csv \
  --type student \
  --admin-user admin \
  --admin-pass admin123

# Generate passwords automatically
python -m backend.common.csv_import users.csv \
  --generate-passwords \
  --output results.csv
```

## Writing Tests

### Unit Test Template

```python
def test_feature():
    """Test description"""
    # Setup
    input_data = "test"
    
    # Execute
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Integration Test Template

```python
@pytest.mark.asyncio
async def test_workflow(client, admin_token):
    """Test complete workflow"""
    # Step 1: Setup
    response = await client.post(
        f"{SERVICE_URL}/endpoint",
        json={"data": "value"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Step 2: Verify
    data = response.json()
    assert data["success"] == True
```

## Test Fixtures

### Available Fixtures

```python
@pytest.fixture
async def client():
    """Async HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

@pytest.fixture
async def admin_token(client):
    """Admin access token"""
    response = await client.post(
        f"{AUTH_URL}/login/admin",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]
```

## Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest tests/ --cov=backend --cov-report=html

# Open report in browser
open htmlcov/index.html
```

### Coverage Goals

- **Overall:** > 80%
- **Critical paths:** > 90%
- **Security code:** 100%

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run unit tests
      run: pytest tests/test_basic.py -v
```

## Performance Testing

### Load Testing with Locust

Install Locust:
```bash
pip install locust
```

Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class CourseSelectionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def select_course(self):
        self.client.post(
            "/student/course/select",
            json={"course_id": 1},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8004
```

## Debugging Tests

### Enable Verbose Output

```bash
pytest tests/ -v -s
```

### Run Specific Test

```bash
pytest tests/test_integration.py::test_complete_workflow -v -s
```

### Use Debugger

```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger:
1. Set breakpoint
2. Run "Python: Debug Tests"

## Common Issues

### Services Not Running

**Error:** Connection refused

**Solution:**
```bash
./start_backend.sh
# Wait for services to start
sleep 5
pytest tests/test_integration.py -v
```

### Rate Limiting in Tests

**Error:** 429 Too Many Requests

**Solution:** Add delays between requests:
```python
await asyncio.sleep(1)
```

### Database Lock Errors

**Error:** Database is locked

**Solution:** Ensure tests clean up properly:
```python
@pytest.fixture(autouse=True)
async def cleanup(db):
    yield
    db.close()
```

### 2FA Code Expired

**Error:** Invalid 2FA code

**Solution:** Generate code immediately before use:
```python
totp = pyotp.TOTP(secret)
code = totp.now()  # Use immediately
```

## Best Practices

1. **Isolate Tests:** Each test should be independent
2. **Clean Up:** Always clean up test data
3. **Mock External Services:** Use mocks for external APIs
4. **Use Fixtures:** Share common setup code
5. **Name Clearly:** Test names should describe what they test
6. **Assert Meaningful:** Check specific conditions, not just success
7. **Test Edge Cases:** Include boundary conditions
8. **Document Complex Tests:** Add comments for clarity

## Testing Checklist

Before committing:

- [ ] All unit tests pass
- [ ] Integration tests pass (with services running)
- [ ] No console warnings or errors
- [ ] Code coverage > 80%
- [ ] New features have tests
- [ ] Edge cases tested
- [ ] Error handling tested
- [ ] Documentation updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX Testing](https://www.python-httpx.org/advanced/#testing)
- [Coverage.py](https://coverage.readthedocs.io/)

---

Happy testing! 🧪

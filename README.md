# Course Selection System

一个使用 FastAPI (Python) 后端和 Vue3 + Ant Design 前端构建的综合学生选课系统。

A comprehensive student course selection system built with FastAPI (Python) backend and Vue3 + Ant Design frontend.

## Features / 功能特性

### Backend (FastAPI Microservices) / 后端（FastAPI 微服务）
- **Course Data Node / 课程数据节点**: Course and student data management with SQLite / 使用 SQLite 进行课程和学生数据管理
- **Authentication Node / 认证节点**: User authentication with JWT tokens and 2FA / 使用 JWT 令牌和双因素认证的用户认证
- **Teacher Service / 教师服务**: Course CRUD operations and student management / 课程增删改查操作和学生管理
- **Student Service / 学生服务**: Course selection and schedule viewing / 选课和课程表查看
- **Queue Buffer Node / 队列缓冲节点**: Rate limiting with token bucket algorithm / 使用令牌桶算法的限流控制

### Frontend (Vue3 + Ant Design) / 前端（Vue3 + Ant Design）
- **Student Interface / 学生界面**: Course selection with 2FA authentication / 带双因素认证的选课功能
- **Teacher Interface / 教师界面**: Course management and student import / 课程管理和学生导入
- **Admin Interface / 管理员界面**: User management and registration code generation / 用户管理和注册码生成

### Key Features / 核心功能
- Dual rate limiting (frontend token pool + backend rate limiting) / 双重限速（前端令牌池 + 后端限速）
- IP-based rate limiting with X-Forwarded-For support / 支持 X-Forwarded-For 的 IP 限速
- 2FA authentication for students / 学生双因素认证
- Refresh token + access token mechanism / 刷新令牌 + 访问令牌机制
- SQLite database with master-slave replication support / SQLite 数据库支持主从复制
- Role-based access control (Student, Teacher, Admin) / 基于角色的访问控制（学生、教师、管理员）
- **CSV user import / CSV 用户导入** ✨ NEW
- **Random user generation / 随机用户生成** ✨ NEW
- **Complete test suite / 完整测试套件** ✨ NEW
- **DevContainer support / DevContainer 支持** ✨ NEW

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

## Quick Start / 快速开始

For detailed setup instructions, see [SETUP.md](SETUP.md)

For developer guide, see [DEVELOPER.md](DEVELOPER.md)

For user guide, see [USER_GUIDE.md](USER_GUIDE.md)

详细的安装说明请参阅 [SETUP.md](SETUP.md)

开发者指南请参阅 [DEVELOPER.md](DEVELOPER.md)

用户指南请参阅 [USER_GUIDE.md](USER_GUIDE.md)

### Option 1: DevContainer (Recommended) / 使用 DevContainer（推荐）

1. Install Docker and VS Code with Dev Containers extension
2. Open project in VS Code
3. Click "Reopen in Container"
4. Wait for setup to complete
5. Start developing!

### Option 2: Manual Setup / 手动安装

Backend / 后端:
```bash
pip install -e .
# or use uv: uv sync
```

Frontend / 前端:
```bash
cd frontend
npm install
```

Configure Environment / 配置环境:
```bash
# Copy example config files
cd backend/data_node && cp .env.example .env
cd ../auth_node && cp .env.example .env
cd ../teacher_node && cp .env.example .env
cd ../student_node && cp .env.example .env
cd ../queue_node && cp .env.example .env
```

Start all backend services:
```bash
./start_backend.sh
```

Start frontend:
```bash
cd frontend
npm run dev
```

### Access / 访问

- Frontend: http://localhost:3000
- API Docs: http://localhost:8002/docs (Auth), http://localhost:8004/docs (Student), etc.

Default admin credentials / 默认管理员凭据:
- Username: `admin`
- Password: `admin123`

## Tools & Utilities / 工具

### Generate Random Users / 生成随机用户

```bash
# Generate 50 students
python -m backend.common.user_generator 50 --output students.csv

# Generate 20 teachers
python -m backend.common.user_generator 20 --type teacher --output teachers.csv
```

### Import Users from CSV / 从 CSV 导入用户

```bash
# Import from CSV file
python -m backend.common.csv_import students.csv --type student

# With auto-generated passwords
python -m backend.common.csv_import users.csv --generate-passwords --output results.csv
```

CSV Format:
```csv
username,password,name,email
alice.johnson,pass123,Alice Johnson,alice@example.com
```

See `examples/users_example.csv` for a complete example.

### Run Tests / 运行测试

```bash
# Unit tests
pytest tests/test_basic.py -v

# Integration tests (requires running services)
pytest tests/test_integration.py -v -s

# All tests with coverage
pytest tests/ --cov=backend --cov-report=html

# System integration test
python test_system.py
```

## Architecture / 架构

The system is built as a microservices architecture:

```
Frontend (Vue3 + Ant Design)
    ↓
API Gateway / Proxy (Vite Dev Server)
    ↓
┌─────────────────────────────────────┐
│   Backend Microservices             │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │Auth Node │  │Data Node │       │
│  └────┬─────┘  └────┬─────┘       │
│       │             │              │
│  ┌────▼─────┐  ┌───▼──────┐       │
│  │Teacher   │  │Student   │       │
│  │Service   │  │Service   │       │
│  └──────────┘  └────┬─────┘       │
│                     │              │
│                ┌────▼─────┐        │
│                │Queue Node│        │
│                └──────────┘        │
└─────────────────────────────────────┘
         ↓
    SQLite Database
```

## Testing / 测试

Run unit tests:
```bash
pytest tests/ -v
```

Run system tests:
```bash
python test_system.py
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

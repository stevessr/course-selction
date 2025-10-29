# 选课系统 (Course Selection System)

一个基于 FastAPI + Vue.js 的分布式选课管理系统，支持管理员、教师和学生三种角色的完整选课流程。

## 📋 目录

- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [用户管理](#用户管理)
- [开发指南](#开发指南)

## 📖 文档导航

- **[快速开始指南](./QUICK_START.md)** - 5 分钟快速启动系统
- **[代码结构文档](./CODE_STRUCTURE.md)** - 详细的代码组织和模块说明
- **[项目计划](./plan.md)** - 原始需求和 API 设计文档
- **本文档 (README.md)** - 系统概览和完整功能介绍

## 🏗️ 系统架构

本系统采用**微服务架构**，后端分为 5 个独立的 FastAPI 服务节点：

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue.js)                       │
│                    http://localhost:5173                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Vite Proxy Layer                          │
│  /api/course  → 8001  |  /api/login   → 8002                │
│  /api/teacher → 8003  |  /api/student → 8004                │
│  /api/queue   → 8005                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Course Data  │  │    Login     │  │   Teacher    │
│   Node       │  │    Node      │  │    Node      │
│   :8001      │  │    :8002     │  │    :8003     │
└──────────────┘  └──────────────┘  └──────────────┘
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐
│   Student    │  │    Queue     │
│    Node      │  │    Node      │
│    :8004     │  │    :8005     │
└──────────────┘  └──────────────┘
        │                  │
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │  SQLite Database │
        │ course_selection │
        └──────────────────┘
```

### 节点职责

| 节点 | 端口 | 职责 | API 数量 |
|------|------|------|----------|
| **Course Data** | 8001 | 课程数据的 CRUD 操作，受 protection_token 保护 | 14 |
| **Login** | 8002 | 用户认证、JWT token 管理、2FA 验证 | 24 |
| **Teacher** | 8003 | 教师课程管理、学生管理、统计功能 | 8 |
| **Student** | 8004 | 学生选课、退课、课程表查询 | 9 |
| **Queue** | 8005 | 高并发选课的消息队列管理 | 8 |

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: SQLite (通过 SQLAlchemy 2.0 ORM)
- **认证**: JWT (python-jose) + 2FA (pyotp)
- **密码加密**: bcrypt (12 rounds)
- **异步支持**: uvicorn + asyncio
- **包管理**: uv

### 前端
- **框架**: Vue.js 3.5 (Composition API)
- **语言**: TypeScript 5.9
- **状态管理**: Pinia 3.0
- **路由**: Vue Router 4.6
- **HTTP 客户端**: Axios 1.13
- **构建工具**: Vite (Rolldown)
- **包管理**: Bun

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 20.19+ 或 22.12+
- uv (Python 包管理器)
- Bun (JavaScript 包管理器)

### 1. 克隆项目

```bash
git clone <repository-url>
cd course-selection
```

### 2. 安装依赖

#### 后端依赖
```bash
# 使用 uv 安装
uv sync
```

#### 前端依赖
```bash
cd ui-of-course-selection
bun install
```

### 3. 初始化数据库

```bash
# 创建数据库表结构
python init_db.py

# 创建初始管理员账户（可选）
uv run python manage-users.py add-admin admin password123
```

### 4. 启动服务

#### 启动后端集群
```bash
# 启动所有 5 个后端服务
./start-dev-cluster.sh start

# 查看服务状态
./start-dev-cluster.sh status

# 停止所有服务
./start-dev-cluster.sh stop
```

#### 启动前端开发服务器
```bash
cd ui-of-course-selection
bun dev
```

### 5. 访问系统

- **前端界面**: http://localhost:5173
- **API 文档**:
  - Course Data: http://localhost:8001/docs
  - Login: http://localhost:8002/docs
  - Teacher: http://localhost:8003/docs
  - Student: http://localhost:8004/docs
  - Queue: http://localhost:8005/docs

### 默认测试账户

开发模式下可用的测试账户：

| 角色 | 用户名 | 密码 | 2FA 验证码 |
|------|--------|------|-----------|
| Admin | admin | password | 123456 |
| Teacher | teacher | password | 123456 |
| Student | student | password | 123456 |

## ✨ 功能特性

### 管理员功能
- ✅ 用户管理（添加/删除/修改管理员、教师、学生）
- ✅ 课程管理（创建/删除/修改课程信息）
- ✅ 系统配置管理
- ✅ 数据统计和报表

### 教师功能
- ✅ 查看自己的课程列表
- ✅ 查看课程的选课学生名单
- ✅ 管理课程容量和时间
- ✅ 导出学生名单

### 学生功能
- ✅ 浏览可选课程列表
- ✅ 选课（支持高并发队列）
- ✅ 退课
- ✅ 查看个人课程表
- ✅ 课程时间冲突检测
- ✅ 学分统计

### 安全特性
- ✅ JWT Token 认证（refresh_token + access_token）
- ✅ 双因素认证 (2FA TOTP)
- ✅ bcrypt 密码加密
- ✅ protection_token 保护内部 API
- ✅ 角色权限控制

### 高级特性
- ✅ 消息队列处理高并发选课
- ✅ 课程容量实时计算
- ✅ 课程时间冲突检测
- ✅ 分布式节点支持（master/slave）
- ✅ 命令行用户管理工具

## 📁 项目结构

详见 [CODE_STRUCTURE.md](./CODE_STRUCTURE.md)

```
course-selection/
├── backend/                    # 后端代码
│   ├── course_data/           # 课程数据节点 (8001)
│   ├── login/                 # 登录认证节点 (8002)
│   ├── teacher/               # 教师功能节点 (8003)
│   ├── student/               # 学生功能节点 (8004)
│   ├── queue/                 # 队列管理节点 (8005)
│   ├── database.py            # 数据库模型
│   ├── utils.py               # 工具函数
│   ├── settings.py            # 配置管理
│   └── cli.py                 # 命令行工具
├── ui-of-course-selection/    # 前端代码
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 可复用组件
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── router/           # 路由配置
│   │   └── services/         # API 服务
│   └── vite.config.ts        # Vite 配置
├── manage-users.py            # 用户管理脚本
├── start-dev-cluster.sh       # 启动脚本
├── init_db.py                 # 数据库初始化
└── pyproject.toml             # Python 项目配置
```

## 📚 API 文档

### 认证流程

```
1. POST /api/login/v1
   ├─ 输入: username, password
   └─ 输出: refresh_token

2. POST /api/login/v2
   ├─ 输入: two_fa (2FA 验证码)
   ├─ Header: refresh_token
   └─ 输出: access_token

3. GET /api/login/get/user
   ├─ Header: access_token
   └─ 输出: 用户信息
```

### 主要 API 端点

详细 API 文档请访问各节点的 `/docs` 页面（Swagger UI）。

#### Course Data Node (8001)
- `POST /add/course` - 添加课程
- `GET /get/course/{course_id}` - 获取课程信息
- `POST /update/course` - 更新课程信息
- `POST /delete/course` - 删除课程
- `GET /get/all/courses` - 获取所有课程

#### Login Node (8002)
- `POST /v1` - 第一阶段登录
- `POST /v2` - 第二阶段登录（2FA）
- `GET /get/user` - 获取用户信息
- `POST /add/admin` - 添加管理员
- `POST /add/teacher` - 添加教师
- `POST /add/students` - 批量添加学生

#### Teacher Node (8003)
- `GET /get/courses` - 获取教师课程列表
- `GET /get/students/{course_id}` - 获取课程学生名单
- `POST /update/course` - 更新课程信息

#### Student Node (8004)
- `GET /get/courses` - 获取可选课程列表
- `POST /select/course` - 选课
- `POST /drop/course` - 退课
- `GET /get/schedule` - 获取个人课程表

#### Queue Node (8005)
- `POST /submit/task` - 提交选课任务
- `GET /get/task/{task_id}` - 查询任务状态
- `POST /cancel/task` - 取消任务

## 👥 用户管理

系统提供命令行工具进行用户管理：

### 添加用户

```bash
# 添加管理员
uv run python manage-users.py add-admin <username> <password>

# 添加教师
uv run python manage-users.py add-teacher <username> <password> <teacher_id>

# 添加学生
uv run python manage-users.py add-student <username> <password> <student_id>
```

### 查看用户

```bash
# 列出所有用户
uv run python manage-users.py list-users

# 按类型筛选
uv run python manage-users.py list-users --type admin
uv run python manage-users.py list-users --type teacher
uv run python manage-users.py list-users --type student

# 查看用户详情（包含 2FA 信息）
uv run python manage-users.py show-user <username>
```

### 更新用户

```bash
# 修改密码
uv run python manage-users.py update-user <username> --password <new_password>

# 修改显示名称
uv run python manage-users.py update-user <username> --name <new_name>
```

### 删除用户

```bash
uv run python manage-users.py delete-user <username>
```

更多详情请查看 `python manage-users.py --help`

## 🔧 开发指南

### 后端开发

```bash
# 运行单个服务
cd backend
uvicorn login.main:app --reload --port 8002

# 运行测试
pytest backend/test_backend.py

# 代码格式化
black backend/
ruff check backend/ --fix
```

### 前端开发

```bash
cd ui-of-course-selection

# 开发模式
bun dev

# 类型检查
bun run type-check

# 代码检查
bun run lint

# 代码格式化
bun run format

# 构建生产版本
bun run build

# 预览生产版本
bun run preview
```

### 数据库管理

```bash
# 重新初始化数据库（警告：会删除所有数据）
rm course_selection.db
python init_db.py

# 查看数据库
sqlite3 course_selection.db
```

## 📝 配置说明

### 后端配置 (`backend/settings.py`)

```python
# JWT 配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 数据库配置
DATABASE_URL = "sqlite:///./course_selection.db"

# 节点配置
COURSE_DATA_PORT = 8001
LOGIN_PORT = 8002
TEACHER_PORT = 8003
STUDENT_PORT = 8004
QUEUE_PORT = 8005
```

### 前端配置 (`ui-of-course-selection/vite.config.ts`)

```typescript
// API 代理配置
proxy: {
  '/api/course': { target: 'http://localhost:8001' },
  '/api/login': { target: 'http://localhost:8002' },
  '/api/teacher': { target: 'http://localhost:8003' },
  '/api/student': { target: 'http://localhost:8004' },
  '/api/queue': { target: 'http://localhost:8005' }
}
```

## 🐛 故障排除

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8001

# 停止所有后端服务
./start-dev-cluster.sh stop
```

### 数据库锁定

```bash
# 关闭所有访问数据库的进程
./start-dev-cluster.sh stop

# 删除锁文件
rm course_selection.db-journal
```

### 2FA 验证码错误

使用 CLI 工具查看当前有效的 2FA 验证码：

```bash
uv run python manage-users.py show-user <username>
```

## 📄 许可证

本项目仅供学习和研究使用。

## 👨‍💻 贡献者

Course Selection Team

## 📞 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。


# 代码结构文档

本文档详细描述了选课系统的代码组织结构、模块职责和关键文件说明。

## 📂 总体目录结构

```
course-selection/
├── backend/                          # 后端代码目录
│   ├── course_data/                 # 课程数据节点 (端口 8001)
│   │   ├── __init__.py
│   │   └── main.py                  # 课程数据 API 实现
│   ├── login/                       # 登录认证节点 (端口 8002)
│   │   ├── __init__.py
│   │   └── main.py                  # 认证和用户管理 API
│   ├── teacher/                     # 教师功能节点 (端口 8003)
│   │   ├── __init__.py
│   │   └── main.py                  # 教师功能 API
│   ├── student/                     # 学生功能节点 (端口 8004)
│   │   ├── __init__.py
│   │   └── main.py                  # 学生功能 API
│   ├── queue/                       # 队列管理节点 (端口 8005)
│   │   ├── __init__.py
│   │   └── main.py                  # 消息队列 API
│   ├── __main__.py                  # CLI 模块入口点
│   ├── cli.py                       # 命令行用户管理工具
│   ├── database.py                  # 数据库模型定义
│   ├── utils.py                     # 工具函数（密码、JWT）
│   ├── settings.py                  # 配置管理
│   ├── config.py                    # 配置加载
│   ├── default_config.py            # 默认配置
│   ├── server.py                    # 服务器启动脚本
│   ├── initialize.py                # 数据库初始化
│   ├── node_manager.py              # 节点管理（master/slave）
│   ├── test_backend.py              # 后端测试
│   ├── requirements.txt             # Python 依赖（已废弃，使用 pyproject.toml）
│   └── README.md                    # 后端文档
├── ui-of-course-selection/          # 前端代码目录
│   ├── src/
│   │   ├── views/                   # 页面组件
│   │   │   ├── Login.vue           # 登录页面
│   │   │   ├── NotFound.vue        # 404 页面
│   │   │   ├── admin/              # 管理员页面
│   │   │   ├── teacher/            # 教师页面
│   │   │   └── student/            # 学生页面
│   │   ├── components/              # 可复用组件
│   │   │   ├── teacher/            # 教师组件
│   │   │   └── student/            # 学生组件
│   │   ├── layouts/                 # 布局组件
│   │   │   ├── AdminLayout.vue     # 管理员布局
│   │   │   ├── TeacherLayout.vue   # 教师布局
│   │   │   └── StudentLayout.vue   # 学生布局
│   │   ├── stores/                  # Pinia 状态管理
│   │   │   ├── auth.ts             # 认证状态
│   │   │   ├── admin.ts            # 管理员状态
│   │   │   ├── teacher.ts          # 教师状态
│   │   │   ├── student.ts          # 学生状态
│   │   │   └── counter.ts          # 示例状态
│   │   ├── router/                  # 路由配置
│   │   │   └── index.ts            # 路由定义
│   │   ├── services/                # API 服务
│   │   │   └── api.ts              # API 封装
│   │   ├── __tests__/               # 测试文件
│   │   │   └── App.spec.ts
│   │   ├── App.vue                  # 根组件
│   │   └── main.ts                  # 入口文件
│   ├── public/                      # 静态资源
│   ├── env.d.ts                     # 环境变量类型定义
│   ├── vite.config.ts               # Vite 配置
│   ├── tsconfig.json                # TypeScript 配置
│   ├── package.json                 # 前端依赖
│   └── README.md                    # 前端文档
├── manage-users.py                  # 用户管理脚本（独立可执行）
├── start-dev-cluster.sh             # 开发集群启动脚本
├── init_db.py                       # 数据库初始化脚本
├── create_admins.py                 # 创建管理员脚本（已废弃）
├── pyproject.toml                   # Python 项目配置
├── uv.lock                          # uv 锁文件
├── plan.md                          # 项目计划文档
├── README.md                        # 项目主文档
├── CODE_STRUCTURE.md                # 本文档
└── course_selection.db              # SQLite 数据库文件
```

## 🗄️ 数据库结构

### 数据库模型 (`backend/database.py`)

#### 1. User 表（用户表）
```python
class User(Base):
    __tablename__ = "users"
    
    user_id: int                    # 主键，自增
    user_name: str                  # 用户名，唯一
    user_password_hash: str         # 密码哈希
    user_type: str                  # 用户类型：teacher/student
    two_factor_code: str            # 2FA 密钥（base32）
    created_at: datetime            # 创建时间
```

#### 2. Admin 表（管理员表）
```python
class Admin(Base):
    __tablename__ = "admins"
    
    admin_id: int                   # 主键，自增
    admin_name: str                 # 管理员用户名，唯一
    admin_password_hash: str        # 密码哈希
    created_at: datetime            # 创建时间
```

#### 3. Teacher 表（教师表）
```python
class Teacher(Base):
    __tablename__ = "teachers"
    
    teacher_id: int                 # 主键，教师工号
    teacher_name: str               # 教师姓名
```

#### 4. Student 表（学生表）
```python
class Student(Base):
    __tablename__ = "students"
    
    student_id: int                 # 主键，学号
    student_name: str               # 学生姓名
```

#### 5. Course 表（课程表）
```python
class Course(Base):
    __tablename__ = "courses"
    
    course_id: int                  # 主键，课程编号
    course_name: str                # 课程名称
    course_credit: int              # 学分
    course_type: str                # 课程类型
    course_teacher_id: int          # 教师 ID（外键）
    course_time_begin: int          # 开始时间
    course_time_end: int            # 结束时间
    course_location: str            # 上课地点
    course_capacity: int            # 课程容量
    course_selected: int            # 已选人数
    # course_left 由 API 实时计算
```

#### 6. QueueTask 表（队列任务表）
```python
class QueueTask(Base):
    __tablename__ = "queue_tasks"
    
    task_id: str                    # 主键，UUID
    student_id: int                 # 学生 ID
    course_id: int                  # 课程 ID
    task_type: str                  # 任务类型：select/drop
    status: str                     # 状态：pending/processing/completed/failed
    priority: int                   # 优先级
    created_at: datetime            # 创建时间
    updated_at: datetime            # 更新时间
    result: str                     # 执行结果（JSON）
```

## 🔌 后端节点详解

### 1. Course Data Node (8001)

**文件**: `backend/course_data/main.py`

**职责**: 课程数据的 CRUD 操作，所有 API 受 `protection_token` 保护

**主要 API**:
- `POST /add/course` - 添加课程
- `POST /add/student` - 添加学生
- `POST /add/teacher` - 添加教师
- `POST /delete/course` - 删除课程
- `POST /delete/student` - 删除学生
- `POST /delete/teacher` - 删除教师
- `GET /get/course/{course_id}` - 获取课程信息
- `GET /get/student/{student_id}` - 获取学生信息
- `GET /get/teacher/{teacher_id}` - 获取教师信息
- `POST /update/course` - 更新课程信息
- `POST /update/student` - 更新学生信息
- `POST /update/teacher` - 更新教师信息
- `GET /get/all/courses` - 获取所有课程
- `GET /get/all/students` - 获取所有学生

**关键特性**:
- 使用 `protection_token` 验证所有请求
- 自动计算 `course_left`（剩余容量）
- 支持批量操作

### 2. Login Node (8002)

**文件**: `backend/login/main.py`

**职责**: 用户认证、JWT token 管理、用户 CRUD

**主要 API**:
- `POST /v1` - 第一阶段登录（用户名密码）
- `POST /v2` - 第二阶段登录（2FA 验证）
- `GET /get/user` - 获取用户信息
- `POST /refresh` - 刷新 access_token
- `POST /logout` - 登出
- `POST /add/admin` - 添加管理员
- `POST /add/teacher` - 添加教师
- `POST /add/students` - 批量添加学生
- `POST /delete/admin` - 删除管理员
- `POST /delete/teacher` - 删除教师
- `POST /delete/student` - 删除学生
- `POST /update/admin` - 更新管理员
- `POST /update/teacher` - 更新教师
- `POST /update/student` - 更新学生

**认证流程**:
```
1. POST /v1 (username, password)
   └─> 返回 refresh_token

2. POST /v2 (two_fa, Header: refresh_token)
   └─> 返回 access_token

3. 后续请求 (Header: access_token)
   └─> 访问受保护资源
```

**关键特性**:
- 两阶段登录（密码 + 2FA）
- JWT token 管理（refresh_token 7天，access_token 30分钟）
- bcrypt 密码加密
- TOTP 2FA 验证

### 3. Teacher Node (8003)

**文件**: `backend/teacher/main.py`

**职责**: 教师功能（课程管理、学生管理）

**主要 API**:
- `GET /get/courses` - 获取教师的课程列表
- `GET /get/students/{course_id}` - 获取课程的学生名单
- `POST /add/course` - 添加课程
- `POST /update/course` - 更新课程信息
- `POST /delete/course` - 删除课程
- `GET /get/statistics` - 获取教学统计
- `POST /export/students` - 导出学生名单
- `GET /get/schedule` - 获取教师课程表

**关键特性**:
- 所有 API 需要 access_token 认证
- 自动验证教师权限
- 支持课程统计和导出

### 4. Student Node (8004)

**文件**: `backend/student/main.py`

**职责**: 学生功能（选课、退课、课程表）

**主要 API**:
- `GET /get/courses` - 获取可选课程列表
- `GET /get/my/courses` - 获取已选课程
- `POST /select/course` - 选课
- `POST /drop/course` - 退课
- `GET /get/schedule` - 获取个人课程表
- `GET /get/credits` - 获取学分统计
- `POST /check/conflict` - 检查课程冲突
- `GET /get/available/courses` - 获取有余量的课程
- `GET /search/courses` - 搜索课程

**关键特性**:
- 选课通过队列系统提交
- 自动检测课程时间冲突
- 实时计算学分
- 支持课程搜索和筛选

### 5. Queue Node (8005)

**文件**: `backend/queue/main.py`

**职责**: 高并发选课的消息队列管理

**主要 API**:
- `POST /submit/task` - 提交选课/退课任务
- `GET /get/task/{task_id}` - 查询任务状态
- `POST /cancel/task` - 取消任务
- `GET /get/my/tasks` - 获取我的任务列表
- `POST /retry/task` - 重试失败任务
- `GET /get/queue/status` - 获取队列状态
- `POST /set/priority` - 设置任务优先级
- `GET /get/statistics` - 获取队列统计

**关键特性**:
- 异步任务处理
- 优先级队列
- 任务状态追踪
- 自动重试机制

## 🎨 前端结构详解

### 页面组件 (`src/views/`)

#### Login.vue
- 登录页面
- 支持角色选择（开发模式）
- 两阶段登录流程
- 2FA 验证

#### Admin Pages (`src/views/admin/`)
- 用户管理
- 课程管理
- 系统配置
- 数据统计

#### Teacher Pages (`src/views/teacher/`)
- 课程列表
- 学生管理
- 课程统计
- 课程表

#### Student Pages (`src/views/student/`)
- 课程浏览
- 选课/退课
- 个人课程表
- 学分统计

### 状态管理 (`src/stores/`)

#### auth.ts
```typescript
// 认证状态
interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

// 主要方法
- login(username, password)
- verify2FA(code)
- logout()
- refreshAccessToken()
```

#### admin.ts / teacher.ts / student.ts
- 各角色的业务状态管理
- API 调用封装
- 数据缓存

### API 服务 (`src/services/api.ts`)

```typescript
// Axios 实例配置
const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器：添加 token
api.interceptors.request.use(config => {
  const token = useAuthStore().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理错误和 token 刷新
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，刷新或跳转登录
    }
    return Promise.reject(error)
  }
)
```

## 🔧 核心工具模块

### backend/utils.py

```python
# 密码加密和验证
def get_password_hash(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool

# JWT Token 管理
def create_access_token(data: dict) -> str
def create_refresh_token(data: dict) -> str
def verify_token(token: str) -> dict
def get_current_user(token: str) -> User
```

### backend/cli.py

命令行用户管理工具，提供以下功能：
- `add_admin()` - 添加管理员
- `add_teacher()` - 添加教师（自动生成 2FA）
- `add_student()` - 添加学生（自动生成 2FA）
- `update_user_password()` - 更新密码
- `update_user_name()` - 更新显示名称
- `delete_user()` - 删除用户
- `list_users()` - 列出用户
- `show_user()` - 显示用户详情

## 🚀 启动脚本

### start-dev-cluster.sh

```bash
# 启动所有服务
./start-dev-cluster.sh start

# 停止所有服务
./start-dev-cluster.sh stop

# 查看服务状态
./start-dev-cluster.sh status

# 重启所有服务
./start-dev-cluster.sh restart
```

**功能**:
- 按顺序启动 5 个后端节点
- 检查端口占用
- 日志输出到 `logs/` 目录
- 支持优雅关闭

## 📝 配置文件

### backend/settings.py

```python
# JWT 配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 数据库配置
DATABASE_URL = "sqlite:///./course_selection.db"

# 节点端口配置
COURSE_DATA_PORT = 8001
LOGIN_PORT = 8002
TEACHER_PORT = 8003
STUDENT_PORT = 8004
QUEUE_PORT = 8005

# 安全配置
PROTECTION_TOKEN = "random-protection-token"
INTERNAL_TOKEN = "random-internal-token"
```

### ui-of-course-selection/vite.config.ts

```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api/course': { target: 'http://localhost:8001', changeOrigin: true },
      '/api/login': { target: 'http://localhost:8002', changeOrigin: true },
      '/api/teacher': { target: 'http://localhost:8003', changeOrigin: true },
      '/api/student': { target: 'http://localhost:8004', changeOrigin: true },
      '/api/queue': { target: 'http://localhost:8005', changeOrigin: true }
    }
  }
})
```

## 🔐 安全机制

### 1. 密码安全
- bcrypt 加密（12 rounds）
- 自动处理 72 字节限制
- 密码哈希存储

### 2. Token 安全
- JWT 签名验证
- Token 过期时间控制
- Refresh token 轮换

### 3. API 保护
- `protection_token` 保护内部 API
- `access_token` 保护用户 API
- 角色权限验证

### 4. 2FA 认证
- TOTP 算法（30秒有效期）
- Base32 密钥存储
- 防暴力破解

## 📊 数据流图

```
用户登录流程:
User → Login.vue → POST /api/login/v1 → Login Node
                                        ↓
                                   验证密码
                                        ↓
                                 返回 refresh_token
                                        ↓
User ← Login.vue ← refresh_token ← Login Node

User → 输入 2FA → POST /api/login/v2 → Login Node
                                        ↓
                                   验证 2FA
                                        ↓
                                 返回 access_token
                                        ↓
User ← 跳转主页 ← access_token ← Login Node

选课流程:
Student → 选择课程 → POST /api/student/select/course → Student Node
                                                        ↓
                                                  提交到队列
                                                        ↓
                                                   Queue Node
                                                        ↓
                                                  异步处理任务
                                                        ↓
                                              Course Data Node
                                                        ↓
                                                  更新课程数据
                                                        ↓
Student ← 查询结果 ← GET /api/queue/get/task ← Queue Node
```

## 🧪 测试

### 后端测试
```bash
# 运行所有测试
pytest backend/test_backend.py

# 运行特定测试
pytest backend/test_backend.py::test_login

# 查看覆盖率
pytest --cov=backend backend/test_backend.py
```

### 前端测试
```bash
cd ui-of-course-selection

# 运行单元测试
bun run test:unit

# 查看覆盖率
bun run test:unit --coverage
```

## 📚 扩展阅读

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue.js 官方文档](https://vuejs.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [JWT 介绍](https://jwt.io/)
- [TOTP 算法](https://tools.ietf.org/html/rfc6238)


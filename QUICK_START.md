# 快速开始指南

本指南将帮助你在 5 分钟内启动并运行选课系统。

## 📋 前置要求

确保你已安装以下工具：

- ✅ Python 3.9+ 
- ✅ Node.js 20.19+ 或 22.12+
- ✅ uv (Python 包管理器)
- ✅ Bun (JavaScript 包管理器)

### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 安装 Bun

```bash
# macOS/Linux
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"
```

## 🚀 5 分钟快速启动

### 步骤 1: 安装依赖 (1 分钟)

```bash
# 后端依赖
uv sync

# 前端依赖
cd ui-of-course-selection
bun install
cd ..
```

### 步骤 2: 初始化数据库 (30 秒)

```bash
# 创建数据库表结构
python init_db.py

# 创建测试管理员账户
uv run python manage-users.py add-admin admin password123

# 创建测试教师账户
uv run python manage-users.py add-teacher teacher pass123 1001

# 创建测试学生账户
uv run python manage-users.py add-student student pass123 2001
```

### 步骤 3: 启动后端服务 (30 秒)

```bash
# 启动所有 5 个后端节点
./start-dev-cluster.sh start

# 等待几秒钟让服务完全启动
sleep 3

# 验证服务状态
./start-dev-cluster.sh status
```

你应该看到类似这样的输出：
```
✅ Course Data Node (8001) - Running
✅ Login Node (8002) - Running
✅ Teacher Node (8003) - Running
✅ Student Node (8004) - Running
✅ Queue Node (8005) - Running
```

### 步骤 4: 启动前端 (30 秒)

打开新的终端窗口：

```bash
cd ui-of-course-selection
bun dev
```

你应该看到：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 步骤 5: 访问系统 (1 分钟)

1. 打开浏览器访问: http://localhost:5173

2. 使用测试账户登录：

   **管理员账户**:
   - 用户名: `admin`
   - 密码: `password123`
   - 2FA: 使用 CLI 查看当前验证码
     ```bash
     uv run python manage-users.py show-user admin
     ```

   **教师账户**:
   - 用户名: `teacher`
   - 密码: `pass123`
   - 2FA: 使用 CLI 查看当前验证码
     ```bash
     uv run python manage-users.py show-user teacher
     ```

   **学生账户**:
   - 用户名: `student`
   - 密码: `pass123`
   - 2FA: 使用 CLI 查看当前验证码
     ```bash
     uv run python manage-users.py show-user student
     ```

3. 开发模式下，登录页面会显示角色选择器，可以直接选择角色登录

## 🎯 下一步

### 添加更多用户

```bash
# 添加教师
uv run python manage-users.py add-teacher zhang_san pass123 1002
uv run python manage-users.py add-teacher li_si pass123 1003

# 添加学生
uv run python manage-users.py add-student stu001 pass123 2002
uv run python manage-users.py add-student stu002 pass123 2003
uv run python manage-users.py add-student stu003 pass123 2004

# 查看所有用户
uv run python manage-users.py list-users
```

### 添加课程数据

使用管理员账户登录后，在管理界面添加课程，或者通过 API：

```bash
# 使用 curl 添加课程（需要先获取 access_token）
curl -X POST http://localhost:8001/add/course \
  -H "Content-Type: application/json" \
  -H "protection_token: your-protection-token" \
  -d '{
    "course_id": 1001,
    "course_name": "数据结构",
    "course_credit": 4,
    "course_type": "必修",
    "course_teacher_id": 1001,
    "course_time_begin": 1,
    "course_time_end": 3,
    "course_location": "教学楼A101",
    "course_capacity": 50,
    "course_selected": 0
  }'
```

### 查看 API 文档

访问各节点的 Swagger UI 文档：

- Course Data: http://localhost:8001/docs
- Login: http://localhost:8002/docs
- Teacher: http://localhost:8003/docs
- Student: http://localhost:8004/docs
- Queue: http://localhost:8005/docs

## 🛑 停止服务

### 停止后端服务

```bash
./start-dev-cluster.sh stop
```

### 停止前端服务

在前端终端按 `Ctrl + C`

## 🔧 常见问题

### Q1: 端口被占用怎么办？

```bash
# 查找占用端口的进程
lsof -i :8001
lsof -i :8002
# ... 等等

# 杀死进程
kill -9 <PID>

# 或者直接停止所有服务
./start-dev-cluster.sh stop
```

### Q2: 数据库锁定错误

```bash
# 停止所有服务
./start-dev-cluster.sh stop

# 删除锁文件
rm -f course_selection.db-journal

# 重新启动
./start-dev-cluster.sh start
```

### Q3: 2FA 验证码一直错误

2FA 验证码每 30 秒更新一次，使用 CLI 工具查看当前有效的验证码：

```bash
uv run python manage-users.py show-user <username>
```

输出会显示当前有效的 2FA 验证码。

### Q4: 忘记密码怎么办？

使用 CLI 工具重置密码：

```bash
uv run python manage-users.py update-user <username> --password <new_password>
```

### Q5: 如何重置整个系统？

```bash
# 停止所有服务
./start-dev-cluster.sh stop

# 删除数据库
rm course_selection.db

# 重新初始化
python init_db.py

# 重新创建用户
uv run python manage-users.py add-admin admin password123
# ... 添加其他用户

# 重新启动服务
./start-dev-cluster.sh start
```

## 📚 更多资源

- [完整文档](./README.md) - 系统架构和功能详解
- [代码结构](./CODE_STRUCTURE.md) - 详细的代码组织说明
- [项目计划](./plan.md) - 原始需求和设计文档

## 💡 开发技巧

### 实时查看日志

```bash
# 查看所有服务日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/course_data.log
tail -f logs/login.log
```

### 热重载开发

后端和前端都支持热重载：

- **后端**: 修改代码后自动重启（uvicorn --reload）
- **前端**: 修改代码后自动刷新（Vite HMR）

### 调试模式

```bash
# 后端调试模式（显示详细日志）
export DEBUG=1
./start-dev-cluster.sh start

# 前端调试模式（已默认开启）
cd ui-of-course-selection
bun dev
```

### 数据库查看

```bash
# 使用 SQLite 命令行工具
sqlite3 course_selection.db

# 查看所有表
.tables

# 查看表结构
.schema users

# 查询数据
SELECT * FROM users;

# 退出
.quit
```

## 🎉 完成！

现在你已经成功启动了选课系统！

- 🌐 前端: http://localhost:5173
- 📚 API 文档: http://localhost:8001/docs (以及其他节点)
- 💻 命令行工具: `uv run python manage-users.py --help`

祝你使用愉快！如有问题，请查看完整文档或提交 Issue。


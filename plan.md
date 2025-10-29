# 1 综述

这是一个 python fastapi + vue 前端的分离式项目
fastapi 后端分为多个部分，各自独立部署

# 2 fastapi 后端职责分配

## 2.1 选课数据节点

### 2.1.1 职责

负责存储 & 接受 选课数据的读写（不应该裸露在外，要有随机 token 保护）

### 2.1.2 配置

目前使用 sqlite 作为后端
可选配置多个节点（需要配置其他节点 ip，配置后投票决定作为写的主节点和作为读取的从节点）

### 2.1.3 表结构

存储课程的

couse :{
course_id: int,
course_name: str,
course_credit: int,
course_type: str,
course_teacher_id: int, // 指向老师的 id
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
course_selected: int,
//course_left 将由返回值实时计算
}

存储学生选课数据的

student :{
student_id: int,
student_name: str,
student_course: list[int],
}

存储老师上课数据的

teacher :{
teacher_id: int,
teacher_name: str,
teacher_course: list[int],
}

### 2.1.4 api

### 2.1.4.1 `/add/course` : 添加课程

body:{
course_id: int,
course_name: str,
course_credit: int,
course_type: str,
course_teacher_id: int, // 指向老师的 id
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
course_selected: int,
//course_left 将由返回值实时计算
}
//自动先更新对应老师，找不到时返回 404

### 2.1.4.2 `/add/student` : 添加学生

body:{
student_id: int,
student_name: str,
}
// 禁止在添加学生的时候添加课程，防止课程错乱

### 2.1.4.3 `/add/teacher` : 添加老师

body:{
teacher_id: int,
teacher_name: str,
}

### 2.1.4.4 `/delete/course` : 删除课程

body:{
course_id: int,
}

### 2.1.4.5 `/delete/student` : 删除学生

body:{
student_id: int,
}

### 2.1.4.6 `/delete/teacher` : 删除老师

body:{
teacher_id: int,
}

### 2.1.4.7 `/update/course` : 更新课程

body:{
course_id: int,
course_name: str,
course_credit: int,
course_type: str,
course_teacher_id: int, // 指向老师的 id
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
course_selected: int,
//course_left 将由返回值实时计算
}

### 2.1.4.8 `/update/student` : 更新学生

body:{
student_id: int,
student_name: str,
}

### 2.1.4.9 `/update/teacher` : 更新老师

body:{
teacher_id: int,
teacher_name: str,
}

### 2.1.4.10 `/select/course` : 选课

body:{
student_id: int,
course_id: int,
}

### 2.1.4.11 `/deselect/course` : 取消选课

body:{
student_id: int,
course_id: int,
}

### 2.1.4.12 `/get/course` : 获取课程信息

body:{
course_id: int,
}

### 2.1.4.13 `/master` : 获取主节点信息

body:{}

retrun {
ip: str,
port: int,
}

### 2.1.4.14 `/slave` : 获取从节点信息

body:{}

retrun {
map<int,int> [ip,port]
}

## 2.2 登陆节点

### 2.2.1 职责

负责用户登陆，签发 token

### 2.2.2 配置

目前使用 sqlite 作为后端
必须配置数据库节点 ip (创建用户时同步处理)
可选配置多个节点（需要配置其他节点 ip，配置后投票决定作为写的主节点和作为读取的从节点）

### 2.2.3 表结构

存储用户信息的

user :{
user_id: int,
user_name: str,
user_password: str,
user_type: str,
2fa_code: str,
}

存储管理员信息的

admin :{
admin_id: int,
admin_name: str,
admin_password: str,
}

存储老师信息的

teacher :{
teacher_id: int,
teacher_name: str,
teacher_password: str,
}

### 2.2.4 api

### 2.2.4.1 `/login/v1` : 登陆第一阶段

body:{
user_name: str,
user_password: str,
}

retrun {
refresh_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.2 `/login/v2` : 登陆第二阶段

head :{
refresh_token: str,
}
body:{
2fa: number,
}

retrun {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.3 `/logout` : 登出

head:{
access_token: jwt
}

或
body:{
refresh_token: str
}

### 2.2.4.4 `/register/v1` : 注册账号第一阶段

body:{
user_name: str,
user_password: str,
user_type: str,
}

return {
2fa_code: str,
refresh_token: str, // jwt
expire: int, // 迆期时间
}

### 2.2.4.5 `/register/v2` : 注册第二阶段 | 索取新 2fa

head:{
refresh_token: str,
}
body:{
2fa: number,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.6 `/change/password` : 修改密码

head:{
access_token: str,
}
body:{

old_password: str,
new_password: str,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.7 `/change/2fa` : 修改 2fa

head:{
refresh_token: str,
}
body:{
one_time_credit: number,
new_2fa: number,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.8 `/change/name` : 修改用户名

head:{
access_token: str,
}
body:{
new_name: str,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.9 `/master` : 获取主节点信息

body:{}

retrun {
ip: str,
port: int,
}

### 2.2.4.10 `/slave` : 获取从节点信息

body:{}

retrun {
map<int,int> [ip,port]
}

### 2.2.4.11 `/get/user` : 获取用户信息

body:{
access_token: str,
}

return {
user_id: int,
user_name: str,
user_type: str,
}

### 2.2.4.12 `/login/admin` : 管理员登陆

body:{
admin_name: str,
admin_password: str,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.13 `/add/admin` : 管理员注册

head:{
access_token: str,
}

body:{
admin_name: str,
admin_password: str,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.14 `/delete/admin` : 管理员删除

head:{
access_token: str,
}

body:{
admin_name: str,
}

return {
success: bool,
}

### 2.2.4.15 `/get/admin` : 管理员获取

head:{
access_token: str,
}
body:{
admin_name: str,
}

return {
admin_id: int,
admin_name: str,
}

### 2.2.4.16 `/get/admin/all` : 管理员获取所有

head:{
access_token: str,
}
body:{
}

return {
list<admin_id, admin_name>,
}

### 2.2.4.17 `/add/teacher` : 添加老师

head:{
access_token: str,
}
body:{
teacher_name: str,
teacher_password: str,
}

return {
access_token: str, // jwt
expire: int, // 过期时间
}

### 2.2.4.18 `/delete/teacher` : 删除老师

head:{
access_token: str,
}
body:{
teacher_name: str,
}

return {
success: bool,
}

### 2.2.4.19 `/get/teacher` : 获取老师信息

head:{
access_token: str,
}
body:{
teacher_name: str,
}

return {
teacher_id: int,
teacher_name: str,
}

### 2.2.4.20 `/get/teacher/all` : 获取所有老师信息

head:{
access_token: str,
}
body:{
}

return {
list<teacher_id, teacher_name>,
}

### 2.2.4.17 `/add/students` : 添加学生（批量导入）

head:{
access_token: str,
}
body:{
students: list<{
    stdent_id: int,
    student_name: str,
    student_password: str,
    student_type: str,
}>,
}

return {
success: bool,
}

### 2.2.4.18 `/delete/students` : 删除学生（批量导入）

head:{
access_token: str,
}
body:{
students: list<student_name>,
}

return {
success: bool,
}

### 2.2.4.19 `/get/students` : 获取学生信息（批量导入）

head:{
access_token: str,
}
body:{
students: list<student_name>,
}

return {
list<student_id, student_name>,
}

### 2.2.4.20 `/get/students/all` : 获取所有学生信息

head:{
access_token: str,
}
body:{
}

return {
list<student_id, student_name>,
}

## 2.3 教师处理节点

### 2.3.1 职责

负责处理教师相关的业务逻辑，包括课程管理、学生管理、成绩查询等功能。需要验证教师身份（通过登陆节点签发的 access_token）

### 2.3.2 配置

必须配置登陆节点 ip (用于验证 token)
必须配置选课数据节点 ip (用于读写课程数据)
可选配置多个节点（需要配置其他节点 ip，实现负载均衡）

### 2.3.3 依赖服务

- 登陆节点：验证教师 token
- 选课数据节点：读写课程和学生数据

### 2.3.4 api

#### 2.3.4.1 `/teacher/courses` : 获取教师所有课程

head:{
access_token: str,
}
body:{}

return {
courses: list<{
    course_id: int,
    course_name: str,
    course_credit: int,
    course_type: str,
    course_time_begin: int,
    course_time_end: int,
    course_location: str,
    course_capacity: int,
    course_selected: int,
    course_left: int,
}>,
}

#### 2.3.4.2 `/teacher/course/detail` : 获取课程详细信息

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
course_id: int,
course_name: str,
course_credit: int,
course_type: str,
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
course_selected: int,
course_left: int,
students: list<{
    student_id: int,
    student_name: str,
}>,
}

#### 2.3.4.3 `/teacher/course/students` : 获取课程学生列表

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
students: list<{
    student_id: int,
    student_name: str,
}>,
}

#### 2.3.4.4 `/teacher/course/update` : 更新课程信息

head:{
access_token: str,
}
body:{
course_id: int,
course_name: str (optional),
course_credit: int (optional),
course_type: str (optional),
course_time_begin: int (optional),
course_time_end: int (optional),
course_location: str (optional),
course_capacity: int (optional),
}

return {
success: bool,
message: str,
}

#### 2.3.4.5 `/teacher/course/create` : 创建新课程

head:{
access_token: str,
}
body:{
course_name: str,
course_credit: int,
course_type: str,
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
}

return {
success: bool,
course_id: int,
message: str,
}

#### 2.3.4.6 `/teacher/course/delete` : 删除课程

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
success: bool,
message: str,
}

#### 2.3.4.7 `/teacher/student/remove` : 从课程移除学生

head:{
access_token: str,
}
body:{
course_id: int,
student_id: int,
}

return {
success: bool,
message: str,
}

#### 2.3.4.8 `/teacher/stats` : 获取教师统计信息

head:{
access_token: str,
}
body:{}

return {
total_courses: int,
total_students: int,
courses_by_type: map<str, int>,
}

## 2.4 学生处理节点

### 2.4.1 职责

负责处理学生相关的业务逻辑，包括选课、退课、查看课程表、查看已选课程等功能。需要验证学生身份（通过登陆节点签发的 access_token）

### 2.4.2 配置

必须配置登陆节点 ip (用于验证 token)
必须配置选课数据节点 ip (用于读写选课数据)
必须配置队列缓冲节点 ip (用于处理高并发选课请求)
可选配置多个节点（需要配置其他节点 ip，实现负载均衡）

### 2.4.3 依赖服务

- 登陆节点：验证学生 token
- 选课数据节点：读写课程和学生数据
- 队列缓冲节点：处理选课/退课请求

### 2.4.4 api

#### 2.4.4.1 `/student/courses/available` : 获取可选课程列表

head:{
access_token: str,
}
body:{
course_type: str (optional),
teacher_name: str (optional),
page: int (optional, default: 1),
page_size: int (optional, default: 20),
}

return {
courses: list<{
    course_id: int,
    course_name: str,
    course_credit: int,
    course_type: str,
    teacher_name: str,
    course_time_begin: int,
    course_time_end: int,
    course_location: str,
    course_capacity: int,
    course_selected: int,
    course_left: int,
}>,
total: int,
page: int,
page_size: int,
}

#### 2.4.4.2 `/student/courses/selected` : 获取已选课程列表

head:{
access_token: str,
}
body:{}

return {
courses: list<{
    course_id: int,
    course_name: str,
    course_credit: int,
    course_type: str,
    teacher_name: str,
    course_time_begin: int,
    course_time_end: int,
    course_location: str,
}>,
total_credit: int,
}

#### 2.4.4.3 `/student/course/select` : 选课（提交到队列）

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
success: bool,
message: str,
queue_id: str, // 队列任务 id
estimated_time: int, // 预计处理时间（秒）
}

#### 2.4.4.4 `/student/course/deselect` : 退课（提交到队列）

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
success: bool,
message: str,
queue_id: str, // 队列任务 id
}

#### 2.4.4.5 `/student/course/detail` : 获取课程详细信息

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
course_id: int,
course_name: str,
course_credit: int,
course_type: str,
teacher_name: str,
course_time_begin: int,
course_time_end: int,
course_location: str,
course_capacity: int,
course_selected: int,
course_left: int,
is_selected: bool, // 当前学生是否已选
}

#### 2.4.4.6 `/student/schedule` : 获取课程表

head:{
access_token: str,
}
body:{
week: int (optional), // 周数，默认当前周
}

return {
schedule: map<int, list<{
    course_id: int,
    course_name: str,
    teacher_name: str,
    course_time_begin: int,
    course_time_end: int,
    course_location: str,
}>>, // key: 星期几 (1-7)
}

#### 2.4.4.7 `/student/stats` : 获取学生选课统计

head:{
access_token: str,
}
body:{}

return {
total_courses: int,
total_credit: int,
courses_by_type: map<str, int>,
credit_by_type: map<str, int>,
}

#### 2.4.4.8 `/student/queue/status` : 查询队列任务状态

head:{
access_token: str,
}
body:{
queue_id: str,
}

return {
status: str, // pending, processing, completed, failed
message: str,
created_at: int,
completed_at: int (optional),
}

#### 2.4.4.9 `/student/course/check` : 检查选课冲突

head:{
access_token: str,
}
body:{
course_id: int,
}

return {
can_select: bool,
conflicts: list<{
    type: str, // time_conflict, credit_limit, already_selected, course_full
    message: str,
    course_id: int (optional),
    course_name: str (optional),
}>,
}

## 2.5 队列缓冲节点

### 2.5.1 职责

负责处理高并发的选课/退课请求，使用消息队列缓冲请求，保证数据一致性和系统稳定性。防止选课高峰期直接冲击数据库。

### 2.5.2 配置

必须配置选课数据节点 ip (用于执行实际的选课/退课操作)
必须配置 Redis/RabbitMQ 等消息队列服务
可选配置多个消费者进程数量（根据负载动态调整）
可选配置请求优先级策略
可选配置限流策略（防止单用户刷接口）

### 2.5.3 技术栈

- 消息队列：Redis (使用 Redis List/Stream) 或 RabbitMQ
- 缓存：Redis (用于存储任务状态和限流信息)
- 任务持久化：SQLite/PostgreSQL (记录任务历史)

### 2.5.4 表结构

存储队列任务的

queue_task :{
task_id: str, // uuid
student_id: int,
course_id: int,
task_type: str, // select, deselect
status: str, // pending, processing, completed, failed
priority: int, // 优先级，默认 0
created_at: int,
started_at: int (optional),
completed_at: int (optional),
error_message: str (optional),
retry_count: int,
}

### 2.5.5 api

#### 2.5.5.1 `/queue/submit` : 提交任务到队列

head:{
internal_token: str, // 内部服务认证 token
}
body:{
student_id: int,
course_id: int,
task_type: str, // select, deselect
priority: int (optional, default: 0),
}

return {
success: bool,
task_id: str,
position: int, // 在队列中的位置
estimated_time: int, // 预计等待时间（秒）
}

#### 2.5.5.2 `/queue/status` : 查询任务状态

head:{
internal_token: str,
}
body:{
task_id: str,
}

return {
task_id: str,
status: str,
message: str,
created_at: int,
started_at: int (optional),
completed_at: int (optional),
position: int (optional), // 如果还在队列中
}

#### 2.5.5.3 `/queue/cancel` : 取消任务

head:{
internal_token: str,
}
body:{
task_id: str,
student_id: int, // 用于验证权限
}

return {
success: bool,
message: str,
}

#### 2.5.5.4 `/queue/stats` : 获取队列统计信息

head:{
internal_token: str,
}
body:{}

return {
pending_tasks: int,
processing_tasks: int,
completed_tasks_today: int,
failed_tasks_today: int,
average_processing_time: float, // 秒
queue_length: int,
}

#### 2.5.5.5 `/queue/student/tasks` : 获取学生的所有任务

head:{
internal_token: str,
}
body:{
student_id: int,
status: str (optional), // 筛选特定状态
limit: int (optional, default: 10),
}

return {
tasks: list<{
    task_id: str,
    course_id: int,
    task_type: str,
    status: str,
    created_at: int,
    completed_at: int (optional),
}>,
}

#### 2.5.5.6 `/queue/health` : 健康检查

body:{}

return {
status: str, // healthy, degraded, unhealthy
queue_status: str,
consumer_count: int,
redis_connected: bool,
database_connected: bool,
last_processed_at: int,
}

#### 2.5.5.7 `/queue/priority/update` : 更新任务优先级（管理员）

head:{
internal_token: str,
admin_token: str,
}
body:{
task_id: str,
priority: int,
}

return {
success: bool,
message: str,
}

#### 2.5.5.8 `/queue/retry` : 重试失败的任务

head:{
internal_token: str,
}
body:{
task_id: str,
}

return {
success: bool,
message: str,
new_task_id: str (optional),
}

### 2.5.6 队列处理逻辑

1. **任务接收**：从学生处理节点接收选课/退课请求
2. **限流检查**：检查学生是否超过频率限制（如：每分钟最多 10 次请求）
3. **任务入队**：将任务加入 Redis 队列，分配唯一 task_id
4. **任务消费**：多个消费者进程并发处理队列任务
5. **执行操作**：调用选课数据节点的 API 执行实际的选课/退课
6. **结果更新**：更新任务状态，通知结果
7. **失败重试**：失败任务自动重试（最多 3 次）
8. **任务清理**：定期清理完成的历史任务（保留 7 天）

### 2.5.7 限流策略

- 单用户限流：每分钟最多 10 次请求，超过返回 429 错误
- 全局限流：队列长度超过 10000 时，拒绝新任务
- 自适应限流：根据数据节点响应时间动态调整消费速度

### 2.5.8 优先级策略

- 默认优先级：0
- 退课优先级：10（优先处理退课，释放名额）
- VIP 用户优先级：5（可选功能）
- 超时补偿优先级：20（等待超过 5 分钟的任务自动提升优先级）



# Database Architecture Refactoring Guide

## Overview

This guide explains the database architecture refactoring that separates authentication data from course data into two distinct databases.

## Problem Statement

The original error was:
```
{"detail":"Failed to create student in data node: {\"detail\":\"Invalid internal token\"}"}
```

This occurred because:
1. The Internal-Token header was sent with "Bearer " prefix (auth_node line 166)
2. Authentication data was incorrectly stored in course_data.db instead of auth_data.db

## Architecture Changes

### Before (Old Architecture)
- **auth_data.db**: Only Admin, RefreshToken, RegistrationCode, ResetCode
- **course_data.db**: Student and Teacher WITH auth fields (username, password_hash, totp_secret)

### After (New Architecture)
- **auth_data.db**: ALL authentication data
  - Student (username, password_hash, totp_secret, is_active)
  - Teacher (username, password_hash, is_active)
  - Admin, RefreshToken, RegistrationCode, ResetCode
  
- **course_data.db**: ALL course-related data
  - StudentCourseData (student_name, student_courses, student_tags)
  - TeacherCourseData (teacher_name, teacher_courses)
  - Course

## Migration Steps

### Step 1: Backup Databases
```bash
cp auth_data.db auth_data.db.backup
cp course_data.db course_data.db.backup
```

### Step 2: Run Migration Script
```bash
python -m backend.common.migrate_auth_data
```

### Step 3: Restart Services
```bash
pkill -f "python.*backend"
python -m backend.data_node.main &
python -m backend.auth_node.main &
python -m backend.queue_node.main &
python -m backend.student_node.main &
python -m backend.teacher_node.main &
```

### Step 4: Test Registration
```bash
curl -X POST http://localhost:8002/register/v1 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "user_type": "student",
    "registration_code": "YOUR_CODE"
  }'
```

## Key Code Changes

### 1. Models (backend/common/models.py)
- Split Student into: Student (AuthBase) + StudentCourseData (DataBase)
- Split Teacher into: Teacher (AuthBase) + TeacherCourseData (DataBase)

### 2. Auth Node (backend/auth_node/main.py)
- Fixed: Removed "Bearer " prefix from Internal-Token header
- Changed: Creates users in auth_data.db, then calls data_node for course data

### 3. Data Node (backend/data_node/main.py)
- Removed: `/add/student-with-auth`, `/add/teacher-with-auth`, `/data/users`
- Updated: All endpoints use StudentCourseData/TeacherCourseData

### 4. Auth Helpers (backend/common/auth_helpers.py)
- Changed: Queries auth_data.db directly instead of calling data_node API

## Files Modified
- backend/common/models.py
- backend/common/__init__.py
- backend/auth_node/main.py
- backend/data_node/main.py
- backend/common/auth_helpers.py
- backend/common/db_edit.py

## Files Created
- backend/common/migrate_auth_data.py
- DATABASE_REFACTORING_GUIDE.md


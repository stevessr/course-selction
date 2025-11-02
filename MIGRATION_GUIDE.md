# Database Migration Guide

## Overview

This guide helps you migrate from the old schema (with a single `users` table) to the new schema (with separate `students`, `teachers`, and `admins` tables).

## Why This Migration?

The old schema incorrectly mixed all user types into a single `users` table. The new schema properly separates:
- **Students** → `students` table (with 2FA support)
- **Teachers** → `teachers` table (no 2FA)
- **Admins** → `admins` table (no 2FA)

## Migration Steps

### 1. Backup Your Database

```bash
# Backup all databases
cp backend/data_node/course_data.db backend/data_node/course_data.db.backup
cp backend/auth_node/auth_data.db backend/auth_node/auth_data.db.backup
cp backend/queue_node/queue_data.db backend/queue_node/queue_data.db.backup
```

### 2. Add New Columns to Existing Tables

Run these SQL commands on your `course_data.db`:

```sql
-- Add auth fields to students table
ALTER TABLE students ADD COLUMN username VARCHAR(100) UNIQUE;
ALTER TABLE students ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE students ADD COLUMN totp_secret VARCHAR(32);
ALTER TABLE students ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Add auth fields to teachers table  
ALTER TABLE teachers ADD COLUMN username VARCHAR(100) UNIQUE;
ALTER TABLE teachers ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE teachers ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
```

### 3. Migrate Data from users Table

Run this Python script to migrate user data:

```python
import sqlite3
from pathlib import Path

# Connect to databases
auth_db = sqlite3.connect('backend/auth_node/auth_data.db')
data_db = sqlite3.connect('backend/data_node/course_data.db')

auth_cursor = auth_db.cursor()
data_cursor = data_db.cursor()

# Get all users from old users table
auth_cursor.execute("SELECT user_id, username, password_hash, user_type, totp_secret, is_active FROM users")
users = auth_cursor.fetchall()

for user_id, username, password_hash, user_type, totp_secret, is_active in users:
    if user_type == "student":
        # Find matching student by name (assuming username == student_name initially)
        data_cursor.execute(
            "SELECT student_id FROM students WHERE student_name = ?",
            (username,)
        )
        result = data_cursor.fetchone()
        
        if result:
            student_id = result[0]
            # Update student with auth fields
            data_cursor.execute(
                """UPDATE students 
                   SET username = ?, password_hash = ?, totp_secret = ?, is_active = ?
                   WHERE student_id = ?""",
                (username, password_hash, totp_secret, is_active, student_id)
            )
            print(f"Migrated student: {username}")
        else:
            print(f"Warning: No matching student found for {username}")
    
    elif user_type == "teacher":
        # Find matching teacher by name
        data_cursor.execute(
            "SELECT teacher_id FROM teachers WHERE teacher_name = ?",
            (username,)
        )
        result = data_cursor.fetchone()
        
        if result:
            teacher_id = result[0]
            # Update teacher with auth fields (no totp_secret for teachers)
            data_cursor.execute(
                """UPDATE teachers 
                   SET username = ?, password_hash = ?, is_active = ?
                   WHERE teacher_id = ?""",
                (username, password_hash, is_active, teacher_id)
            )
            print(f"Migrated teacher: {username}")
        else:
            print(f"Warning: No matching teacher found for {username}")
    
    # Admins are already in separate table, no migration needed

# Commit changes
data_db.commit()

# Update refresh_tokens to use correct user_ids
# Note: You may need to regenerate tokens if IDs changed

data_db.close()
auth_db.close()

print("Migration complete!")
```

### 4. Drop Old users Table

After verifying the migration was successful:

```sql
-- On auth_data.db
DROP TABLE IF EXISTS users;
```

### 5. Restart Services

```bash
./start_backend.sh
```

## Verification

Check that everything works:

```bash
# Test student login
curl -X POST http://localhost:8002/login/v1 \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "password123"}'

# Test teacher login  
curl -X POST http://localhost:8002/login/v1 \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher1", "password": "password123"}'

# Test admin login
curl -X POST http://localhost:8002/login/admin \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## Rollback

If something goes wrong:

```bash
# Restore backups
cp backend/data_node/course_data.db.backup backend/data_node/course_data.db
cp backend/auth_node/auth_data.db.backup backend/auth_node/auth_data.db
cp backend/queue_node/queue_data.db.backup backend/queue_node/queue_data.db

# Restart with old code
git checkout <previous_commit>
./start_backend.sh
```

## Fresh Installation

If you're starting fresh (no existing data), you don't need to migrate. Just:

1. Delete old database files
2. Restart services - tables will be created automatically
3. Create initial admin:
   - Will be created automatically on first run
   - Username: `admin`
   - Password: Set via `ADMIN_PASSWORD` env var or defaults to `admin123`

## Notes

- **Students**: Have username, password, totp_secret (2FA), and is_active
- **Teachers**: Have username, password, and is_active (NO 2FA)
- **Admins**: Separate table, unchanged from before
- **Refresh Tokens**: May need regeneration if user_ids changed during migration
- **Registration Codes**: Will be deleted after use (immediate cleanup)
- **Revoked Tokens**: Will be automatically cleaned up

## Support

If you encounter issues:
1. Check logs: `tail -f backend/*_node/logs/*.log`
2. Verify database schema: `sqlite3 <db_file> ".schema"`
3. Check for constraint violations
4. Ensure all services are running

## Security Notes

After migration:
- Change the default admin password
- Generate new registration codes for new users
- Review and revoke old refresh tokens if needed
- Test 2FA for students
- Verify teachers can login without 2FA

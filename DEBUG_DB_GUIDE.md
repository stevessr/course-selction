# Debug Panel and Database Editor Guide

This guide covers two powerful development and debugging tools:
1. **Debug Panel** - Visual runtime error tracking in the browser
2. **Database Editor** - Direct database manipulation CLI tool

---

## 1. Debug Panel Component

### Overview

The Debug Panel is a browser-based debugging tool that displays runtime errors, network failures, and console logs in a beautiful, organized interface.

### Features

- **Real-time Error Tracking**: Captures JavaScript errors, unhandled promise rejections
- **Network Error Monitoring**: Tracks failed API calls with full details
- **Console Log Capture**: Intercepts console.log/warn/error calls
- **Beautiful UI**: Dark-themed, minimizable panel with tabs
- **Stack Traces**: Expandable stack traces for detailed debugging
- **Context Information**: Shows error context and metadata
- **Keyboard Shortcut**: Toggle with `Ctrl+Shift+D`
- **Persistent**: Remembers state across page reloads

### Activation

#### Method 1: Keyboard Shortcut
```
Press Ctrl+Shift+D anywhere in the application
```

#### Method 2: From Console
```javascript
// Enable debug panel
localStorage.setItem('debug_mode', 'enabled')
// Reload page
location.reload()
```

#### Method 3: Programmatic
```javascript
import { useDebugStore } from '@/store/debug'

const debugStore = useDebugStore()
debugStore.enable()
```

### UI Features

#### Tabs

1. **Errors Tab**
   - JavaScript runtime errors
   - Unhandled promise rejections
   - Error type badge (ERROR, WARNING)
   - Timestamp
   - Expandable stack trace
   - Context information

2. **Network Tab**
   - Failed HTTP requests
   - HTTP method and status code
   - Request URL
   - Response data
   - Timestamp

3. **Console Tab**
   - console.log messages
   - console.warn messages
   - console.error messages
   - Color-coded by level
   - Timestamps

#### Controls

- **Clear All**: Remove all captured errors
- **Minimize/Expand**: Toggle panel size
- **Close**: Disable debug panel
- **Delete Individual**: Remove specific errors

### Integration

The debug panel is automatically integrated into the application:

```vue
<!-- Already included in App.vue -->
<template>
  <a-config-provider>
    <router-view />
    <DebugPanel />  <!-- Always rendered when enabled -->
  </a-config-provider>
</template>
```

### Network Error Tracking

Network errors are automatically tracked via Axios interceptor:

```javascript
// In request.js
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Automatically logs to debug panel if enabled
    debugStore.addNetworkError({
      method: 'GET',
      url: '/api/courses',
      status: 500,
      response: { detail: 'Server error' }
    })
    return Promise.reject(error)
  }
)
```

### Custom Error Logging

Add custom errors to the panel:

```javascript
import { useDebugStore } from '@/store/debug'

const debugStore = useDebugStore()

// Add custom error
debugStore.addError({
  type: 'error',
  message: 'Custom validation failed',
  stack: new Error().stack,
  context: {
    userId: 123,
    operation: 'course_selection'
  }
})
```

### Screenshot Example

```
┌────────────────────────────────────────────────────────┐
│ 🐛 Debug Panel                          [5]  🗑️ ⬇️ ✕ │
├────────────────────────────────────────────────────────┤
│ Errors │ Network │ Console                             │
├────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐    │
│ │ ERROR         2:30:45 PM              🗑️        │    │
│ │ Cannot read property 'id' of undefined         │    │
│ │ ▶ Stack Trace                                  │    │
│ │ ▶ Context                                      │    │
│ └────────────────────────────────────────────────┘    │
│ ┌────────────────────────────────────────────────┐    │
│ │ WARNING       2:28:12 PM              🗑️        │    │
│ │ API rate limit approaching                     │    │
│ └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

### Best Practices

1. **Development Only**: Enable debug panel in development, not production
2. **Privacy**: Debug panel may show sensitive data - be cautious
3. **Performance**: Captures last 50 errors, 50 network errors, 100 console logs
4. **Clean Up**: Clear errors periodically to avoid clutter

---

## 2. Database Editor CLI Tool

### Overview

The Database Editor (`course-db-edit`) is a powerful command-line tool for direct database manipulation with **full permissions**, bypassing all application logic and constraints.

⚠️ **WARNING**: This tool can break data integrity. Use with extreme caution!

### Installation

```bash
# Install the package
pip install -e .

# Verify installation
course-db-edit --help
```

### Available Commands

#### 1. List Tables

View all tables and their columns in a database:

```bash
course-db-edit list-tables --database data
course-db-edit list-tables -d auth
```

**Output:**
```
Tables in data database:

  📋 courses (11 columns)
     Columns: course_id, course_name, course_credit, ...

  📋 students (5 columns)
     Columns: student_id, student_name, student_courses, ...

  📋 teachers (5 columns)
     Columns: teacher_id, teacher_name, teacher_courses, ...
```

#### 2. Query Records

View records from any table:

```bash
# Query courses (table format)
course-db-edit query -d data -t courses -l 10

# Query users (JSON format)
course-db-edit query -d auth -t users --format json --limit 5
```

**Output:**
```
Records from courses: (showing 10 of 10)

┌───────────┬────────────────┬────────────┬─────────────┐
│ course_id │ course_name    │ credit     │ capacity    │
├───────────┼────────────────┼────────────┼─────────────┤
│ 1         │ Calculus I     │ 4          │ 100         │
│ 2         │ Physics II     │ 4          │ 80          │
└───────────┴────────────────┴────────────┴─────────────┘
```

#### 3. Insert Record

Add a new record to a table:

```bash
course-db-edit insert-record \
  --database data \
  --table courses \
  --values '{"course_name":"New Course","course_credit":3,"course_type":"elective","course_teacher_id":1,"course_time_begin":1,"course_time_end":3,"course_location":"Room 101","course_capacity":50}'
```

**Output:**
```
✓ Record inserted successfully! ID: 15
```

#### 4. Update Record

Modify existing records:

```bash
# Update course capacity
course-db-edit update-record \
  --database data \
  --table courses \
  --where '{"course_id":1}' \
  --values '{"course_capacity":150}'

# Update user status
course-db-edit update-record \
  -d auth \
  -t users \
  -w '{"username":"alice"}' \
  -v '{"is_active":true}'
```

**Output:**
```
Are you sure you want to update records in courses where {"course_id":1}? [y/N]: y
✓ Updated 1 record(s) successfully!
```

#### 5. Delete Record

Remove records from a table:

```bash
course-db-edit delete-record \
  --database auth \
  --table registration_codes \
  --where '{"is_used":true}'
```

**Output:**
```
⚠ WARNING: Are you sure you want to DELETE records from registration_codes where {"is_used":true}? [y/N]: y
✓ Deleted 5 record(s) successfully!
```

#### 6. Column Info

Get detailed information about a specific column:

```bash
course-db-edit column-info -d data -t courses -c course_name
```

**Output:**
```
Column: course_name
  Type: VARCHAR(200)
  Nullable: False
  Default: None
  Primary Key: False
```

#### 7. Raw Query

Execute custom SELECT queries:

```bash
course-db-edit raw-query \
  --database data \
  --sql "SELECT course_name, course_capacity, course_selected FROM courses WHERE course_capacity - course_selected < 10" \
  --format table
```

**Output:**
```
Query Results: (3 rows)

┌─────────────────┬──────────────┬─────────────────┐
│ course_name     │ capacity     │ selected        │
├─────────────────┼──────────────┼─────────────────┤
│ Popular Course  │ 100          │ 95              │
│ Hot Class       │ 50           │ 48              │
└─────────────────┴──────────────┴─────────────────┘
```

### Database Targets

Three databases are available:

1. **data** (`./course_data.db`)
   - Tables: courses, students, teachers
   - Main application data

2. **auth** (`./auth_data.db`)
   - Tables: users, admins, refresh_tokens, registration_codes, reset_codes
   - Authentication data

3. **queue** (`./queue_data.db`)
   - Queue and task data

### Common Use Cases

#### 1. Manually Add a Course

```bash
course-db-edit insert-record -d data -t courses -v '{
  "course_name": "Advanced AI",
  "course_credit": 4,
  "course_type": "required",
  "course_teacher_id": 2,
  "course_time_begin": 10,
  "course_time_end": 12,
  "course_location": "CS Building 301",
  "course_capacity": 60,
  "course_selected": 0
}'
```

#### 2. Reset User Password

```bash
# Get password hash
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('newpassword123'))"

# Update user
course-db-edit update-record \
  -d auth \
  -t users \
  -w '{"username":"alice"}' \
  -v '{"password_hash":"$2b$12$..."}'
```

#### 3. Bulk Enable Users

```bash
# First, check current status
course-db-edit query -d auth -t users -l 100

# Update all inactive users
course-db-edit raw-query -d auth -s "SELECT user_id, username, is_active FROM users WHERE is_active = 0"

# Note: For updates, use update-record command with appropriate where clause
```

#### 4. Clean Old Tokens

```bash
course-db-edit delete-record \
  -d auth \
  -t refresh_tokens \
  -w '{"is_revoked":true}'
```

#### 5. View Course Enrollment

```bash
course-db-edit raw-query -d data -s "
  SELECT 
    course_name, 
    course_capacity, 
    course_selected,
    ROUND((course_selected * 100.0 / course_capacity), 2) as fill_percent
  FROM courses
  ORDER BY fill_percent DESC
" -f table
```

#### 6. Export Data

```bash
# Export to JSON for backup/analysis
course-db-edit query -d data -t courses -l 1000 -f json > courses_backup.json
```

### Safety Features

1. **Confirmation Prompts**: Update and delete operations require confirmation
2. **Read-Only Raw Queries**: Only SELECT allowed in raw-query command
3. **No Cascade Deletes**: Must manually handle relationships
4. **JSON Validation**: Validates JSON input before execution

### Limitations

- ⚠️ **No Validation**: Bypasses all application validation logic
- ⚠️ **No Constraints**: Can create invalid data states
- ⚠️ **No Triggers**: Application triggers won't fire
- ⚠️ **No Audit**: Changes aren't logged in application audit log
- ⚠️ **Direct Access**: Requires file system access to database files

### Security Considerations

1. **Production Use**: Should NOT be used on production databases directly
2. **Backups**: Always backup databases before bulk modifications
3. **Access Control**: Restrict access to authorized personnel only
4. **Audit Trail**: Manually log any changes made via this tool

### Troubleshooting

#### Database Not Found

```
✗ Database not found: ./course_data.db
```

**Solution**: Make sure you're in the correct directory where database files exist.

#### Invalid JSON

```
✗ Invalid JSON format for values
```

**Solution**: Check JSON syntax. Use single quotes for shell, double quotes in JSON:
```bash
--values '{"key":"value"}'  # Correct
--values "{"key":"value"}"  # Wrong
```

#### Table Not Found

```
✗ Table not found: coursess
```

**Solution**: Use `list-tables` to see available tables (note: typo above)

---

## Examples & Workflows

### Workflow 1: Fix Corrupted Course Data

```bash
# 1. Identify problem
course-db-edit query -d data -t courses -l 100

# 2. Check specific course
course-db-edit raw-query -d data -s "SELECT * FROM courses WHERE course_id = 5"

# 3. Fix the data
course-db-edit update-record \
  -d data -t courses \
  -w '{"course_id":5}' \
  -v '{"course_selected":0,"course_capacity":100}'

# 4. Verify fix
course-db-edit query -d data -t courses -l 5
```

### Workflow 2: Bulk User Management

```bash
# 1. Export current users
course-db-edit query -d auth -t users -f json > users_backup.json

# 2. View inactive users
course-db-edit raw-query -d auth -s "SELECT username, user_type, is_active FROM users WHERE is_active = 0"

# 3. Re-activate specific user
course-db-edit update-record \
  -d auth -t users \
  -w '{"username":"bob"}' \
  -v '{"is_active":true}'
```

### Workflow 3: Debug Authentication Issues

```bash
# 1. Check user exists
course-db-edit raw-query -d auth -s "SELECT user_id, username, user_type, is_active FROM users WHERE username = 'alice'"

# 2. Check tokens
course-db-edit raw-query -d auth -s "SELECT id, user_id, is_revoked, expires_at FROM refresh_tokens WHERE user_id = 1"

# 3. Revoke old tokens
course-db-edit update-record \
  -d auth -t refresh_tokens \
  -w '{"user_id":1}' \
  -v '{"is_revoked":true}'
```

---

## Best Practices

### Debug Panel

1. ✅ Enable only in development
2. ✅ Clear errors regularly
3. ✅ Use for troubleshooting, not monitoring
4. ✅ Review stack traces for root causes
5. ❌ Don't leave enabled in production
6. ❌ Don't share screenshots with sensitive data

### Database Editor

1. ✅ Backup before bulk changes
2. ✅ Test on development database first
3. ✅ Use transactions when possible
4. ✅ Document all manual changes
5. ❌ Don't use in production without approval
6. ❌ Don't skip validation unless necessary
7. ❌ Don't modify data without understanding impact

---

## FAQ

**Q: Can debug panel impact performance?**
A: Minimal impact. Stores last 50 errors, 50 network errors, 100 console logs.

**Q: Is debug panel secure?**
A: It captures all errors including potentially sensitive data. Use only in development.

**Q: Can I customize debug panel appearance?**
A: Yes, edit `/frontend/src/components/DebugPanel.vue` styles.

**Q: Does db-edit work with production databases?**
A: Yes, but NOT recommended. Always use development/staging databases.

**Q: Can I undo changes made with db-edit?**
A: No automatic undo. Maintain backups and manual records of changes.

**Q: What if I delete critical data?**
A: Restore from backup. Always backup before using delete operations.

**Q: Can multiple users use db-edit simultaneously?**
A: SQLite supports this, but concurrent writes may cause locking. Coordinate access.

---

## Keyboard Shortcuts

- **Ctrl+Shift+D**: Toggle debug panel
- **(In terminal)** Ctrl+C: Cancel db-edit operation

---

## Integration with CI/CD

### Debug Panel

```yaml
# .github/workflows/test.yml
- name: Run E2E tests with debug panel
  run: |
    npm run test:e2e
  env:
    DEBUG_MODE: enabled
```

### Database Editor

```yaml
# Database migration script
- name: Apply data fixes
  run: |
    course-db-edit update-record \
      -d data -t courses \
      -w '{"course_id":1}' \
      -v '{"course_capacity":150}'
```

---

## Support

For issues or questions:
- Check `DEVELOPER.md` for architecture details
- Review `TROUBLESHOOTING.md` for common problems
- Open issue on GitHub with debug panel screenshot


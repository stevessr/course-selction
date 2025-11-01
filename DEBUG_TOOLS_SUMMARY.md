# Debug Tools Feature Summary

## Overview

This document summarizes the two powerful debugging and development tools added to the course selection system.

## 1. Debug Panel Component

### Description
A browser-based runtime error tracking system with a beautiful, VS Code-inspired dark theme UI.

### Key Features
- **Real-time Error Capture**: Automatically captures JavaScript errors and unhandled promise rejections
- **Network Error Monitoring**: Tracks failed API calls with full request/response details
- **Console Log Interception**: Intercepts and displays console.log/warn/error calls
- **Beautiful UI**: Dark-themed, minimizable floating panel positioned at bottom-right
- **Three Tabs**: 
  - Errors: Runtime JavaScript errors with stack traces
  - Network: Failed HTTP requests
  - Console: Console output logs
- **Keyboard Shortcut**: `Ctrl+Shift+D` to toggle
- **Persistent**: Remembers enabled state across page reloads
- **Performance**: Stores last 50 errors, 50 network errors, 100 console logs

### Implementation Details
- **Component**: `frontend/src/components/DebugPanel.vue` (360 lines)
- **Store**: `frontend/src/store/debug.js` (155 lines)
- **Integration**: Automatically included in App.vue
- **Axios Integration**: Network errors tracked via response interceptor
- **Global Handlers**: Window error and unhandled rejection events

### Activation Methods

#### Method 1: Keyboard Shortcut
```
Press Ctrl+Shift+D anywhere in the application
```

#### Method 2: LocalStorage
```javascript
localStorage.setItem('debug_mode', 'enabled')
location.reload()
```

#### Method 3: Programmatic
```javascript
import { useDebugStore } from '@/store/debug'
const debugStore = useDebugStore()
debugStore.enable()
```

### UI Controls
- **Clear All**: Remove all captured errors
- **Minimize/Expand**: Toggle panel size
- **Close**: Disable debug panel
- **Delete Individual**: Remove specific error entries

### Use Cases
- Development debugging
- Production error monitoring (if enabled)
- QA testing and bug reporting
- Performance monitoring
- API error troubleshooting

### Best Practices
1. Enable only in development environments
2. Clear errors periodically to avoid clutter
3. Review stack traces for root cause analysis
4. Use for troubleshooting, not permanent monitoring
5. Be cautious with sensitive data exposure

## 2. Database Editor CLI Tool

### Description
A powerful command-line tool for direct database manipulation with full administrative permissions, bypassing all application logic and constraints.

⚠️ **WARNING**: This tool can break data integrity. Use with extreme caution!

### Key Features
- **Direct Database Access**: Manipulate SQLite databases directly
- **7 Commands**: list-tables, query, insert-record, update-record, delete-record, column-info, raw-query
- **Beautiful Output**: Table format (ASCII grid) or JSON format
- **Safety Features**:
  - Confirmation prompts for update/delete operations
  - Read-only raw queries (SELECT only)
  - JSON validation before execution
  - Clear error messages
- **Full Control**: Access to all three databases (data, auth, queue)

### Implementation Details
- **File**: `backend/common/db_edit.py` (360 lines)
- **CLI Script**: `course-db-edit` (registered in pyproject.toml)
- **Framework**: Click for CLI interface, SQLAlchemy for database operations
- **Dependencies**: tabulate for table output, json for data formatting

### Available Commands

#### 1. list-tables
List all tables and their columns in a database.

```bash
course-db-edit list-tables --database data
course-db-edit list-tables -d auth
```

#### 2. query
View records from any table with pagination and format options.

```bash
# Table format
course-db-edit query -d data -t courses -l 10

# JSON format
course-db-edit query -d auth -t users --format json --limit 5
```

#### 3. insert-record
Add a new record to a table.

```bash
course-db-edit insert-record -d data -t courses \
  -v '{"course_name":"New Course","course_credit":3,"course_type":"elective",...}'
```

#### 4. update-record
Modify existing records (with confirmation).

```bash
course-db-edit update-record -d data -t courses \
  -w '{"course_id":1}' -v '{"course_capacity":150}'
```

#### 5. delete-record
Remove records from a table (with warning confirmation).

```bash
course-db-edit delete-record -d auth -t refresh_tokens \
  -w '{"is_revoked":true}'
```

#### 6. column-info
Get detailed information about a specific column.

```bash
course-db-edit column-info -d data -t courses -c course_name
```

#### 7. raw-query
Execute custom SELECT queries.

```bash
course-db-edit raw-query -d data \
  -s "SELECT * FROM courses WHERE course_capacity > 100" \
  --format table
```

### Database Targets

1. **data** (`./course_data.db`)
   - Tables: courses, students, teachers
   - Main application data

2. **auth** (`./auth_data.db`)
   - Tables: users, admins, refresh_tokens, registration_codes, reset_codes
   - Authentication data

3. **queue** (`./queue_data.db`)
   - Queue and task data

### Common Use Cases

#### 1. Fix Corrupted Data
```bash
course-db-edit update-record -d data -t courses \
  -w '{"course_id":5}' -v '{"course_selected":0}'
```

#### 2. Bulk User Management
```bash
# Export users
course-db-edit query -d auth -t users -f json > users_backup.json

# Re-activate user
course-db-edit update-record -d auth -t users \
  -w '{"username":"bob"}' -v '{"is_active":true}'
```

#### 3. Clean Old Tokens
```bash
course-db-edit delete-record -d auth -t refresh_tokens \
  -w '{"is_revoked":true}'
```

#### 4. Data Analysis
```bash
course-db-edit raw-query -d data -s "
  SELECT course_name, 
         ROUND((course_selected * 100.0 / course_capacity), 2) as fill_percent
  FROM courses
  ORDER BY fill_percent DESC
"
```

#### 5. Export for Backup
```bash
course-db-edit query -d data -t courses -l 1000 -f json > courses_backup.json
```

### Safety Considerations

**Confirmations:**
- Update operations require `[y/N]` confirmation
- Delete operations show WARNING and require confirmation

**Limitations:**
- No automatic validation
- No cascade deletes
- Changes aren't logged in application audit log
- Requires file system access to database files

**Best Practices:**
1. Always backup databases before bulk modifications
2. Test on development database first
3. Document all manual changes
4. Don't use in production without approval
5. Understand data relationships before modifying

## Documentation

### Main Guide
**DEBUG_DB_GUIDE.md** (15,000+ characters)
- Complete usage guide for both tools
- 20+ usage examples and workflows
- Best practices and safety considerations
- Troubleshooting guide
- FAQ section
- Integration examples

### Updated Files
- **README.md**: Added new features section with quick reference
- **pyproject.toml**: Added `course-db-edit` CLI script
- **App.vue**: Integrated debug panel component
- **request.js**: Added network error tracking to Axios interceptor

## Installation

Both tools are automatically available after package installation:

```bash
pip install -e .

# Verify installations
course-db-edit --help
# Debug panel available in browser (Ctrl+Shift+D)
```

## Testing

### Debug Panel
1. Open application in browser
2. Press `Ctrl+Shift+D`
3. Trigger an error (e.g., undefined property access)
4. See error captured in panel with stack trace

### Database Editor
```bash
# Test commands
course-db-edit list-tables -d data
course-db-edit query -d data -t courses -l 5
course-db-edit --help
```

## Performance Impact

### Debug Panel
- Minimal performance impact
- Stores limited history (50/50/100)
- Can be disabled anytime with `Ctrl+Shift+D`

### Database Editor
- Direct SQLite operations (fast)
- No performance impact on running application
- Works on database files directly

## Security Considerations

### Debug Panel
- May expose sensitive data in errors
- Should be disabled in production
- Captures all console output
- Network errors include request/response data

### Database Editor
- Full administrative access
- No audit trail
- Bypasses all application security
- Should be restricted to authorized personnel only
- Recommend using only on development/staging

## Integration with Existing Tools

### CLI Tool
Works alongside existing `course-cli`:
```bash
course-cli user login              # User management
course-db-edit query -d auth -t users  # Direct database access
```

### Debug Panel
Works with existing error handling:
- Complements Vue error boundaries
- Enhances Axios error handling
- Provides visual feedback for all errors

## Future Enhancements

### Debug Panel
- [ ] Export errors to JSON
- [ ] Filter by error type
- [ ] Search functionality
- [ ] Performance metrics tracking

### Database Editor
- [ ] Backup/restore commands
- [ ] Diff between records
- [ ] SQL query history
- [ ] Interactive mode (REPL)

## Summary

Both tools provide powerful capabilities for development and debugging:

**Debug Panel**: Perfect for frontend debugging with visual, real-time error tracking
**Database Editor**: Essential for backend data management with direct database access

Together, they significantly improve the development and debugging experience for the course selection system.

## Support

For issues or questions:
- See [DEBUG_DB_GUIDE.md](DEBUG_DB_GUIDE.md) for detailed documentation
- Check [DEVELOPER.md](DEVELOPER.md) for architecture details
- Open GitHub issue with debug panel screenshot if applicable

---

**Files Added:**
- `frontend/src/components/DebugPanel.vue` (360 lines)
- `frontend/src/store/debug.js` (155 lines)
- `backend/common/db_edit.py` (360 lines)
- `DEBUG_DB_GUIDE.md` (500+ lines)

**Files Updated:**
- `README.md` (2 sections)
- `pyproject.toml` (1 script entry)
- `frontend/src/App.vue` (debug panel integration)
- `frontend/src/api/request.js` (network error tracking)

**Total**: 1,500+ lines of code, 15,000+ characters of documentation

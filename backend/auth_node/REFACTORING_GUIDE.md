# Auth Node Refactoring Guide

## Current Status
- **Current size**: 2134 lines
- **Target**: Under 500 lines
- **Progress**: admin_course_routes.py module created (saves ~184 lines)

## Recommended Refactoring Approach

The auth_node/main.py file should be split into the following router modules:

### 1. Authentication Routes Module (`auth_routes.py`)
**Lines**: 177-776 (~600 lines)
**Endpoints**:
- `/register/v1` - User registration phase 1
- `/register/v2` - User registration phase 2
- `/login/v1` - User login v1 with refresh token
- `/login/v2` - User login v2 with access token
- `/check/2fa-status` - Check 2FA status
- `/login/no-2fa` - Login without 2FA
- `/logout` - User logout
- `/setup/2fa/v1` - Setup 2FA v1
- `/setup/2fa/v2` - Setup 2FA v2
- `/refresh` - Refresh access token
- `/get/user` - Get current user info

### 2. Admin Basic Routes Module (`admin_basic_routes.py`)
**Lines**: 777-997 (~221 lines)
**Endpoints**:
- `/login/admin` - Admin login
- `/add/admin` - Add new admin
- `/generate/registration-code` - Generate registration code
- `/generate/reset-code` - Generate reset code
- `/admin/reset-codes` - List reset codes
- `/reset/2fa` - Reset user 2FA

### 3. User Management Routes Module (`user_management_routes.py`)
**Lines**: 998-1639 (~642 lines) - **LARGEST SECTION**
**Endpoints**:
- `/admin/users` - List all users
- `/admin/user` - Get user by username
- `/admin/user/add` - Add new user
- `/admin/user/delete` - Delete user
- `/admin/user/reset-2fa` - Reset user 2FA
- `/admin/user/toggle-status` - Toggle user active status
- `/admin/user/reset-password` - Reset user password
- `/admin/student/update-tags` - Update student tags
- `/admin/student/batch-import-tags` - Batch import student tags
- `/admin/tags/available` - Get available tags

### 4. Admin Course Routes Module (`admin_course_routes.py`) ✅ DONE
**Lines**: 1639-1823 (~185 lines)
**Endpoints**:
- `/admin/courses` - List all courses
- `/admin/course/update` - Update course
- `/admin/course/delete` - Delete course
- `/admin/courses/bulk-import` - Bulk import courses
- `/admin/courses/batch-assign-teacher` - Batch assign teacher

### 5. Settings Routes Module (`settings_routes.py`)
**Lines**: 1823-1876 (~54 lines + ensure_system_settings helper)
**Endpoints**:
- `/admin/settings` (GET) - Get system settings
- `/admin/settings` (PUT) - Update system settings
**Helper Functions**:
- `ensure_system_settings()` - Ensure settings exist

### 6. User Account Routes Module (`user_account_routes.py`)
**Lines**: 1953-2122 (~170 lines)
**Endpoints**:
- `/user/change-password` - Change password
- `/user/2fa/setup` - Setup 2FA
- `/user/2fa/verify` - Verify 2FA
- `/user/2fa/disable` - Disable 2FA
- `/user/2fa/status` - Get 2FA status

## Implementation Pattern

Use the factory pattern established in data_node:

```python
def create_auth_router(get_db: Callable, verify_admin: Callable) -> APIRouter:
    router = APIRouter()
    
    @router.post("/register/v1")
    async def register_v1(...):
        # Implementation
    
    return router
```

Then in main.py:

```python
from backend.auth_node.routers.auth_routes import create_auth_router
from backend.auth_node.routers.admin_course_routes import create_admin_course_router
# ... other imports

auth_router = create_auth_router(get_db, get_current_admin)
admin_course_router = create_admin_course_router(get_db, get_current_admin)
# ... create other routers

app.include_router(auth_router)
app.include_router(admin_course_router)
# ... include other routers
```

## Expected Final Size

After extracting all sections:
- Authentication routes: ~600 lines → separate module
- Admin basic: ~221 lines → separate module
- User management: ~642 lines → separate module
- Admin course: ~185 lines → separate module ✅
- Settings: ~54 lines → separate module
- User account: ~170 lines → separate module
- **Remaining in main.py**: ~262 lines (imports, setup, dependencies, health check)

This would reduce main.py from 2134 lines to approximately **262 lines**, well under the 500-line threshold.

## Dependencies to Handle

Key dependencies that routes need:
- `get_db()` - Database session
- `get_current_admin()` - Admin authentication
- `verify_admin_or_internal()` - Admin or internal auth
- `verify_internal_token_header()` - Internal token verification
- `ensure_system_settings()` - Settings helper

These should remain in main.py or be moved to a shared `dependencies.py` module if needed.

## Testing After Refactoring

After each router extraction:
1. Run `python -m pytest tests/test_basic.py`
2. Start the auth_node server and test health endpoint
3. Test key endpoints with curl or httpx
4. Run integration tests if available

# Development Checklist

## Completed ✓

- [x] Project structure setup
  - [x] Backend directory structure
  - [x] Frontend directory structure
  - [x] Configuration files

- [x] Backend Implementation
  - [x] Common utilities package
    - [x] Database models (Course, Student, Teacher, User, Admin, etc.)
    - [x] Pydantic schemas for validation
    - [x] Security utilities (JWT, 2FA, password hashing)
    - [x] Rate limiter (Token bucket algorithm)
    - [x] Utility functions
  - [x] Data Node Service (Port 8001)
    - [x] Course CRUD operations
    - [x] Student management
    - [x] Teacher management
    - [x] Course selection/deselection
  - [x] Authentication Node Service (Port 8002)
    - [x] Student/Teacher login with 2FA
    - [x] Registration with 2FA setup
    - [x] Admin login (no 2FA)
    - [x] Token management (refresh + access)
    - [x] Registration code generation
    - [x] 2FA reset code generation
  - [x] Teacher Service Node (Port 8003)
    - [x] Course management
    - [x] Student removal from courses
    - [x] Statistics
  - [x] Student Service Node (Port 8004)
    - [x] Browse available courses
    - [x] Select/deselect courses (via queue)
    - [x] View selected courses
    - [x] View schedule
    - [x] Check course conflicts
  - [x] Queue Buffer Node (Port 8005)
    - [x] Queue management for course selection
    - [x] Rate limiting (IP + user-based)
    - [x] Priority queue (deselect > select)
    - [x] Task status tracking

- [x] Frontend Implementation
  - [x] Vue3 + Ant Design setup
  - [x] Router configuration
  - [x] State management (Pinia)
  - [x] API client modules
  - [x] Login view (Student/Teacher/Admin)
  - [x] Registration view with 2FA setup
  - [x] Student interface
    - [x] Available courses view
    - [x] Selected courses view
    - [x] Schedule view
  - [x] Teacher interface
    - [x] Course management view
    - [x] Create course view
  - [x] Admin interface
    - [x] User management view
    - [x] Registration code generation view

- [x] Features Implementation
  - [x] Two-Factor Authentication (TOTP)
    - [x] QR code generation
    - [x] Secret key backup
    - [x] 2FA verification on login
    - [x] 2FA on token refresh (students only)
  - [x] Rate Limiting
    - [x] Token bucket algorithm
    - [x] IP-based limiting
    - [x] X-Forwarded-For support
    - [x] Per-user limiting
  - [x] Queue System
    - [x] Asynchronous task processing
    - [x] Priority queue
    - [x] Status tracking
  - [x] Role-Based Access Control
    - [x] Student role
    - [x] Teacher role
    - [x] Admin role
    - [x] Route guards

- [x] Documentation
  - [x] README.md (overview)
  - [x] SETUP.md (detailed setup guide)
  - [x] plan.md (architecture design)
  - [x] Code comments

- [x] Testing
  - [x] Unit tests for common utilities
  - [x] System test script
  - [x] Test documentation

- [x] DevOps
  - [x] .gitignore configuration
  - [x] Startup script (start_backend.sh)
  - [x] Environment configuration examples

## TODO / Future Enhancements

- [ ] Master-slave replication implementation
  - [ ] Database synchronization
  - [ ] Failover mechanism
  - [ ] Read-only node configuration

- [ ] Additional Features
  - [ ] Course prerequisites
  - [ ] Grade management
  - [ ] Credit limits per student
  - [ ] Email notifications
  - [ ] Export/import functionality

- [ ] Production Readiness
  - [ ] Docker containerization
  - [ ] CI/CD pipeline
  - [ ] Production environment variables
  - [ ] SSL/TLS configuration
  - [ ] Database migration scripts
  - [ ] Backup and restore procedures
  - [ ] Monitoring and logging
  - [ ] Performance optimization

- [ ] Testing
  - [ ] Integration tests
  - [ ] E2E tests with Playwright
  - [ ] Load testing
  - [ ] Security testing

## Notes

- Default admin credentials: admin/admin123 (change in production!)
- All services use INTERNAL_TOKEN for inter-service communication
- Students require 2FA for login and token refresh
- Teachers and admins don't require 2FA
- Rate limiting is enabled by default
- SQLite is used for all databases (can be changed to PostgreSQL for production)

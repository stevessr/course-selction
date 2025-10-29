# Default admin configuration
# This file defines default admin accounts and system configuration

# Admin accounts - these will be created on first system startup
DEFAULT_ADMINS = [
    {
        "admin_name": "admin",
        "admin_password": "admin123",  # This should be changed in production
        "is_super_admin": True
    },
    {
        "admin_name": "super_admin",
        "admin_password": "super123",  # This should be changed in production, kept under 72 bytes
        "is_super_admin": True
    }
]

# System configuration
SYSTEM_CONFIG = {
    "system_name": "Course Selection System",
    "version": "1.0.0",
    "debug_mode": False,
    "max_login_attempts": 5,
    "login_lockout_duration": 900,  # 15 minutes in seconds
    "session_timeout": 3600,  # 1 hour in seconds
    "default_timezone": "UTC",
    "default_language": "en",
    "maintenance_mode": False,
    "rate_limit_enabled": True,
    "max_requests_per_minute": 100,
    "enable_2fa_by_default": True
}

# Course configuration
COURSE_CONFIG = {
    "max_courses_per_student": 6,
    "max_credits_per_student": 18,
    "course_selection_start_date": "2023-09-01T00:00:00Z",
    "course_selection_end_date": "2023-09-15T23:59:59Z",
    "course_drop_deadline": "2023-09-30T23:59:59Z",
    "allow_time_conflicts": False,
    "enable_waitlist": True,
    "max_waitlist_size": 20
}

# Security configuration
SECURITY_CONFIG = {
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_numbers": True,
    "password_require_special_chars": True,
    "enable_cors": True,
    "allowed_origins": ["http://localhost:3000", "http://localhost:8080", "https://yourdomain.com"],
    "enable_csrf_protection": True,
    "jwt_algorithm": "HS256",
    "token_expiration_hours": 24
}

# Database configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo_sql": False  # Set to True for debugging SQL queries
}

# Queue configuration
QUEUE_CONFIG = {
    "max_queue_size": 10000,
    "default_priority": 0,
    "high_priority_threshold": 5,
    "max_retry_attempts": 3,
    "retry_delay_seconds": 5,
    "processing_timeout_seconds": 300,  # 5 minutes
    "enable_priority_queue": True
}

# Notification configuration
NOTIFICATION_CONFIG = {
    "email_enabled": True,
    "email_from_address": "noreply@coursesystem.edu",
    "email_smtp_server": "smtp.coursesystem.edu",
    "email_smtp_port": 587,
    "email_smtp_username": "smtp_user",
    "email_smtp_password": "smtp_password",
    "sms_enabled": False,
    "sms_provider": "twilio",
    "sms_api_key": "your_sms_api_key"
}
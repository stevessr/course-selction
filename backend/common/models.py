"""Common database models used across services"""
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

# Separate base classes for different service databases
DataBase = declarative_base()  # For data_node: courses, course-related student/teacher data
AuthBase = declarative_base()  # For auth_node: authentication, admins, tokens, codes
QueueBase = declarative_base()  # For queue_node: queue_tasks


class Course(DataBase):
    """Course model with enhanced scheduling and tagging system"""
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    course_name = Column(String(200), nullable=False)
    course_credit = Column(Integer, nullable=False)
    course_type = Column(String(50), nullable=False)
    course_teacher_id = Column(Integer, nullable=False)

    # Course period enum: 1-13 (representing class periods)
    course_time_start = Column(Integer, nullable=True)  # Start period (1-13)
    course_time_end = Column(Integer, nullable=True)  # End period (1-13)

    # Weekdays: Array of integers 1-7 (1=Monday, 2=Tuesday, ..., 7=Sunday)
    course_weekdays = Column(JSON, default=list)  # e.g., [1, 3, 5] for Mon, Wed, Fri

    # Legacy fields for backward compatibility
    course_time_begin = Column(Integer, nullable=True)
    course_time_end_legacy = Column(Integer, nullable=True)

    # New scheduling system: {"monday": [1,2,5], "wednesday": [3,4], ...}
    # Time slots: 1-4 (morning), 5-8 (afternoon), 9-11 (evening)
    course_schedule = Column(JSON, nullable=True)

    course_location = Column(String(100), nullable=False)
    course_capacity = Column(Integer, nullable=False)
    course_selected = Column(JSON, default=list)  # List of student IDs who selected this course
    course_selected_count = Column(Integer, default=0)  # For backward compatibility and quick count

    # New fields for enhanced course management
    course_tags = Column(JSON, default=list)  # Student must have matching tags
    course_notes = Column(String(500), default="")  # Additional information
    course_cost = Column(Integer, default=0)  # 0 for free courses
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class StudentCourseData(DataBase):
    """Student course-related data (stored in course_data.db)"""
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(100), nullable=False)
    student_courses = Column(JSON, default=list)  # List of course IDs
    student_tags = Column(JSON, default=list)  # Tags for course enrollment eligibility
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TeacherCourseData(DataBase):
    """Teacher course-related data (stored in course_data.db)"""
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_name = Column(String(100), nullable=False)
    teacher_courses = Column(JSON, default=list)  # List of course IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AvailableTag(DataBase):
    """Available tags for auto-completion"""
    __tablename__ = "available_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(100), nullable=False, unique=True)
    tag_type = Column(String(20), nullable=False)  # 'user' or 'course'
    usage_count = Column(Integer, default=0)  # Track how many times this tag is used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Authentication models (stored in auth_data.db)
class Student(AuthBase):
    """Student authentication model (stored in auth_data.db)"""
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(32))  # For 2FA (required for students)
    has_2fa = Column(Boolean, default=False)  # Track if student has enabled 2FA
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Teacher(AuthBase):
    """Teacher authentication model (stored in auth_data.db)"""
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(32))  # For 2FA (optional for teachers)
    has_2fa = Column(Boolean, default=False)  # Track if teacher has enabled 2FA
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Admin(AuthBase):
    """Admin model"""
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RefreshToken(AuthBase):
    """Refresh token storage"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RegistrationCode(AuthBase):
    """Registration codes generated by admin"""
    __tablename__ = "registration_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    user_type = Column(String(20), nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    # Tags that will be automatically assigned to users who register with this code
    code_tags = Column(JSON, default=list)


class ResetCode(AuthBase):
    """2FA reset codes generated by admin"""
    __tablename__ = "reset_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    user_id = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)


class SystemSettings(AuthBase):
    """System-wide settings for registration control"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_registration_enabled = Column(Boolean, default=True)
    teacher_registration_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))





class QueueTask(QueueBase):
    """Queue task for course selection"""
    __tablename__ = "queue_tasks"

    task_id = Column(String(36), primary_key=True)
    student_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    task_type = Column(String(20), nullable=False)  # select, deselect
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    priority = Column(Integer, default=0)
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

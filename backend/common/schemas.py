"""Pydantic schemas for API validation"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# Course schemas
class CourseBase(BaseModel):
    course_name: str = Field(..., min_length=1, max_length=200)
    course_credit: int = Field(..., ge=0)
    course_type: str = Field(..., min_length=1, max_length=50)
    course_teacher_id: int = Field(..., ge=1)
    course_time_begin: Optional[int] = Field(None)  # Legacy field, optional
    course_time_end: Optional[int] = Field(None)  # Legacy field, optional
    course_schedule: Optional[dict] = Field(None)  # New: {"monday": [1,2], ...}
    course_location: str = Field(..., min_length=1, max_length=100)
    course_capacity: int = Field(..., ge=1)
    course_tags: List[str] = Field(default_factory=list)  # Tags for enrollment
    course_notes: str = Field(default="", max_length=500)
    course_cost: int = Field(default=0, ge=0)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_name: Optional[str] = Field(None, min_length=1, max_length=200)
    course_credit: Optional[int] = Field(None, ge=0)
    course_type: Optional[str] = Field(None, min_length=1, max_length=50)
    course_teacher_id: Optional[int] = Field(None, ge=1)
    course_time_begin: Optional[int] = None
    course_time_end: Optional[int] = None
    course_schedule: Optional[dict] = None
    course_location: Optional[str] = Field(None, min_length=1, max_length=100)
    course_capacity: Optional[int] = Field(None, ge=1)
    course_tags: Optional[List[str]] = None
    course_notes: Optional[str] = Field(None, max_length=500)
    course_cost: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    course_id: int
    course_selected: int
    course_left: int  # Available seats (calculated as capacity - selected)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Student schemas
class StudentCreate(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    student_tags: List[str] = Field(default_factory=list)


class StudentResponse(BaseModel):
    student_id: int
    student_name: str
    student_courses: List[int] = []
    student_tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Teacher schemas
class TeacherCreate(BaseModel):
    teacher_name: str = Field(..., min_length=1, max_length=100)


class TeacherResponse(BaseModel):
    teacher_id: int
    teacher_name: str
    teacher_courses: List[int] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    user_type: str = Field(..., pattern="^(student|teacher)$")  # Exclude admin from registration
    registration_code: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class User2FA(BaseModel):
    totp_code: str = Field(..., pattern="^[0-9]{6}$")


class UserResponse(BaseModel):
    user_id: int
    username: str
    user_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminResponse(BaseModel):
    admin_id: int
    username: str
    user_type: str = "admin"  # Always admin
    is_active: bool = True  # Admins are always active
    created_at: datetime

    class Config:
        from_attributes = True


# Token schemas
class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenResponse(BaseModel):
    refresh_token: str
    expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Course selection schemas
class CourseSelectionRequest(BaseModel):
    course_id: int = Field(..., ge=1)


class CourseSelectionData(BaseModel):
    """Schema for internal course selection data (used by queue_node -> data_node)"""
    student_id: int = Field(..., ge=1)
    course_id: int = Field(..., ge=1)


class QueueTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    position: Optional[int] = None
    estimated_time: Optional[int] = None


# Admin schemas
class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class AdminLogin(BaseModel):
    username: str
    password: str


class RegistrationCodeCreate(BaseModel):
    user_type: str = Field(..., pattern="^(student|teacher)$")
    expires_days: int = Field(default=7, ge=1, le=365)


class RegistrationCodeResponse(BaseModel):
    code: str
    user_type: str
    expires_at: datetime


class ResetCodeCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    expires_days: int = Field(default=7, ge=1, le=365)


class ResetCodeResponse(BaseModel):
    code: str
    username: str
    expires_at: datetime


# Batch operations
class BatchStudentCreate(BaseModel):
    students: List[dict] = Field(..., min_length=1)

    @field_validator('students')
    def validate_students(cls, v):
        for student in v:
            if 'student_name' not in student or 'password' not in student:
                raise ValueError("Each student must have student_name and password")
        return v


# Statistics
class TeacherStats(BaseModel):
    total_courses: int
    total_students: int
    courses_by_type: dict


class StudentStats(BaseModel):
    total_courses: int
    total_credit: int
    courses_by_type: dict
    credit_by_type: dict


# Queue task
class QueueTaskSubmit(BaseModel):
    student_id: int
    course_id: int
    task_type: str = Field(..., pattern="^(select|deselect)$")
    priority: int = Field(default=0)


class QueueTaskStatus(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    position: Optional[int] = None

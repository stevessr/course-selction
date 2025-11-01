"""Authentication helper functions for querying correct user tables"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, Union
from .models import Student, Teacher, Admin


def get_user_by_username(db: Session, username: str, user_type: Optional[str] = None) -> Optional[Union[Student, Teacher, Admin]]:
    """Get user by username from appropriate table.
    
    Args:
        db: Database session
        username: Username to search for
        user_type: Optional user type filter ("student", "teacher", "admin")
    
    Returns:
        User object (Student, Teacher, or Admin) or None
    """
    if user_type == "student" or user_type is None:
        student = db.query(Student).filter(Student.username == username).first()
        if student:
            return student
    
    if user_type == "teacher" or user_type is None:
        teacher = db.query(Teacher).filter(Teacher.username == username).first()
        if teacher:
            return teacher
    
    if user_type == "admin" or user_type is None:
        admin = db.query(Admin).filter(Admin.username == username).first()
        if admin:
            return admin
    
    return None


def get_user_by_id(db: Session, user_id: int, user_type: str) -> Optional[Union[Student, Teacher, Admin]]:
    """Get user by ID from appropriate table.
    
    Args:
        db: Database session
        user_id: User ID to search for
        user_type: User type ("student", "teacher", "admin")
    
    Returns:
        User object (Student, Teacher, or Admin) or None
    """
    if user_type == "student":
        return db.query(Student).filter(Student.student_id == user_id).first()
    elif user_type == "teacher":
        return db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
    elif user_type == "admin":
        return db.query(Admin).filter(Admin.admin_id == user_id).first()
    return None


def get_user_id(user: Union[Student, Teacher, Admin]) -> int:
    """Get the ID from any user object.
    
    Args:
        user: User object (Student, Teacher, or Admin)
    
    Returns:
        User ID
    """
    if isinstance(user, Student):
        return user.student_id
    elif isinstance(user, Teacher):
        return user.teacher_id
    elif isinstance(user, Admin):
        return user.admin_id
    raise ValueError("Invalid user type")


def get_user_type(user: Union[Student, Teacher, Admin]) -> str:
    """Get the type of user.
    
    Args:
        user: User object (Student, Teacher, or Admin)
    
    Returns:
        User type string ("student", "teacher", or "admin")
    """
    if isinstance(user, Student):
        return "student"
    elif isinstance(user, Teacher):
        return "teacher"
    elif isinstance(user, Admin):
        return "admin"
    raise ValueError("Invalid user type")


def has_2fa(user: Union[Student, Teacher, Admin]) -> bool:
    """Check if user has 2FA enabled.
    
    Args:
        user: User object (Student, Teacher, or Admin)
    
    Returns:
        True if user has 2FA enabled, False otherwise
    """
    # Only students have 2FA
    if isinstance(user, Student):
        return user.totp_secret is not None and user.totp_secret != ""
    return False


def get_totp_secret(user: Union[Student, Teacher, Admin]) -> Optional[str]:
    """Get TOTP secret from user.
    
    Args:
        user: User object (Student, Teacher, or Admin)
    
    Returns:
        TOTP secret if available, None otherwise
    """
    if isinstance(user, Student):
        return user.totp_secret
    return None


def set_totp_secret(user: Union[Student, Teacher, Admin], totp_secret: Optional[str]) -> None:
    """Set TOTP secret for user.
    
    Args:
        user: User object (Student, Teacher, or Admin)
        totp_secret: TOTP secret to set
    """
    if isinstance(user, Student):
        user.totp_secret = totp_secret
    # Teachers and admins don't have 2FA


def is_active(user: Union[Student, Teacher, Admin]) -> bool:
    """Check if user is active.
    
    Args:
        user: User object (Student, Teacher, or Admin)
    
    Returns:
        True if user is active, False otherwise
    """
    return user.is_active if hasattr(user, 'is_active') else True

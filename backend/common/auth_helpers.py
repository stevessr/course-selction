"""Authentication helper functions for querying correct user tables"""
import httpx
import os
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, Union
from .models import Student, Teacher, Admin


async def get_user_by_username(db: Session, username: str, user_type: Optional[str] = None) -> Optional[Union[Student, Teacher, Admin]]:
    """Get user by username from appropriate table.
    
    Args:
        db: Database session
        username: Username to search for
        user_type: Optional user type filter ("student", "teacher", "admin")
    
    Returns:
        User object (Student, Teacher, or Admin) or None
    """
    # First check admin table in auth database
    if user_type == "admin" or user_type is None:
        admin = db.query(Admin).filter(Admin.username == username).first()
        if admin:
            return admin
    
    # For student and teacher, check in data_node database via API if user_type is not admin
    if user_type != "admin":
        # Get data node URL from environment
        data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
        internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
        
        try:
            async with httpx.AsyncClient() as client:
                # Check student table in data node
                if user_type == "student" or user_type is None:
                    params = {"search": username, "page": 1, "page_size": 1, "user_type": "student"}
                    headers = {"Internal-Token": f"Bearer {internal_token}"}
                    response = await client.get(f"{data_node_url}/data/users", params=params, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("users"):
                            # Return a minimal Student object with the info we have
                            user_data = data["users"][0]
                            # Create a pseudo object with the required attributes
                            class PseudoStudent:
                                def __init__(self, data):
                                    self.student_id = data.get("user_id") or data.get("student_id")
                                    self.username = data.get("username")
                                    self.password_hash = data.get("password_hash")
                                    self.student_name = data.get("student_name", data.get("username"))
                                    self.student_courses = data.get("student_courses", [])
                                    self.student_tags = data.get("student_tags", [])
                                    self.totp_secret = data.get("totp_secret")
                                    self.is_active = data.get("is_active", True)
                                    self.created_at = data.get("created_at")
                                    self.updated_at = data.get("updated_at")
                            
                            return PseudoStudent(user_data)
                
                # Check teacher table in data node
                if user_type == "teacher" or user_type is None:
                    params = {"search": username, "page": 1, "page_size": 1, "user_type": "teacher"}
                    headers = {"Internal-Token": f"Bearer {internal_token}"}
                    response = await client.get(f"{data_node_url}/data/users", params=params, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("users"):
                            # Return a minimal Teacher object with the info we have
                            user_data = data["users"][0]
                            # Create a pseudo object with the required attributes
                            class PseudoTeacher:
                                def __init__(self, data):
                                    self.teacher_id = data.get("user_id") or data.get("teacher_id")
                                    self.username = data.get("username")
                                    self.password_hash = data.get("password_hash")
                                    self.teacher_name = data.get("teacher_name", data.get("username"))
                                    self.teacher_courses = data.get("teacher_courses", [])
                                    self.is_active = data.get("is_active", True)
                                    self.created_at = data.get("created_at")
                                    self.updated_at = data.get("updated_at")
                            
                            return PseudoTeacher(user_data)
        
        except httpx.RequestError:
            # If the data node is not available, return None
            return None

    return None


async def get_user_by_id(db: Session, user_id: int, user_type: str) -> Optional[Union[Student, Teacher, Admin]]:
    """Get user by ID from appropriate table.
    
    Args:
        db: Database session
        user_id: User ID to search for
        user_type: User type ("student", "teacher", "admin")
    
    Returns:
        User object (Student, Teacher, or Admin) or None
    """
    if user_type == "admin":
        return db.query(Admin).filter(Admin.admin_id == user_id).first()
    elif user_type in ("student", "teacher"):
        # For student and teacher, check in data_node database via API
        data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
        internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
        
        try:
            async with httpx.AsyncClient() as client:
                params = {"user_type": user_type, "page": 1, "page_size": 1, "search": ""}
                headers = {"Internal-Token": f"Bearer {internal_token}"}
                
                response = await client.get(f"{data_node_url}/data/users", params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    
                    # Find user by ID
                    for user_data in users:
                        if user_data.get("user_id") == user_id:
                            # Return appropriate pseudo object
                            if user_type == "student":
                                class PseudoStudent:
                                    def __init__(self, data):
                                        self.student_id = data.get("user_id") or data.get("student_id")
                                        self.username = data.get("username")
                                        self.password_hash = data.get("password_hash")
                                        self.student_name = data.get("student_name", data.get("username"))
                                        self.student_courses = data.get("student_courses", [])
                                        self.student_tags = data.get("student_tags", [])
                                        self.totp_secret = data.get("totp_secret")
                                        self.is_active = data.get("is_active", True)
                                        self.created_at = data.get("created_at")
                                        self.updated_at = data.get("updated_at")
                                
                                return PseudoStudent(user_data)
                            elif user_type == "teacher":
                                class PseudoTeacher:
                                    def __init__(self, data):
                                        self.teacher_id = data.get("user_id") or data.get("teacher_id")
                                        self.username = data.get("username")
                                        self.password_hash = data.get("password_hash")
                                        self.teacher_name = data.get("teacher_name", data.get("username"))
                                        self.teacher_courses = data.get("teacher_courses", [])
                                        self.is_active = data.get("is_active", True)
                                        self.created_at = data.get("created_at")
                                        self.updated_at = data.get("updated_at")
                                
                                return PseudoTeacher(user_data)
        
        except httpx.RequestError:
            # If the data node is not available, return None
            return None
    
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

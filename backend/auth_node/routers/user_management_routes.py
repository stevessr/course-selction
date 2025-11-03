"""User management routes for Auth Node - admin user operations"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Callable
from datetime import datetime, timezone
import os
import httpx

from backend.common import (
    Admin, Student, Teacher, AvailableTag,
    verify_password, get_password_hash,
)
from backend.common.auth_helpers import (
    get_user_by_username, get_user_by_id, get_user_type, get_user_id,
)

# Configuration
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")


def create_user_management_router(get_db: Callable, verify_admin_or_internal: Callable, get_current_admin: Callable) -> APIRouter:
    """
    Factory function to create user management router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_admin_or_internal: Admin or internal auth dependency
        get_current_admin: Admin authentication dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.get("/admin/users")
    async def list_users(
        user_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: str = "",
        _: None = Depends(verify_admin_or_internal),
        db: Session = Depends(get_db)
    ):
        """List all users (admin or internal service only)"""
        all_users_data = []
        total = 0
        
        # Get admin users from local database
        if not user_type or user_type == "admin":
            query_admins = db.query(Admin)
            if search:
                query_admins = query_admins.filter(Admin.username.contains(search))
            total_admins = query_admins.count()
            
            # Apply pagination only if filtering by admin type specifically
            if user_type == "admin":
                db_admins = query_admins.order_by(Admin.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
            else:
                db_admins = query_admins.order_by(Admin.created_at.desc()).all()
            
            for admin in db_admins:
                all_users_data.append({
                    "user_id": admin.admin_id,
                    "username": admin.username,
                    "user_type": "admin",
                    "is_active": True,
                    "totp_secret": None,
                    "created_at": admin.created_at.isoformat() if admin.created_at else None,
                    "updated_at": None,
                })
            total += total_admins
        
        # Get students from local auth database
        if not user_type or user_type == "student":
            query_students = db.query(Student)
            if search:
                query_students = query_students.filter(Student.username.contains(search))
            total_students = query_students.count()
            
            # Apply pagination only if filtering by student type specifically
            if user_type == "student":
                db_students = query_students.order_by(Student.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
            else:
                db_students = query_students.order_by(Student.created_at.desc()).all()
            
            # Fetch student tags from data node
            data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
            internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
            
            for student in db_students:
                student_tags = []
                try:
                    # Fetch student data from data node to get tags
                    async with httpx.AsyncClient() as client:
                        headers = {"Internal-Token": internal_token}
                        response = await client.get(
                            f"{data_node_url}/get/student",
                            params={"student_id": student.student_id},
                            headers=headers
                        )
                        if response.status_code == 200:
                            student_data = response.json()
                            student_tags = student_data.get("student_tags", [])
                except Exception as e:
                    # If we can't fetch tags, continue with empty list
                    pass
                
                all_users_data.append({
                    "user_id": student.student_id,
                    "username": student.username,
                    "user_type": "student",
                    "is_active": student.is_active,
                    "totp_secret": student.totp_secret,
                    "student_tags": student_tags,
                    "created_at": student.created_at.isoformat() if student.created_at else None,
                    "updated_at": student.updated_at.isoformat() if student.updated_at else None,
                })
            total += total_students
        
        # Get teachers from local auth database
        if not user_type or user_type == "teacher":
            query_teachers = db.query(Teacher)
            if search:
                query_teachers = query_teachers.filter(Teacher.username.contains(search))
            total_teachers = query_teachers.count()
            
            # Apply pagination only if filtering by teacher type specifically
            if user_type == "teacher":
                db_teachers = query_teachers.order_by(Teacher.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
            else:
                db_teachers = query_teachers.order_by(Teacher.created_at.desc()).all()
            
            for teacher in db_teachers:
                all_users_data.append({
                    "user_id": teacher.teacher_id,
                    "username": teacher.username,
                    "user_type": "teacher",
                    "is_active": teacher.is_active,
                    "totp_secret": None,  # Teachers don't have 2FA
                    "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                    "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
                })
            total += total_teachers
        
        # Sort the combined list by created_at in descending order
        all_users_data.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        # Apply pagination if we're combining multiple user types
        if user_type is None:  # Only paginate if getting all types
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            all_users_data = all_users_data[start_index:end_index]
        
        return {
            "users": all_users_data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    
    @router.get("/admin/user")
    async def get_user_by_username_endpoint(
        username: str,
        _: None = Depends(verify_admin_or_internal),
        db: Session = Depends(get_db)
    ):
        """Get user by username (internal only)"""
        user = get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "name": user.name,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "email": user.email
        }
    
    
    @router.post("/admin/user/add")
    async def add_user_endpoint(
        user_data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Add new user (admin only)"""
        import secrets
        import string
        
        username = user_data.get("username")
        password = user_data.get("password")
        user_type = user_data.get("user_type")
        
        if not username or not user_type:
            raise HTTPException(status_code=400, detail="Username and user_type required")
        
        # Generate password if not provided
        if not password:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Check if user exists in the appropriate table
        if user_type == "admin":
            existing = db.query(Admin).filter(Admin.username == username).first()
            if existing:
                raise HTTPException(status_code=400, detail="Admin already exists")
            
            # Create admin
            new_admin = Admin(
                username=username,
                password_hash=get_password_hash(password)
            )
            db.add(new_admin)
        else:
            # Check both student and teacher tables
            existing_student = db.query(Student).filter(Student.username == username).first()
            existing_teacher = db.query(Teacher).filter(Teacher.username == username).first()
            if existing_student or existing_teacher:
                raise HTTPException(status_code=400, detail="User already exists")
            
            # Create user in the appropriate auth table and also provision course data in data-node
            if user_type == "student":
                # Create student in auth DB
                new_student = Student(
                    username=username,
                    password_hash=get_password_hash(password),
                    totp_secret=generate_totp_secret(),
                    has_2fa=False,  # Student needs to complete 2FA setup
                    is_active=True,
                )
                db.add(new_student)
                db.commit()
                db.refresh(new_student)
    
                # Create corresponding student record in data-node
                data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
                internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
                student_payload = {
                    "student_id": new_student.student_id,  # Sync student_id from auth to course data
                    "student_name": username,
                    "student_tags": []
                }
                headers = {"Internal-Token": internal_token}
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{data_node_url}/add/student", json=student_payload, headers=headers)
                    if response.status_code != status.HTTP_201_CREATED:
                        # Rollback auth record if course data creation fails
                        db.delete(new_student)
                        db.commit()
                        raise HTTPException(status_code=500, detail=f"Failed to create student course data: {response.text}")
                except httpx.HTTPError as e:
                    db.delete(new_student)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")
    
            elif user_type == "teacher":
                # Create teacher in auth DB
                new_teacher = Teacher(
                    username=username,
                    password_hash=get_password_hash(password),
                    is_active=True,
                )
                db.add(new_teacher)
                db.commit()
                db.refresh(new_teacher)
    
                # Create corresponding teacher record in data-node
                data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
                internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
                teacher_payload = {
                    "teacher_id": new_teacher.teacher_id,  # Sync teacher_id from auth to course data
                    "teacher_name": username,
                }
                headers = {"Internal-Token": internal_token}
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{data_node_url}/add/teacher", json=teacher_payload, headers=headers)
                    if response.status_code != status.HTTP_201_CREATED:
                        # Rollback auth record if course data creation fails
                        db.delete(new_teacher)
                        db.commit()
                        raise HTTPException(status_code=500, detail=f"Failed to create teacher course data: {response.text}")
                except httpx.HTTPError as e:
                    db.delete(new_teacher)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")
            else:
                raise HTTPException(status_code=400, detail="Invalid user type")
        
        db.commit()
        
        return {
            "success": True,
            "message": "User created successfully",
            "username": username,
            "password": password,  # Return generated password
            "user_type": user_type
        }
    
    
    @router.post("/admin/user/delete")
    async def delete_user_endpoint(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Delete user (admin only)"""
        user_id = data.get("user_id")
        user_type = data.get("user_type")
        
        if not user_id or not user_type:
            raise HTTPException(status_code=400, detail="user_id and user_type required")
        
        if user_type == "admin":
            admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
            if not admin:
                raise HTTPException(status_code=404, detail="Admin not found")
            db.delete(admin)
        elif user_type == "student":
            student = db.query(Student).filter(Student.student_id == user_id).first()
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            db.delete(student)
        elif user_type == "teacher":
            teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
            if not teacher:
                raise HTTPException(status_code=404, detail="Teacher not found")
            db.delete(teacher)
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        db.commit()
        return {"success": True, "message": "User deleted successfully"}
    
    
    @router.post("/admin/user/reset-2fa")
    async def reset_user_2fa_endpoint(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Reset user 2FA (admin only)"""
        username = data.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="Username required")
        
        user = get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only students can have 2FA enabled (teachers don't have 2FA)
        if get_user_type(user) != "student":
            raise HTTPException(status_code=400, detail="Only students can have 2FA")
        
        # Reset TOTP secret using auth_helpers
        set_totp_secret(user, None)
        db.commit()
        
        return {"success": True, "message": "2FA reset successfully"}
    
    
    @router.post("/admin/user/toggle-status")
    async def toggle_user_status_endpoint(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Toggle user active status (admin only). Accepts optional user_type to avoid ID collisions."""
        user_id = data.get("user_id")
        is_active = data.get("is_active")
        user_type = data.get("user_type")
        
        if user_id is None or is_active is None:
            raise HTTPException(status_code=400, detail="user_id and is_active required")
        
        # If caller specifies user_type, use it directly to avoid cross-table ID collisions
        if user_type == "student":
            student = db.query(Student).filter(Student.student_id == user_id).first()
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            student.is_active = is_active
            db.commit()
            return {"success": True, "message": f"Student {'activated' if is_active else 'deactivated'} successfully"}
        elif user_type == "teacher":
            teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
            if not teacher:
                raise HTTPException(status_code=404, detail="Teacher not found")
            teacher.is_active = is_active
            db.commit()
            return {"success": True, "message": f"Teacher {'activated' if is_active else 'deactivated'} successfully"}
        elif user_type == "admin":
            admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
            if not admin:
                raise HTTPException(status_code=404, detail="Admin not found")
            # Admin model may not have is_active; treat toggle as unsupported for admins
            raise HTTPException(status_code=400, detail="Toggling admin status is not supported")
        
        # Fallback: detect by probing tables in order (may be ambiguous if IDs overlap)
        student = db.query(Student).filter(Student.student_id == user_id).first()
        if student:
            student.is_active = is_active
            db.commit()
            return {"success": True, "message": f"Student {'activated' if is_active else 'deactivated'} successfully"}
        
        teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
        if teacher:
            teacher.is_active = is_active
            db.commit()
            return {"success": True, "message": f"Teacher {'activated' if is_active else 'deactivated'} successfully"}
        
        admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
        if admin:
            # Admin model may not have is_active; return a clear error
            raise HTTPException(status_code=400, detail="Toggling admin status is not supported")
        
        raise HTTPException(status_code=404, detail="User not found")
    
    
    @router.post("/admin/user/reset-password")
    async def reset_user_password_endpoint(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Reset user password (admin only) - can set custom password or generate random one"""
        import secrets
        import string
        
        username = data.get("username")
        user_type = data.get("user_type")
        custom_password = data.get("new_password")  # Optional custom password
        
        if not username or not user_type:
            raise HTTPException(status_code=400, detail="username and user_type required")
        
        # Use custom password if provided, otherwise generate random
        if custom_password:
            if len(custom_password) < 6:
                raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
            new_password = custom_password
        else:
            # Generate a secure random password (12 characters)
            alphabet = string.ascii_letters + string.digits + "!@#$%&*"
            new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        new_password_hash = get_password_hash(new_password)
        
        # Update password in the appropriate table
        if user_type == "student":
            user = db.query(Student).filter(Student.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Student not found")
            user.password_hash = new_password_hash
        elif user_type == "teacher":
            user = db.query(Teacher).filter(Teacher.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Teacher not found")
            user.password_hash = new_password_hash
        elif user_type == "admin":
            user = db.query(Admin).filter(Admin.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Admin not found")
            user.password_hash = new_password_hash
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "new_password": new_password,
            "username": username
        }
    
    
    @router.post("/admin/student/update-tags")
    async def update_student_tags_endpoint(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Update student tags (admin only)"""
        student_id = data.get("student_id")
        student_tags = data.get("student_tags")
        
        if student_id is None or student_tags is None:
            raise HTTPException(status_code=400, detail="student_id and student_tags required")
        
        # Verify student exists in auth database
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Update student tags in data node
        data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
        internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": internal_token}
                # data_node expects student_id and student_tags as query params;
                # student_tags is a List[str] query param (repeated keys)
                params = {"student_id": student_id, "student_tags": student_tags}
                response = await client.post(
                    f"{data_node_url}/update/student",
                    params=params,
                    headers=headers
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"Failed to update student tags: {response.text}")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")
        
        return {"success": True, "message": "Student tags updated successfully"}
    
    
    @router.post("/admin/student/batch-import-tags")
    async def batch_import_user_tags(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """
        Batch import user tags from CSV format
        CSV format: username,tag1,tag2,...,tagn
        """
        csv_text = data.get("csv_text")
        if not csv_text:
            raise HTTPException(status_code=400, detail="csv_text is required")
        
        results = {
            "success": [],
            "failed": [],
            "total": 0
        }
        
        data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
        internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
        
        # Parse CSV
        lines = csv_text.strip().split('\n')
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            results["total"] += 1
            parts = [p.strip() for p in line.split(',')]
            
            if len(parts) < 2:
                results["failed"].append({
                    "line": line_num,
                    "error": "Invalid format. Expected: username,tag1,tag2,..."
                })
                continue
            
            username = parts[0]
            tags = [tag for tag in parts[1:] if tag]
            
            # Find student by username
            student = db.query(Student).filter(Student.username == username).first()
            if not student:
                results["failed"].append({
                    "line": line_num,
                    "username": username,
                    "error": "Student not found"
                })
                continue
            
            # Get current tags for the student
            try:
                async with httpx.AsyncClient() as client:
                    headers = {"Internal-Token": internal_token}
                    # Get student details to retrieve current tags
                    response = await client.get(
                        f"{data_node_url}/get/student",
                        params={"student_id": student.student_id},
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        student_data = response.json()
                        existing_tags = student_data.get("student_tags", [])
                    else:
                        existing_tags = []
                    
                    # Merge tags (avoid duplicates)
                    updated_tags = list(set(existing_tags + tags))
                    
                    # Update student tags
                    params = {"student_id": student.student_id, "student_tags": updated_tags}
                    response = await client.post(
                        f"{data_node_url}/update/student",
                        params=params,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        results["success"].append({
                            "username": username,
                            "tags_added": tags,
                            "total_tags": len(updated_tags)
                        })
                    else:
                        results["failed"].append({
                            "line": line_num,
                            "username": username,
                            "error": f"Failed to update: {response.text}"
                        })
            except httpx.HTTPError as e:
                results["failed"].append({
                    "line": line_num,
                    "username": username,
                    "error": f"HTTP error: {str(e)}"
                })
            except Exception as e:
                results["failed"].append({
                    "line": line_num,
                    "username": username,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "imported_count": len(results["success"]),
            "failed_count": len(results["failed"]),
            "total": results["total"],
            "details": results
        }
    
    
    @router.get("/admin/tags/available")
    async def get_available_tags_admin(
        tag_type: Optional[str] = None,
        current_admin: Admin = Depends(get_current_admin)
    ):
        """Get available tags for autocomplete (admin only)"""
        data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
        internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": internal_token}
                params = {}
                if tag_type:
                    params["tag_type"] = tag_type
                
                response = await client.get(
                    f"{data_node_url}/tags/available",
                    params=params,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to get available tags: {response.text}"
                    )
                
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error contacting data node: {str(e)}"
            )
    
    
    # ===== Refresh Token Endpoint =====

    return router

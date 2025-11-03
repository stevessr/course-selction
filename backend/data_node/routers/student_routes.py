"""Student management routes for Data Node"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Callable
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified

from backend.common import (
    Course, StudentCourseData, AvailableTag,
    StudentCreate, StudentResponse,
)


def create_student_router(get_db: Callable, verify_internal_token: Callable) -> APIRouter:
    """
    Factory function to create student router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_internal_token: Internal token verification dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/add/student", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
    async def add_student(
        student: StudentCreate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Add a new student"""
        # Check if student already exists by ID or name
        if student.student_id:
            existing = db.query(StudentCourseData).filter(StudentCourseData.student_id == student.student_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Student with this ID already exists")
        
        existing_name = db.query(StudentCourseData).filter(StudentCourseData.student_name == student.student_name).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Student with this name already exists")

        # Create student with explicit ID if provided (for auth sync)
        student_data = {
            "student_name": student.student_name,
            "student_courses": [],
            "student_tags": student.student_tags
        }
        if student.student_id:
            student_data["student_id"] = student.student_id
        
        db_student = StudentCourseData(**student_data)
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student

    @router.post("/update/student", response_model=StudentResponse)
    async def update_student(
        student_id: int,
        student_name: Optional[str] = None,
        student_tags: Optional[List[str]] = Query(None),
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Update student information"""
        db_student = db.query(StudentCourseData).filter(StudentCourseData.student_id == student_id).first()
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")

        if student_name is not None:
            db_student.student_name = student_name
        if student_tags is not None:
            # Ensure it's a list (FastAPI may pass a single item as str in some environments)
            if isinstance(student_tags, str):
                student_tags = [student_tags]
            db_student.student_tags = list(student_tags)
            
            # Upsert into AvailableTag table (tag_type='user') without over-counting
            existing_names = set(
                t.tag_name for t in db.query(AvailableTag).filter(AvailableTag.tag_type == 'user').all()
            )
            for tag_name in db_student.student_tags:
                if tag_name not in existing_names:
                    db.add(AvailableTag(tag_name=tag_name, tag_type='user', usage_count=1))
        
        db_student.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_student)
        return db_student

    @router.post("/delete/student")
    async def delete_student(
        student_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Delete a student"""
        db_student = db.query(StudentCourseData).filter(StudentCourseData.student_id == student_id).first()
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Remove student from courses
        for course_id in db_student.student_courses or []:
            course = db.query(Course).filter(Course.course_id == course_id).first()
            if course:
                # Remove student from course_selected list
                if isinstance(course.course_selected, list) and student_id in course.course_selected:
                    course.course_selected.remove(student_id)
                    flag_modified(course, "course_selected")
                # Update count
                course.course_selected_count = max(0, course.course_selected_count - 1)

        db.delete(db_student)
        db.commit()
        return {"success": True, "message": "Student deleted successfully"}

    @router.get("/get/student", response_model=StudentResponse)
    async def get_student(
        student_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Get student information"""
        db_student = db.query(StudentCourseData).filter(StudentCourseData.student_id == student_id).first()
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")
        return db_student

    return router

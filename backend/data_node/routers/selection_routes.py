"""Course selection routes for Data Node"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified

from backend.common import (
    Course, StudentCourseData,
    CourseSelectionData,
)


def create_selection_router(get_db: Callable, verify_internal_token: Callable) -> APIRouter:
    """
    Factory function to create course selection router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_internal_token: Internal token verification dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/select/course")
    async def select_course(
        selection: CourseSelectionData,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Student selects a course"""
        student = db.query(StudentCourseData).filter(StudentCourseData.student_id == selection.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        course = db.query(Course).filter(Course.course_id == selection.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Initialize course_selected as array if it's still an integer (migration support)
        course_selected_list = course.course_selected if isinstance(course.course_selected, list) else []
        course_selected_count = len(course_selected_list) if isinstance(course.course_selected, list) else course.course_selected
        
        # Check if course is full
        if course_selected_count >= course.course_capacity:
            raise HTTPException(status_code=400, detail="Course is full")
        
        # Check if student already selected this course
        student_courses = student.student_courses or []
        if selection.course_id in student_courses:
            raise HTTPException(status_code=400, detail="Student already selected this course")
        
        # Check if student ID is already in course selected list
        if selection.student_id in course_selected_list:
            raise HTTPException(status_code=400, detail="Student already in course selection list")
        
        # Add course to student
        student_courses.append(selection.course_id)
        student.student_courses = student_courses
        student.updated_at = datetime.now(timezone.utc)
        
        # Add student ID to course selected list
        course_selected_list.append(selection.student_id)
        course.course_selected = course_selected_list
        course.course_selected_count = len(course_selected_list)
        course.updated_at = datetime.now(timezone.utc)
        
        # Explicitly mark as modified for SQLAlchemy to detect JSON changes
        flag_modified(student, "student_courses")
        flag_modified(course, "course_selected")
        
        db.commit()
        db.refresh(student)
        db.refresh(course)
        
        return {"success": True, "message": "Course selected successfully"}

    @router.post("/deselect/course")
    async def deselect_course(
        selection: CourseSelectionData,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Student deselects a course"""
        student = db.query(StudentCourseData).filter(StudentCourseData.student_id == selection.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        course = db.query(Course).filter(Course.course_id == selection.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check if student has selected this course
        student_courses = student.student_courses or []
        if selection.course_id not in student_courses:
            raise HTTPException(status_code=400, detail="Student has not selected this course")
        
        # Initialize course_selected as array if it's still an integer (migration support)
        course_selected_list = course.course_selected if isinstance(course.course_selected, list) else []
        
        # Remove course from student
        student_courses.remove(selection.course_id)
        student.student_courses = student_courses
        student.updated_at = datetime.now(timezone.utc)
        
        # Remove student ID from course selected list
        if selection.student_id in course_selected_list:
            course_selected_list.remove(selection.student_id)
        course.course_selected = course_selected_list
        course.course_selected_count = len(course_selected_list)
        course.updated_at = datetime.now(timezone.utc)
        
        # Explicitly mark as modified for SQLAlchemy to detect JSON changes
        flag_modified(student, "student_courses")
        flag_modified(course, "course_selected")
        
        db.commit()
        db.refresh(student)
        db.refresh(course)
        
        return {"success": True, "message": "Course deselected successfully"}

    return router

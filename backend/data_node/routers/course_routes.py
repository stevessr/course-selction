"""Course management routes for Data Node"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Callable
from datetime import datetime, timezone

from backend.common import (
    Course, StudentCourseData, TeacherCourseData,
    CourseCreate, CourseUpdate, CourseResponse,
)


def create_course_router(get_db: Callable, verify_internal_token: Callable) -> APIRouter:
    """
    Factory function to create course router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_internal_token: Internal token verification dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/add/course", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
    async def add_course(
        course: CourseCreate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Add a new course"""
        # Check if teacher exists (if not, still allow course creation for flexibility in tests)
        teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == course.course_teacher_id).first()

        # Create course
        db_course = Course(**course.model_dump(), course_selected=[], course_selected_count=0)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)

        # Update teacher's courses if teacher exists
        if teacher:
            teacher_courses = teacher.teacher_courses or []
            if db_course.course_id not in teacher_courses:
                teacher_courses.append(db_course.course_id)
                teacher.teacher_courses = teacher_courses
                db.commit()

        # Calculate course_left and add it as an attribute for response
        # Use course_selected_count for calculation
        db_course.course_left = db_course.course_capacity - db_course.course_selected_count
        # Set course_selected to count for API response (schema expects int)
        db_course.course_selected = db_course.course_selected_count
        return db_course

    @router.get("/courses", response_model=List[CourseResponse])
    async def list_courses(
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """List all courses"""
        courses = db.query(Course).all()
        for c in courses:
            c.course_left = c.course_capacity - c.course_selected_count
            c.course_selected = c.course_selected_count  # Set to count for response
        return courses

    @router.post("/update/course", response_model=CourseResponse)
    async def update_course(
        course_id: int,
        course: CourseUpdate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Update course information"""
        db_course = db.query(Course).filter(Course.course_id == course_id).first()
        if not db_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Update fields
        update_data = course.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_course, field, value)
        
        db_course.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_course)
        
        db_course.course_left = db_course.course_capacity - db_course.course_selected_count
        db_course.course_selected = db_course.course_selected_count  # Set to count for response
        return db_course

    @router.post("/delete/course")
    async def delete_course(
        course_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Delete a course"""
        db_course = db.query(Course).filter(Course.course_id == course_id).first()
        if not db_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Remove from teacher's courses
        teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == db_course.course_teacher_id).first()
        if teacher and teacher.teacher_courses:
            teacher_courses = teacher.teacher_courses
            if course_id in teacher_courses:
                teacher_courses.remove(course_id)
                teacher.teacher_courses = teacher_courses

        # Remove from students' courses
        students = db.query(StudentCourseData).all()
        for student in students:
            if student.student_courses and course_id in student.student_courses:
                student_courses = student.student_courses
                student_courses.remove(course_id)
                student.student_courses = student_courses
        
        db.delete(db_course)
        db.commit()
        return {"success": True, "message": "Course deleted successfully"}

    @router.post("/bulk/import/courses")
    async def bulk_import_courses(
        courses_data: List[CourseCreate],
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Bulk import courses"""
        imported = []
        errors = []
        
        for idx, course_data in enumerate(courses_data):
            try:
                # Check if course with same name already exists
                existing = db.query(Course).filter(Course.course_name == course_data.course_name).first()
                if existing:
                    errors.append({
                        "index": idx,
                        "course_name": course_data.course_name,
                        "error": "Course with this name already exists"
                    })
                    continue
                
                # Create new course
                db_course = Course(
                    course_name=course_data.course_name,
                    course_credit=course_data.course_credit,
                    course_type=course_data.course_type,
                    course_location=course_data.course_location,
                    course_capacity=course_data.course_capacity,
                    course_selected=[],
                    course_selected_count=0,
                    course_time_begin=course_data.course_time_begin,
                    course_time_end=course_data.course_time_end,
                    course_teacher_id=course_data.course_teacher_id if hasattr(course_data, 'course_teacher_id') else None,
                    course_tags=course_data.course_tags if hasattr(course_data, 'course_tags') else [],
                    course_notes=course_data.course_notes if hasattr(course_data, 'course_notes') else None,
                    course_cost=course_data.course_cost if hasattr(course_data, 'course_cost') else 0,
                )
                db.add(db_course)
                db.commit()
                db.refresh(db_course)
                imported.append({
                    "course_id": db_course.course_id,
                    "course_name": db_course.course_name
                })
            except Exception as e:
                errors.append({
                    "index": idx,
                    "course_name": course_data.course_name if hasattr(course_data, 'course_name') else f"Course {idx}",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "imported_count": len(imported),
            "error_count": len(errors),
            "imported": imported,
            "errors": errors
        }

    @router.get("/get/course", response_model=CourseResponse)
    async def get_course(
        course_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Get course information"""
        db_course = db.query(Course).filter(Course.course_id == course_id).first()
        if not db_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        db_course.course_left = db_course.course_capacity - db_course.course_selected_count
        db_course.course_selected = db_course.course_selected_count  # Set to count for response
        return db_course

    @router.get("/get/courses")
    async def get_courses(
        teacher_id: Optional[int] = None,
        course_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Get list of courses with optional filters"""
        query = db.query(Course)
        
        if teacher_id:
            query = query.filter(Course.course_teacher_id == teacher_id)
        
        if course_type:
            query = query.filter(Course.course_type == course_type)
        
        if search:
            # Search in course name, location, and notes
            search_pattern = f"%{search}%"
            query = query.filter(
                (Course.course_name.ilike(search_pattern)) |
                (Course.course_location.ilike(search_pattern)) |
                (Course.course_notes.ilike(search_pattern))
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        courses = query.offset(offset).limit(page_size).all()
        
        result = []
        for course in courses:
            course.course_left = course.course_capacity - course.course_selected_count
            course.course_selected = course.course_selected_count  # Set to count for response
            result.append(course)
        
        return {"courses": result, "total": total}

    @router.get("/get/course/students")
    async def get_course_students(
        course_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Get list of students enrolled in a specific course"""
        # Get all students
        students = db.query(StudentCourseData).all()
        
        # Filter students who have selected this course
        enrolled_students = []
        for student in students:
            if course_id in student.student_courses:
                enrolled_students.append({
                    "student_id": student.student_id,
                    "name": student.student_name,
                    "user_id": student.student_id
                })
        
        return {
            "students": enrolled_students,
            "total": len(enrolled_students)
        }

    return router

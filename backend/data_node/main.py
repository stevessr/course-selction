"""Data Node - Course data management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime, timezone
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables: root .env first, then service-level .env overrides
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).with_name('.env'), override=True)

from backend.common import (
    DataBase, Course, StudentCourseData, TeacherCourseData, AvailableTag,
    CourseCreate, CourseUpdate, CourseResponse,
    StudentCreate, StudentResponse,
    TeacherCreate, TeacherResponse,
    CourseSelectionData,
    get_database_url, create_db_engine, create_session_factory, init_database,
    create_socket_server_config,
)

# Configuration
DATABASE_URL = get_database_url("course_data.db")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
PORT = int(os.getenv("PORT", "8001"))

# Database setup
engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)
init_database(engine, DataBase)

# FastAPI app
app = FastAPI(title="Course Data Node", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_internal_token_header(
    internal_token: str = Header(..., alias="Internal-Token")
):
    """Verify internal service token"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal token"
        )


# Course endpoints
@app.post("/add/course", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def add_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """List all courses"""
    courses = db.query(Course).all()
    for c in courses:
        c.course_left = c.course_capacity - c.course_selected_count
        c.course_selected = c.course_selected_count  # Set to count for response
    return courses


@app.post("/update/course", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course: CourseUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.post("/delete/course")
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.post("/bulk/import/courses")
async def bulk_import_courses(
    courses_data: List[CourseCreate],
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.get("/get/course", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Get course information"""
    db_course = db.query(Course).filter(Course.course_id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_course.course_left = db_course.course_capacity - db_course.course_selected_count
    db_course.course_selected = db_course.course_selected_count  # Set to count for response
    return db_course


@app.get("/get/courses")
async def get_courses(
    teacher_id: Optional[int] = None,
    course_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.get("/get/course/students")
async def get_course_students(
    course_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


# Student endpoints
@app.post("/add/student", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add a new student"""
    # Check if student already exists
    existing = db.query(StudentCourseData).filter(StudentCourseData.student_name == student.student_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")

    db_student = StudentCourseData(student_name=student.student_name, student_courses=[], student_tags=student.student_tags)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student





@app.post("/update/student", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_name: Optional[str] = None,
    student_tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.post("/delete/student")
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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


@app.get("/get/student", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Get student information"""
    db_student = db.query(StudentCourseData).filter(StudentCourseData.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


# Teacher endpoints
@app.post("/add/teacher", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def add_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add a new teacher"""
    existing = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_name == teacher.teacher_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher already exists")

    db_teacher = TeacherCourseData(teacher_name=teacher.teacher_name, teacher_courses=[])
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


@app.post("/update/teacher", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_name: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Update teacher information"""
    db_teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    db_teacher.teacher_name = teacher_name
    db_teacher.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


@app.post("/delete/teacher")
async def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Delete a teacher"""
    db_teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Check if teacher has courses
    if db_teacher.teacher_courses:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete teacher with assigned courses"
        )

    db.delete(db_teacher)
    db.commit()
    return {"success": True, "message": "Teacher deleted successfully"}


@app.get("/get/teacher", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Get teacher information"""
    db_teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_teacher


# Course selection endpoints
@app.post("/select/course")
async def select_course(
    selection: CourseSelectionData,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(student, "student_courses")
    flag_modified(course, "course_selected")
    
    db.commit()
    db.refresh(student)
    db.refresh(course)
    
    return {"success": True, "message": "Course selected successfully"}


@app.post("/deselect/course")
async def deselect_course(
    selection: CourseSelectionData,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
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
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(student, "student_courses")
    flag_modified(course, "course_selected")
    
    db.commit()
    db.refresh(student)
    db.refresh(course)
    
    return {"success": True, "message": "Course deselected successfully"}


# Available tags endpoints
@app.get("/tags/available")
async def get_available_tags(
    tag_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Get list of available tags for auto-completion"""
    query = db.query(AvailableTag)
    if tag_type:
        query = query.filter(AvailableTag.tag_type == tag_type)
    tags = query.order_by(AvailableTag.usage_count.desc(), AvailableTag.tag_name).all()
    return {
        "tags": [
            {
                "tag_name": tag.tag_name,
                "tag_type": tag.tag_type,
                "usage_count": tag.usage_count
            }
            for tag in tags
        ]
    }


@app.post("/tags/add")
async def add_available_tag(
    tag_name: str,
    tag_type: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add or update an available tag"""
    if tag_type not in ['user', 'course']:
        raise HTTPException(status_code=400, detail="tag_type must be 'user' or 'course'")
    
    # Check if tag already exists
    existing = db.query(AvailableTag).filter(
        AvailableTag.tag_name == tag_name,
        AvailableTag.tag_type == tag_type
    ).first()
    
    if existing:
        existing.usage_count += 1
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"success": True, "message": "Tag usage count incremented"}
    
    # Create new tag
    new_tag = AvailableTag(
        tag_name=tag_name,
        tag_type=tag_type,
        usage_count=1
    )
    db.add(new_tag)
    db.commit()
    return {"success": True, "message": "Tag added successfully"}


@app.post("/tags/sync")
async def sync_available_tags(
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Sync available tags from existing courses and students"""
    # Get all unique tags from courses
    courses = db.query(Course).all()
    course_tags = set()
    for course in courses:
        if course.course_tags:
            course_tags.update(course.course_tags)
    
    # Get all unique tags from students
    students = db.query(StudentCourseData).all()
    student_tags = set()
    for student in students:
        if student.student_tags:
            student_tags.update(student.student_tags)
    
    # Add or update course tags
    for tag_name in course_tags:
        existing = db.query(AvailableTag).filter(
            AvailableTag.tag_name == tag_name,
            AvailableTag.tag_type == 'course'
        ).first()
        
        if not existing:
            new_tag = AvailableTag(tag_name=tag_name, tag_type='course', usage_count=1)
            db.add(new_tag)
    
    # Add or update user tags
    for tag_name in student_tags:
        existing = db.query(AvailableTag).filter(
            AvailableTag.tag_name == tag_name,
            AvailableTag.tag_type == 'user'
        ).first()
        
        if not existing:
            new_tag = AvailableTag(tag_name=tag_name, tag_type='user', usage_count=1)
            db.add(new_tag)
    
    db.commit()
    return {
        "success": True,
        "message": "Tags synced successfully",
        "course_tags_count": len(course_tags),
        "user_tags_count": len(student_tags)
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data_node"}


if __name__ == "__main__":
    import uvicorn
    # Get socket or HTTP config based on environment
    config = create_socket_server_config('data_node', PORT)
    uvicorn.run(app, **config)

"""Data Node - Course data management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime, timezone
from pydantic import BaseModel

from backend.common import (
    DataBase, Course, Student, Teacher,
    CourseCreate, CourseUpdate, CourseResponse,
    StudentCreate, StudentResponse,
    TeacherCreate, TeacherResponse,
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
    # Check if teacher exists
    teacher = db.query(Teacher).filter(Teacher.teacher_id == course.course_teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Create course
    db_course = Course(**course.model_dump(), course_selected=0)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    # Update teacher's courses
    teacher_courses = teacher.teacher_courses or []
    if db_course.course_id not in teacher_courses:
        teacher_courses.append(db_course.course_id)
        teacher.teacher_courses = teacher_courses
        db.commit()
    
    # Calculate course_left
    course_dict = {
        **db_course.__dict__,
        "course_left": db_course.course_capacity - db_course.course_selected
    }
    return course_dict


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
    
    course_dict = {
        **db_course.__dict__,
        "course_left": db_course.course_capacity - db_course.course_selected
    }
    return course_dict


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
    teacher = db.query(Teacher).filter(Teacher.teacher_id == db_course.course_teacher_id).first()
    if teacher and teacher.teacher_courses:
        teacher_courses = teacher.teacher_courses
        if course_id in teacher_courses:
            teacher_courses.remove(course_id)
            teacher.teacher_courses = teacher_courses
    
    # Remove from students' courses
    students = db.query(Student).all()
    for student in students:
        if student.student_courses and course_id in student.student_courses:
            student_courses = student.student_courses
            student_courses.remove(course_id)
            student.student_courses = student_courses
    
    db.delete(db_course)
    db.commit()
    return {"success": True, "message": "Course deleted successfully"}


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
    
    course_dict = {
        **db_course.__dict__,
        "course_left": db_course.course_capacity - db_course.course_selected
    }
    return course_dict


@app.get("/get/courses")
async def get_courses(
    teacher_id: Optional[int] = None,
    course_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Get list of courses with optional filters"""
    query = db.query(Course)
    
    if teacher_id:
        query = query.filter(Course.course_teacher_id == teacher_id)
    
    if course_type:
        query = query.filter(Course.course_type == course_type)
    
    courses = query.all()
    
    result = []
    for course in courses:
        course_dict = {
            **course.__dict__,
            "course_left": course.course_capacity - course.course_selected
        }
        result.append(course_dict)
    
    return {"courses": result, "total": len(result)}


# Student endpoints
@app.post("/add/student", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add a new student"""
    # Check if student already exists
    existing = db.query(Student).filter(Student.student_name == student.student_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    db_student = Student(student_name=student.student_name, student_courses=[])
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


# Extended student endpoints for registration with auth details
class StudentWithAuth(BaseModel):
    """Student model with authentication details - for internal use only"""
    username: str
    password_hash: str
    student_name: str
    totp_secret: Optional[str] = None
    is_active: bool = True
    student_courses: List[int] = []
    student_tags: List[str] = []


@app.post("/add/student-with-auth", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student_with_auth(
    student_data: StudentWithAuth,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add a new student with authentication details (internal use only)"""
    # Check if student already exists by username
    existing = db.query(Student).filter(
        (Student.username == student_data.username) |
        (Student.student_name == student_data.student_name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    db_student = Student(
        username=student_data.username,
        password_hash=student_data.password_hash,
        student_name=student_data.student_name,
        totp_secret=student_data.totp_secret,
        is_active=student_data.is_active,
        student_courses=student_data.student_courses,
        student_tags=student_data.student_tags
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@app.post("/update/student", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_name: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Update student information"""
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db_student.student_name = student_name
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
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Remove student from courses
    for course_id in db_student.student_courses or []:
        course = db.query(Course).filter(Course.course_id == course_id).first()
        if course:
            course.course_selected = max(0, course.course_selected - 1)
    
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
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
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
    existing = db.query(Teacher).filter(Teacher.teacher_name == teacher.teacher_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher already exists")
    
    db_teacher = Teacher(teacher_name=teacher.teacher_name, teacher_courses=[])
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


# Extended teacher endpoint for registration with auth details
class TeacherWithAuth(BaseModel):
    """Teacher model with authentication details - for internal use only"""
    username: str
    password_hash: str
    teacher_name: str
    is_active: bool = True
    teacher_courses: List[int] = []


@app.post("/add/teacher-with-auth", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def add_teacher_with_auth(
    teacher_data: TeacherWithAuth,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Add a new teacher with authentication details (internal use only)"""
    # Check if teacher already exists by username
    existing = db.query(Teacher).filter(
        (Teacher.username == teacher_data.username) |
        (Teacher.teacher_name == teacher_data.teacher_name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher already exists")
    
    db_teacher = Teacher(
        username=teacher_data.username,
        password_hash=teacher_data.password_hash,
        teacher_name=teacher_data.teacher_name,
        is_active=teacher_data.is_active,
        teacher_courses=teacher_data.teacher_courses
    )
    
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
    db_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
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
    db_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
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
    db_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_teacher


# Course selection endpoints
@app.post("/select/course")
async def select_course(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Student selects a course"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course is full
    if course.course_selected >= course.course_capacity:
        raise HTTPException(status_code=400, detail="Course is full")
    
    # Check if student already selected this course
    student_courses = student.student_courses or []
    if course_id in student_courses:
        raise HTTPException(status_code=400, detail="Student already selected this course")
    
    # Add course to student
    student_courses.append(course_id)
    student.student_courses = student_courses
    student.updated_at = datetime.now(timezone.utc)
    
    # Increment course selection count
    course.course_selected += 1
    course.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"success": True, "message": "Course selected successfully"}


@app.post("/deselect/course")
async def deselect_course(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """Student deselects a course"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if student has selected this course
    student_courses = student.student_courses or []
    if course_id not in student_courses:
        raise HTTPException(status_code=400, detail="Student has not selected this course")
    
    # Remove course from student
    student_courses.remove(course_id)
    student.student_courses = student_courses
    student.updated_at = datetime.now(timezone.utc)
    
    # Decrement course selection count
    course.course_selected = max(0, course.course_selected - 1)
    course.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"success": True, "message": "Course deselected successfully"}


@app.get("/data/users")
async def list_users(
    user_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token_header)
):
    """List users (students or teachers) - used by auth node admin panel"""
    users = []
    total = 0
    
    if user_type == "student" or user_type is None:
        # Query students
        query = db.query(Student)
        if search:
            query = query.filter(Student.username.contains(search))
        total = query.count()
        
        # Apply pagination
        students = query.order_by(Student.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        for student in students:
            users.append({
                "user_id": student.student_id,
                "username": student.username,
                "user_type": "student",
                "is_active": student.is_active,
                "totp_secret": student.totp_secret,
                "created_at": student.created_at.isoformat() if student.created_at else None,
                "updated_at": student.updated_at.isoformat() if student.updated_at else None,
            })
    
    elif user_type == "teacher":
        # Query teachers
        query = db.query(Teacher)
        if search:
            query = query.filter(Teacher.username.contains(search))
        total = query.count()
        
        # Apply pagination
        teachers = query.order_by(Teacher.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        for teacher in teachers:
            users.append({
                "user_id": teacher.teacher_id,
                "username": teacher.username,
                "user_type": "teacher",
                "is_active": teacher.is_active,
                "totp_secret": None,  # Teachers don't have 2FA
                "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
            })
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size
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

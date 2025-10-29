from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx
from ..database import Course, Student, Teacher, SessionLocal, engine
from ..settings import settings
from ..utils import verify_token
from ..node_manager import node_manager, verify_protection_token


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class TeacherCoursesResponse(BaseModel):
    courses: List[Dict[str, Any]]

class CourseDetailResponse(BaseModel):
    course_id: int
    course_name: str
    course_credit: int
    course_type: str
    course_time_begin: int
    course_time_end: int
    course_location: str
    course_capacity: int
    course_selected: int
    course_left: int
    students: List[Dict[str, Any]]

class CourseStudentsResponse(BaseModel):
    students: List[Dict[str, Any]]

class UpdateCourseRequest(BaseModel):
    course_id: int
    course_name: Optional[str] = None
    course_credit: Optional[int] = None
    course_type: Optional[str] = None
    course_time_begin: Optional[int] = None
    course_time_end: Optional[int] = None
    course_location: Optional[str] = None
    course_capacity: Optional[int] = None

class UpdateCourseResponse(BaseModel):
    success: bool
    message: str

class CreateCourseRequest(BaseModel):
    course_name: str
    course_credit: int
    course_type: str
    course_time_begin: int
    course_time_end: int
    course_location: str
    course_capacity: int

class CreateCourseResponse(BaseModel):
    success: bool
    course_id: int
    message: str

class DeleteCourseRequest(BaseModel):
    course_id: int

class DeleteCourseResponse(BaseModel):
    success: bool
    message: str

class RemoveStudentRequest(BaseModel):
    course_id: int
    student_id: int

class RemoveStudentResponse(BaseModel):
    success: bool
    message: str

class TeacherStatsResponse(BaseModel):
    total_courses: int
    total_students: int
    courses_by_type: Dict[str, int]


# Initialize the app
app = FastAPI(title="Teacher Processing Node", version="1.0.0")

# Add startup event to initialize node manager
@app.on_event("startup")
async def startup_event():
    from ..node_manager import initialize_node
    await initialize_node()

# Create tables
from ..database import Base
Base.metadata.create_all(bind=engine)


async def verify_teacher_token(access_token: str):
    """Verify teacher access token with the login node"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # In a real implementation, we would call the login node to verify the token
    # For now, we'll use the local verification function
    user_id = verify_token(access_token, credentials_exception)
    
    # Verify that the user is a teacher
    # In a real implementation, we would verify this via the login service
    # For now, we'll just check that it's a teacher token
    if not user_id.startswith("teacher_"):
        raise credentials_exception
    
    return user_id


@app.post("/teacher/courses")
async def get_teacher_courses(request: Request, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    teacher_id = await verify_teacher_token(access_token)
    # Extract teacher_id from token (in a real implementation)
    # For now we'll use a placeholder
    teacher_id_num = 1  # Placeholder - would be extracted from token
    
    # Get courses taught by this teacher
    courses = db.query(Course).filter(Course.course_teacher_id == teacher_id_num).all()
    
    result = []
    for course in courses:
        course_left = course.course_capacity - course.course_selected
        result.append({
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_credit": course.course_credit,
            "course_type": course.course_type,
            "course_time_begin": course.course_time_begin,
            "course_time_end": course.course_time_end,
            "course_location": course.course_location,
            "course_capacity": course.course_capacity,
            "course_selected": course.course_selected,
            "course_left": course_left
        })
    
    return TeacherCoursesResponse(courses=result)


@app.post("/teacher/course/detail")
async def get_course_detail(request: Request, course_id: int, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # In a real implementation, we would also verify that this teacher teaches this course
    # For now, we assume they do
    
    # Calculate course_left
    course_left = course.course_capacity - course.course_selected
    
    # Get students enrolled in this course
    # This would require proper relationships in the database
    # For now, we'll return an empty list
    students = []
    
    return CourseDetailResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        course_credit=course.course_credit,
        course_type=course.course_type,
        course_time_begin=course.course_time_begin,
        course_time_end=course.course_time_end,
        course_location=course.course_location,
        course_capacity=course.course_capacity,
        course_selected=course.course_selected,
        course_left=course_left,
        students=students
    )


@app.post("/teacher/course/students")
async def get_course_students(request: Request, course_id: int, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # In a real implementation, we would get the list of students enrolled in this course
    # This would require proper relationships in the database
    # For now, we'll return an empty list
    students = []
    
    return CourseStudentsResponse(students=students)


@app.post("/teacher/course/update")
async def update_course(request: Request, update_request: UpdateCourseRequest, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == update_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # In a real implementation, we would verify that this teacher teaches this course
    # For now, we assume they do
    
    # Update only provided fields
    update_data = update_request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "course_id":  # Don't update the ID
            setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    return UpdateCourseResponse(success=True, message="Course updated successfully")


@app.post("/teacher/course/create")
async def create_course(request: Request, create_request: CreateCourseRequest, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # In a real implementation, we would extract teacher_id from the token
    # For now, we'll use a placeholder
    teacher_id = 1  # Placeholder - would be extracted from token
    
    # Create new course
    db_course = Course(
        course_name=create_request.course_name,
        course_credit=create_request.course_credit,
        course_type=create_request.course_type,
        course_teacher_id=teacher_id,
        course_time_begin=create_request.course_time_begin,
        course_time_end=create_request.course_time_end,
        course_location=create_request.course_location,
        course_capacity=create_request.course_capacity,
        course_selected=0
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    return CreateCourseResponse(
        success=True,
        course_id=db_course.course_id,
        message="Course created successfully"
    )


@app.post("/teacher/course/delete")
async def delete_course(request: Request, delete_request: DeleteCourseRequest, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == delete_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # In a real implementation, we would verify that this teacher teaches this course
    # For now, we assume they do
    
    db.delete(course)
    db.commit()
    
    return DeleteCourseResponse(success=True, message="Course deleted successfully")


@app.post("/teacher/student/remove")
async def remove_student_from_course(
    request: Request,
    remove_request: RemoveStudentRequest,
    db: Session = Depends(get_db)
):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == remove_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # In a real implementation, we would verify that this teacher teaches this course
    # For now, we assume they do
    
    # Check if student is enrolled in the course
    # For now, we'll just decrement the selected count
    if course.course_selected > 0:
        course.course_selected -= 1
        db.commit()
    
    return RemoveStudentResponse(success=True, message="Student removed from course successfully")


@app.post("/teacher/stats")
async def get_teacher_stats(request: Request, db: Session = Depends(get_db)):
    # Verify teacher token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_teacher_token(access_token)
    
    # In a real implementation, we would extract teacher_id from the token
    # For now, we'll use a placeholder
    teacher_id = 1  # Placeholder - would be extracted from token
    
    # Get courses taught by this teacher
    courses = db.query(Course).filter(Course.course_teacher_id == teacher_id).all()
    
    total_courses = len(courses)
    
    # Calculate total students across all courses
    total_students = sum(course.course_selected for course in courses)
    
    # Calculate courses by type
    courses_by_type: Dict[str, int] = {}
    for course in courses:
        course_type = course.course_type
        if course_type in courses_by_type:
            courses_by_type[course_type] += 1
        else:
            courses_by_type[course_type] = 1
    
    return TeacherStatsResponse(
        total_courses=total_courses,
        total_students=total_students,
        courses_by_type=courses_by_type
    )
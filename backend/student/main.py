from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx
from ..database import Course, Student, SessionLocal, engine
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
class AvailableCoursesRequest(BaseModel):
    course_type: Optional[str] = None
    teacher_name: Optional[str] = None
    page: int = 1
    page_size: int = 20

class AvailableCoursesResponse(BaseModel):
    courses: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int

class SelectedCoursesResponse(BaseModel):
    courses: List[Dict[str, Any]]
    total_credit: int

class SelectCourseRequest(BaseModel):
    course_id: int

class SelectCourseResponse(BaseModel):
    success: bool
    message: str
    queue_id: str
    estimated_time: int

class DeselectCourseRequest(BaseModel):
    course_id: int

class DeselectCourseResponse(BaseModel):
    success: bool
    message: str
    queue_id: str

class CourseDetailRequest(BaseModel):
    course_id: int

class CourseDetailResponse(BaseModel):
    course_id: int
    course_name: str
    course_credit: int
    course_type: str
    teacher_name: str
    course_time_begin: int
    course_time_end: int
    course_location: str
    course_capacity: int
    course_selected: int
    course_left: int
    is_selected: bool

class ScheduleRequest(BaseModel):
    week: Optional[int] = None

class ScheduleResponse(BaseModel):
    schedule: Dict[int, List[Dict[str, Any]]]  # key: day of week (1-7)

class StudentStatsResponse(BaseModel):
    total_courses: int
    total_credit: int
    courses_by_type: Dict[str, int]
    credit_by_type: Dict[str, int]

class QueueStatusRequest(BaseModel):
    queue_id: str

class QueueStatusResponse(BaseModel):
    status: str  # pending, processing, completed, failed
    message: str
    created_at: int
    completed_at: Optional[int] = None

class CheckCourseRequest(BaseModel):
    course_id: int

class CheckCourseConflictResponse(BaseModel):
    can_select: bool
    conflicts: List[Dict[str, Any]]  # {type: str, message: str, course_id: Optional[int], course_name: Optional[str]}


# Initialize the app
app = FastAPI(title="Student Processing Node", version="1.0.0")

# Add startup event to initialize node manager
@app.on_event("startup")
async def startup_event():
    from ..node_manager import initialize_node
    await initialize_node()

# Create tables
from ..database import Base
Base.metadata.create_all(bind=engine)


async def verify_student_token(access_token: str):
    """Verify student access token with the login node"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # In a real implementation, we would call the login node to verify the token
    # For now, we'll use the local verification function
    user_id = verify_token(access_token, credentials_exception)
    
    # Verify that the user is a student
    # In a real implementation, we would verify this via the login service
    # For now, we'll just check that it's a student token
    if not user_id.startswith("student_"):
        raise credentials_exception
    
    return user_id


@app.post("/student/courses/available")
async def get_available_courses(
    request: Request,
    available_request: AvailableCoursesRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # Build query based on filters
    query = db.query(Course)
    
    if available_request.course_type:
        query = query.filter(Course.course_type == available_request.course_type)
    
    # Apply pagination
    offset = (available_request.page - 1) * available_request.page_size
    courses = query.offset(offset).limit(available_request.page_size).all()
    total = query.count()
    
    result = []
    for course in courses:
        course_left = course.course_capacity - course.course_selected
        # In a real implementation, we would get teacher name by joining with teacher table
        teacher_name = f"Teacher {course.course_teacher_id}"  # Placeholder
        result.append({
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_credit": course.course_credit,
            "course_type": course.course_type,
            "teacher_name": teacher_name,
            "course_time_begin": course.course_time_begin,
            "course_time_end": course.course_time_end,
            "course_location": course.course_location,
            "course_capacity": course.course_capacity,
            "course_selected": course.course_selected,
            "course_left": course_left
        })
    
    return AvailableCoursesResponse(
        courses=result,
        total=total,
        page=available_request.page,
        page_size=available_request.page_size
    )


@app.post("/student/courses/selected")
async def get_selected_courses(request: Request, db: Session = Depends(get_db)):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would get courses selected by this student
    # This would require proper relationships in the database
    # For now, we'll return an empty list
    courses = []
    total_credit = 0
    
    return SelectedCoursesResponse(
        courses=courses,
        total_credit=total_credit
    )


@app.post("/student/course/select")
async def select_course(
    request: Request,
    select_request: SelectCourseRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would submit the request to the queue node
    # For now, we'll return a simulated response
    import uuid
    from datetime import datetime
    queue_id = str(uuid.uuid4())
    
    # Check if course exists
    course = db.query(Course).filter(Course.course_id == select_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Submit to queue (placeholder)
    # In a real implementation, we would call the queue node API
    return SelectCourseResponse(
        success=True,
        message="Course selection request submitted to queue",
        queue_id=queue_id,
        estimated_time=30  # seconds
    )


@app.post("/student/course/deselect")
async def deselect_course(
    request: Request,
    deselect_request: DeselectCourseRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would submit the request to the queue node
    # For now, we'll return a simulated response
    import uuid
    queue_id = str(uuid.uuid4())
    
    # Check if course exists
    course = db.query(Course).filter(Course.course_id == deselect_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Submit to queue (placeholder)
    # In a real implementation, we would call the queue node API
    return DeselectCourseResponse(
        success=True,
        message="Course deselection request submitted to queue",
        queue_id=queue_id
    )


@app.post("/student/course/detail")
async def get_course_detail(
    request: Request,
    detail_request: CourseDetailRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == detail_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course_left = course.course_capacity - course.course_selected
    
    # Check if student has selected this course
    # In a real implementation, we would check the student-course relationship
    is_selected = False  # Placeholder
    
    # In a real implementation, we would get teacher name by joining with teacher table
    teacher_name = f"Teacher {course.course_teacher_id}"  # Placeholder
    
    return CourseDetailResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        course_credit=course.course_credit,
        course_type=course.course_type,
        teacher_name=teacher_name,
        course_time_begin=course.course_time_begin,
        course_time_end=course.course_time_end,
        course_location=course.course_location,
        course_capacity=course.course_capacity,
        course_selected=course.course_selected,
        course_left=course_left,
        is_selected=is_selected
    )


@app.post("/student/schedule")
async def get_schedule(request: Request, schedule_request: ScheduleRequest, db: Session = Depends(get_db)):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would get the student's schedule
    # This would require getting courses selected by the student and organizing by time
    # For now, we'll return an empty schedule
    
    schedule: Dict[int, List[Dict[str, Any]]] = {day: [] for day in range(1, 8)}  # 1-7 for Monday-Sunday
    
    return ScheduleResponse(schedule=schedule)


@app.post("/student/stats")
async def get_student_stats(request: Request, db: Session = Depends(get_db)):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would calculate student stats based on selected courses
    # For now, we'll return placeholder values
    total_courses = 0
    total_credit = 0
    courses_by_type: Dict[str, int] = {}
    credit_by_type: Dict[str, int] = {}
    
    return StudentStatsResponse(
        total_courses=total_courses,
        total_credit=total_credit,
        courses_by_type=courses_by_type,
        credit_by_type=credit_by_type
    )


@app.post("/student/queue/status")
async def get_queue_status(
    request: Request,
    status_request: QueueStatusRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # In a real implementation, we would call the queue node to get status
    # For now, we'll return a placeholder response
    return QueueStatusResponse(
        status="completed",  # placeholder
        message="Task completed successfully",
        created_at=0,  # placeholder
        completed_at=0  # placeholder
    )


@app.post("/student/course/check")
async def check_course_conflict(
    request: Request,
    check_request: CheckCourseRequest,
    db: Session = Depends(get_db)
):
    # Verify student token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    await verify_student_token(access_token)
    
    # Get the course to check
    course = db.query(Course).filter(Course.course_id == check_request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check for conflicts
    # For now we'll just check if the course is full
    course_left = course.course_capacity - course.course_selected
    conflicts = []
    
    if course_left <= 0:
        conflicts.append({
            "type": "course_full",
            "message": "Course is already full",
            "course_id": course.course_id,
            "course_name": course.course_name
        })
    
    # In a real implementation, we would check for time conflicts, credit limits, etc.
    # For now, we'll just return the course full check
    
    return CheckCourseConflictResponse(
        can_select=len(conflicts) == 0,
        conflicts=conflicts
    )
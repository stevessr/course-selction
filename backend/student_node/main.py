"""Student Service Node - Student course selection and management"""
from fastapi import FastAPI, HTTPException, Depends, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables: root .env first, then service-level .env overrides
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).with_name('.env'), override=True)

from backend.common import (
    CourseSelectionRequest,
    get_current_user_from_token, verify_user_type,
    call_service_api, get_request_headers, api_limiter,
    create_socket_server_config, SocketClient,
)

# Configuration
AUTH_NODE_URL = os.getenv("AUTH_NODE_URL", "http://localhost:8002")
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
QUEUE_NODE_URL = os.getenv("QUEUE_NODE_URL", "http://localhost:8005")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
PORT = int(os.getenv("PORT", "8004"))

# FastAPI app
app = FastAPI(title="Student Service Node", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies
async def get_current_student(
    request: Request,
    authorization: str = Header(..., alias="Authorization")
):
    """Verify student token and rate limit"""
    # Rate limiting
    headers = get_request_headers(request)
    if not api_limiter.check_rate_limit(headers):
        wait_time = api_limiter.get_wait_time(headers)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {int(wait_time)} seconds."
        )
    
    # Verify token
    token = authorization.replace("Bearer ", "")
    payload = await get_current_user_from_token(token)
    
    # Verify user type
    if not await verify_user_type(payload, ["student"]):
        raise HTTPException(status_code=403, detail="Student access required")
    
    return payload


# Student endpoints
@app.post("/student/courses/available")
async def get_available_courses(
    course_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get list of available courses"""
    student_id = current_user.get("user_id")
    
    # Get student data to check tags
    student_url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student_result = await call_service_api(
        student_url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    student_tags = set(student_result.get("student_tags", []))
    
    # Get all courses from data node
    url = f"{DATA_NODE_URL}/get/courses"
    if course_type:
        url += f"?course_type={course_type}"
    
    result = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    courses = result.get("courses", [])
    
    # Filter courses: student must have ALL course tags
    filtered_courses = []
    for course in courses:
        course_tags = set(course.get("course_tags", []))
        # If course has no tags or student has all required tags, include the course
        if not course_tags or course_tags.issubset(student_tags):
            filtered_courses.append(course)
    
    # Implement pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_courses = filtered_courses[start:end]
    
    return {
        "courses": paginated_courses,
        "total": len(filtered_courses),
        "page": page,
        "page_size": page_size
    }


@app.get("/student/courses/selected")
async def get_selected_courses(
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get list of courses the student has selected"""
    student_id = current_user.get("user_id")
    
    # Get student info from data node
    url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    student_courses = student.get("student_courses", [])
    
    # Get details for each course
    courses = []
    total_credit = 0
    
    for course_id in student_courses:
        try:
            url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
            course = await call_service_api(
                url,
                method="GET",
                headers={"Internal-Token": INTERNAL_TOKEN}
            )
            courses.append(course)
            total_credit += course.get("course_credit", 0)
        except:
            continue
    
    return {
        "courses": courses,
        "total_credit": total_credit
    }


@app.post("/student/course/select")
async def select_course(
    request: Request,
    selection: CourseSelectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Submit course selection request to queue"""
    student_id = current_user.get("user_id")
    
    # Check if course exists and has space
    url = f"{DATA_NODE_URL}/get/course?course_id={selection.course_id}"
    try:
        course = await call_service_api(
            url,
            method="GET",
            headers={"Internal-Token": INTERNAL_TOKEN}
        )
    except:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course is full
    if course.get("course_left", 0) <= 0:
        raise HTTPException(status_code=400, detail="Course is full")
    
    # Submit to queue
    headers = get_request_headers(request)
    url = f"{QUEUE_NODE_URL}/queue/submit"
    result = await call_service_api(
        url,
        method="POST",
        headers={
            "Internal-Token": INTERNAL_TOKEN,
            "X-Forwarded-For": headers.get("x-forwarded-for", ""),
            "X-Real-IP": headers.get("x-real-ip", "")
        },
        json_data={
            "student_id": student_id,
            "course_id": selection.course_id,
            "task_type": "select",
            "priority": 0
        }
    )
    
    return {
        "success": True,
        "message": "Course selection submitted to queue",
        "task_id": result.get("task_id"),
        "position": result.get("position"),
        "estimated_time": result.get("estimated_time")
    }


@app.post("/student/course/deselect")
async def deselect_course(
    request: Request,
    selection: CourseSelectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Submit course deselection request to queue"""
    student_id = current_user.get("user_id")
    
    # Submit to queue with higher priority (退课优先)
    headers = get_request_headers(request)
    url = f"{QUEUE_NODE_URL}/queue/submit"
    result = await call_service_api(
        url,
        method="POST",
        headers={
            "Internal-Token": INTERNAL_TOKEN,
            "X-Forwarded-For": headers.get("x-forwarded-for", ""),
            "X-Real-IP": headers.get("x-real-ip", "")
        },
        json_data={
            "student_id": student_id,
            "course_id": selection.course_id,
            "task_type": "deselect",
            "priority": 10  # Higher priority for deselection
        }
    )
    
    return {
        "success": True,
        "message": "Course deselection submitted to queue",
        "task_id": result.get("task_id"),
        "position": result.get("position"),
        "estimated_time": result.get("estimated_time")
    }


@app.post("/student/course/detail")
async def get_course_detail(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get detailed information about a course"""
    student_id = current_user.get("user_id")
    
    # Get course_id from request body
    body = await request.json()
    course_id = body.get("course_id")
    
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    
    # Get course info
    url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
    course = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Get student info to check if already selected
    url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    is_selected = course_id in student.get("student_courses", [])
    
    return {
        **course,
        "is_selected": is_selected
    }


@app.get("/student/schedule")
async def get_student_schedule(
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get student's course schedule"""
    student_id = current_user.get("user_id")
    
    # Get student's selected courses
    url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    student_courses = student.get("student_courses", [])
    
    # Get details for each course
    # Initialize schedule for all days (1=Monday, 7=Sunday)
    schedule = {}
    for i in range(1, 8):
        schedule[i] = []
    
    for course_id in student_courses:
        try:
            url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
            course = await call_service_api(
                url,
                method="GET",
                headers={"Internal-Token": INTERNAL_TOKEN}
            )
            
            # PLACEHOLDER: This is a simplified schedule mapping
            # In production, implement proper time slot handling based on course_time_begin/end
            # For now, map courses to days based on course_id modulo 7
            day = ((course.get("course_id", 0) - 1) % 7) + 1
            schedule[day].append({
                "course_id": course.get("course_id"),
                "course_name": course.get("course_name"),
                "course_time_begin": course.get("course_time_begin"),
                "course_time_end": course.get("course_time_end"),
                "course_location": course.get("course_location")
            })
        except:
            continue
    
    return {"schedule": schedule}


@app.get("/student/stats")
async def get_student_stats(
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get student's course statistics"""
    student_id = current_user.get("user_id")
    
    # Get student's selected courses
    url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    student_courses = student.get("student_courses", [])
    
    total_courses = len(student_courses)
    total_credit = 0
    courses_by_type = {}
    credit_by_type = {}
    
    for course_id in student_courses:
        try:
            url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
            course = await call_service_api(
                url,
                method="GET",
                headers={"Internal-Token": INTERNAL_TOKEN}
            )
            
            credit = course.get("course_credit", 0)
            course_type = course.get("course_type", "Unknown")
            
            total_credit += credit
            courses_by_type[course_type] = courses_by_type.get(course_type, 0) + 1
            credit_by_type[course_type] = credit_by_type.get(course_type, 0) + credit
        except:
            continue
    
    return {
        "total_courses": total_courses,
        "total_credit": total_credit,
        "courses_by_type": courses_by_type,
        "credit_by_type": credit_by_type
    }


@app.get("/student/queue/status")
async def get_queue_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Get status of a queue task"""
    url = f"{QUEUE_NODE_URL}/queue/status?task_id={task_id}"
    result = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    return result


@app.post("/student/course/check")
async def check_course_conflicts(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_student)
):
    """Check if student can select a course (conflicts, capacity, etc.)"""
    student_id = current_user.get("user_id")
    
    # Get course_id from request body
    body = await request.json()
    course_id = body.get("course_id")
    
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    
    conflicts = []
    can_select = True
    
    # Get course info
    try:
        url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
        course = await call_service_api(
            url,
            method="GET",
            headers={"Internal-Token": INTERNAL_TOKEN}
        )
    except:
        return {
            "can_select": False,
            "conflicts": [{"type": "not_found", "message": "Course not found"}]
        }
    
    # Check if course is full
    if course.get("course_left", 0) <= 0:
        can_select = False
        conflicts.append({
            "type": "course_full",
            "message": "Course is full"
        })
    
    # Get student's current courses
    url = f"{DATA_NODE_URL}/get/student?student_id={student_id}"
    student = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Check if already selected
    if course_id in student.get("student_courses", []):
        can_select = False
        conflicts.append({
            "type": "already_selected",
            "message": "Course already selected"
        })
    
    # Check for time conflicts
    # This is a simplified version - in production you'd have more sophisticated conflict detection
    for existing_course_id in student.get("student_courses", []):
        try:
            url = f"{DATA_NODE_URL}/get/course?course_id={existing_course_id}"
            existing_course = await call_service_api(
                url,
                method="GET",
                headers={"Internal-Token": INTERNAL_TOKEN}
            )
            
            # Simple time conflict check
            if (course.get("course_time_begin") <= existing_course.get("course_time_end") and
                course.get("course_time_end") >= existing_course.get("course_time_begin")):
                can_select = False
                conflicts.append({
                    "type": "time_conflict",
                    "message": f"Time conflict with {existing_course.get('course_name')}",
                    "course_id": existing_course_id,
                    "course_name": existing_course.get("course_name")
                })
        except:
            continue
    
    return {
        "can_select": can_select,
        "conflicts": conflicts
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "student_node"}


if __name__ == "__main__":
    import uvicorn
    # Get socket or HTTP config based on environment
    config = create_socket_server_config('student_node', PORT)
    uvicorn.run(app, **config)

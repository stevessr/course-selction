"""Teacher Service Node - Teacher course management"""
from fastapi import FastAPI, HTTPException, Depends, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import httpx

from backend.common import (
    CourseCreate, CourseUpdate,
    get_current_user_from_token, verify_user_type,
    call_service_api, get_request_headers, api_limiter,
)

# Configuration
AUTH_NODE_URL = os.getenv("AUTH_NODE_URL", "http://localhost:8002")
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
PORT = int(os.getenv("PORT", "8003"))

# FastAPI app
app = FastAPI(title="Teacher Service Node", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies
async def get_current_teacher(
    request: Request,
    authorization: str = Header(..., alias="Authorization")
):
    """Verify teacher token and rate limit"""
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
    if not await verify_user_type(payload, ["teacher", "admin"]):
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    
    return payload


# Teacher endpoints
@app.get("/teacher/courses")
async def get_teacher_courses(
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Get all courses for the current teacher"""
    teacher_id = current_user.get("user_id")
    
    # Call data node to get teacher's courses
    url = f"{DATA_NODE_URL}/get/courses?teacher_id={teacher_id}"
    result = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    return result


@app.post("/teacher/course/detail")
async def get_course_detail(
    course_id: int,
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Get detailed information about a specific course"""
    # Get course info
    url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
    course = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Verify teacher owns this course (unless admin)
    if current_user.get("user_type") != "admin":
        if course["course_teacher_id"] != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to view this course")
    
    # Get students enrolled in this course
    # We need to query all students and filter by course
    # This is a simplified version - in production, you'd want a more efficient query
    students = []
    
    return {
        **course,
        "students": students
    }


@app.post("/teacher/course/create")
async def create_course(
    course_data: CourseCreate,
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Create a new course"""
    teacher_id = current_user.get("user_id")
    
    # Set teacher_id to current user (unless admin specifies otherwise)
    if current_user.get("user_type") != "admin":
        course_data.course_teacher_id = teacher_id
    
    # Call data node to create course
    url = f"{DATA_NODE_URL}/add/course"
    result = await call_service_api(
        url,
        method="POST",
        headers={"Internal-Token": INTERNAL_TOKEN},
        json_data=course_data.model_dump()
    )
    
    return {
        "success": True,
        "course_id": result.get("course_id"),
        "message": "Course created successfully"
    }


@app.put("/teacher/course/update")
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Update course information"""
    # Get course to verify ownership
    url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
    course = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Verify teacher owns this course (unless admin)
    if current_user.get("user_type") != "admin":
        if course["course_teacher_id"] != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to update this course")
    
    # Call data node to update course
    url = f"{DATA_NODE_URL}/update/course?course_id={course_id}"
    await call_service_api(
        url,
        method="POST",
        headers={"Internal-Token": INTERNAL_TOKEN},
        json_data=course_data.model_dump(exclude_unset=True)
    )
    
    return {
        "success": True,
        "message": "Course updated successfully"
    }


@app.delete("/teacher/course/delete")
async def delete_course(
    course_id: int,
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Delete a course"""
    # Get course to verify ownership
    url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
    course = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Verify teacher owns this course (unless admin)
    if current_user.get("user_type") != "admin":
        if course["course_teacher_id"] != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to delete this course")
    
    # Call data node to delete course
    url = f"{DATA_NODE_URL}/delete/course?course_id={course_id}"
    await call_service_api(
        url,
        method="POST",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    return {
        "success": True,
        "message": "Course deleted successfully"
    }


@app.post("/teacher/student/remove")
async def remove_student_from_course(
    course_id: int,
    student_id: int,
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Remove a student from a course"""
    # Get course to verify ownership
    url = f"{DATA_NODE_URL}/get/course?course_id={course_id}"
    course = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    # Verify teacher owns this course (unless admin)
    if current_user.get("user_type") != "admin":
        if course["course_teacher_id"] != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to modify this course")
    
    # Call data node to deselect course for student
    url = f"{DATA_NODE_URL}/deselect/course"
    await call_service_api(
        url,
        method="POST",
        headers={"Internal-Token": INTERNAL_TOKEN},
        json_data={"student_id": student_id, "course_id": course_id}
    )
    
    return {
        "success": True,
        "message": "Student removed from course successfully"
    }


@app.get("/teacher/stats")
async def get_teacher_stats(
    current_user: Dict[str, Any] = Depends(get_current_teacher)
):
    """Get statistics for the current teacher"""
    teacher_id = current_user.get("user_id")
    
    # Get teacher's courses
    url = f"{DATA_NODE_URL}/get/courses?teacher_id={teacher_id}"
    result = await call_service_api(
        url,
        method="GET",
        headers={"Internal-Token": INTERNAL_TOKEN}
    )
    
    courses = result.get("courses", [])
    total_courses = len(courses)
    total_students = sum(course.get("course_selected", 0) for course in courses)
    
    # Count courses by type
    courses_by_type = {}
    for course in courses:
        course_type = course.get("course_type", "Unknown")
        courses_by_type[course_type] = courses_by_type.get(course_type, 0) + 1
    
    return {
        "total_courses": total_courses,
        "total_students": total_students,
        "courses_by_type": courses_by_type
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "teacher_node"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

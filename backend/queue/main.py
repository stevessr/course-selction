from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import redis
import uuid
from datetime import datetime
from ..database import QueueTask, SessionLocal, engine
from ..settings import settings
from ..node_manager import node_manager, verify_protection_token


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class QueueSubmitRequest(BaseModel):
    student_id: int
    course_id: int
    task_type: str  # 'select' or 'deselect'
    priority: int = 0

class QueueSubmitResponse(BaseModel):
    success: bool
    task_id: str
    position: int
    estimated_time: int

class QueueStatusRequest(BaseModel):
    task_id: str

class QueueStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: int
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    position: Optional[int] = None

class QueueCancelRequest(BaseModel):
    task_id: str
    student_id: int

class QueueCancelResponse(BaseModel):
    success: bool
    message: str

class QueueStatsResponse(BaseModel):
    pending_tasks: int
    processing_tasks: int
    completed_tasks_today: int
    failed_tasks_today: int
    average_processing_time: float
    queue_length: int

class StudentTasksRequest(BaseModel):
    student_id: int
    status: Optional[str] = None
    limit: int = 10

class StudentTasksResponse(BaseModel):
    tasks: List[Dict[str, Any]]

class QueuePriorityUpdateRequest(BaseModel):
    task_id: str
    priority: int

class QueuePriorityUpdateResponse(BaseModel):
    success: bool
    message: str

class QueueRetryRequest(BaseModel):
    task_id: str

class QueueRetryResponse(BaseModel):
    success: bool
    message: str
    new_task_id: Optional[str] = None


# Initialize the app
app = FastAPI(title="Queue Buffer Node", version="1.0.0")

# Add startup event to initialize node manager
@app.on_event("startup")
async def startup_event():
    from ..node_manager import initialize_node
    await initialize_node()

# Create tables
from ..database import Base
Base.metadata.create_all(bind=engine)

# Initialize Redis connection
redis_client = redis.Redis.from_url(settings.redis_url)


def verify_internal_token(internal_token: str):
    """Verify internal service token"""
    # In a real implementation, this would validate the internal token
    # For now, we'll just check if it matches a predefined value
    if internal_token != "internal_service_token":  # This should be in settings
        raise HTTPException(status_code=401, detail="Invalid internal token")


def verify_admin_token(admin_token: str):
    """Verify admin token"""
    # In a real implementation, this would validate the admin token
    # For now, we'll just check if it's provided
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")


@app.post("/queue/submit")
def submit_to_queue(
    request: Request,
    queue_request: QueueSubmitRequest,
    db: Session = Depends(get_db)
):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Validate task type
    if queue_request.task_type not in ["select", "deselect"]:
        raise HTTPException(status_code=400, detail="Invalid task type, must be 'select' or 'deselect'")
    
    # Create new task
    task_id = str(uuid.uuid4())
    db_task = QueueTask(
        task_id=task_id,
        student_id=queue_request.student_id,
        course_id=queue_request.course_id,
        task_type=queue_request.task_type,
        priority=queue_request.priority
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Add to Redis queue
    # In a real implementation, we would add to the proper queue based on priority
    redis_client.lpush("course_selection_queue", task_id)
    
    # Calculate position in queue (approximate)
    position = redis_client.llen("course_selection_queue")
    
    return QueueSubmitResponse(
        success=True,
        task_id=task_id,
        position=position,
        estimated_time=position * 5  # 5 seconds per task as estimate
    )


@app.post("/queue/status")
def get_queue_status(
    request: Request,
    status_request: QueueStatusRequest,
    db: Session = Depends(get_db)
):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Get task from database
    task = db.query(QueueTask).filter(QueueTask.task_id == status_request.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Calculate position in queue if still pending
    position = None
    if task.status == "pending":
        # This is an approximation - in reality, this would be more complex
        all_pending = db.query(QueueTask).filter(QueueTask.status == "pending").count()
        position = all_pending  # This is a simplification
    
    return QueueStatusResponse(
        task_id=task.task_id,
        status=task.status,
        message=f"Task is {task.status}",
        created_at=int(task.created_at.timestamp()) if task.created_at else 0,
        started_at=int(task.started_at.timestamp()) if task.started_at else None,
        completed_at=int(task.completed_at.timestamp()) if task.completed_at else None,
        position=position
    )


@app.post("/queue/cancel")
def cancel_queue_task(
    request: Request,
    cancel_request: QueueCancelRequest,
    db: Session = Depends(get_db)
):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Get task from database
    task = db.query(QueueTask).filter(
        QueueTask.task_id == cancel_request.task_id,
        QueueTask.student_id == cancel_request.student_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
    
    # Update task status
    task.status = "failed"
    task.error_message = "Cancelled by user"
    db.commit()
    
    # Remove from Redis queue if it's still there
    # This is simplified - in reality, removing from a Redis list by value can be inefficient
    redis_client.lrem("course_selection_queue", 0, cancel_request.task_id)
    
    return QueueCancelResponse(
        success=True,
        message="Task cancelled successfully"
    )


@app.post("/queue/stats")
def get_queue_stats(request: Request, db: Session = Depends(get_db)):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Get stats from database
    pending_tasks = db.query(QueueTask).filter(QueueTask.status == "pending").count()
    processing_tasks = db.query(QueueTask).filter(QueueTask.status == "processing").count()
    completed_tasks_today = db.query(QueueTask).filter(QueueTask.status == "completed").count()
    failed_tasks_today = db.query(QueueTask).filter(QueueTask.status == "failed").count()
    
    # Queue length from Redis
    queue_length = redis_client.llen("course_selection_queue")
    
    # Calculate average processing time (simplified)
    average_processing_time = 5.0  # Placeholder in seconds
    
    return QueueStatsResponse(
        pending_tasks=pending_tasks,
        processing_tasks=processing_tasks,
        completed_tasks_today=completed_tasks_today,
        failed_tasks_today=failed_tasks_today,
        average_processing_time=average_processing_time,
        queue_length=queue_length
    )


@app.post("/queue/student/tasks")
def get_student_tasks(
    request: Request,
    student_request: StudentTasksRequest,
    db: Session = Depends(get_db)
):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Build query
    query = db.query(QueueTask).filter(QueueTask.student_id == student_request.student_id)
    
    if student_request.status:
        query = query.filter(QueueTask.status == student_request.status)
    
    # Order by creation time descending and limit
    tasks = query.order_by(QueueTask.created_at.desc()).limit(student_request.limit).all()
    
    result = []
    for task in tasks:
        result.append({
            "task_id": task.task_id,
            "course_id": task.course_id,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": int(task.created_at.timestamp()) if task.created_at else 0,
            "completed_at": int(task.completed_at.timestamp()) if task.completed_at else None
        })
    
    return StudentTasksResponse(tasks=result)


@app.get("/queue/health")
def queue_health_check():
    # Check Redis connection
    try:
        redis_connected = redis_client.ping()
    except:
        redis_connected = False
    
    # Check database connection
    try:
        # Make a simple query to test DB connection
        db_test = SessionLocal()
        db_connected = True
        db_test.close()
    except:
        db_connected = False
    
    # Calculate status based on checks
    if redis_connected and db_connected:
        status = "healthy"
    elif redis_connected or db_connected:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "queue_status": "healthy" if redis_connected else "unhealthy",
        "consumer_count": 2,  # Placeholder
        "redis_connected": redis_connected,
        "database_connected": db_connected,
        "last_processed_at": int(datetime.now().timestamp())  # Placeholder
    }


@app.post("/queue/priority/update")
def update_task_priority(
    request: Request,
    priority_request: QueuePriorityUpdateRequest,
    db: Session = Depends(get_db)
):
    # Verify internal and admin tokens
    internal_token = request.headers.get("internal_token")
    admin_token = request.headers.get("admin_token")
    
    if not internal_token or not admin_token:
        raise HTTPException(status_code=401, detail="Internal and admin tokens required")
    
    verify_internal_token(internal_token)
    verify_admin_token(admin_token)
    
    # Get task from database
    task = db.query(QueueTask).filter(QueueTask.task_id == priority_request.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update priority
    task.priority = priority_request.priority
    db.commit()
    
    return QueuePriorityUpdateResponse(
        success=True,
        message="Task priority updated successfully"
    )


@app.post("/queue/retry")
def retry_failed_task(
    request: Request,
    retry_request: QueueRetryRequest,
    db: Session = Depends(get_db)
):
    # Verify internal token
    internal_token = request.headers.get("internal_token")
    if not internal_token:
        raise HTTPException(status_code=401, detail="Internal token required")
    
    verify_internal_token(internal_token)
    
    # Get task from database
    task = db.query(QueueTask).filter(QueueTask.task_id == retry_request.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task is failed
    if task.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed tasks can be retried")
    
    # Reset task for retry
    task.status = "pending"
    task.started_at = None
    task.completed_at = None
    task.error_message = None
    task.retry_count += 1
    db.commit()
    
    # Add back to Redis queue
    redis_client.lpush("course_selection_queue", retry_request.task_id)
    
    return QueueRetryResponse(
        success=True,
        message="Task retry scheduled successfully"
    )
"""Queue Buffer Node - Rate limiting and queue management for course selection"""
from fastapi import FastAPI, HTTPException, Depends, Header, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
from datetime import datetime, timezone
import asyncio
import httpx

from backend.common import (
    QueueBase, QueueTask,
    QueueTaskSubmit, QueueTaskStatus,
    get_database_url, create_db_engine, create_session_factory, init_database,
    IPRateLimiter, course_selection_limiter,
    create_socket_server_config, SocketClient,
)

# Configuration
DATABASE_URL = get_database_url("queue_data.db")
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
PORT = int(os.getenv("PORT", "8005"))

# Rate limiter configuration
# Students can select courses: 10 requests max, refill 1 token per 10 seconds
selection_limiter = IPRateLimiter(capacity=10, refill_rate=0.1)

# Database setup
engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)
init_database(engine, QueueBase)

# FastAPI app
app = FastAPI(title="Queue Buffer Node", version="1.0.0")

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


async def process_task(task_id: str):
    """Background task processor"""
    db = SessionLocal()
    try:
        task = db.query(QueueTask).filter(QueueTask.task_id == task_id).first()
        if not task:
            return
        
        # Update task status to processing
        task.status = "processing"
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Call data node API
        async with httpx.AsyncClient(timeout=30.0) as client:
            endpoint = "/select/course" if task.task_type == "select" else "/deselect/course"
            url = f"{DATA_NODE_URL}{endpoint}"
            
            response = await client.post(
                url,
                json={
                    "student_id": task.student_id,
                    "course_id": task.course_id
                },
                headers={"Internal-Token": INTERNAL_TOKEN}
            )
            
            if response.status_code == 200:
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)
            else:
                task.status = "failed"
                task.error_message = response.text
                task.completed_at = datetime.now(timezone.utc)
                task.retry_count += 1
        
        db.commit()
        
    except Exception as e:
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            task.retry_count += 1
            db.commit()
    finally:
        db.close()


# Queue management endpoints
@app.post("/queue/submit")
async def submit_task(
    task_data: QueueTaskSubmit,
    background_tasks: BackgroundTasks,
    internal_token: str = Header(..., alias="Internal-Token"),
    x_forwarded_for: Optional[str] = Header(None, alias="X-Forwarded-For"),
    x_real_ip: Optional[str] = Header(None, alias="X-Real-IP"),
    db: Session = Depends(get_db)
):
    """Submit a course selection/deselection task to queue"""
    # Verify internal token
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    
    # Rate limiting check
    headers = {
        "x-forwarded-for": x_forwarded_for or "",
        "x-real-ip": x_real_ip or "unknown"
    }
    
    if not selection_limiter.check_rate_limit(headers, task_data.student_id, tokens=1):
        wait_time = selection_limiter.get_wait_time(headers, task_data.student_id, tokens=1)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {int(wait_time)} seconds."
        )
    
    # Create task
    task_id = str(uuid.uuid4())
    db_task = QueueTask(
        task_id=task_id,
        student_id=task_data.student_id,
        course_id=task_data.course_id,
        task_type=task_data.task_type,
        priority=task_data.priority,
        status="pending"
    )
    
    db.add(db_task)
    db.commit()
    
    # Get queue position
    pending_count = db.query(QueueTask).filter(
        QueueTask.status == "pending",
        QueueTask.priority >= task_data.priority
    ).count()
    
    # Process task in background
    background_tasks.add_task(process_task, task_id)
    
    return {
        "success": True,
        "task_id": task_id,
        "position": pending_count,
        "estimated_time": pending_count * 2  # Estimate 2 seconds per task
    }


@app.get("/queue/status")
async def get_task_status(
    task_id: str,
    internal_token: str = Header(..., alias="Internal-Token"),
    db: Session = Depends(get_db)
):
    """Get status of a queued task"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    
    task = db.query(QueueTask).filter(QueueTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Calculate position if still pending
    position = None
    if task.status == "pending":
        position = db.query(QueueTask).filter(
            QueueTask.status == "pending",
            QueueTask.created_at < task.created_at
        ).count() + 1
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "message": task.error_message or "Task completed successfully" if task.status == "completed" else task.error_message or "Task in progress",
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "position": position
    }


@app.post("/queue/cancel")
async def cancel_task(
    task_id: str,
    student_id: int,
    internal_token: str = Header(..., alias="Internal-Token"),
    db: Session = Depends(get_db)
):
    """Cancel a pending task"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    
    task = db.query(QueueTask).filter(
        QueueTask.task_id == task_id,
        QueueTask.student_id == student_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status: {task.status}"
        )
    
    task.status = "failed"
    task.error_message = "Cancelled by user"
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"success": True, "message": "Task cancelled successfully"}


@app.get("/queue/stats")
async def get_queue_stats(
    internal_token: str = Header(..., alias="Internal-Token"),
    db: Session = Depends(get_db)
):
    """Get queue statistics"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    pending_tasks = db.query(QueueTask).filter(QueueTask.status == "pending").count()
    processing_tasks = db.query(QueueTask).filter(QueueTask.status == "processing").count()
    completed_today = db.query(QueueTask).filter(
        QueueTask.status == "completed",
        QueueTask.completed_at >= today
    ).count()
    failed_today = db.query(QueueTask).filter(
        QueueTask.status == "failed",
        QueueTask.completed_at >= today
    ).count()
    
    # Calculate average processing time
    completed_tasks = db.query(QueueTask).filter(
        QueueTask.status == "completed",
        QueueTask.started_at.isnot(None),
        QueueTask.completed_at.isnot(None)
    ).limit(100).all()
    
    avg_processing_time = 0
    if completed_tasks:
        total_time = sum([
            (task.completed_at - task.started_at).total_seconds()
            for task in completed_tasks
        ])
        avg_processing_time = total_time / len(completed_tasks)
    
    return {
        "pending_tasks": pending_tasks,
        "processing_tasks": processing_tasks,
        "completed_tasks_today": completed_today,
        "failed_tasks_today": failed_today,
        "average_processing_time": round(avg_processing_time, 2),
        "queue_length": pending_tasks + processing_tasks
    }


@app.get("/queue/student/tasks")
async def get_student_tasks(
    student_id: int,
    status_filter: Optional[str] = None,
    limit: int = 10,
    internal_token: str = Header(..., alias="Internal-Token"),
    db: Session = Depends(get_db)
):
    """Get all tasks for a student"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    
    query = db.query(QueueTask).filter(QueueTask.student_id == student_id)
    
    if status_filter:
        query = query.filter(QueueTask.status == status_filter)
    
    tasks = query.order_by(QueueTask.created_at.desc()).limit(limit).all()
    
    return {
        "tasks": [
            {
                "task_id": task.task_id,
                "course_id": task.course_id,
                "task_type": task.task_type,
                "status": task.status,
                "created_at": task.created_at,
                "completed_at": task.completed_at
            }
            for task in tasks
        ]
    }


@app.get("/queue/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        # Check queue status
        pending = db.query(QueueTask).filter(QueueTask.status == "pending").count()
        processing = db.query(QueueTask).filter(QueueTask.status == "processing").count()
        
        status_text = "healthy"
        if pending + processing > 1000:
            status_text = "degraded"
        if pending + processing > 5000:
            status_text = "unhealthy"
        
        return {
            "status": status_text,
            "queue_status": "active",
            "database_connected": True,
            "pending_tasks": pending,
            "processing_tasks": processing
        }
    except Exception:
        # SECURITY: Don't expose internal error details
        return {
            "status": "unhealthy",
            "error": "Service unavailable",
            "database_connected": False
        }


if __name__ == "__main__":
    import uvicorn
    # Get socket or HTTP config based on environment
    config = create_socket_server_config('queue_node', PORT)
    uvicorn.run(app, **config)

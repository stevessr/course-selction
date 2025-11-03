"""Data Node - Course data management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables: root .env first, then service-level .env overrides
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).with_name('.env'), override=True)

from backend.common import (
    DataBase,
    get_database_url, create_db_engine, create_session_factory, init_database,
    create_socket_server_config,
)

# Import router factories
from backend.data_node.routers.course_routes import create_course_router
from backend.data_node.routers.student_routes import create_student_router
from backend.data_node.routers.teacher_routes import create_teacher_router
from backend.data_node.routers.selection_routes import create_selection_router
from backend.data_node.routers.tag_routes import create_tag_router

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


# Create and include routers
course_router = create_course_router(get_db, verify_internal_token_header)
student_router = create_student_router(get_db, verify_internal_token_header)
teacher_router = create_teacher_router(get_db, verify_internal_token_header)
selection_router = create_selection_router(get_db, verify_internal_token_header)
tag_router = create_tag_router(get_db, verify_internal_token_header)

app.include_router(course_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(selection_router)
app.include_router(tag_router)


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

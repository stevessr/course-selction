"""Teacher management routes for Data Node"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timezone

from backend.common import (
    TeacherCourseData,
    TeacherCreate, TeacherResponse,
)


def create_teacher_router(get_db: Callable, verify_internal_token: Callable) -> APIRouter:
    """
    Factory function to create teacher router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_internal_token: Internal token verification dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/add/teacher", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
    async def add_teacher(
        teacher: TeacherCreate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Add a new teacher"""
        # Check if teacher already exists by ID or name
        if teacher.teacher_id:
            existing = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == teacher.teacher_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Teacher with this ID already exists")
        
        existing_name = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_name == teacher.teacher_name).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Teacher with this name already exists")

        # Create teacher with explicit ID if provided (for auth sync)
        teacher_data = {
            "teacher_name": teacher.teacher_name,
            "teacher_courses": []
        }
        if teacher.teacher_id:
            teacher_data["teacher_id"] = teacher.teacher_id
        
        db_teacher = TeacherCourseData(**teacher_data)
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return db_teacher

    @router.post("/update/teacher", response_model=TeacherResponse)
    async def update_teacher(
        teacher_id: int,
        teacher_name: str,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
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

    @router.post("/delete/teacher")
    async def delete_teacher(
        teacher_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
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

    @router.get("/get/teacher", response_model=TeacherResponse)
    async def get_teacher(
        teacher_id: int,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
    ):
        """Get teacher information"""
        db_teacher = db.query(TeacherCourseData).filter(TeacherCourseData.teacher_id == teacher_id).first()
        if not db_teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        return db_teacher

    return router

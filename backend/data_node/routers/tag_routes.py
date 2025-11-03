"""Tag management routes for Data Node"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Callable
from datetime import datetime, timezone

from backend.common import (
    Course, StudentCourseData, AvailableTag,
)


def create_tag_router(get_db: Callable, verify_internal_token: Callable) -> APIRouter:
    """
    Factory function to create tag router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        verify_internal_token: Internal token verification dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.get("/tags/available")
    async def get_available_tags(
        tag_type: Optional[str] = None,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
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

    @router.post("/tags/add")
    async def add_available_tag(
        tag_name: str,
        tag_type: str,
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
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

    @router.post("/tags/sync")
    async def sync_available_tags(
        db: Session = Depends(get_db),
        _: None = Depends(verify_internal_token)
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

    return router

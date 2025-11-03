"""Admin course management routes for Auth Node"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Callable
import os
import httpx

from backend.common import Admin, Teacher


def create_admin_course_router(get_db: Callable, get_current_admin: Callable) -> APIRouter:
    """
    Factory function to create admin course management router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        get_current_admin: Admin authentication dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()
    
    # Get environment variables
    DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")

    @router.get("/admin/courses")
    async def list_all_courses(
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        course_type: Optional[str] = None,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """List all courses (admin only)"""
        try:
            async with httpx.AsyncClient() as client:
                params = {"page": page, "page_size": page_size}
                if search:
                    params["search"] = search
                if course_type:
                    params["course_type"] = course_type
                    
                headers = {"Internal-Token": INTERNAL_TOKEN}
                response = await client.get(f"{DATA_NODE_URL}/get/courses", params=params, headers=headers)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {response.text}")
                
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

    @router.post("/admin/course/update")
    async def update_course_admin(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Update course (admin only)"""
        course_id = data.get("course_id")
        if not course_id:
            raise HTTPException(status_code=400, detail="course_id is required")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": INTERNAL_TOKEN}
                response = await client.post(
                    f"{DATA_NODE_URL}/update/course",
                    params={"course_id": course_id},
                    json=data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"Failed to update course: {response.text}")
                
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

    @router.post("/admin/course/delete")
    async def delete_course_admin(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Delete course (admin only)"""
        course_id = data.get("course_id")
        if not course_id:
            raise HTTPException(status_code=400, detail="course_id is required")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": INTERNAL_TOKEN}
                response = await client.post(
                    f"{DATA_NODE_URL}/delete/course",
                    params={"course_id": course_id},
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"Failed to delete course: {response.text}")
                
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

    @router.post("/admin/courses/bulk-import")
    async def bulk_import_courses_admin(
        courses: List[dict],
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Bulk import courses (admin only)"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Internal-Token": INTERNAL_TOKEN}
                response = await client.post(
                    f"{DATA_NODE_URL}/bulk/import/courses",
                    json=courses,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"Failed to import courses: {response.text}")
                
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

    @router.post("/admin/courses/batch-assign-teacher")
    async def batch_assign_teacher_admin(
        data: dict,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Batch assign teacher to courses (admin only)"""
        course_ids = data.get("course_ids", [])
        teacher_id = data.get("teacher_id")
        
        if not course_ids or not teacher_id:
            raise HTTPException(status_code=400, detail="course_ids and teacher_id are required")
        
        # Verify teacher exists
        teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        updated = []
        errors = []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": INTERNAL_TOKEN}
                
                for course_id in course_ids:
                    try:
                        response = await client.post(
                            f"{DATA_NODE_URL}/update/course",
                            params={"course_id": course_id},
                            json={"course_teacher_id": teacher_id},
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            updated.append(course_id)
                        else:
                            errors.append({
                                "course_id": course_id,
                                "error": response.text
                            })
                    except Exception as e:
                        errors.append({
                            "course_id": course_id,
                            "error": str(e)
                        })
            
            return {
                "success": True,
                "updated_count": len(updated),
                "error_count": len(errors),
                "updated": updated,
                "errors": errors
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

    return router

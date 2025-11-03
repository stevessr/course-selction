"""System settings management routes for Auth Node"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timezone

from backend.common import (
    Admin, SystemSettings,
    SystemSettingsResponse, SystemSettingsUpdate,
)


def ensure_system_settings(db: Session):
    """Ensure system settings exist, create with defaults if not"""
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings(
            student_registration_enabled=True,
            teacher_registration_enabled=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def create_settings_router(get_db: Callable, get_current_admin: Callable) -> APIRouter:
    """
    Factory function to create settings router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        get_current_admin: Admin authentication dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.get("/admin/settings", response_model=SystemSettingsResponse)
    async def get_system_settings(
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Get system settings (admin only)"""
        settings = ensure_system_settings(db)
        return SystemSettingsResponse(
            student_registration_enabled=settings.student_registration_enabled,
            teacher_registration_enabled=settings.teacher_registration_enabled,
            updated_at=settings.updated_at
        )

    @router.put("/admin/settings", response_model=SystemSettingsResponse)
    async def update_system_settings(
        settings_update: SystemSettingsUpdate,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Update system settings (admin only)"""
        settings = ensure_system_settings(db)
        
        if settings_update.student_registration_enabled is not None:
            settings.student_registration_enabled = settings_update.student_registration_enabled
        if settings_update.teacher_registration_enabled is not None:
            settings.teacher_registration_enabled = settings_update.teacher_registration_enabled
        
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(settings)
        
        return SystemSettingsResponse(
            student_registration_enabled=settings.student_registration_enabled,
            teacher_registration_enabled=settings.teacher_registration_enabled,
            updated_at=settings.updated_at
        )

    return router

"""User account management routes for Auth Node - password and 2FA"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Callable

from backend.common import (
    PasswordChangeRequest, TwoFASetupRequest, TwoFAVerifyRequest, TwoFADisableRequest,
    get_current_user_from_token,
    verify_password, get_password_hash,
    generate_totp_secret, verify_totp, get_totp_uri,
)
from backend.common.auth_helpers import (
    get_user_by_id, has_2fa, get_totp_secret as get_user_totp_secret,
)


def create_user_account_router(get_db: Callable) -> APIRouter:
    """
    Factory function to create user account router with injected dependencies.
    
    Args:
        get_db: Database session dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/user/change-password")
    async def change_password(
        password_change: PasswordChangeRequest,
        current_user: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
    ):
        """Change user password (requires old password verification)"""
        user_id = current_user.get("user_id")
        user_type = current_user.get("user_type")
        
        # Get user from database
        user = get_user_by_id(db, user_id, user_type)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if not verify_password(password_change.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect old password")
        
        # Update password
        user.password_hash = get_password_hash(password_change.new_password)
        db.commit()
        
        return {"success": True, "message": "Password changed successfully"}

    @router.post("/user/2fa/setup")
    async def setup_2fa(
        setup_request: TwoFASetupRequest,
        current_user: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
    ):
        """Setup 2FA for user (verify password first)"""
        user_id = current_user.get("user_id")
        user_type = current_user.get("user_type")
        
        # Get user from database
        user = get_user_by_id(db, user_id, user_type)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if not verify_password(setup_request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        # Check if 2FA is already enabled
        if has_2fa(user):
            raise HTTPException(status_code=400, detail="2FA is already enabled")
        
        # Generate TOTP secret
        totp_secret = generate_totp_secret()
        
        # Generate QR code URI
        totp_uri = get_totp_uri(
            secret=totp_secret,
            issuer="Course Selection System",
            account_name=f"{user_type}:{user.username}"
        )
        
        # Temporarily store secret (will be confirmed in verify endpoint)
        # For now, store it directly - in production, might want to use a temporary storage
        user.totp_secret = totp_secret
        if user_type == "student":
            user.has_2fa = True
        elif user_type == "teacher" and hasattr(user, 'has_2fa'):
            user.has_2fa = True
        db.commit()
        
        return {
            "success": True,
            "totp_secret": totp_secret,
            "totp_uri": totp_uri,
            "message": "2FA setup initiated. Please verify with a code from your authenticator app."
        }

    @router.post("/user/2fa/verify")
    async def verify_2fa_setup(
        verify_request: TwoFAVerifyRequest,
        current_user: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
    ):
        """Verify 2FA setup with TOTP code"""
        user_id = current_user.get("user_id")
        user_type = current_user.get("user_type")
        
        # Get user from database
        user = get_user_by_id(db, user_id, user_type)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify the TOTP code
        if not get_user_totp_secret(user):
            raise HTTPException(status_code=400, detail="2FA not set up")
        
        if not verify_totp(get_user_totp_secret(user), verify_request.totp_code):
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        return {
            "success": True,
            "message": "2FA verified successfully"
        }

    @router.post("/user/2fa/disable")
    async def disable_2fa(
        disable_request: TwoFADisableRequest,
        current_user: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
    ):
        """Disable 2FA for user (requires password and current 2FA code)"""
        user_id = current_user.get("user_id")
        user_type = current_user.get("user_type")
        
        # Get user from database
        user = get_user_by_id(db, user_id, user_type)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if not verify_password(disable_request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        # Verify 2FA code
        if not has_2fa(user):
            raise HTTPException(status_code=400, detail="2FA is not enabled")
        
        if not verify_totp(get_user_totp_secret(user), disable_request.totp_code):
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Disable 2FA
        user.totp_secret = None
        if user_type == "student":
            user.has_2fa = False
        elif user_type == "teacher" and hasattr(user, 'has_2fa'):
            user.has_2fa = False
        db.commit()
        
        return {"success": True, "message": "2FA disabled successfully"}

    @router.get("/user/2fa/status")
    async def get_2fa_status(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Get current user's 2FA status"""
        try:
            token = authorization.replace("Bearer ", "")
            payload = await get_current_user_from_token(token)
            
            user_id = payload.get("user_id")
            user_type = payload.get("user_type")
            
            # Get user from database
            user = get_user_by_id(db, user_id, user_type)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "has_2fa": has_2fa(user),
                "user_type": user_type,
                "username": user.username
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    return router

"""Admin basic routes for Auth Node - login, admin management, codes"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timedelta, timezone

from backend.common import (
    Admin, RefreshToken, RegistrationCode, ResetCode,
    AdminCreate, AdminLogin,
    RegistrationCodeCreate,
    ResetCodeCreate, ResetCodeResponse,
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, hash_token,
    generate_totp_secret, verify_totp, get_totp_uri,
    generate_registration_code, generate_reset_code,
)
from backend.common.auth_helpers import (
    get_user_by_username, get_user_by_id, get_user_id, set_totp_secret,
)


def create_admin_basic_router(get_db: Callable, get_current_admin: Callable) -> APIRouter:
    """
    Factory function to create admin basic router with injected dependencies.
    
    Args:
        get_db: Database session dependency
        get_current_admin: Admin authentication dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/login/admin")
    async def admin_login(
        login_data: AdminLogin,
        db: Session = Depends(get_db)
    ):
        """Admin login (no 2FA required)"""
        admin = db.query(Admin).filter(Admin.username == login_data.username).first()
        
        if not admin or not verify_password(login_data.password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate access token
        access_token = create_access_token({
            "user_id": admin.admin_id,
            "username": admin.username,
            "user_type": "admin"
        }, expires_delta=timedelta(hours=8))

        # Also generate an admin refresh token for consistency with tests
        refresh_token = create_refresh_token({
            "user_id": admin.admin_id,
            "username": admin.username,
            "user_type": "admin"
        })

        # Store refresh token hash (so it can be revoked later if needed)
        token_hash = hash_token(refresh_token)
        db_token = RefreshToken(
            user_id=admin.admin_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(db_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 8 * 3600
        }

    @router.post("/add/admin", response_model=dict)
    async def add_admin(
        admin_data: AdminCreate,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Create a new admin (admin only)"""
        # Check if admin exists
        existing = db.query(Admin).filter(Admin.username == admin_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Admin already exists")
        
        # Create admin
        db_admin = Admin(
            username=admin_data.username,
            password_hash=get_password_hash(admin_data.password)
        )
        db.add(db_admin)
        db.commit()
        
        return {"success": True, "message": "Admin created successfully"}

    @router.post("/generate/registration-code")
    async def generate_registration_code_endpoint(
        code_data: RegistrationCodeCreate,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Generate registration code(s) (admin only) - supports bulk generation"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=code_data.expires_days)
        
        generated_codes = []
        for _ in range(code_data.count):
            code = generate_registration_code()
            
            db_code = RegistrationCode(
                code=code,
                user_type=code_data.user_type,
                created_by=current_admin.admin_id,
                expires_at=expires_at,
                code_tags=code_data.code_tags or []
            )
            db.add(db_code)
            
            generated_codes.append({
                "code": code,
                "user_type": code_data.user_type,
                "expires_at": expires_at,
                "code_tags": code_data.code_tags
            })
        
        db.commit()
        
        # Return single code format for backward compatibility if count=1
        if code_data.count == 1:
            return generated_codes[0]
        else:
            return {
                "codes": generated_codes,
                "count": len(generated_codes)
            }

    @router.post("/generate/reset-code", response_model=ResetCodeResponse)
    async def generate_reset_code_endpoint(
        reset_data: ResetCodeCreate,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """Generate 2FA reset code (admin only)"""
        # Find user
        user = get_user_by_username(db, reset_data.username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        code = generate_reset_code()
        expires_at = datetime.now(timezone.utc) + timedelta(days=reset_data.expires_days)
        
        db_code = ResetCode(
            code=code,
            user_id=get_user_id(user),
            created_by=current_admin.admin_id,
            expires_at=expires_at
        )
        db.add(db_code)
        db.commit()
        
        return {
            "code": code,
            "username": user.username,
            "expires_at": expires_at
        }

    @router.get("/admin/reset-codes")
    async def list_reset_codes(
        page: int = 1,
        page_size: int = 20,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)
    ):
        """List all reset codes (admin only)"""
        # Get total count
        total = db.query(ResetCode).count()
        
        # Get paginated codes
        db_codes = db.query(ResetCode).order_by(ResetCode.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        
        codes_data = []
        for code in db_codes:
            # Get the username for this code
            user = get_user_by_id(db, code.user_id, "student")
            username = user.username if user else "Unknown"
            
            codes_data.append({
                "id": code.id,
                "code": code.code,
                "username": username,
                "is_used": code.is_used,
                "expires_at": code.expires_at.isoformat() if code.expires_at else None,
                "created_at": code.created_at.isoformat() if code.created_at else None,
            })
        
        return {
            "codes": codes_data,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @router.post("/reset/2fa")
    async def reset_2fa(
        reset_code: str,
        new_totp_code: str,
        db: Session = Depends(get_db)
    ):
        """Reset 2FA with reset code"""
        # Verify reset code
        db_code = db.query(ResetCode).filter(
            ResetCode.code == reset_code,
            ResetCode.is_used == False,
            ResetCode.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not db_code:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        
        # Get user using the user_id from the reset code
        user = get_user_by_id(db, db_code.user_id, "student")  # Only students have reset codes
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate new TOTP secret
        new_secret = generate_totp_secret()
        
        # Verify the new TOTP code with new secret
        if not verify_totp(new_secret, new_totp_code):
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Update user's TOTP secret using auth_helpers
        set_totp_secret(user, new_secret)
        db_code.is_used = True
        db.commit()
        
        # Get TOTP URI for QR code
        totp_uri = get_totp_uri(new_secret, user.username)
        
        return {
            "success": True,
            "message": "2FA reset successfully",
            "totp_secret": new_secret,
            "totp_uri": totp_uri
        }

    return router

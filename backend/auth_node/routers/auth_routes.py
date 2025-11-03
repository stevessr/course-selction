"""Authentication routes for Auth Node - registration, login, 2FA"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timedelta, timezone
import os
import httpx

from backend.common import (
    Student, Teacher, RefreshToken, RegistrationCode,
    UserCreate, UserLogin,
    AccessTokenResponse, RefreshTokenResponse,
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token, hash_token,
    generate_totp_secret, verify_totp, get_totp_uri,
)
from backend.common.auth_helpers import (
    get_user_by_username, get_user_by_id, has_2fa,
)
from backend.auth_node.routers.settings_routes import ensure_system_settings

# Configuration
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")


def create_auth_router(get_db: Callable) -> APIRouter:
    """
    Factory function to create authentication router with injected dependencies.
    
    Args:
        get_db: Database session dependency
    
    Returns:
        Configured APIRouter instance
    """
    router = APIRouter()

    @router.post("/register/v1", response_model=dict)
    async def register_v1(
        user_data: UserCreate,
        db: Session = Depends(get_db)
    ):
        """Register user - phase 1: Create account and generate 2FA"""
        # Check system settings for registration availability
        settings = ensure_system_settings(db)
        if user_data.user_type == "student" and not settings.student_registration_enabled:
            raise HTTPException(status_code=403, detail="Student registration is currently disabled")
        if user_data.user_type == "teacher" and not settings.teacher_registration_enabled:
            raise HTTPException(status_code=403, detail="Teacher registration is currently disabled")
        
        # Verify registration code (now mandatory)
        if not user_data.registration_code:
            raise HTTPException(status_code=400, detail="Registration code is required")
        
        reg_code = db.query(RegistrationCode).filter(
            RegistrationCode.code == user_data.registration_code,
            RegistrationCode.is_used == False,
            RegistrationCode.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not reg_code:
            raise HTTPException(status_code=400, detail="Invalid or expired registration code")
        
        if reg_code.user_type != user_data.user_type:
            raise HTTPException(status_code=400, detail="Registration code type mismatch")
        
        # Check if user already exists in the auth database
        existing_user = get_user_by_username(db, user_data.username, user_data.user_type)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
        # Generate 2FA secret only for students (not for teachers/admins)
        totp_secret = generate_totp_secret() if user_data.user_type == "student" else None
    
        # Create password hash
        password_hash = get_password_hash(user_data.password)
    
        # Create user in auth database
        user_id = None
        if user_data.user_type == "student":
            # Create student auth record
            new_student = Student(
                username=user_data.username,
                password_hash=password_hash,
                totp_secret=totp_secret,
                is_active=True
            )
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            user_id = new_student.student_id
    
            # Also create student course data record in data node
            data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
            internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": internal_token}
                # Apply tags from registration code if available
                student_tags = []
                if user_data.registration_code and reg_code:
                    student_tags = reg_code.code_tags or []
                
                student_payload = {
                    "student_id": user_id,  # Sync student_id from auth to course data
                    "student_name": user_data.username,  # Set to username initially
                    "student_tags": student_tags
                }
                response = await client.post(f"{data_node_url}/add/student", json=student_payload, headers=headers)
                if response.status_code != 201:
                    # Rollback auth record if course data creation fails
                    db.delete(new_student)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Failed to create student course data: {response.text}")
    
        elif user_data.user_type == "teacher":
            # Create teacher auth record
            new_teacher = Teacher(
                username=user_data.username,
                password_hash=password_hash,
                is_active=True
            )
            db.add(new_teacher)
            db.commit()
            db.refresh(new_teacher)
            user_id = new_teacher.teacher_id
    
            # Also create teacher course data record in data node
            data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
            internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"Internal-Token": internal_token}
                teacher_payload = {
                    "teacher_id": user_id,  # Sync teacher_id from auth to course data
                    "teacher_name": user_data.username  # Set to username initially
                }
                response = await client.post(f"{data_node_url}/add/teacher", json=teacher_payload, headers=headers)
                if response.status_code != 201:
                    # Rollback auth record if course data creation fails
                    db.delete(new_teacher)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Failed to create teacher course data: {response.text}")
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
    
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Mark registration code as used
        if user_data.registration_code:
            reg_code.is_used = True
            reg_code.used_by = user_id
            db.commit()
        
        # Revoke any existing refresh tokens for this user (shouldn't exist for new user, but be safe)
        existing_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        for token in existing_tokens:
            token.is_revoked = True
        
        # Generate new refresh token
        refresh_token = create_refresh_token({
            "user_id": user_id,
            "username": user_data.username,
            "user_type": user_data.user_type
        })
        
        # Store new refresh token
        token_hash = hash_token(refresh_token)
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(db_token)
        db.commit()
        
        # Get TOTP URI for QR code (only for students)
        totp_uri = get_totp_uri(totp_secret, user_data.username) if totp_secret else None
        
        return {
            "totp_secret": totp_secret,
            "totp_uri": totp_uri,
            "refresh_token": refresh_token,
            "expires_in": 7 * 24 * 3600,
            "message": "Registration successful. Please scan QR code to setup 2FA."
        }
    
    
    @router.post("/register/v2", response_model=AccessTokenResponse)
    async def register_v2(
        totp_data: User2FA,
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Register user - phase 2: Verify 2FA and get access token"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Verify TOTP code only if user has 2FA enabled (students only)
            if has_2fa(user):
                if not verify_totp(get_totp_secret(user), totp_data.totp_code):
                    raise HTTPException(status_code=400, detail="Invalid 2FA code")
            
            # Generate access token with different expiration based on user type
            from datetime import timedelta
            if get_user_type(user) == "teacher":
                # Teachers get 2 hours for longer sessions managing courses
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                }, expires_delta=timedelta(hours=2))
                expires_in = 2 * 3600  # 2 hours in seconds
            else:
                # Default 30 minutes for students and other user types
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                })
                expires_in = 30 * 60  # 30 minutes in seconds
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.post("/login/v1", response_model=RefreshTokenResponse)
    async def login_v1(
        login_data: UserLogin,
        db: Session = Depends(get_db)
    ):
        """Login phase 1: Verify credentials and get refresh token"""
        user = get_user_by_username(db, login_data.username)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not is_active(user):
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        # Revoke any existing refresh tokens for this user
        existing_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == get_user_id(user),
            RefreshToken.is_revoked == False
        ).all()
        for token in existing_tokens:
            token.is_revoked = True
        
        # Generate new refresh token
        refresh_token = create_refresh_token({
            "user_id": get_user_id(user),
            "username": user.username,
            "user_type": get_user_type(user)
        })
        
        # Store new refresh token
        token_hash = hash_token(refresh_token)
        db_token = RefreshToken(
            user_id=get_user_id(user),
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(db_token)
        db.commit()
        
        return {
            "refresh_token": refresh_token,
            "expires_in": 7 * 24 * 3600
        }
    
    
    @router.post("/login/v2", response_model=AccessTokenResponse)
    async def login_v2(
        totp_data: User2FA,
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Login phase 2: Verify 2FA and get access token"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Verify TOTP code only if user has 2FA enabled (students only)
            if has_2fa(user):
                if not verify_totp(get_totp_secret(user), totp_data.totp_code):
                    raise HTTPException(status_code=400, detail="Invalid 2FA code")
            
            # Generate access token with different expiration based on user type
            from datetime import timedelta
            if get_user_type(user) == "teacher":
                # Teachers get 2 hours for longer sessions managing courses
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                }, expires_delta=timedelta(hours=2))
                expires_in = 2 * 3600  # 2 hours in seconds
            else:
                # Default 30 minutes for students and other user types
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                })
                expires_in = 30 * 60  # 30 minutes in seconds
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.get("/check/2fa-status")
    async def check_2fa_status(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Check if user has 2FA enabled"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if user has 2FA enabled (only for students)
            user_has_2fa = has_2fa(user)
            
            return {
                "has_2fa": user_has_2fa,
                "user_type": get_user_type(user),
                "username": user.username
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.post("/login/no-2fa", response_model=AccessTokenResponse)
    async def login_no_2fa(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Login without 2FA for teachers only (students must have 2FA)"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Students MUST have 2FA enabled - reject if student tries this endpoint
            if get_user_type(user) == "student":
                raise HTTPException(status_code=403, detail="Students must set up 2FA before logging in")
            
            # Only teachers without 2FA can use this endpoint
            if get_user_type(user) == "teacher" and has_2fa(user):
                raise HTTPException(status_code=400, detail="User has 2FA enabled, cannot use this endpoint")
            
            # Generate access token with different expiration based on user type
            from datetime import timedelta
            if get_user_type(user) == "teacher":
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                }, expires_delta=timedelta(hours=2))
                expires_in = 2 * 3600
            else:
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                })
                expires_in = 30 * 60
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.post("/logout")
    async def logout(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Logout - revoke refresh token"""
        try:
            token = authorization.replace("Bearer ", "")
            token_hash = hash_token(token)
            
            db_token = db.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()
            
            if db_token:
                db_token.is_revoked = True
                db.commit()
            
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    
    @router.post("/setup/2fa/v1")
    async def setup_2fa_v1(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Setup 2FA for student without 2FA - phase 1: Generate TOTP secret"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Only students can setup 2FA
            if get_user_type(user) != "student":
                raise HTTPException(status_code=400, detail="Only students can setup 2FA")
            
            # Check if user already has 2FA
            if has_2fa(user):
                raise HTTPException(status_code=400, detail="User already has 2FA enabled")
            
            # Generate new TOTP secret
            new_secret = generate_totp_secret()
            
            # Get TOTP URI for QR code
            totp_uri = get_totp_uri(new_secret, user.username)
            
            return {
                "totp_secret": new_secret,
                "totp_uri": totp_uri,
                "message": "Please scan QR code to setup 2FA."
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.post("/setup/2fa/v2")
    async def setup_2fa_v2(
        setup_data: dict,
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Setup 2FA for student - phase 2: Verify TOTP and save secret"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Only students can setup 2FA
            if get_user_type(user) != "student":
                raise HTTPException(status_code=400, detail="Only students can setup 2FA")
            
            # Get secret and code from request
            totp_secret = setup_data.get("totp_secret")
            totp_code = setup_data.get("totp_code")
            
            if not totp_secret or not totp_code:
                raise HTTPException(status_code=400, detail="Missing totp_secret or totp_code")
            
            # Verify the TOTP code with the provided secret
            if not verify_totp(totp_secret, totp_code):
                raise HTTPException(status_code=400, detail="Invalid 2FA code")
            
            # Save the TOTP secret to the user
            set_totp_secret(user, totp_secret)
            db.commit()
            
            return {
                "success": True,
                "message": "2FA setup successful. Please login again."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.post("/refresh", response_model=AccessTokenResponse)
    async def refresh_access_token(
        totp_data: User2FA,
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Refresh access token (requires 2FA for students)"""
        try:
            refresh_token = authorization.replace("Bearer ", "")
            payload = decode_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            # Check if token is revoked
            token_hash = hash_token(refresh_token)
            db_token = db.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False
            ).first()
            
            if not db_token:
                raise HTTPException(status_code=401, detail="Token revoked or not found")
            
            user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # For students, verify 2FA
            if get_user_type(user) == "student":
                if not verify_totp(get_totp_secret(user), totp_data.totp_code):
                    raise HTTPException(status_code=400, detail="Invalid 2FA code")
            
            # Generate new access token with different expiration based on user type
            from datetime import timedelta
            if get_user_type(user) == "teacher":
                # Teachers get 2 hours for longer sessions managing courses
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                }, expires_delta=timedelta(hours=2))
                expires_in = 2 * 3600  # 2 hours in seconds
            else:
                # Default 30 minutes for students and other user types
                access_token = create_access_token({
                    "user_id": get_user_id(user),
                    "username": user.username,
                    "user_type": get_user_type(user)
                })
                expires_in = 30 * 60  # 30 minutes in seconds
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    @router.get("/get/user")
    async def get_user_info(
        authorization: str = Header(..., alias="Authorization"),
        db: Session = Depends(get_db)
    ):
        """Get user information from access token"""
        try:
            token = authorization.replace("Bearer ", "")
            payload = await get_current_user_from_token(token)
    
            user_id = payload.get("user_id")
            user_type = payload.get("user_type")
    
            if user_type == "admin":
                # Look up admin user
                admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
                if not admin:
                    raise HTTPException(status_code=404, detail="Admin not found")
                
                # Return AdminResponse
                return AdminResponse(
                    admin_id=admin.admin_id,
                    username=admin.username,
                    created_at=admin.created_at
                )
            else:
                # Look up regular user using auth_helpers
                user = get_user_by_id(db, user_id, user_type)
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Return UserResponse
                return UserResponse(
                    user_id=get_user_id(user),
                    username=user.username,
                    user_type=get_user_type(user),
                    is_active=is_active(user),
                    has_2fa=has_2fa(user),
                    created_at=user.created_at
                )
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    
    # Admin User Management Endpoints

    return router

"""Authentication Node - User authentication and token management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables: root .env first, then service-level .env overrides
load_dotenv()  # project root .env (fallbacks)
load_dotenv(dotenv_path=Path(__file__).with_name('.env'), override=True)

from backend.common import (
    AuthBase, Student, Teacher, Admin, RefreshToken, RegistrationCode, ResetCode,
    UserCreate, UserLogin, User2FA, UserResponse, AdminResponse,
    AdminCreate, AdminLogin,
    RegistrationCodeCreate, RegistrationCodeResponse,
    ResetCodeCreate, ResetCodeResponse,
    RefreshTokenResponse, AccessTokenResponse,
    SystemSettingsResponse, SystemSettingsUpdate,
    PasswordChangeRequest, TwoFASetupRequest, TwoFAVerifyRequest, TwoFADisableRequest,
    get_database_url, create_db_engine, create_session_factory, init_database,
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    generate_totp_secret, verify_totp, get_totp_uri,
    generate_registration_code, generate_reset_code, hash_token,
    get_current_user_from_token,
    create_socket_server_config, SocketClient,
)
from backend.common.auth_helpers import (
    get_user_by_username, get_user_by_id, get_user_id, get_user_type,
    has_2fa, get_totp_secret, set_totp_secret, is_active
)

# Configuration
DATABASE_URL = get_database_url("auth_data.db")
DATA_NODE_URL = os.getenv("DATA_NODE_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
PORT = int(os.getenv("PORT", "8002"))

# Database setup
engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)
init_database(engine, AuthBase)


def ensure_initial_admin():
    """Ensure a default admin user exists in the database.

    This runs at startup so the admin is created regardless of how the
    FastAPI app is launched (uvicorn module, python -m, etc.). Uses
    ADMIN_PASSWORD env var or falls back to a known default for demos.
    """
    try:
        with SessionLocal() as db:
            admin = db.query(Admin).filter(Admin.username == "admin").first()
            if not admin:
                default_password = os.getenv("ADMIN_PASSWORD", "admin123")
                admin = Admin(
                    username="admin",
                    password_hash=get_password_hash(default_password)
                )
                db.add(admin)
                db.commit()
                print("=" * 60)
                print("IMPORTANT: Initial admin created")
                print("Username: admin")
                # SECURITY: Don't log the actual password in production
                if default_password == "admin123":
                    print("Password: admin123 (DEFAULT - CHANGE IMMEDIATELY!)")
                    print("WARNING: Using default password! Change it in production!")
                    print("Set ADMIN_PASSWORD environment variable to use a custom password.")
                else:
                    print("Password: <set via ADMIN_PASSWORD environment variable>")
                print("=" * 60)
    except Exception:
        # If DB isn't ready yet or there's another error, don't crash the app
        # The admin can be created later by calling this function again.
        pass


# Ensure default admin exists at startup (works for uvicorn or python -m)
ensure_initial_admin()

# FastAPI app
app = FastAPI(title="Authentication Node", version="1.0.0")

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


async def get_current_admin(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Verify admin token"""
    try:
        token = authorization.replace("Bearer ", "")
        payload = await get_current_user_from_token(token)
        
        if payload.get("user_type") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        admin = db.query(Admin).filter(Admin.admin_id == payload.get("user_id")).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return admin
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


# Student/Teacher Registration and Login
@app.post("/register/v1", response_model=dict)
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
    existing_user = await get_user_by_username(db, user_data.username, user_data.user_type)
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


@app.post("/register/v2", response_model=AccessTokenResponse)
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.post("/login/v1", response_model=RefreshTokenResponse)
async def login_v1(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login phase 1: Verify credentials and get refresh token"""
    user = await get_user_by_username(db, login_data.username)
    
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


@app.post("/login/v2", response_model=AccessTokenResponse)
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.get("/check/2fa-status")
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.post("/login/no-2fa", response_model=AccessTokenResponse)
async def login_no_2fa(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
):
    """Login without 2FA for users who have 2FA disabled"""
    try:
        refresh_token = authorization.replace("Bearer ", "")
        payload = decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has 2FA disabled
        # Only students with 2FA enabled are restricted from this endpoint
        if (get_user_type(user) == "student" and has_2fa(user)):
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


@app.post("/logout")
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


@app.post("/setup/2fa/v1")
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.post("/setup/2fa/v2")
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.post("/refresh", response_model=AccessTokenResponse)
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
        
        user = await get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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


@app.get("/get/user")
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
            user = await get_user_by_id(db, user_id, user_type)
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


# Admin endpoints
@app.post("/login/admin")
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


@app.post("/add/admin", response_model=dict)
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


@app.post("/generate/registration-code")
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


@app.post("/generate/reset-code", response_model=ResetCodeResponse)
async def generate_reset_code_endpoint(
    reset_data: ResetCodeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate 2FA reset code (admin only)"""
    # Find user
    user = await get_user_by_username(db, reset_data.username)
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


@app.get("/admin/reset-codes")
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
        user = await get_user_by_id(db, code.user_id, "student")
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


@app.post("/reset/2fa")
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
    user = await get_user_by_id(db, db_code.user_id, "student")  # Only students have reset codes
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


# Admin User Management Endpoints

@app.get("/admin/users")
async def list_users(
    user_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    all_users_data = []
    total = 0
    
    # Get admin users from local database
    if not user_type or user_type == "admin":
        query_admins = db.query(Admin)
        if search:
            query_admins = query_admins.filter(Admin.username.contains(search))
        total_admins = query_admins.count()
        
        # Apply pagination only if filtering by admin type specifically
        if user_type == "admin":
            db_admins = query_admins.order_by(Admin.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        else:
            db_admins = query_admins.order_by(Admin.created_at.desc()).all()
        
        for admin in db_admins:
            all_users_data.append({
                "user_id": admin.admin_id,
                "username": admin.username,
                "user_type": "admin",
                "is_active": True,
                "totp_secret": None,
                "created_at": admin.created_at.isoformat() if admin.created_at else None,
                "updated_at": None,
            })
        total += total_admins
    
    # Get students from local auth database
    if not user_type or user_type == "student":
        query_students = db.query(Student)
        if search:
            query_students = query_students.filter(Student.username.contains(search))
        total_students = query_students.count()
        
        # Apply pagination only if filtering by student type specifically
        if user_type == "student":
            db_students = query_students.order_by(Student.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        else:
            db_students = query_students.order_by(Student.created_at.desc()).all()
        
        for student in db_students:
            all_users_data.append({
                "user_id": student.student_id,
                "username": student.username,
                "user_type": "student",
                "is_active": student.is_active,
                "totp_secret": student.totp_secret,
                "created_at": student.created_at.isoformat() if student.created_at else None,
                "updated_at": student.updated_at.isoformat() if student.updated_at else None,
            })
        total += total_students
    
    # Get teachers from local auth database
    if not user_type or user_type == "teacher":
        query_teachers = db.query(Teacher)
        if search:
            query_teachers = query_teachers.filter(Teacher.username.contains(search))
        total_teachers = query_teachers.count()
        
        # Apply pagination only if filtering by teacher type specifically
        if user_type == "teacher":
            db_teachers = query_teachers.order_by(Teacher.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        else:
            db_teachers = query_teachers.order_by(Teacher.created_at.desc()).all()
        
        for teacher in db_teachers:
            all_users_data.append({
                "user_id": teacher.teacher_id,
                "username": teacher.username,
                "user_type": "teacher",
                "is_active": teacher.is_active,
                "totp_secret": None,  # Teachers don't have 2FA
                "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
            })
        total += total_teachers
    
    # Sort the combined list by created_at in descending order
    all_users_data.sort(key=lambda x: x['created_at'] or '', reverse=True)
    
    # Apply pagination if we're combining multiple user types
    if user_type is None:  # Only paginate if getting all types
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        all_users_data = all_users_data[start_index:end_index]
    
    return {
        "users": all_users_data,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@app.post("/admin/user/add")
async def add_user_endpoint(
    user_data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Add new user (admin only)"""
    import secrets
    import string
    
    username = user_data.get("username")
    password = user_data.get("password")
    user_type = user_data.get("user_type")
    
    if not username or not user_type:
        raise HTTPException(status_code=400, detail="Username and user_type required")
    
    # Generate password if not provided
    if not password:
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    # Check if user exists in the appropriate table
    if user_type == "admin":
        existing = db.query(Admin).filter(Admin.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Admin already exists")
        
        # Create admin
        new_admin = Admin(
            username=username,
            password_hash=get_password_hash(password)
        )
        db.add(new_admin)
    else:
        # Check both student and teacher tables
        existing_student = db.query(Student).filter(Student.username == username).first()
        existing_teacher = db.query(Teacher).filter(Teacher.username == username).first()
        if existing_student or existing_teacher:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user in the appropriate auth table and also provision course data in data-node
        if user_type == "student":
            # Create student in auth DB
            new_student = Student(
                username=username,
                password_hash=get_password_hash(password),
                totp_secret=generate_totp_secret(),
                is_active=True,
            )
            db.add(new_student)
            db.commit()
            db.refresh(new_student)

            # Create corresponding student record in data-node
            data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
            internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")

            student_payload = {
                "student_name": username,
                "student_tags": []
            }
            headers = {"Internal-Token": internal_token}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{data_node_url}/add/student", json=student_payload, headers=headers)
                if response.status_code != status.HTTP_201_CREATED:
                    # Rollback auth record if course data creation fails
                    db.delete(new_student)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Failed to create student course data: {response.text}")
            except httpx.HTTPError as e:
                db.delete(new_student)
                db.commit()
                raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")

        elif user_type == "teacher":
            # Create teacher in auth DB
            new_teacher = Teacher(
                username=username,
                password_hash=get_password_hash(password),
                is_active=True,
            )
            db.add(new_teacher)
            db.commit()
            db.refresh(new_teacher)

            # Create corresponding teacher record in data-node
            data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
            internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")

            teacher_payload = {
                "teacher_name": username,
            }
            headers = {"Internal-Token": internal_token}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{data_node_url}/add/teacher", json=teacher_payload, headers=headers)
                if response.status_code != status.HTTP_201_CREATED:
                    # Rollback auth record if course data creation fails
                    db.delete(new_teacher)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Failed to create teacher course data: {response.text}")
            except httpx.HTTPError as e:
                db.delete(new_teacher)
                db.commit()
                raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
    
    db.commit()
    
    return {
        "success": True,
        "message": "User created successfully",
        "username": username,
        "password": password,  # Return generated password
        "user_type": user_type
    }


@app.post("/admin/user/delete")
async def delete_user_endpoint(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    user_id = data.get("user_id")
    user_type = data.get("user_type")
    
    if not user_id or not user_type:
        raise HTTPException(status_code=400, detail="user_id and user_type required")
    
    if user_type == "admin":
        admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        db.delete(admin)
    elif user_type == "student":
        student = db.query(Student).filter(Student.student_id == user_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        db.delete(student)
    elif user_type == "teacher":
        teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        db.delete(teacher)
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    db.commit()
    return {"success": True, "message": "User deleted successfully"}


@app.post("/admin/user/reset-2fa")
async def reset_user_2fa_endpoint(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reset user 2FA (admin only)"""
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username required")
    
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only students can have 2FA enabled (teachers don't have 2FA)
    if get_user_type(user) != "student":
        raise HTTPException(status_code=400, detail="Only students can have 2FA")
    
    # Reset TOTP secret using auth_helpers
    set_totp_secret(user, None)
    db.commit()
    
    return {"success": True, "message": "2FA reset successfully"}


@app.post("/admin/user/toggle-status")
async def toggle_user_status_endpoint(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only). Accepts optional user_type to avoid ID collisions."""
    user_id = data.get("user_id")
    is_active = data.get("is_active")
    user_type = data.get("user_type")
    
    if user_id is None or is_active is None:
        raise HTTPException(status_code=400, detail="user_id and is_active required")
    
    # If caller specifies user_type, use it directly to avoid cross-table ID collisions
    if user_type == "student":
        student = db.query(Student).filter(Student.student_id == user_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        student.is_active = is_active
        db.commit()
        return {"success": True, "message": f"Student {'activated' if is_active else 'deactivated'} successfully"}
    elif user_type == "teacher":
        teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        teacher.is_active = is_active
        db.commit()
        return {"success": True, "message": f"Teacher {'activated' if is_active else 'deactivated'} successfully"}
    elif user_type == "admin":
        admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        # Admin model may not have is_active; treat toggle as unsupported for admins
        raise HTTPException(status_code=400, detail="Toggling admin status is not supported")
    
    # Fallback: detect by probing tables in order (may be ambiguous if IDs overlap)
    student = db.query(Student).filter(Student.student_id == user_id).first()
    if student:
        student.is_active = is_active
        db.commit()
        return {"success": True, "message": f"Student {'activated' if is_active else 'deactivated'} successfully"}
    
    teacher = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
    if teacher:
        teacher.is_active = is_active
        db.commit()
        return {"success": True, "message": f"Teacher {'activated' if is_active else 'deactivated'} successfully"}
    
    admin = db.query(Admin).filter(Admin.admin_id == user_id).first()
    if admin:
        # Admin model may not have is_active; return a clear error
        raise HTTPException(status_code=400, detail="Toggling admin status is not supported")
    
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/admin/user/reset-password")
async def reset_user_password_endpoint(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only) - can set custom password or generate random one"""
    import secrets
    import string
    
    username = data.get("username")
    user_type = data.get("user_type")
    custom_password = data.get("new_password")  # Optional custom password
    
    if not username or not user_type:
        raise HTTPException(status_code=400, detail="username and user_type required")
    
    # Use custom password if provided, otherwise generate random
    if custom_password:
        if len(custom_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        new_password = custom_password
    else:
        # Generate a secure random password (12 characters)
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    new_password_hash = get_password_hash(new_password)
    
    # Update password in the appropriate table
    if user_type == "student":
        user = db.query(Student).filter(Student.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")
        user.password_hash = new_password_hash
    elif user_type == "teacher":
        user = db.query(Teacher).filter(Teacher.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="Teacher not found")
        user.password_hash = new_password_hash
    elif user_type == "admin":
        user = db.query(Admin).filter(Admin.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="Admin not found")
        user.password_hash = new_password_hash
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    db.commit()
    
    return {
        "success": True,
        "message": "Password reset successfully",
        "new_password": new_password,
        "username": username
    }


@app.post("/admin/student/update-tags")
async def update_student_tags_endpoint(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update student tags (admin only)"""
    student_id = data.get("student_id")
    student_tags = data.get("student_tags")
    
    if student_id is None or student_tags is None:
        raise HTTPException(status_code=400, detail="student_id and student_tags required")
    
    # Verify student exists in auth database
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student tags in data node
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Token": internal_token}
            payload = {
                "student_id": student_id,
                "student_tags": student_tags
            }
            response = await client.post(f"{data_node_url}/update/student", params={"student_id": student_id}, json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to update student tags: {response.text}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")
    
    return {"success": True, "message": "Student tags updated successfully"}


# Admin course management endpoints
@app.get("/admin/courses")
async def list_all_courses(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    course_type: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all courses (admin only)"""
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
    try:
        async with httpx.AsyncClient() as client:
            params = {"page": page, "page_size": page_size}
            if search:
                params["search"] = search
            if course_type:
                params["course_type"] = course_type
                
            headers = {"Internal-Token": internal_token}
            response = await client.get(f"{data_node_url}/get/courses", params=params, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {response.text}")
            
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")


@app.post("/admin/course/update")
async def update_course_admin(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update course (admin only)"""
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
    course_id = data.get("course_id")
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Token": internal_token}
            response = await client.post(
                f"{data_node_url}/update/course",
                params={"course_id": course_id},
                json=data,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to update course: {response.text}")
            
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")


@app.post("/admin/course/delete")
async def delete_course_admin(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete course (admin only)"""
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
    course_id = data.get("course_id")
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Token": internal_token}
            response = await client.post(
                f"{data_node_url}/delete/course",
                params={"course_id": course_id},
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to delete course: {response.text}")
            
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")


@app.post("/admin/courses/bulk-import")
async def bulk_import_courses_admin(
    courses: List[dict],
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Bulk import courses (admin only)"""
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Internal-Token": internal_token}
            response = await client.post(
                f"{data_node_url}/bulk/import/courses",
                json=courses,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to import courses: {response.text}")
            
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error contacting data node: {str(e)}")


@app.post("/admin/courses/batch-assign-teacher")
async def batch_assign_teacher_admin(
    data: dict,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Batch assign teacher to courses (admin only)"""
    data_node_url = os.getenv("DATA_NODE_URL", "http://localhost:8001")
    internal_token = os.getenv("INTERNAL_TOKEN", "change-this-internal-token")
    
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
            headers = {"Internal-Token": internal_token}
            
            for course_id in course_ids:
                try:
                    response = await client.post(
                        f"{data_node_url}/update/course",
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


# ===== System Settings Management =====
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


@app.get("/admin/settings", response_model=SystemSettingsResponse)
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


@app.put("/admin/settings", response_model=SystemSettingsResponse)
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


# ===== Refresh Token Endpoint =====
@app.post("/auth/refresh")
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Exchange refresh token for new access and refresh tokens"""
    try:
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("user_id")
        user_type = payload.get("user_type")
        username = payload.get("username")
        
        if not all([user_id, user_type, username]):
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Check if refresh token is revoked
        token_hash = hash_token(refresh_token)
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
        
        # Verify user still exists and is active
        user = await get_user_by_id(db, user_id, user_type)
        if not user or not is_active(user):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Revoke old refresh token
        db_token.is_revoked = True
        db.commit()
        
        # Generate new tokens
        new_access_token = create_access_token({
            "user_id": user_id,
            "username": username,
            "user_type": user_type
        })
        
        new_refresh_token = create_refresh_token({
            "user_id": user_id,
            "username": username,
            "user_type": user_type
        })
        
        # Store new refresh token in database
        new_token_hash = hash_token(new_refresh_token)
        new_db_token = RefreshToken(
            user_id=user_id,
            user_type=user_type,
            token_hash=new_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(new_db_token)
        db.commit()
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")


# ===== Password & 2FA Management Endpoints =====
@app.post("/user/change-password")
async def change_password(
    password_change: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Change user password (requires old password verification)"""
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # Get user from database
    user = await get_user_by_id(db, user_id, user_type)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify old password
    if not verify_password(password_change.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    user.password_hash = get_password_hash(password_change.new_password)
    db.commit()
    
    return {"success": True, "message": "Password changed successfully"}


@app.post("/user/2fa/setup")
async def setup_2fa(
    setup_request: TwoFASetupRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Setup 2FA for user (verify password first)"""
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # Get user from database
    user = await get_user_by_id(db, user_id, user_type)
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


@app.post("/user/2fa/verify")
async def verify_2fa_setup(
    verify_request: TwoFAVerifyRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with TOTP code"""
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # Get user from database
    user = await get_user_by_id(db, user_id, user_type)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify the TOTP code
    if not get_totp_secret(user):
        raise HTTPException(status_code=400, detail="2FA not set up")
    
    if not verify_totp(get_totp_secret(user), verify_request.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    return {
        "success": True,
        "message": "2FA verified successfully"
    }


@app.post("/user/2fa/disable")
async def disable_2fa(
    disable_request: TwoFADisableRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Disable 2FA for user (requires password and current 2FA code)"""
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # Get user from database
    user = await get_user_by_id(db, user_id, user_type)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not verify_password(disable_request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    # Verify 2FA code
    if not has_2fa(user):
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    
    if not verify_totp(get_totp_secret(user), disable_request.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    # Disable 2FA
    user.totp_secret = None
    if user_type == "student":
        user.has_2fa = False
    elif user_type == "teacher" and hasattr(user, 'has_2fa'):
        user.has_2fa = False
    db.commit()
    
    return {"success": True, "message": "2FA disabled successfully"}


@app.get("/user/2fa/status")
async def get_2fa_status(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get current user's 2FA status"""
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # Get user from database
    user = await get_user_by_id(db, user_id, user_type)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "has_2fa": has_2fa(user),
        "user_type": user_type,
        "username": user.username
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth_node"}


if __name__ == "__main__":
    import uvicorn

    # Get socket or HTTP config based on environment
    config = create_socket_server_config('auth_node', PORT)
    uvicorn.run(app, **config)

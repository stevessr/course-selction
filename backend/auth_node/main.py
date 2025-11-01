"""Authentication Node - User authentication and token management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os

from backend.common import (
    Base, Student, Teacher, Admin, RefreshToken, RegistrationCode, ResetCode,
    UserCreate, UserLogin, User2FA, UserResponse, AdminResponse,
    AdminCreate, AdminLogin,
    RegistrationCodeCreate, RegistrationCodeResponse,
    ResetCodeCreate, ResetCodeResponse,
    RefreshTokenResponse, AccessTokenResponse,
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
init_database(engine, Base)


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
    # Verify registration code if provided
    if user_data.registration_code:
        reg_code = db.query(RegistrationCode).filter(
            RegistrationCode.code == user_data.registration_code,
            RegistrationCode.is_used == False,
            RegistrationCode.expires_at > datetime.utcnow()
        ).first()
        
        if not reg_code:
            raise HTTPException(status_code=400, detail="Invalid or expired registration code")
        
        if reg_code.user_type != user_data.user_type:
            raise HTTPException(status_code=400, detail="Registration code type mismatch")
    else:
        # For now, allow registration without code for testing
        pass
    
    # Check if user already exists in the appropriate table
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate 2FA secret only for students (not for teachers/admins)
    totp_secret = generate_totp_secret() if user_data.user_type == "student" else None
    
    # Create user in appropriate table
    if user_data.user_type == "student":
        db_user = Student(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            student_name=user_data.username,  # Set to username initially
            totp_secret=totp_secret,
            is_active=True,
            student_courses=[],
            student_tags=[]
        )
    elif user_data.user_type == "teacher":
        db_user = Teacher(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            teacher_name=user_data.username,  # Set to username initially
            is_active=True,
            teacher_courses=[]
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Mark registration code as used
    if user_data.registration_code:
        reg_code.is_used = True
        reg_code.used_by = get_user_id(db_user)
        db.commit()
    
    # Revoke any existing refresh tokens for this user (shouldn't exist for new user, but be safe)
    existing_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == get_user_id(db_user),
        RefreshToken.is_revoked == False
    ).all()
    for token in existing_tokens:
        token.is_revoked = True
    
    # Generate new refresh token
    refresh_token = create_refresh_token({
        "user_id": get_user_id(db_user),
        "username": db_user.username,
        "user_type": user_data.user_type
    })
    
    # Store new refresh token
    token_hash = hash_token(refresh_token)
    db_token = RefreshToken(
        user_id=get_user_id(db_user),
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_token)
    db.commit()
    
    # Get TOTP URI for QR code
    totp_uri = get_totp_uri(totp_secret, user_data.username)
    
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


@app.post("/login/v1", response_model=RefreshTokenResponse)
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
        expires_at=datetime.utcnow() + timedelta(days=7)
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
        
        user = get_user_by_id(db, payload.get("user_id"), payload.get("user_type"))
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
            user = get_user_by_id(db, user_id, user_type)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Return UserResponse
            return UserResponse(
                user_id=get_user_id(user),
                username=user.username,
                user_type=get_user_type(user),
                is_active=is_active(user),
                created_at=user.created_at
            )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# Admin endpoints
@app.post("/login/admin", response_model=AccessTokenResponse)
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
    
    return {
        "access_token": access_token,
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


@app.post("/generate/registration-code", response_model=RegistrationCodeResponse)
async def generate_registration_code_endpoint(
    code_data: RegistrationCodeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate registration code (admin only)"""
    code = generate_registration_code()
    expires_at = datetime.utcnow() + timedelta(days=code_data.expires_days)
    
    db_code = RegistrationCode(
        code=code,
        user_type=code_data.user_type,
        created_by=current_admin.admin_id,
        expires_at=expires_at
    )
    db.add(db_code)
    db.commit()
    
    return {
        "code": code,
        "user_type": code_data.user_type,
        "expires_at": expires_at
    }


@app.post("/generate/reset-code", response_model=ResetCodeResponse)
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
    expires_at = datetime.utcnow() + timedelta(days=reset_data.expires_days)
    
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
        ResetCode.expires_at > datetime.utcnow()
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
    # This endpoint now needs to handle separate tables for students and teachers
    students_list = []
    teachers_list = []
    admins_list = []
    
    # Query students if needed
    if not user_type or user_type == "student":
        query_students = db.query(Student)
        if search:
            query_students = query_students.filter(Student.username.contains(search))
        total_students = query_students.count()
        db_students = query_students.order_by(Student.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        for student in db_students:
            students_list.append({
                "user_id": student.student_id,
                "username": student.username,
                "user_type": "student",
                "is_active": student.is_active,
                "totp_secret": student.totp_secret if student.totp_secret else None,
                "created_at": student.created_at.isoformat() if student.created_at else None,
                "updated_at": student.updated_at.isoformat() if student.updated_at else None,
            })
    
    # Query teachers if needed
    if not user_type or user_type == "teacher":
        query_teachers = db.query(Teacher)
        if search:
            query_teachers = query_teachers.filter(Teacher.username.contains(search))
        total_teachers = query_teachers.count()
        db_teachers = query_teachers.order_by(Teacher.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        for teacher in db_teachers:
            teachers_list.append({
                "user_id": teacher.teacher_id,
                "username": teacher.username,
                "user_type": "teacher",
                "is_active": teacher.is_active,
                "totp_secret": None,  # Teachers don't have 2FA
                "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
            })
    
    # Query admins if needed
    if not user_type or user_type == "admin":
        query_admins = db.query(Admin)
        if search:
            query_admins = query_admins.filter(Admin.username.contains(search))
        total_admins = query_admins.count()
        db_admins = query_admins.order_by(Admin.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
        for admin in db_admins:
            admins_list.append({
                "user_id": admin.admin_id,
                "username": admin.username,
                "user_type": "admin",
                "is_active": True,
                "totp_secret": None,
                "created_at": admin.created_at.isoformat() if admin.created_at else None,
                "updated_at": None,
            })
    
    # Combine lists based on user_type filter and pagination
    all_users = []
    if user_type == "student":
        all_users = students_list
        total = total_students
    elif user_type == "teacher":
        all_users = teachers_list
        total = total_teachers
    elif user_type == "admin":
        all_users = admins_list
        total = total_admins
    else:
        # Combine all user types - this is more complex to handle pagination properly
        # For simplicity, let's implement it as separate queries and combine the results
        all_users = students_list + teachers_list + admins_list
        total = total_students + total_teachers + total_admins
    
    return {
        "users": all_users,
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
        
        # Create user in the appropriate table
        if user_type == "student":
            new_user = Student(
                username=username,
                password_hash=get_password_hash(password),
                student_name=username,  # Set to username initially
                is_active=True,
                student_courses=[],
                student_tags=[]
            )
        elif user_type == "teacher":
            new_user = Teacher(
                username=username,
                password_hash=get_password_hash(password),
                teacher_name=username,  # Set to username initially
                is_active=True,
                teacher_courses=[]
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        db.add(new_user)
    
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
    
    user = get_user_by_username(db, username)
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
    """Toggle user active status (admin only)"""
    user_id = data.get("user_id")
    is_active = data.get("is_active")
    
    if user_id is None or is_active is None:
        raise HTTPException(status_code=400, detail="user_id and is_active required")
    
    # Determine user type to query the correct table
    # We'll try each table based on the ID
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
    
    raise HTTPException(status_code=404, detail="User not found")


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

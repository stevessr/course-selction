"""Authentication Node - User authentication and token management service"""
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os

from backend.common import (
    Base, User, Admin, RefreshToken, RegistrationCode, ResetCode,
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
    
    # Check if user already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate 2FA secret
    totp_secret = generate_totp_secret()
    
    # Create user
    db_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        user_type=user_data.user_type,
        totp_secret=totp_secret,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Mark registration code as used
    if user_data.registration_code:
        reg_code.is_used = True
        reg_code.used_by = db_user.user_id
        db.commit()
    
    # Generate refresh token
    refresh_token = create_refresh_token({
        "user_id": db_user.user_id,
        "username": db_user.username,
        "user_type": db_user.user_type
    })
    
    # Store refresh token
    token_hash = hash_token(refresh_token)
    db_token = RefreshToken(
        user_id=db_user.user_id,
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
        
        user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify TOTP code
        if not verify_totp(user.totp_secret, totp_data.totp_code):
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Generate access token with different expiration based on user type
        from datetime import timedelta
        if user.user_type == "teacher":
            # Teachers get 2 hours for longer sessions managing courses
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
            }, expires_delta=timedelta(hours=2))
            expires_in = 2 * 3600  # 2 hours in seconds
        else:
            # Default 30 minutes for students and other user types
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
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
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    # Generate refresh token
    refresh_token = create_refresh_token({
        "user_id": user.user_id,
        "username": user.username,
        "user_type": user.user_type
    })
    
    # Store refresh token
    token_hash = hash_token(refresh_token)
    db_token = RefreshToken(
        user_id=user.user_id,
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
        
        user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify TOTP code
        if not verify_totp(user.totp_secret, totp_data.totp_code):
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Generate access token with different expiration based on user type
        from datetime import timedelta
        if user.user_type == "teacher":
            # Teachers get 2 hours for longer sessions managing courses
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
            }, expires_delta=timedelta(hours=2))
            expires_in = 2 * 3600  # 2 hours in seconds
        else:
            # Default 30 minutes for students and other user types
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
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
        
        user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has 2FA enabled (totp_secret is not NULL)
        has_2fa = user.totp_secret is not None and user.totp_secret != ""
        
        return {
            "has_2fa": has_2fa,
            "user_type": user.user_type,
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
        
        user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has 2FA disabled
        if user.totp_secret is not None and user.totp_secret != "":
            raise HTTPException(status_code=400, detail="User has 2FA enabled, cannot use this endpoint")
        
        # Generate access token with different expiration based on user type
        from datetime import timedelta
        if user.user_type == "teacher":
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
            }, expires_delta=timedelta(hours=2))
            expires_in = 2 * 3600
        else:
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
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
        
        user = db.query(User).filter(User.user_id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For students, verify 2FA
        if user.user_type == "student":
            if not verify_totp(user.totp_secret, totp_data.totp_code):
                raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Generate new access token with different expiration based on user type
        from datetime import timedelta
        if user.user_type == "teacher":
            # Teachers get 2 hours for longer sessions managing courses
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
            }, expires_delta=timedelta(hours=2))
            expires_in = 2 * 3600  # 2 hours in seconds
        else:
            # Default 30 minutes for students and other user types
            access_token = create_access_token({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type
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
            # Look up regular user
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Return UserResponse
            return UserResponse(
                user_id=user.user_id,
                username=user.username,
                user_type=user.user_type,
                is_active=user.is_active,
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
    user = db.query(User).filter(User.username == reset_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    code = generate_reset_code()
    expires_at = datetime.utcnow() + timedelta(days=reset_data.expires_days)
    
    db_code = ResetCode(
        code=code,
        user_id=user.user_id,
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
    
    # Get user
    user = db.query(User).filter(User.user_id == db_code.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new TOTP secret
    new_secret = generate_totp_secret()
    
    # Verify the new TOTP code with new secret
    if not verify_totp(new_secret, new_totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    # Update user's TOTP secret
    user.totp_secret = new_secret
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
    query_users = db.query(User)
    query_admins = db.query(Admin)
    
    # Apply filters
    if user_type:
        if user_type == "admin":
            query_users = query_users.filter(User.user_id == -1)  # No match
        else:
            query_users = query_users.filter(User.user_type == user_type)
            query_admins = query_admins.filter(Admin.admin_id == -1)  # No match
    
    if search:
        query_users = query_users.filter(User.username.contains(search))
        query_admins = query_admins.filter(Admin.username.contains(search))
    
    # Get total count
    total_users = query_users.count()
    total_admins = query_admins.count() if not user_type or user_type == "admin" else 0
    total = total_users + total_admins
    
    # Pagination
    offset = (page - 1) * page_size
    users_list = []
    
    # Get users
    if not user_type or user_type != "admin":
        db_users = query_users.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        for user in db_users:
            users_list.append({
                "user_id": user.user_id,
                "username": user.username,
                "user_type": user.user_type,
                "is_active": user.is_active,
                "totp_secret": user.totp_secret if user.user_type == "student" else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            })
    
    # Get admins if needed
    remaining = page_size - len(users_list)
    if remaining > 0 and (not user_type or user_type == "admin"):
        admin_offset = max(0, offset - total_users)
        db_admins = query_admins.order_by(Admin.created_at.desc()).offset(admin_offset).limit(remaining).all()
        for admin in db_admins:
            users_list.append({
                "user_id": None,
                "admin_id": admin.admin_id,
                "username": admin.username,
                "user_type": "admin",
                "is_active": True,
                "totp_secret": None,
                "created_at": admin.created_at.isoformat() if admin.created_at else None,
                "updated_at": None,
            })
    
    return {
        "users": users_list,
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
    
    # Check if user exists
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
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        new_user = User(
            username=username,
            password_hash=get_password_hash(password),
            user_type=user_type,
            is_active=True
        )
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
    else:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
    
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
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_type != "student":
        raise HTTPException(status_code=400, detail="Only students have 2FA")
    
    # Reset TOTP secret
    user.totp_secret = None
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
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    
    return {"success": True, "message": f"User {'activated' if is_active else 'deactivated'} successfully"}


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

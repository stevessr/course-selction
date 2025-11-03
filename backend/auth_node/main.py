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
    AuthBase, Student, Teacher, Admin, RefreshToken, RegistrationCode, ResetCode, SystemSettings,
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

# Import router factories
from backend.auth_node.routers.admin_course_routes import create_admin_course_router
from backend.auth_node.routers.settings_routes import create_settings_router, ensure_system_settings
from backend.auth_node.routers.user_account_routes import create_user_account_router
from backend.auth_node.routers.admin_basic_routes import create_admin_basic_router
from backend.auth_node.routers.auth_routes import create_auth_router
from backend.auth_node.routers.user_management_routes import create_user_management_router

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


async def verify_internal_token_header(
    internal_token: str = Header(..., alias="Internal-Token")
):
    """Verify internal service token"""
    if internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal token"
        )


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


async def verify_admin_or_internal(
    authorization: Optional[str] = Header(None),
    internal_token: Optional[str] = Header(None, alias="Internal-Token"),
    db: Session = Depends(get_db)
):
    """Verify either admin token or internal service token"""
    # Check internal token first
    if internal_token and internal_token == INTERNAL_TOKEN:
        return None  # Internal service call
    
    # Otherwise require admin auth
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required"
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = await get_current_user_from_token(token)
        
        if payload.get("user_type") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        admin = db.query(Admin).filter(Admin.admin_id == payload.get("user_id")).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return admin
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


# Create and include routers
admin_course_router = create_admin_course_router(get_db, get_current_admin)
settings_router = create_settings_router(get_db, get_current_admin)
user_account_router = create_user_account_router(get_db)
admin_basic_router = create_admin_basic_router(get_db, get_current_admin)
auth_router = create_auth_router(get_db)
user_management_router = create_user_management_router(get_db, verify_admin_or_internal, get_current_admin)

app.include_router(admin_course_router)
app.include_router(settings_router)
app.include_router(user_account_router)
app.include_router(admin_basic_router)
app.include_router(auth_router)
app.include_router(user_management_router)
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
        user = get_user_by_id(db, user_id, user_type)
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
        raise HTTPException(status_code=401, detail=str(e))


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

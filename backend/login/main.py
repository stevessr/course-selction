from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import secrets
import pyotp
from ..database import User, Admin, Teacher, Student, OneTimeCredit, SessionLocal, engine
from ..settings import settings
from ..utils import create_access_token, create_refresh_token, verify_password, get_password_hash, verify_token
from ..node_manager import node_manager, verify_protection_token


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class LoginRequest(BaseModel):
    user_name: str
    user_password: str

class LoginResponse(BaseModel):
    refresh_token: str
    expire: int

class Login2FABody(BaseModel):
    two_fa: int

class Login2FAHeader(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class RegisterRequest(BaseModel):
    user_name: str
    user_password: str
    user_type: str

class RegisterResponse(BaseModel):
    two_fa_code: str
    refresh_token: str
    expire: int

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class Change2FARequest(BaseModel):
    one_time_credit: int
    new_2fa: int

class ChangeNameRequest(BaseModel):
    new_name: str

class GetUserRequest(BaseModel):
    access_token: str

class GetUserResponse(BaseModel):
    user_id: int
    user_name: str
    user_type: str

class AdminLoginRequest(BaseModel):
    admin_name: str
    admin_password: str

class AddAdminRequest(BaseModel):
    admin_name: str
    admin_password: str

class DeleteAdminRequest(BaseModel):
    admin_name: str

class GetAdminRequest(BaseModel):
    admin_name: str

class GetAdminResponse(BaseModel):
    admin_id: int
    admin_name: str

class GetAdminAllResponse(BaseModel):
    admins: List[Dict[str, Any]]

class AddTeacherRequest(BaseModel):
    teacher_name: str
    teacher_password: str

class DeleteTeacherRequest(BaseModel):
    teacher_name: str

class GetTeacherRequest(BaseModel):
    teacher_name: str

class GetTeacherResponse(BaseModel):
    teacher_id: int
    teacher_name: str

class GetTeacherAllResponse(BaseModel):
    teachers: List[Dict[str, Any]]

class AddStudentsRequest(BaseModel):
    students: List[Dict[str, Any]]  # {student_id: int, student_name: str, student_password: str, student_type: str}

class DeleteStudentsRequest(BaseModel):
    students: List[str]

class GetStudentsRequest(BaseModel):
    students: List[str]

class GetStudentsResponse(BaseModel):
    students: List[Dict[str, Any]]  # {student_id: int, student_name: str}

class GetStudentsAllResponse(BaseModel):
    students: List[Dict[str, Any]]  # {student_id: int, student_name: str}

class AdminResetPasswordRequest(BaseModel):
    user_name: str
    new_password: str

class AdminUpdateUserRequest(BaseModel):
    user_name: str
    new_user_name: str

class AdminGenerateCreditRequest(BaseModel):
    credit_count: int = 1

class CreditInfo(BaseModel):
    credit_id: str
    created_at: str

class AdminGenerateCreditResponse(BaseModel):
    credits: List[CreditInfo]

class MasterResponse(BaseModel):
    ip: str
    port: int

class SlaveResponse(BaseModel):
    slaves: Dict[str, int]  # map of ip to port


# Initialize the app
app = FastAPI(title="Login Node", version="1.0.0")

# Add startup event to initialize node manager and default data
@app.on_event("startup")
async def startup_event():
    from ..node_manager import initialize_node
    from ..initialize import initialize_system
    await initialize_node()
    # Initialize default admins and configuration
    initialize_system()

# Create tables
from ..database import Base
Base.metadata.create_all(bind=engine)


@app.post("/login/v1")
def login_v1(request: LoginRequest, db: Session = Depends(get_db)):
    # Find user by username
    user = db.query(User).filter(User.user_name == request.user_name).first()
    if not user or not verify_password(request.user_password, user.user_password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate refresh token
    refresh_token_data = {"sub": str(user.user_id), "type": "refresh"}
    refresh_token = create_refresh_token(
        data=refresh_token_data,
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

    return LoginResponse(
        refresh_token=refresh_token,
        expire=int((datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)).timestamp())
    )


@app.post("/login/v2")
def login_v2(request: Request, two_fa: Login2FABody, db: Session = Depends(get_db)):
    # Extract refresh token from header
    refresh_token = request.headers.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    # Verify refresh token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(refresh_token, credentials_exception)

    # Find user in database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise credentials_exception

    # Verify 2FA code (in a real implementation, this would be more secure)
    # For now we'll just check if the provided 2FA matches the stored code
    if user.two_factor_code and str(two_fa.two_fa) != user.two_factor_code:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # Generate access token
    access_token_data = {"sub": str(user.user_id), "type": "access"}
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/logout")
def logout(request: Request, body: LogoutRequest = None, db: Session = Depends(get_db)):
    # Logout can use either access token in header or refresh token in body
    access_token = request.headers.get("access_token")
    refresh_token = body.refresh_token if body else None

    # In a real implementation, we would invalidate the tokens
    # For now we just return success
    return {"message": "Logged out successfully"}


@app.post("/register/v1")
def register_v1(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.user_name == request.user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Generate 2FA secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    two_fa_code = totp.now()  # Current code

    # Hash the password
    password_hash = get_password_hash(request.user_password)

    # Create new user
    db_user = User(
        user_name=request.user_name,
        user_password_hash=password_hash,
        user_type=request.user_type,
        two_factor_code=secret  # Store the secret, not the current code
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate refresh token
    refresh_token_data = {"sub": str(db_user.user_id), "type": "refresh"}
    refresh_token = create_refresh_token(
        data=refresh_token_data,
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

    return RegisterResponse(
        two_fa_code=two_fa_code,
        refresh_token=refresh_token,
        expire=int((datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)).timestamp())
    )


@app.post("/register/v2")
def register_v2(request: Request, two_fa: Login2FABody, db: Session = Depends(get_db)):
    # Extract refresh token from header
    refresh_token = request.headers.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    # Verify refresh token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(refresh_token, credentials_exception)

    # Find user in database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise credentials_exception

    # Verify 2FA code
    totp = pyotp.TOTP(user.two_factor_code)
    if not totp.verify(str(two_fa.two_fa)):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # Generate access token
    access_token_data = {"sub": str(user.user_id), "type": "access"}
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/change/password")
def change_password(request: Request, change_request: ChangePasswordRequest, db: Session = Depends(get_db)):
    # Extract access token from header
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify access token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(access_token, credentials_exception)

    # Find user in database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise credentials_exception

    # Verify old password
    if not verify_password(change_request.old_password, user.user_password_hash):
        raise HTTPException(status_code=401, detail="Old password incorrect")

    # Hash new password
    new_password_hash = get_password_hash(change_request.new_password)

    # Update password
    user.user_password_hash = new_password_hash
    db.commit()

    # Generate new access token
    new_access_token_data = {"sub": str(user.user_id), "type": "access"}
    new_access_token = create_access_token(
        data=new_access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": new_access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/change/2fa")
def change_2fa(request: Request, change_request: Change2FARequest, db: Session = Depends(get_db)):
    # Extract refresh token from header
    refresh_token = request.headers.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    # Verify refresh token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(refresh_token, credentials_exception)

    # Find user in database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise credentials_exception

    # Verify one-time credential (in a real implementation, this might be an OTP sent to email/phone)
    # For this example, we'll just accept the provided value as verification
    # In reality, you'd have some other verification mechanism

    # Update 2FA secret
    new_secret = pyotp.random_base32()
    user.two_factor_code = new_secret
    db.commit()

    # Generate new access token
    new_access_token_data = {"sub": str(user.user_id), "type": "access"}
    new_access_token = create_access_token(
        data=new_access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": new_access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/change/name")
def change_name(request: Request, change_request: ChangeNameRequest, db: Session = Depends(get_db)):
    # Extract access token from header
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify access token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(access_token, credentials_exception)

    # Find user in database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise credentials_exception

    # Update username
    user.user_name = change_request.new_name
    db.commit()

    # Generate new access token
    new_access_token_data = {"sub": str(user.user_id), "type": "access"}
    new_access_token = create_access_token(
        data=new_access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": new_access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/get/user")
def get_user(request: Request, db: Session = Depends(get_db)):
    # Extract access token from header
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify access token
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id_str = verify_token(access_token, credentials_exception)

    # Check if this is an admin token (format: "admin_{admin_id}")
    if user_id_str.startswith("admin_"):
        admin_id = int(user_id_str.replace("admin_", ""))
        admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
        if not admin:
            raise credentials_exception

        return GetUserResponse(
            user_id=admin.admin_id,
            user_name=admin.admin_name,
            user_type="admin"
        )
    else:
        # Regular user (teacher or student)
        user = db.query(User).filter(User.user_id == int(user_id_str)).first()
        if not user:
            raise credentials_exception

        return GetUserResponse(
            user_id=user.user_id,
            user_name=user.user_name,
            user_type=user.user_type
        )


@app.post("/login/admin")
def login_admin(request: AdminLoginRequest, db: Session = Depends(get_db)):
    # Find admin by name
    admin = db.query(Admin).filter(Admin.admin_name == request.admin_name).first()
    if not admin or not verify_password(request.admin_password, admin.admin_password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate access token
    access_token_data = {"sub": f"admin_{admin.admin_id}", "type": "access"}
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/add/admin")
def add_admin(request: Request, admin_request: AddAdminRequest, db: Session = Depends(get_db)):
    # Verify admin access token (in a real implementation, this would validate the admin token)
    # For now we'll just check that the token was provided
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.admin_name == admin_request.admin_name).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Hash the password
    password_hash = get_password_hash(admin_request.admin_password)

    # Create new admin
    db_admin = Admin(
        admin_name=admin_request.admin_name,
        admin_password_hash=password_hash
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)

    # Generate new access token
    new_access_token_data = {"sub": f"admin_{db_admin.admin_id}", "type": "access"}
    new_access_token = create_access_token(
        data=new_access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": new_access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/delete/admin")
def delete_admin(request: Request, admin_request: DeleteAdminRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Find admin to delete
    admin = db.query(Admin).filter(Admin.admin_name == admin_request.admin_name).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    db.delete(admin)
    db.commit()

    return {"success": True}


@app.post("/get/admin")
def get_admin(request: Request, admin_request: GetAdminRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Find admin
    admin = db.query(Admin).filter(Admin.admin_name == admin_request.admin_name).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    return GetAdminResponse(
        admin_id=admin.admin_id,
        admin_name=admin.admin_name
    )


@app.post("/get/admin/all")
def get_all_admins(request: Request, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Get all admins
    admins = db.query(Admin).all()

    result = []
    for admin in admins:
        result.append({
            "admin_id": admin.admin_id,
            "admin_name": admin.admin_name
        })

    return GetAdminAllResponse(admins=result)


@app.post("/add/teacher")
def add_teacher(request: Request, teacher_request: AddTeacherRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Check if teacher already exists
    existing_teacher = db.query(Teacher).filter(Teacher.teacher_name == teacher_request.teacher_name).first()
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Teacher already exists")

    # Hash the password
    password_hash = get_password_hash(teacher_request.teacher_password)

    # Create new teacher
    db_teacher = Teacher(
        teacher_name=teacher_request.teacher_name,
        # Note: Teachers table in our schema doesn't have a password field
        # We might need to modify the schema to include teacher_password
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)

    # Generate new access token
    new_access_token_data = {"sub": f"teacher_{db_teacher.teacher_id}", "type": "access"}
    new_access_token = create_access_token(
        data=new_access_token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": new_access_token,
        "expire": int((datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    }


@app.post("/delete/teacher")
def delete_teacher(request: Request, teacher_request: DeleteTeacherRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Find teacher to delete
    teacher = db.query(Teacher).filter(Teacher.teacher_name == teacher_request.teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    db.delete(teacher)
    db.commit()

    return {"success": True}


@app.post("/get/teacher")
def get_teacher(request: Request, teacher_request: GetTeacherRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Find teacher
    teacher = db.query(Teacher).filter(Teacher.teacher_name == teacher_request.teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return GetTeacherResponse(
        teacher_id=teacher.teacher_id,
        teacher_name=teacher.teacher_name
    )


@app.post("/get/teacher/all")
def get_all_teachers(request: Request, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Get all teachers
    teachers = db.query(Teacher).all()

    result = []
    for teacher in teachers:
        result.append({
            "teacher_id": teacher.teacher_id,
            "teacher_name": teacher.teacher_name
        })

    return GetTeacherAllResponse(teachers=result)


@app.post("/add/students")
def add_students(request: Request, students_request: AddStudentsRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    for student_data in students_request.students:
        # Check if student already exists
        existing_student = db.query(Student).filter(Student.student_name == student_data["student_name"]).first()
        if existing_student:
            continue  # Skip if already exists

        # Create new student
        db_student = Student(
            student_id=student_data["student_id"],
            student_name=student_data["student_name"]
        )
        db.add(db_student)

    db.commit()

    return {"success": True}


@app.post("/delete/students")
def delete_students(request: Request, students_request: DeleteStudentsRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    for student_name in students_request.students:
        # Find student to delete
        student = db.query(Student).filter(Student.student_name == student_name).first()
        if student:
            db.delete(student)

    db.commit()

    return {"success": True}


@app.post("/get/students")
def get_students(request: Request, students_request: GetStudentsRequest, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    result = []
    for student_name in students_request.students:
        student = db.query(Student).filter(Student.student_name == student_name).first()
        if student:
            result.append({
                "student_id": student.student_id,
                "student_name": student.student_name
            })

    return GetStudentsResponse(students=result)


@app.post("/get/students/all")
def get_all_students(request: Request, db: Session = Depends(get_db)):
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Get all students
    students = db.query(Student).all()

    result = []
    for student in students:
        result.append({
            "student_id": student.student_id,
            "student_name": student.student_name
        })

    return GetStudentsAllResponse(students=result)


@app.post("/master")
async def get_master(request: Request):
    # Verify protection token
    protection_token = request.headers.get("protection_token")
    verify_protection_token(protection_token)

    # Use node manager to get the actual master
    master_node = await node_manager.get_master_node("login")
    if master_node:
        # Parse the URL to get host and port
        import urllib.parse
        parsed = urllib.parse.urlparse(master_node)
        ip = parsed.hostname
        port = parsed.port
        return MasterResponse(ip=ip, port=port)
    else:
        # Fallback to this node
        return MasterResponse(ip="localhost", port=8002)


@app.post("/slave")
async def get_slaves(request: Request):
    # Verify protection token
    protection_token = request.headers.get("protection_token")
    verify_protection_token(protection_token)

    # Use node manager to get slave nodes
    slave_nodes = await node_manager.get_slave_nodes("login")
    slaves = {}
    for node in slave_nodes:
        import urllib.parse
        parsed = urllib.parse.urlparse(node)
        slaves[parsed.hostname] = parsed.port

    return SlaveResponse(slaves=slaves)



# Admin management endpoints

@app.post("/admin/reset-password")
def admin_reset_password(request: Request, reset_request: AdminResetPasswordRequest, db: Session = Depends(get_db)):
    """Admin endpoint to reset a user's password"""
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify it's an admin token
    try:
        user_id_str = verify_token(access_token, HTTPException(status_code=401, detail="Invalid token"))
        if not user_id_str.startswith("admin_"):
            raise HTTPException(status_code=403, detail="Admin access required")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Find user
    user = db.query(User).filter(User.user_name == reset_request.user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash new password
    new_password_hash = get_password_hash(reset_request.new_password)

    # Update password
    user.user_password_hash = new_password_hash
    db.commit()

    return {"success": True, "message": f"Password reset for user {reset_request.user_name}"}


@app.post("/admin/update-user")
def admin_update_user(request: Request, update_request: AdminUpdateUserRequest, db: Session = Depends(get_db)):
    """Admin endpoint to update a user's username"""
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify it's an admin token
    try:
        user_id_str = verify_token(access_token, HTTPException(status_code=401, detail="Invalid token"))
        if not user_id_str.startswith("admin_"):
            raise HTTPException(status_code=403, detail="Admin access required")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Find user
    user = db.query(User).filter(User.user_name == update_request.user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if new username already exists
    existing_user = db.query(User).filter(User.user_name == update_request.new_user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Update username
    user.user_name = update_request.new_user_name
    db.commit()

    return {"success": True, "message": f"Username updated to {update_request.new_user_name}"}


@app.post("/admin/generate-credit", response_model=AdminGenerateCreditResponse)
def admin_generate_credit(request: Request, credit_request: AdminGenerateCreditRequest, db: Session = Depends(get_db)):
    """Admin endpoint to generate one_time_credits for 2FA reset (UUID-based, anyone can use)"""
    # Verify admin access token
    access_token = request.headers.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Verify it's an admin token
    try:
        user_id_str = verify_token(access_token, HTTPException(status_code=401, detail="Invalid token"))
        if not user_id_str.startswith("admin_"):
            raise HTTPException(status_code=403, detail="Admin access required")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Generate multiple UUID-based credits
    import uuid
    credits = []
    for _ in range(credit_request.credit_count):
        credit = OneTimeCredit(
            credit_id=str(uuid.uuid4()),
            is_used=False,
            created_at=datetime.utcnow()
        )
        db.add(credit)
        credits.append(CreditInfo(
            credit_id=credit.credit_id,
            created_at=credit.created_at.isoformat()
        ))

    db.commit()

    return AdminGenerateCreditResponse(credits=credits)
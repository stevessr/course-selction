from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import uuid
from ..database import Course, Student, Teacher, SessionLocal, engine
from ..settings import settings
from ..node_manager import node_manager, verify_protection_token


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class CourseBase(BaseModel):
    course_id: int
    course_name: str
    course_credit: int
    course_type: str
    course_teacher_id: int
    course_time_begin: int
    course_time_end: int
    course_location: str
    course_capacity: int
    course_selected: int = 0

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    course_id: int
    course_name: Optional[str] = None
    course_credit: Optional[int] = None
    course_type: Optional[str] = None
    course_teacher_id: Optional[int] = None
    course_time_begin: Optional[int] = None
    course_time_end: Optional[int] = None
    course_location: Optional[str] = None
    course_capacity: Optional[int] = None
    course_selected: Optional[int] = None

class StudentBase(BaseModel):
    student_id: int
    student_name: str

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    student_id: int
    student_name: Optional[str] = None

class TeacherBase(BaseModel):
    teacher_id: int
    teacher_name: str

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(BaseModel):
    teacher_id: int
    teacher_name: Optional[str] = None

class SelectCourseRequest(BaseModel):
    student_id: int
    course_id: int

class DeselectCourseRequest(BaseModel):
    student_id: int
    course_id: int

class GetCourseRequest(BaseModel):
    course_id: int

class DeleteCourseRequest(BaseModel):
    course_id: int

class DeleteStudentRequest(BaseModel):
    student_id: int

class DeleteTeacherRequest(BaseModel):
    teacher_id: int

class MasterResponse(BaseModel):
    ip: str
    port: int

class SlaveResponse(BaseModel):
    slaves: Dict[str, int]  # map of ip to port


# Initialize the app
app = FastAPI(title="Course Data Node", version="1.0.0")

# Add startup event to initialize node manager
@app.on_event("startup")
async def startup_event():
    from ..node_manager import initialize_node
    await initialize_node()

# Create tables
from ..database import Base
Base.metadata.create_all(bind=engine)


@app.post("/add/course")
def add_course(course: CourseCreate, db: Session = Depends(get_db)):
    # Check if course already exists
    existing_course = db.query(Course).filter(Course.course_id == course.course_id).first()
    if existing_course:
        raise HTTPException(status_code=400, detail="Course already exists")
    
    # Check if teacher exists (for now, just verify it's a positive ID)
    if course.course_teacher_id <= 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Create new course
    db_course = Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return {"message": "Course added successfully", "course_id": db_course.course_id}


@app.post("/add/student")
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    # Check if student already exists
    existing_student = db.query(Student).filter(Student.student_id == student.student_id).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    # Create new student
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"message": "Student added successfully", "student_id": db_student.student_id}


@app.post("/add/teacher")
def add_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    # Check if teacher already exists
    existing_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher.teacher_id).first()
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Teacher already exists")
    
    # Create new teacher
    db_teacher = Teacher(**teacher.dict())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return {"message": "Teacher added successfully", "teacher_id": db_teacher.teacher_id}


@app.post("/delete/course")
def delete_course(request: DeleteCourseRequest, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.course_id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}


@app.post("/delete/student")
def delete_student(request: DeleteStudentRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}


@app.post("/delete/teacher")
def delete_teacher(request: DeleteTeacherRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.teacher_id == request.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted successfully"}


@app.post("/update/course")
def update_course(course_update: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.course_id == course_update.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Update only provided fields
    update_data = course_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "course_id":  # Don't update the ID
            setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    return {"message": "Course updated successfully", "course_id": course.course_id}


@app.post("/update/student")
def update_student(student_update: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_update.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update only provided fields
    update_data = student_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "student_id":  # Don't update the ID
            setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    return {"message": "Student updated successfully", "student_id": student.student_id}


@app.post("/update/teacher")
def update_teacher(teacher_update: TeacherUpdate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_update.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Update only provided fields
    update_data = teacher_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "teacher_id":  # Don't update the ID
            setattr(teacher, field, value)
    
    db.commit()
    db.refresh(teacher)
    return {"message": "Teacher updated successfully", "teacher_id": teacher.teacher_id}


@app.post("/select/course")
def select_course(request: SelectCourseRequest, db: Session = Depends(get_db)):
    # Get the student
    student = db.query(Student).filter(Student.student_id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course is full
    if course.course_selected >= course.course_capacity:
        raise HTTPException(status_code=400, detail="Course is full")
    
    # Check if student already selected this course
    # This would require a proper relationship implementation in the database
    # For now we'll simulate by checking if the relationship exists
    # In practice, you'd have a student_course table and check that
    
    # Update the course selected count
    course.course_selected += 1
    db.commit()
    
    return {"message": "Course selected successfully", "student_id": request.student_id, "course_id": request.course_id}


@app.post("/deselect/course")
def deselect_course(request: DeselectCourseRequest, db: Session = Depends(get_db)):
    # Get the student
    student = db.query(Student).filter(Student.student_id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get the course
    course = db.query(Course).filter(Course.course_id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course selected count is greater than 0
    if course.course_selected <= 0:
        raise HTTPException(status_code=400, detail="Course not selected by student")
    
    # Update the course selected count
    course.course_selected -= 1
    db.commit()
    
    return {"message": "Course deselected successfully", "student_id": request.student_id, "course_id": request.course_id}


@app.post("/get/course")
def get_course(request: GetCourseRequest, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.course_id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Calculate course_left
    course_left = course.course_capacity - course.course_selected
    
    course_data = {
        "course_id": course.course_id,
        "course_name": course.course_name,
        "course_credit": course.course_credit,
        "course_type": course.course_type,
        "course_teacher_id": course.course_teacher_id,
        "course_time_begin": course.course_time_begin,
        "course_time_end": course.course_time_end,
        "course_location": course.course_location,
        "course_capacity": course.course_capacity,
        "course_selected": course.course_selected,
        "course_left": course_left
    }
    
    return course_data


@app.post("/master")
async def get_master(request: Request):
    # Verify protection token
    protection_token = request.headers.get("protection_token")
    verify_protection_token(protection_token)
    
    # Use node manager to get the actual master
    master_node = await node_manager.get_master_node("course_data")
    if master_node:
        # Parse the URL to get host and port
        import urllib.parse
        parsed = urllib.parse.urlparse(master_node)
        ip = parsed.hostname
        port = parsed.port
        return MasterResponse(ip=ip, port=port)
    else:
        # Fallback to this node
        return MasterResponse(ip="localhost", port=8001)


@app.post("/slave")
async def get_slaves(request: Request):
    # Verify protection token
    protection_token = request.headers.get("protection_token")
    verify_protection_token(protection_token)
    
    # Use node manager to get slave nodes
    slave_nodes = await node_manager.get_slave_nodes("course_data")
    slaves = {}
    for node in slave_nodes:
        import urllib.parse
        parsed = urllib.parse.urlparse(node)
        slaves[parsed.hostname] = parsed.port
    
    return SlaveResponse(slaves=slaves)
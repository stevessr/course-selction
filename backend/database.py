from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

# Association table for many-to-many relationship between students and courses
student_course_association = Table(
    'student_course_association',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.student_id')),
    Column('course_id', Integer, ForeignKey('courses.course_id'))
)

# Association table for many-to-many relationship between teachers and courses
teacher_course_association = Table(
    'teacher_course_association',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.teacher_id')),
    Column('course_id', Integer, ForeignKey('courses.course_id'))
)


class Course(Base):
    __tablename__ = "courses"
    
    course_id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String, index=True)
    course_credit = Column(Integer)
    course_type = Column(String, index=True)
    course_teacher_id = Column(Integer, index=True)
    course_time_begin = Column(Integer)
    course_time_end = Column(Integer)
    course_location = Column(String)
    course_capacity = Column(Integer)
    course_selected = Column(Integer, default=0)


class Student(Base):
    __tablename__ = "students"
    
    student_id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, index=True)
    student_courses = relationship("Course", secondary=student_course_association, back_populates="students")


class Teacher(Base):
    __tablename__ = "teachers"
    
    teacher_id = Column(Integer, primary_key=True, index=True)
    teacher_name = Column(String, index=True)
    teacher_courses = relationship("Course", secondary=teacher_course_association, back_populates="teachers")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True)
    user_password_hash = Column(String)
    user_type = Column(String, index=True)  # 'student', 'teacher', 'admin'
    two_factor_code = Column(String)  # For 2FA
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"
    
    admin_id = Column(Integer, primary_key=True, index=True)
    admin_name = Column(String, unique=True, index=True)
    admin_password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class OneTimeCredit(Base):
    __tablename__ = "one_time_credits"

    credit_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    used_by = Column(String, nullable=True)  # user_name who used it


class QueueTask(Base):
    __tablename__ = "queue_tasks"

    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(Integer, index=True)
    course_id = Column(Integer, index=True)
    task_type = Column(String)  # 'select' or 'deselect'
    status = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


# Establish relationships
Course.students = relationship("Student", secondary=student_course_association, back_populates="student_courses")
Course.teachers = relationship("Teacher", secondary=teacher_course_association, back_populates="teacher_courses")


from .settings import settings

# For initialization and sync operations, use synchronous SQLite
sync_database_url = settings.database_url.replace("sqlite+aiosqlite:///", "sqlite:///") if "sqlite+aiosqlite:///" in settings.database_url else settings.database_url

# Database setup
engine = create_engine(sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
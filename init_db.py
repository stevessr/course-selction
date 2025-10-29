#!/usr/bin/env python3
"""
Database initialization script for Course Selection System
This script creates the database tables and populates them with default data.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

from backend.database import engine, Base, User, Admin, Course, Student, Teacher
from backend.settings import settings
from backend.utils import get_password_hash
from backend.default_config import DEFAULT_ADMINS, SYSTEM_CONFIG, COURSE_CONFIG


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def create_default_admins():
    """Create default admin accounts"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating default admin accounts...")
        
        for admin_data in DEFAULT_ADMINS:
            # Check if admin already exists
            existing_admin = db.query(Admin).filter(Admin.admin_name == admin_data["admin_name"]).first()
            if existing_admin:
                print(f"Admin {admin_data['admin_name']} already exists, skipping...")
                continue
            
            # Ensure password is within bcrypt limit (72 bytes)
            password = admin_data["admin_password"]
            if len(password.encode('utf-8')) > 72:
                password = password[:72]  # Truncate to 72 characters
                print(f"Warning: Password for {admin_data['admin_name']} truncated to 72 characters")
            
            # Hash the password
            password_hash = get_password_hash(password)
            
            # Create new admin
            db_admin = Admin(
                admin_name=admin_data["admin_name"],
                admin_password_hash=password_hash
            )
            db.add(db_admin)
            print(f"Created admin account: {admin_data['admin_name']}")
        
        db.commit()
        print("Default admin accounts created successfully")
        
    except Exception as e:
        print(f"Error creating default admin accounts: {e}")
        db.rollback()
    finally:
        db.close()


def create_sample_data():
    """Create sample courses, teachers, and students for testing"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating sample data...")
        
        # Create sample teachers
        sample_teachers = [
            {"teacher_id": 1, "teacher_name": "Dr. Smith"},
            {"teacher_id": 2, "teacher_name": "Prof. Johnson"},
            {"teacher_id": 3, "teacher_name": "Dr. Williams"}
        ]
        
        for teacher_data in sample_teachers:
            existing_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_data["teacher_id"]).first()
            if not existing_teacher:
                db_teacher = Teacher(**teacher_data)
                db.add(db_teacher)
        
        # Create sample courses
        sample_courses = [
            {
                "course_id": 1,
                "course_name": "Introduction to Computer Science",
                "course_credit": 3,
                "course_type": "core",
                "course_teacher_id": 1,
                "course_time_begin": 900,  # 9:00 AM in minutes from midnight
                "course_time_end": 1020,   # 10:00 AM in minutes from midnight
                "course_location": "A101",
                "course_capacity": 50,
                "course_selected": 0
            },
            {
                "course_id": 2,
                "course_name": "Data Structures",
                "course_credit": 4,
                "course_type": "core",
                "course_teacher_id": 1,
                "course_time_begin": 1030,  # 10:30 AM
                "course_time_end": 1150,    # 11:50 AM
                "course_location": "A202",
                "course_capacity": 40,
                "course_selected": 0
            },
            {
                "course_id": 3,
                "course_name": "Calculus I",
                "course_credit": 4,
                "course_type": "required",
                "course_teacher_id": 2,
                "course_time_begin": 1300,  # 1:00 PM
                "course_time_end": 1420,    # 2:20 PM
                "course_location": "B301",
                "course_capacity": 60,
                "course_selected": 0
            }
        ]
        
        for course_data in sample_courses:
            existing_course = db.query(Course).filter(Course.course_id == course_data["course_id"]).first()
            if not existing_course:
                db_course = Course(**course_data)
                db.add(db_course)
        
        # Create sample students
        sample_students = [
            {"student_id": 1001, "student_name": "Alice Johnson"},
            {"student_id": 1002, "student_name": "Bob Smith"},
            {"student_id": 1003, "student_name": "Carol Davis"}
        ]
        
        for student_data in sample_students:
            existing_student = db.query(Student).filter(Student.student_id == student_data["student_id"]).first()
            if not existing_student:
                db_student = Student(**student_data)
                db.add(db_student)
        
        db.commit()
        print("Sample data created successfully")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function to initialize the database"""
    print("Initializing Course Selection System Database...")
    
    # Create database tables
    create_tables()
    
    # Create default admin accounts
    create_default_admins()
    
    # Create sample data for testing
    create_sample_data()
    
    print("\nDatabase initialization completed successfully!")
    print(f"Database URL: {settings.database_url}")
    print("Default admin accounts created:")
    for admin in DEFAULT_ADMINS:
        print(f"  - Username: {admin['admin_name']}")


if __name__ == "__main__":
    main()
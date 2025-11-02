"""Migration script to move student and teacher authentication data from course_data.db to auth_data.db"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import get_database_url, create_db_engine, create_session_factory, init_database
from common.models import AuthBase, DataBase, Student, Teacher, StudentCourseData, TeacherCourseData


def migrate_student_data():
    """Migrate student data from course_data.db to auth_data.db"""
    print("Starting student data migration...")

    # Connect to both databases
    course_db_url = get_database_url("course_data.db")
    auth_db_url = get_database_url("auth_data.db")

    course_engine = create_db_engine(course_db_url)
    auth_engine = create_db_engine(auth_db_url)

    # Initialize auth database with new schema
    init_database(auth_engine, AuthBase)

    # Create sessions
    CourseSession = create_session_factory(course_engine)
    AuthSession = create_session_factory(auth_engine)

    course_db = CourseSession()
    auth_db = AuthSession()

    try:
        # Check if old students table exists in course_data.db
        with course_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
            ))
            if not result.fetchone():
                print("No students table found in course_data.db - skipping migration")
                return

            # Check if the table has the old schema (with username column)
            result = conn.execute(text("PRAGMA table_info(students)"))
            columns = {row[1] for row in result.fetchall()}
            has_old_schema = 'username' in columns

            if not has_old_schema:
                print("Students table already has new schema - skipping migration")
                return

            print("Detected old schema with authentication fields - proceeding with migration")
        
        # Get all students from course_data.db (old schema)
        with course_engine.connect() as conn:
            result = conn.execute(text(
                """SELECT student_id, username, password_hash, student_name, 
                   student_courses, student_tags, totp_secret, is_active, 
                   created_at, updated_at 
                   FROM students"""
            ))
            old_students = result.fetchall()
        
        print(f"Found {len(old_students)} students to migrate")
        
        migrated_count = 0
        for old_student in old_students:
            student_id, username, password_hash, student_name, student_courses, \
                student_tags, totp_secret, is_active, created_at, updated_at = old_student
            
            # Check if student already exists in auth_data.db
            existing_auth = auth_db.query(Student).filter(
                Student.student_id == student_id
            ).first()
            
            if not existing_auth:
                # Create student auth record in auth_data.db
                new_auth_student = Student(
                    student_id=student_id,
                    username=username,
                    password_hash=password_hash,
                    totp_secret=totp_secret,
                    is_active=is_active if is_active is not None else True,
                    created_at=created_at if created_at else datetime.now(timezone.utc),
                    updated_at=updated_at if updated_at else datetime.now(timezone.utc)
                )
                auth_db.add(new_auth_student)
                migrated_count += 1
            
            # Check if student course data already exists in course_data.db (new schema)
            existing_course_data = course_db.query(StudentCourseData).filter(
                StudentCourseData.student_id == student_id
            ).first()
            
            if not existing_course_data:
                # Create student course data record in course_data.db (new schema)
                new_course_data = StudentCourseData(
                    student_id=student_id,
                    student_name=student_name if student_name else username,
                    student_courses=student_courses if student_courses else [],
                    student_tags=student_tags if student_tags else [],
                    created_at=created_at if created_at else datetime.now(timezone.utc),
                    updated_at=updated_at if updated_at else datetime.now(timezone.utc)
                )
                course_db.add(new_course_data)
        
        # Commit changes
        auth_db.commit()
        course_db.commit()
        
        print(f"Successfully migrated {migrated_count} students to auth_data.db")

        # Now we need to recreate the students table with the new schema
        print("\nRecreating students table with new schema (StudentCourseData)...")

        with course_engine.connect() as conn:
            # Rename old table
            conn.execute(text("ALTER TABLE students RENAME TO students_old_backup"))
            conn.commit()
            print("Renamed old students table to students_old_backup")

        # Create new students table with StudentCourseData schema
        init_database(course_engine, DataBase)
        print("Created new students table with StudentCourseData schema")

        # Migrate course data to new table
        print("Migrating course data to new students table...")
        with course_engine.connect() as conn:
            result = conn.execute(text(
                """INSERT INTO students (student_id, student_name, student_courses, student_tags, created_at, updated_at)
                   SELECT student_id, student_name, student_courses, student_tags, created_at, updated_at
                   FROM students_old_backup"""
            ))
            conn.commit()
            print(f"Migrated {result.rowcount} student course records to new table")
        
    except Exception as e:
        print(f"Error during student migration: {e}")
        auth_db.rollback()
        course_db.rollback()
        raise
    finally:
        course_db.close()
        auth_db.close()


def migrate_teacher_data():
    """Migrate teacher data from course_data.db to auth_data.db"""
    print("\nStarting teacher data migration...")

    # Connect to both databases
    course_db_url = get_database_url("course_data.db")
    auth_db_url = get_database_url("auth_data.db")

    course_engine = create_db_engine(course_db_url)
    auth_engine = create_db_engine(auth_db_url)

    # Initialize auth database with new schema
    init_database(auth_engine, AuthBase)

    # Create sessions
    CourseSession = create_session_factory(course_engine)
    AuthSession = create_session_factory(auth_engine)

    course_db = CourseSession()
    auth_db = AuthSession()

    try:
        # Check if old teachers table exists in course_data.db
        with course_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='teachers'"
            ))
            if not result.fetchone():
                print("No teachers table found in course_data.db - skipping migration")
                return

            # Check if the table has the old schema (with username column)
            result = conn.execute(text("PRAGMA table_info(teachers)"))
            columns = {row[1] for row in result.fetchall()}
            has_old_schema = 'username' in columns

            if not has_old_schema:
                print("Teachers table already has new schema - skipping migration")
                return

            print("Detected old schema with authentication fields - proceeding with migration")
        
        # Get all teachers from course_data.db (old schema)
        with course_engine.connect() as conn:
            result = conn.execute(text(
                """SELECT teacher_id, username, password_hash, teacher_name, 
                   teacher_courses, is_active, created_at, updated_at 
                   FROM teachers"""
            ))
            old_teachers = result.fetchall()
        
        print(f"Found {len(old_teachers)} teachers to migrate")
        
        migrated_count = 0
        for old_teacher in old_teachers:
            teacher_id, username, password_hash, teacher_name, teacher_courses, \
                is_active, created_at, updated_at = old_teacher
            
            # Check if teacher already exists in auth_data.db
            existing_auth = auth_db.query(Teacher).filter(
                Teacher.teacher_id == teacher_id
            ).first()
            
            if not existing_auth:
                # Create teacher auth record in auth_data.db
                new_auth_teacher = Teacher(
                    teacher_id=teacher_id,
                    username=username,
                    password_hash=password_hash,
                    is_active=is_active if is_active is not None else True,
                    created_at=created_at if created_at else datetime.now(timezone.utc),
                    updated_at=updated_at if updated_at else datetime.now(timezone.utc)
                )
                auth_db.add(new_auth_teacher)
                migrated_count += 1
            
            # Check if teacher course data already exists in course_data.db (new schema)
            existing_course_data = course_db.query(TeacherCourseData).filter(
                TeacherCourseData.teacher_id == teacher_id
            ).first()
            
            if not existing_course_data:
                # Create teacher course data record in course_data.db (new schema)
                new_course_data = TeacherCourseData(
                    teacher_id=teacher_id,
                    teacher_name=teacher_name if teacher_name else username,
                    teacher_courses=teacher_courses if teacher_courses else [],
                    created_at=created_at if created_at else datetime.now(timezone.utc),
                    updated_at=updated_at if updated_at else datetime.now(timezone.utc)
                )
                course_db.add(new_course_data)
        
        # Commit changes
        auth_db.commit()
        course_db.commit()
        
        print(f"Successfully migrated {migrated_count} teachers to auth_data.db")

        # Now we need to recreate the teachers table with the new schema
        print("\nRecreating teachers table with new schema (TeacherCourseData)...")

        with course_engine.connect() as conn:
            # Rename old table
            conn.execute(text("ALTER TABLE teachers RENAME TO teachers_old_backup"))
            conn.commit()
            print("Renamed old teachers table to teachers_old_backup")

        # Create new teachers table with TeacherCourseData schema
        init_database(course_engine, DataBase)
        print("Created new teachers table with TeacherCourseData schema")

        # Migrate course data to new table
        print("Migrating course data to new teachers table...")
        with course_engine.connect() as conn:
            result = conn.execute(text(
                """INSERT INTO teachers (teacher_id, teacher_name, teacher_courses, created_at, updated_at)
                   SELECT teacher_id, teacher_name, teacher_courses, created_at, updated_at
                   FROM teachers_old_backup"""
            ))
            conn.commit()
            print(f"Migrated {result.rowcount} teacher course records to new table")
        
    except Exception as e:
        print(f"Error during teacher migration: {e}")
        auth_db.rollback()
        course_db.rollback()
        raise
    finally:
        course_db.close()
        auth_db.close()


def main():
    """Run the migration"""
    print("=" * 60)
    print("Database Migration: Moving auth data to auth_data.db")
    print("=" * 60)
    
    try:
        migrate_student_data()
        migrate_teacher_data()
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test the application to ensure everything works")
        print("2. If everything works, you can delete the backup tables:")
        print("   - students_old_backup in course_data.db")
        print("   - teachers_old_backup in course_data.db")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        print("Please fix the error and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()


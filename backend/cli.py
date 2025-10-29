#!/usr/bin/env python3
"""
Command-line interface for managing users in the course selection system.

Usage:
    python -m backend.cli add-admin <username> <password>
    python -m backend.cli add-teacher <username> <password> <teacher_id>
    python -m backend.cli add-student <username> <password> <student_id>
    python -m backend.cli update-user <username> --password <new_password>
    python -m backend.cli update-user <username> --name <new_name>
    python -m backend.cli delete-user <username>
    python -m backend.cli list-users [--type admin|teacher|student]
    python -m backend.cli show-user <username>
"""

import sys
import argparse
from sqlalchemy.orm import sessionmaker
from .database import User, Admin, Teacher, Student, engine, Base
from .utils import get_password_hash, verify_password
import pyotp


# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def add_admin(username: str, password: str):
    """Add a new admin user"""
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.admin_name == username).first()
        if existing_admin:
            print(f"❌ Error: Admin '{username}' already exists")
            return False

        # Ensure password is within bcrypt limit (72 bytes)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            print(f"⚠️  Warning: Password truncated to 72 characters")

        # Hash password
        password_hash = get_password_hash(password)

        # Create admin
        new_admin = Admin(
            admin_name=username,
            admin_password_hash=password_hash
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print(f"✅ Admin '{username}' created successfully (ID: {new_admin.admin_id})")
        return True

    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def add_teacher(username: str, password: str, teacher_id: int):
    """Add a new teacher user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.user_name == username).first()
        if existing_user:
            print(f"❌ Error: User '{username}' already exists")
            return False

        # Check if teacher_id already exists
        existing_teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
        if existing_teacher:
            print(f"❌ Error: Teacher ID {teacher_id} already exists")
            return False

        # Generate 2FA secret
        two_fa_secret = pyotp.random_base32()

        # Ensure password is within bcrypt limit (72 bytes)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            print(f"⚠️  Warning: Password truncated to 72 characters")

        # Hash password
        password_hash = get_password_hash(password)
        
        # Create user
        new_user = User(
            user_name=username,
            user_password_hash=password_hash,
            user_type='teacher',
            two_factor_code=two_fa_secret
        )
        db.add(new_user)
        db.flush()  # Get user_id
        
        # Create teacher
        new_teacher = Teacher(
            teacher_id=teacher_id,
            teacher_name=username
        )
        db.add(new_teacher)
        
        db.commit()
        
        # Generate TOTP for display
        totp = pyotp.TOTP(two_fa_secret)
        current_code = totp.now()
        
        print(f"✅ Teacher '{username}' created successfully")
        print(f"   User ID: {new_user.user_id}")
        print(f"   Teacher ID: {teacher_id}")
        print(f"   2FA Secret: {two_fa_secret}")
        print(f"   Current 2FA Code: {current_code}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating teacher: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def add_student(username: str, password: str, student_id: int):
    """Add a new student user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.user_name == username).first()
        if existing_user:
            print(f"❌ Error: User '{username}' already exists")
            return False

        # Check if student_id already exists
        existing_student = db.query(Student).filter(Student.student_id == student_id).first()
        if existing_student:
            print(f"❌ Error: Student ID {student_id} already exists")
            return False

        # Generate 2FA secret
        two_fa_secret = pyotp.random_base32()

        # Ensure password is within bcrypt limit (72 bytes)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            print(f"⚠️  Warning: Password truncated to 72 characters")

        # Hash password
        password_hash = get_password_hash(password)
        
        # Create user
        new_user = User(
            user_name=username,
            user_password_hash=password_hash,
            user_type='student',
            two_factor_code=two_fa_secret
        )
        db.add(new_user)
        db.flush()  # Get user_id
        
        # Create student
        new_student = Student(
            student_id=student_id,
            student_name=username
        )
        db.add(new_student)
        
        db.commit()
        
        # Generate TOTP for display
        totp = pyotp.TOTP(two_fa_secret)
        current_code = totp.now()
        
        print(f"✅ Student '{username}' created successfully")
        print(f"   User ID: {new_user.user_id}")
        print(f"   Student ID: {student_id}")
        print(f"   2FA Secret: {two_fa_secret}")
        print(f"   Current 2FA Code: {current_code}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating student: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def update_user_password(username: str, new_password: str):
    """Update user password"""
    db = SessionLocal()
    try:
        # Try to find user
        user = db.query(User).filter(User.user_name == username).first()
        admin = db.query(Admin).filter(Admin.admin_name == username).first()

        if not user and not admin:
            print(f"❌ Error: User '{username}' not found")
            return False

        # Ensure password is within bcrypt limit (72 bytes)
        if len(new_password.encode('utf-8')) > 72:
            new_password = new_password[:72]
            print(f"⚠️  Warning: Password truncated to 72 characters")

        # Hash new password
        password_hash = get_password_hash(new_password)
        
        if user:
            user.user_password_hash = password_hash
            print(f"✅ Password updated for user '{username}' (type: {user.user_type})")
        elif admin:
            admin.admin_password_hash = password_hash
            print(f"✅ Password updated for admin '{username}'")
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def update_user_name(username: str, new_name: str):
    """Update user display name"""
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.user_name == username).first()
        
        if not user:
            print(f"❌ Error: User '{username}' not found")
            return False
        
        # Update corresponding teacher or student name
        if user.user_type == 'teacher':
            teacher = db.query(Teacher).filter(Teacher.teacher_name == username).first()
            if teacher:
                teacher.teacher_name = new_name
        elif user.user_type == 'student':
            student = db.query(Student).filter(Student.student_name == username).first()
            if student:
                student.student_name = new_name
        
        db.commit()
        print(f"✅ Display name updated for '{username}' to '{new_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error updating name: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def delete_user(username: str):
    """Delete a user"""
    db = SessionLocal()
    try:
        # Try to find and delete user
        user = db.query(User).filter(User.user_name == username).first()
        admin = db.query(Admin).filter(Admin.admin_name == username).first()

        if not user and not admin:
            print(f"❌ Error: User '{username}' not found")
            return False

        if user:
            # Delete corresponding teacher or student
            if user.user_type == 'teacher':
                teacher = db.query(Teacher).filter(Teacher.teacher_name == username).first()
                if teacher:
                    db.delete(teacher)
            elif user.user_type == 'student':
                student = db.query(Student).filter(Student.student_name == username).first()
                if student:
                    db.delete(student)

            db.delete(user)
            print(f"✅ User '{username}' (type: {user.user_type}) deleted successfully")
        elif admin:
            db.delete(admin)
            print(f"✅ Admin '{username}' deleted successfully")

        db.commit()
        return True

    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_users(user_type: str = None):
    """List all users or users of a specific type"""
    db = SessionLocal()
    try:
        print("\n" + "="*80)

        if user_type == 'admin' or user_type is None:
            admins = db.query(Admin).all()
            if admins:
                print(f"\n📋 ADMINS ({len(admins)})")
                print("-" * 80)
                for admin in admins:
                    print(f"  ID: {admin.admin_id:4d} | Username: {admin.admin_name:20s} | Created: {admin.created_at}")

        if user_type == 'teacher' or user_type is None:
            teachers = db.query(User).filter(User.user_type == 'teacher').all()
            if teachers:
                print(f"\n📋 TEACHERS ({len(teachers)})")
                print("-" * 80)
                for user in teachers:
                    teacher = db.query(Teacher).filter(Teacher.teacher_name == user.user_name).first()
                    teacher_id = teacher.teacher_id if teacher else 'N/A'
                    print(f"  User ID: {user.user_id:4d} | Teacher ID: {str(teacher_id):6s} | Username: {user.user_name:20s} | Created: {user.created_at}")

        if user_type == 'student' or user_type is None:
            students = db.query(User).filter(User.user_type == 'student').all()
            if students:
                print(f"\n📋 STUDENTS ({len(students)})")
                print("-" * 80)
                for user in students:
                    student = db.query(Student).filter(Student.student_name == user.user_name).first()
                    student_id = student.student_id if student else 'N/A'
                    print(f"  User ID: {user.user_id:4d} | Student ID: {str(student_id):6s} | Username: {user.user_name:20s} | Created: {user.created_at}")

        print("\n" + "="*80 + "\n")
        return True

    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return False
    finally:
        db.close()


def show_user(username: str):
    """Show detailed information about a user"""
    db = SessionLocal()
    try:
        # Try to find user
        user = db.query(User).filter(User.user_name == username).first()
        admin = db.query(Admin).filter(Admin.admin_name == username).first()

        if not user and not admin:
            print(f"❌ Error: User '{username}' not found")
            return False

        print("\n" + "="*80)

        if admin:
            print(f"\n👤 ADMIN DETAILS")
            print("-" * 80)
            print(f"  Admin ID:       {admin.admin_id}")
            print(f"  Username:       {admin.admin_name}")
            print(f"  Created At:     {admin.created_at}")
            print(f"  Password Hash:  {admin.admin_password_hash[:50]}...")

        if user:
            print(f"\n👤 USER DETAILS")
            print("-" * 80)
            print(f"  User ID:        {user.user_id}")
            print(f"  Username:       {user.user_name}")
            print(f"  User Type:      {user.user_type}")
            print(f"  Created At:     {user.created_at}")
            print(f"  Password Hash:  {user.user_password_hash[:50]}...")
            print(f"  2FA Secret:     {user.two_factor_code}")

            # Generate current 2FA code
            if user.two_factor_code:
                totp = pyotp.TOTP(user.two_factor_code)
                current_code = totp.now()
                print(f"  Current 2FA:    {current_code}")

            # Show teacher/student specific info
            if user.user_type == 'teacher':
                teacher = db.query(Teacher).filter(Teacher.teacher_name == user.user_name).first()
                if teacher:
                    print(f"\n  📚 Teacher Info:")
                    print(f"     Teacher ID:   {teacher.teacher_id}")
                    print(f"     Teacher Name: {teacher.teacher_name}")

            elif user.user_type == 'student':
                student = db.query(Student).filter(Student.student_name == user.user_name).first()
                if student:
                    print(f"\n  🎓 Student Info:")
                    print(f"     Student ID:   {student.student_id}")
                    print(f"     Student Name: {student.student_name}")

        print("\n" + "="*80 + "\n")
        return True

    except Exception as e:
        print(f"❌ Error showing user: {e}")
        return False
    finally:
        db.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Course Selection System - User Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add users
  python -m backend.cli add-admin admin password123
  python -m backend.cli add-teacher teacher1 pass123 1001
  python -m backend.cli add-student student1 pass123 2001

  # Update users
  python -m backend.cli update-user admin --password newpass123
  python -m backend.cli update-user teacher1 --name "Dr. Smith"

  # List users
  python -m backend.cli list-users
  python -m backend.cli list-users --type admin
  python -m backend.cli list-users --type teacher
  python -m backend.cli list-users --type student

  # Show user details
  python -m backend.cli show-user admin

  # Delete user
  python -m backend.cli delete-user student1
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add admin
    parser_add_admin = subparsers.add_parser('add-admin', help='Add a new admin user')
    parser_add_admin.add_argument('username', help='Admin username')
    parser_add_admin.add_argument('password', help='Admin password')

    # Add teacher
    parser_add_teacher = subparsers.add_parser('add-teacher', help='Add a new teacher user')
    parser_add_teacher.add_argument('username', help='Teacher username')
    parser_add_teacher.add_argument('password', help='Teacher password')
    parser_add_teacher.add_argument('teacher_id', type=int, help='Teacher ID')

    # Add student
    parser_add_student = subparsers.add_parser('add-student', help='Add a new student user')
    parser_add_student.add_argument('username', help='Student username')
    parser_add_student.add_argument('password', help='Student password')
    parser_add_student.add_argument('student_id', type=int, help='Student ID')

    # Update user
    parser_update = subparsers.add_parser('update-user', help='Update user information')
    parser_update.add_argument('username', help='Username to update')
    parser_update.add_argument('--password', help='New password')
    parser_update.add_argument('--name', help='New display name')

    # Delete user
    parser_delete = subparsers.add_parser('delete-user', help='Delete a user')
    parser_delete.add_argument('username', help='Username to delete')

    # List users
    parser_list = subparsers.add_parser('list-users', help='List all users')
    parser_list.add_argument('--type', choices=['admin', 'teacher', 'student'], help='Filter by user type')

    # Show user
    parser_show = subparsers.add_parser('show-user', help='Show detailed user information')
    parser_show.add_argument('username', help='Username to show')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'add-admin':
        add_admin(args.username, args.password)
    elif args.command == 'add-teacher':
        add_teacher(args.username, args.password, args.teacher_id)
    elif args.command == 'add-student':
        add_student(args.username, args.password, args.student_id)
    elif args.command == 'update-user':
        if args.password:
            update_user_password(args.username, args.password)
        if args.name:
            update_user_name(args.username, args.name)
        if not args.password and not args.name:
            print("❌ Error: Please specify --password or --name to update")
    elif args.command == 'delete-user':
        delete_user(args.username)
    elif args.command == 'list-users':
        list_users(args.type)
    elif args.command == 'show-user':
        show_user(args.username)


if __name__ == '__main__':
    main()


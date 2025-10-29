#!/usr/bin/env python3
"""
Standalone script for managing users in the course selection system.
This is a convenience wrapper around backend.cli

Usage:
    python manage-users.py add-admin <username> <password>
    python manage-users.py add-teacher <username> <password> <teacher_id>
    python manage-users.py add-student <username> <password> <student_id>
    python manage-users.py update-user <username> --password <new_password>
    python manage-users.py update-user <username> --name <new_name>
    python manage-users.py delete-user <username>
    python manage-users.py list-users [--type admin|teacher|student]
    python manage-users.py show-user <username>
"""

import sys
import os

# Add the parent directory to the path so we can import backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    from backend.cli import main
    main()


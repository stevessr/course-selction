"""
Migration script to change course_credit from INTEGER to REAL (float)
This allows courses to have fractional credits like 0.5, 1.5, 2.5 etc.
"""
import sqlite3
import sys
from pathlib import Path

def migrate_course_credit(db_path: str):
    """Migrate course_credit column from INTEGER to REAL"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"Migrating {db_path}...")
        
        # SQLite doesn't support ALTER COLUMN directly, so we need to:
        # 1. Create a new table with correct schema
        # 2. Copy data
        # 3. Drop old table
        # 4. Rename new table
        
        # Create new table with REAL type for course_credit
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses_new (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name VARCHAR(200) NOT NULL,
                course_credit REAL NOT NULL,
                course_type VARCHAR(50) NOT NULL,
                course_teacher_id INTEGER NOT NULL,
                course_time_start INTEGER,
                course_time_end INTEGER,
                course_weekdays JSON,
                course_time_begin INTEGER,
                course_time_end_legacy INTEGER,
                course_schedule JSON,
                course_location VARCHAR(100) NOT NULL,
                course_capacity INTEGER NOT NULL,
                course_selected JSON,
                course_selected_count INTEGER DEFAULT 0,
                course_tags JSON,
                course_notes VARCHAR(500) DEFAULT '',
                course_cost INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
        if cursor.fetchone():
            # Copy data from old table to new table
            cursor.execute("""
                INSERT INTO courses_new 
                SELECT * FROM courses
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE courses")
        
        # Rename new table to courses
        cursor.execute("ALTER TABLE courses_new RENAME TO courses")
        
        conn.commit()
        print(f"✓ Successfully migrated {db_path}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error migrating {db_path}: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Migrate course_data.db
    course_db = project_root / "course_data.db"
    if course_db.exists():
        migrate_course_credit(str(course_db))
    else:
        print(f"Database not found: {course_db}")
        sys.exit(1)

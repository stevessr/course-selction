import asyncio
from sqlalchemy.orm import sessionmaker
from .database import Admin, engine
from .settings import settings
from .utils import get_password_hash
from .default_config import DEFAULT_ADMINS


def create_default_admins():
    """Create default admin accounts on system initialization"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if any admins already exist
        existing_admin_count = db.query(Admin).count()
        if existing_admin_count > 0:
            print("Admin accounts already exist, skipping default admin creation")
            return
        
        print("Creating default admin accounts...")
        
        for admin_data in DEFAULT_ADMINS:
            # Check if admin already exists
            existing_admin = db.query(Admin).filter(Admin.admin_name == admin_data["admin_name"]).first()
            if existing_admin:
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


def initialize_system():
    """Initialize the system with default configuration and admin accounts"""
    print("Initializing course selection system...")
    
    # Create default admin accounts
    create_default_admins()
    
    # Additional initialization tasks could go here
    print("System initialization completed")


if __name__ == "__main__":
    initialize_system()
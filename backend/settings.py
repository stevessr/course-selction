from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Course Selection Backend"
    admin_token: str = "random_admin_token_here"
    secret_key: str = "secret_key_for_jwt_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite+aiosqlite:///./course_selection.db"
    redis_url: str = "redis://localhost:6379/0"
    course_data_url: str = "http://localhost:8001"
    login_url: str = "http://localhost:8002"
    teacher_url: str = "http://localhost:8003"
    student_url: str = "http://localhost:8004"
    queue_url: str = "http://localhost:8005"
    # Token protection
    internal_token: str = "random_internal_token_here"
    protection_token: str = "random_protection_token_here"
    # Node configuration
    node_id: str = "node_1"
    node_role: str = "primary"  # primary, replica, or standalone
    other_nodes: str = ""  # comma-separated list of other node URLs
    # Default admin credentials
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    # Security settings
    enable_default_admin_protection: bool = True  # Should require default password change
    
    class Config:
        env_file = ".env"


settings = Settings()
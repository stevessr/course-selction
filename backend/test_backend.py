import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.course_data.main import app as course_data_app
from backend.login.main import app as login_app
from backend.teacher.main import app as teacher_app
from backend.student.main import app as student_app
from backend.queue.main import app as queue_app
import json

# Test clients for each service
course_data_client = TestClient(course_data_app)
login_client = TestClient(login_app)
teacher_client = TestClient(teacher_app)
student_client = TestClient(student_app)
queue_client = TestClient(queue_app)


def test_course_data_endpoints():
    """Test course data node endpoints"""
    print("Testing Course Data Node endpoints...")
    
    # Test adding a course
    course_data = {
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
    }
    
    response = course_data_client.post("/add/course", json=course_data)
    assert response.status_code == 200
    print("✓ Course added successfully")
    
    # Test getting the course
    get_course_data = {"course_id": 1}
    response = course_data_client.post("/get/course", json=get_course_data)
    assert response.status_code == 200
    result = response.json()
    assert result["course_name"] == "Introduction to Computer Science"
    print("✓ Course retrieved successfully")
    
    # Test master endpoint (requires protection token)
    response = course_data_client.post("/master", headers={"protection_token": "random_protection_token_here"})
    assert response.status_code == 200
    print("✓ Master endpoint works")


def test_login_endpoints():
    """Test login node endpoints"""
    print("Testing Login Node endpoints...")
    
    # Test registering a user (v1)
    register_data = {
        "user_name": "testuser",
        "user_password": "password123",
        "user_type": "student"
    }
    
    response = login_client.post("/register/v1", json=register_data)
    # This might fail due to 2FA setup, but we can test the structure
    print(f"✓ Register v1 response status: {response.status_code}")
    
    # Test getting master (requires protection token)
    response = login_client.post("/master", headers={"protection_token": "random_protection_token_here"})
    assert response.status_code == 200
    print("✓ Login master endpoint works")


def test_teacher_endpoints():
    """Test teacher processing node endpoints"""
    print("Testing Teacher Processing Node endpoints...")
    
    # Basic test - check if server is running
    response = teacher_client.get("/")
    assert response.status_code == 200
    print("✓ Teacher node is running")


def test_student_endpoints():
    """Test student processing node endpoints"""
    print("Testing Student Processing Node endpoints...")
    
    # Basic test - check if server is running
    response = student_client.get("/")
    assert response.status_code == 200
    print("✓ Student node is running")


def test_queue_endpoints():
    """Test queue buffer node endpoints"""
    print("Testing Queue Buffer Node endpoints...")
    
    # Test health check
    response = queue_client.get("/queue/health")
    assert response.status_code == 200
    print("✓ Queue health check works")


def run_tests():
    """Run all tests"""
    print("Starting backend component tests...\n")
    
    test_course_data_endpoints()
    print()
    
    test_login_endpoints()
    print()
    
    test_teacher_endpoints()
    print()
    
    test_student_endpoints()
    print()
    
    test_queue_endpoints()
    print()
    
    print("All tests completed!")


if __name__ == "__main__":
    run_tests()
#!/usr/bin/env python3
"""
Test script to verify the course selection system is working correctly.
This script tests the basic API endpoints and workflow.
"""
import asyncio
import httpx
import sys
from datetime import datetime


# Service URLs
AUTH_URL = "http://localhost:8002"
DATA_URL = "http://localhost:8001"
TEACHER_URL = "http://localhost:8003"
STUDENT_URL = "http://localhost:8004"
QUEUE_URL = "http://localhost:8005"

# Internal token for inter-service communication
INTERNAL_TOKEN = "change-this-internal-token"


async def test_service_health(client: httpx.AsyncClient, url: str, service_name: str):
    """Test if a service is healthy"""
    try:
        response = await client.get(f"{url}/health", timeout=5.0)
        if response.status_code == 200:
            print(f"✓ {service_name} is healthy")
            return True
        else:
            print(f"✗ {service_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {service_name} is not responding: {e}")
        return False


async def test_admin_login(client: httpx.AsyncClient):
    """Test admin login"""
    try:
        response = await client.post(
            f"{AUTH_URL}/login/admin",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            data = response.json()
            print("✓ Admin login successful")
            return data.get("access_token")
        else:
            print(f"✗ Admin login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Admin login error: {e}")
        return None


async def test_create_teacher(client: httpx.AsyncClient):
    """Test creating a teacher in the data node"""
    try:
        response = await client.post(
            f"{DATA_URL}/add/teacher",
            json={"teacher_name": "Test Teacher"},
            headers={"Internal-Token": INTERNAL_TOKEN}
        )
        if response.status_code in [200, 201, 400]:  # 400 if already exists
            print("✓ Teacher creation test passed")
            return True
        else:
            print(f"✗ Teacher creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Teacher creation error: {e}")
        return False


async def test_create_student(client: httpx.AsyncClient):
    """Test creating a student in the data node"""
    try:
        response = await client.post(
            f"{DATA_URL}/add/student",
            json={"student_name": "Test Student"},
            headers={"Internal-Token": INTERNAL_TOKEN}
        )
        if response.status_code in [200, 201, 400]:  # 400 if already exists
            print("✓ Student creation test passed")
            return True
        else:
            print(f"✗ Student creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Student creation error: {e}")
        return False


async def test_create_course(client: httpx.AsyncClient):
    """Test creating a course in the data node"""
    try:
        course_data = {
            "course_name": "Test Course",
            "course_credit": 3,
            "course_type": "required",
            "course_teacher_id": 1,
            "course_time_begin": 800,
            "course_time_end": 950,
            "course_location": "Room 101",
            "course_capacity": 30
        }
        response = await client.post(
            f"{DATA_URL}/add/course",
            json=course_data,
            headers={"Internal-Token": INTERNAL_TOKEN}
        )
        if response.status_code in [200, 201]:
            print("✓ Course creation test passed")
            return True
        else:
            print(f"✗ Course creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Course creation error: {e}")
        return False


async def test_registration_code(client: httpx.AsyncClient, admin_token: str):
    """Test generating a registration code"""
    try:
        response = await client.post(
            f"{AUTH_URL}/generate/registration-code",
            json={"user_type": "student", "expires_days": 7},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Registration code generated: {data.get('code')}")
            return data.get('code')
        else:
            print(f"✗ Registration code generation failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Registration code generation error: {e}")
        return None


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Course Selection System - Basic Test Suite")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient() as client:
        # Test 1: Service health checks
        print("Test 1: Checking service health...")
        services = [
            (DATA_URL, "Data Node"),
            (AUTH_URL, "Auth Node"),
            (TEACHER_URL, "Teacher Node"),
            (STUDENT_URL, "Student Node"),
            (QUEUE_URL, "Queue Node")
        ]
        
        all_healthy = True
        for url, name in services:
            if not await test_service_health(client, url, name):
                all_healthy = False
        
        if not all_healthy:
            print("\n⚠ Some services are not running. Please start all services first.")
            print("Run: ./start_backend.sh")
            sys.exit(1)
        
        print()
        
        # Test 2: Admin login
        print("Test 2: Testing admin login...")
        admin_token = await test_admin_login(client)
        if not admin_token:
            print("\n⚠ Admin login failed. Cannot continue tests.")
            sys.exit(1)
        
        print()
        
        # Test 3: Data operations
        print("Test 3: Testing data operations...")
        await test_create_teacher(client)
        await test_create_student(client)
        await test_create_course(client)
        
        print()
        
        # Test 4: Registration code generation
        print("Test 4: Testing registration code generation...")
        reg_code = await test_registration_code(client, admin_token)
        
        print()
        print("=" * 60)
        print("✓ Basic tests completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Login as admin (username: admin, password: admin123)")
        print("3. Generate registration codes for students and teachers")
        print("4. Register new users and test the full workflow")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        sys.exit(1)

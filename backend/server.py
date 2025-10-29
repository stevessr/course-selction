import uvicorn
from fastapi import FastAPI
import sys
import os

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_course_data():
    from backend.course_data.main import app
    uvicorn.run(app, host="0.0.0.0", port=8001)


def run_login():
    from backend.login.main import app
    uvicorn.run(app, host="0.0.0.0", port=8002)


def run_teacher():
    from backend.teacher.main import app
    uvicorn.run(app, host="0.0.0.0", port=8003)


def run_student():
    from backend.student.main import app
    uvicorn.run(app, host="0.0.0.0", port=8004)


def run_queue():
    from backend.queue.main import app
    uvicorn.run(app, host="0.0.0.0", port=8005)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py [course_data|login|teacher|student|queue]")
        sys.exit(1)
    
    service = sys.argv[1]
    
    if service == "course_data":
        run_course_data()
    elif service == "login":
        run_login()
    elif service == "teacher":
        run_teacher()
    elif service == "student":
        run_student()
    elif service == "queue":
        run_queue()
    else:
        print(f"Unknown service: {service}")
        print("Usage: python server.py [course_data|login|teacher|student|queue]")
        sys.exit(1)
"""Top-level backend package initializer.

This file ensures that `backend` is recognized as a regular Python package
so imports like `from backend.common import ...` work reliably in all
environments (including some test runners).
"""

__all__ = [
    "auth_node",
    "common",
    "data_node",
    "queue_node",
    "student_node",
    "teacher_node",
]

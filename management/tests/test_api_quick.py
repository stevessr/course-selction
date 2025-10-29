import os
import importlib

from fastapi.testclient import TestClient


def test_quick_flow(tmp_path):
    """Quick end-to-end smoke test using a temporary sqlite file.

    This test does not require a running uvicorn process — it reloads the
    application module after setting environment variables so the app's
    configuration is initialized against a temporary DB file.
    """
    # prepare temporary sqlite file path
    db_file = tmp_path / "test.db"
    os.environ["DB_URL"] = f"sqlite:///{db_file}"
    os.environ["SECRET_KEY"] = "test-secret"

    # reload api module so it picks up env vars at import-time
    import management.api as api
    importlib.reload(api)

    client = TestClient(api.app)

    # register
    r = client.post("/register", json={"username": "u1", "password": "p"})
    assert r.status_code == 200, r.text

    # login
    r = client.post("/login", json={"username": "u1", "password": "p"})
    assert r.status_code == 200, r.text
    token = r.json().get("access_token")
    assert token, r.text
    headers = {"Authorization": f"Bearer {token}"}

    # create teacher
    r = client.post("/teachers", json={"name": "T1"}, headers=headers)
    assert r.status_code == 200, r.text
    tid = r.json()["teacher_id"]

    # create booking (should succeed)
    r = client.post(
        "/book",
        json={"owner_type": "teacher", "owner_id": tid, "start": 9, "end": 11},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    # conflicting booking (should 409)
    r2 = client.post(
        "/book",
        json={"owner_type": "teacher", "owner_id": tid, "start": 10, "end": 12},
        headers=headers,
    )
    assert r2.status_code == 409, r2.text

    # list bookings
    r = client.get("/bookings", headers=headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list) and len(r.json()) >= 1

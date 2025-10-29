from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from management.auth import register_user, authenticate_user
from management.config import get_config
from management.database.main import (
    init_db,
    add_teacher,
    add_student,
    book_slot,
    get_bookings_for_owner,
    get_bookings_in_range,
    get_connection,
)


# Configuration
CFG = get_config()
DB_URL = CFG.db.url or "sqlite:///./data.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


app = FastAPI(title="Course Selection API")
security = HTTPBearer()


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (uses PyJWT if available).

    The token payload will include 'exp' and 'iat'.
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    try:
        import jwt as _jwt

        return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as exc:  # pragma: no cover - dependency/runtime issue
        raise HTTPException(status_code=500, detail=f"JWT error: {exc}")


def decode_token(token: str) -> dict:
    try:
        import jwt as _jwt

        return _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def get_db():
    return init_db(DB_URL)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    conn = get_connection(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


# Pydantic models
class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class TeacherIn(BaseModel):
    name: str
    email: Optional[str] = None


class StudentIn(BaseModel):
    name: str
    email: Optional[str] = None


class BookingIn(BaseModel):
    owner_type: str
    owner_id: int
    start: int
    end: int
    course_id: Optional[int] = None


@app.post("/register", response_model=dict)
def register(payload: RegisterIn):
    conn = init_db(DB_URL)
    uid = register_user(conn, payload.username, payload.password, is_admin=False)
    return {"user_id": uid}


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    conn = init_db(DB_URL)
    ok = authenticate_user(conn, payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    data = {"sub": payload.username}
    token = create_token(data)
    return {"access_token": token}


@app.post("/teachers", response_model=dict)
def create_teacher(payload: TeacherIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    tid = add_teacher(conn, payload.name, payload.email)
    return {"teacher_id": tid}


@app.post("/students", response_model=dict)
def create_student(payload: StudentIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    sid = add_student(conn, payload.name, payload.email)
    return {"student_id": sid}


@app.post("/book", response_model=dict)
def create_booking(payload: BookingIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    ok = book_slot(conn, payload.owner_type, payload.owner_id, payload.start, payload.end, payload.course_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Time slot conflict")
    return {"booked": True}


@app.get("/bookings")
def list_bookings(owner_type: Optional[str] = None, owner_id: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    if owner_type and owner_id is not None:
        rows = get_bookings_for_owner(conn, owner_type, owner_id)
        return [dict(r) for r in rows]
    if start is not None and end is not None:
        rows = get_bookings_in_range(conn, start, end)
        return [dict(r) for r in rows]
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY start LIMIT 100")
    return [dict(r) for r in cur.fetchall()]
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from management.auth import register_user, authenticate_user
from management.config import get_config
from management.database.main import (
    init_db,
    add_teacher,
    add_student,
    book_slot,
    get_bookings_for_owner,
    get_bookings_in_range,
    get_connection,
)


# Configuration
CFG = get_config()
DB_URL = CFG.db.url or "sqlite:///./data.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


app = FastAPI(title="Course Selection API")
security = HTTPBearer()


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    try:
        import jwt as _jwt

        return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as exc:  # pragma: no cover - dependency/runtime issue
        raise HTTPException(status_code=500, detail=f"JWT error: {exc}")


def decode_token(token: str) -> dict:
    try:
        import jwt as _jwt

        return _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def get_db():
    return init_db(DB_URL)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    conn = get_connection(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


# Pydantic models
class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class TeacherIn(BaseModel):
    name: str
    email: Optional[str] = None


class StudentIn(BaseModel):
    name: str
    email: Optional[str] = None


class BookingIn(BaseModel):
    owner_type: str
    owner_id: int
    start: int
    end: int
    course_id: Optional[int] = None


@app.post("/register", response_model=dict)
def register(payload: RegisterIn):
    conn = init_db(DB_URL)
    uid = register_user(conn, payload.username, payload.password, is_admin=False)
    return {"user_id": uid}


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    conn = init_db(DB_URL)
    """Clean FastAPI API for course selection.

    Provides endpoints for registration, login (JWT), creating teachers/students
    and booking slots. This file keeps routing simple and delegates business
    logic to modules in `management.*`.
    """
    from __future__ import annotations

    import os
    from datetime import datetime, timedelta
    from typing import Optional

    from fastapi import Depends, FastAPI, HTTPException, Security
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel

    from management.auth import register_user, authenticate_user
    from management.config import get_config
    from management.database.main import (
        init_db,
        add_teacher,
        add_student,
        book_slot,
        get_bookings_for_owner,
        get_bookings_in_range,
        get_connection,
    )


    # Configuration
    CFG = get_config()
    DB_URL = CFG.db.url or "sqlite:///./data.db"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


    app = FastAPI(title="Course Selection API")
    security = HTTPBearer()


    def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token (uses PyJWT if available).

        The token payload will include 'exp' and 'iat'.
        """
        to_encode = data.copy()
        now = datetime.utcnow()
        expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "iat": now})
        try:
            import jwt as _jwt

            return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        except Exception as exc:  # pragma: no cover - dependency/runtime issue
            raise HTTPException(status_code=500, detail=f"JWT error: {exc}")


    def decode_token(token: str) -> dict:
        try:
            import jwt as _jwt

            return _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")


    def get_db():
        return init_db(DB_URL)


    def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
        token = credentials.credentials
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        conn = get_connection(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        return row


    # Pydantic models
    class RegisterIn(BaseModel):
        username: str
        password: str


    class TokenOut(BaseModel):
        access_token: str
        token_type: str = "bearer"


    class LoginIn(BaseModel):
        username: str
        password: str


    class TeacherIn(BaseModel):
        name: str
        email: Optional[str] = None


    class StudentIn(BaseModel):
        name: str
        email: Optional[str] = None


    class BookingIn(BaseModel):
        owner_type: str
        owner_id: int
        start: int
        end: int
        course_id: Optional[int] = None


    @app.post("/register", response_model=dict)
    def register(payload: RegisterIn):
        conn = init_db(DB_URL)
        uid = register_user(conn, payload.username, payload.password, is_admin=False)
        return {"user_id": uid}


    @app.post("/login", response_model=TokenOut)
    def login(payload: LoginIn):
        conn = init_db(DB_URL)
        """Clean FastAPI API for course selection.

        Provides endpoints for registration, login (JWT), creating teachers/students
        and booking slots. This file keeps routing simple and delegates business
        logic to modules in `management.*`.
        """
        from __future__ import annotations

        import os
        from datetime import datetime, timedelta
        from typing import Optional

        from fastapi import Depends, FastAPI, HTTPException, Security
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from pydantic import BaseModel

        from management.auth import register_user, authenticate_user
        from management.config import get_config
        from management.database.main import (
            init_db,
            add_teacher,
            add_student,
            book_slot,
            get_bookings_for_owner,
            get_bookings_in_range,
            get_connection,
        )


        # Configuration
        CFG = get_config()
        DB_URL = CFG.db.url or "sqlite:///./data.db"
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


        app = FastAPI(title="Course Selection API")
        security = HTTPBearer()


        def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
            """Create a JWT access token (uses PyJWT if available).

            The token payload will include 'exp' and 'iat'.
            """
            to_encode = data.copy()
            now = datetime.utcnow()
            expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire, "iat": now})
            try:
                import jwt as _jwt

                return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            except Exception as exc:  # pragma: no cover - dependency/runtime issue
                raise HTTPException(status_code=500, detail=f"JWT error: {exc}")


        def decode_token(token: str) -> dict:
            try:
                import jwt as _jwt

                return _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")


        def get_db():
            return init_db(DB_URL)


        def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
            token = credentials.credentials
            payload = decode_token(token)
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            conn = get_connection(DB_URL)
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="User not found")
            return row


        # Pydantic models
        class RegisterIn(BaseModel):
            username: str
            password: str


        class TokenOut(BaseModel):
            access_token: str
            token_type: str = "bearer"


        class LoginIn(BaseModel):
            username: str
            password: str


        class TeacherIn(BaseModel):
            name: str
            email: Optional[str] = None


        class StudentIn(BaseModel):
            name: str
            email: Optional[str] = None


        class BookingIn(BaseModel):
            owner_type: str
            owner_id: int
            start: int
            end: int
            course_id: Optional[int] = None


        @app.post("/register", response_model=dict)
        def register(payload: RegisterIn):
            conn = init_db(DB_URL)
            uid = register_user(conn, payload.username, payload.password, is_admin=False)
            return {"user_id": uid}


        @app.post("/login", response_model=TokenOut)
        def login(payload: LoginIn):
            conn = init_db(DB_URL)
            ok = authenticate_user(conn, payload.username, payload.password)
            if not ok:
                raise HTTPException(status_code=400, detail="Incorrect username or password")
            data = {"sub": payload.username}
            token = create_token(data)
            return {"access_token": token}


        @app.post("/teachers", response_model=dict)
        def create_teacher(payload: TeacherIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            tid = add_teacher(conn, payload.name, payload.email)
            return {"teacher_id": tid}


        @app.post("/students", response_model=dict)
        def create_student(payload: StudentIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            sid = add_student(conn, payload.name, payload.email)
            return {"student_id": sid}


        @app.post("/book", response_model=dict)
        def create_booking(payload: BookingIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            ok = book_slot(conn, payload.owner_type, payload.owner_id, payload.start, payload.end, payload.course_id)
            if not ok:
                raise HTTPException(status_code=409, detail="Time slot conflict")
            return {"booked": True}


        @app.get("/bookings")
        def list_bookings(owner_type: Optional[str] = None, owner_id: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            if owner_type and owner_id is not None:
                rows = get_bookings_for_owner(conn, owner_type, owner_id)
                return [dict(r) for r in rows]
            if start is not None and end is not None:
                rows = get_bookings_in_range(conn, start, end)
                return [dict(r) for r in rows]
            cur = conn.cursor()
            cur.execute("SELECT * FROM bookings ORDER BY start LIMIT 100")
            return [dict(r) for r in cur.fetchall()]

                return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            except Exception as e:  # pragma: no cover - indicates missing dependency or encoding error
                raise HTTPException(status_code=500, detail=f"JWT library error: {e}")


        def decode_token(token: str) -> dict:
            try:
                import jwt as _jwt

                payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                return payload
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")


        def get_db_conn():
            return init_db(DB_URL)


        def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
            token = credentials.credentials
            payload = decode_token(token)
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            # load user from db
            conn = get_connection(DB_URL)
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="User not found")
            return row


        # Pydantic models
        class RegisterIn(BaseModel):
            username: str
            password: str


        class TokenOut(BaseModel):
            access_token: str
            token_type: str = "bearer"


        class LoginIn(BaseModel):
            username: str
            password: str


        class TeacherIn(BaseModel):
            name: str
            email: Optional[str] = None


        class StudentIn(BaseModel):
            name: str
            email: Optional[str] = None


        class BookingIn(BaseModel):
            owner_type: str
            owner_id: int
            start: int
            end: int
            course_id: Optional[int] = None


        @app.post("/register", response_model=dict)
        def register(payload: RegisterIn):
            conn = init_db(DB_URL)
            # reuse register_user which writes hashed password
            uid = register_user(conn, payload.username, payload.password, is_admin=False)
            return {"user_id": uid}


        @app.post("/login", response_model=TokenOut)
        def login(payload: LoginIn):
            conn = init_db(DB_URL)
            ok = authenticate_user(conn, payload.username, payload.password)
            if not ok:
                raise HTTPException(status_code=400, detail="Incorrect username or password")
            data = {"sub": payload.username}
            token = create_token(data)
            return {"access_token": token}


        @app.post("/teachers", response_model=dict)
        def create_teacher(payload: TeacherIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            tid = add_teacher(conn, payload.name, payload.email)
            return {"teacher_id": tid}


        @app.post("/students", response_model=dict)
        def create_student(payload: StudentIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            sid = add_student(conn, payload.name, payload.email)
            return {"student_id": sid}


        @app.post("/book", response_model=dict)
        def create_booking(payload: BookingIn, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            ok = book_slot(conn, payload.owner_type, payload.owner_id, payload.start, payload.end, payload.course_id)
            if not ok:
                raise HTTPException(status_code=409, detail="Time slot conflict")
            return {"booked": True}


        @app.get("/bookings")
        def list_bookings(owner_type: Optional[str] = None, owner_id: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, user=Depends(get_current_user)):
            conn = init_db(DB_URL)
            if owner_type and owner_id is not None:
                rows = get_bookings_for_owner(conn, owner_type, owner_id)
                return [dict(r) for r in rows]
            if start is not None and end is not None:
                rows = get_bookings_in_range(conn, start, end)
                return [dict(r) for r in rows]
            cur = conn.cursor()
            cur.execute("SELECT * FROM bookings ORDER BY start LIMIT 100")
            return [dict(r) for r in cur.fetchall()]
        return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:  # pragma: no cover - indicates missing dependency or encoding error
        raise HTTPException(status_code=500, detail=f"JWT library error: {e}")


def decode_token(token: str) -> dict:
    try:
        import jwt as _jwt

        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def get_db_conn():
    return init_db(DB_URL)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    # load user from db
    conn = get_connection(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


# Pydantic models
class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class TeacherIn(BaseModel):
    name: str
    email: Optional[str] = None


class StudentIn(BaseModel):
    name: str
    email: Optional[str] = None


class BookingIn(BaseModel):
    owner_type: str
    owner_id: int
    start: int
    end: int
    course_id: Optional[int] = None


@app.post("/register", response_model=dict)
def register(payload: RegisterIn):
    conn = init_db(DB_URL)
    # reuse register_user which writes hashed password
    uid = register_user(conn, payload.username, payload.password, is_admin=False)
    return {"user_id": uid}


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    conn = init_db(DB_URL)
    ok = authenticate_user(conn, payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    data = {"sub": payload.username}
    token = create_token(data)
    return {"access_token": token}


@app.post("/teachers", response_model=dict)
def create_teacher(payload: TeacherIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    tid = add_teacher(conn, payload.name, payload.email)
    return {"teacher_id": tid}


@app.post("/students", response_model=dict)
def create_student(payload: StudentIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    sid = add_student(conn, payload.name, payload.email)
    return {"student_id": sid}


@app.post("/book", response_model=dict)
def create_booking(payload: BookingIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    ok = book_slot(conn, payload.owner_type, payload.owner_id, payload.start, payload.end, payload.course_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Time slot conflict")
    return {"booked": True}


@app.get("/bookings")
def list_bookings(owner_type: Optional[str] = None, owner_id: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    if owner_type and owner_id is not None:
        rows = get_bookings_for_owner(conn, owner_type, owner_id)
        return [dict(r) for r in rows]
    if start is not None and end is not None:
        rows = get_bookings_in_range(conn, start, end)
        return [dict(r) for r in rows]
    # fallback: return empty or all bookings (limit)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY start LIMIT 100")
    return [dict(r) for r in cur.fetchall()]
"""FastAPI API for course selection: registration, login (JWT), basic CRUD for teachers/students and bookings."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from management.database.main import (
    init_db,
    add_teacher,
    add_student,
    book_slot,
    get_bookings_for_owner,
    get_bookings_in_range,
    get_connection,
)
from management.config import get_config
from management.auth import register_user, authenticate_user


# Config
CFG = get_config()
DB_URL = CFG.db.url or "sqlite:///./data.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


app = FastAPI(title="Course Selection API")
security = HTTPBearer()


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    try:
        import jwt as _jwt

        return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:  # pragma: no cover - indicates missing dependency or encoding error
        raise HTTPException(status_code=500, detail=f"JWT library error: {e}")


def decode_token(token: str) -> dict:
    try:
        import jwt as _jwt

        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def get_db_conn():
    return init_db(DB_URL)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    # load user from db
    conn = get_connection(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row


# Pydantic models
class RegisterIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class TeacherIn(BaseModel):
    name: str
    email: Optional[str] = None


class StudentIn(BaseModel):
    name: str
    email: Optional[str] = None


class BookingIn(BaseModel):
    owner_type: str
    owner_id: int
    start: int
    end: int
    course_id: Optional[int] = None


@app.post("/register", response_model=dict)
def register(payload: RegisterIn):
    conn = init_db(DB_URL)
    # reuse register_user which writes hashed password
    uid = register_user(conn, payload.username, payload.password, is_admin=False)
    return {"user_id": uid}


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    conn = init_db(DB_URL)
    ok = authenticate_user(conn, payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    data = {"sub": payload.username}
    token = create_token(data)
    return {"access_token": token}


@app.post("/teachers", response_model=dict)
def create_teacher(payload: TeacherIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    tid = add_teacher(conn, payload.name, payload.email)
    return {"teacher_id": tid}


@app.post("/students", response_model=dict)
def create_student(payload: StudentIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    sid = add_student(conn, payload.name, payload.email)
    return {"student_id": sid}


@app.post("/book", response_model=dict)
def create_booking(payload: BookingIn, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    ok = book_slot(conn, payload.owner_type, payload.owner_id, payload.start, payload.end, payload.course_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Time slot conflict")
    return {"booked": True}


@app.get("/bookings")
def list_bookings(owner_type: Optional[str] = None, owner_id: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, user=Depends(get_current_user)):
    conn = init_db(DB_URL)
    if owner_type and owner_id is not None:
        rows = get_bookings_for_owner(conn, owner_type, owner_id)
        return [dict(r) for r in rows]
    if start is not None and end is not None:
        rows = get_bookings_in_range(conn, start, end)
        return [dict(r) for r in rows]
    # fallback: return empty or all bookings (limit)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY start LIMIT 100")
    return [dict(r) for r in cur.fetchall()]

"""快速测试：初始化数据库并创建初始管理员，添加 teacher/student 并尝试预订。"""
from management.config import get_config, hash_password
from management.database.main import (
    init_db,
    create_admin_if_missing,
    add_teacher,
    add_student,
    book_slot,
    get_connection,
    create_user,
    get_user_by_username,
)
from management.auth import register_user, authenticate_user


def main():
    cfg = get_config()
    # 使用 sqlite 本地文件 ./test_data.db 进行测试
    db_url = cfg.db.url or "sqlite:///./test_data.db"
    conn = init_db(db_url)

    # 如果配置中没有 hash，则临时生成一个用于测试
    if not cfg.admin.password_hash or not cfg.admin.salt:
        h, s = hash_password("admin-pass")
        cfg.admin.password_hash = h
        cfg.admin.salt = s

    create_admin_if_missing(conn, cfg.admin)
    print("admin ensured")
    print("-- users --")
    # 创建普通用户并验证登录
    u_id = register_user(conn, "testuser", "secret", is_admin=False)
    print("created user id", u_id)
    assert authenticate_user(conn, "testuser", "secret")
    assert not authenticate_user(conn, "testuser", "wrong")

    t_id = add_teacher(conn, "Alice", "alice@example.com")
    s_id = add_student(conn, "Bob", "bob@example.com")
    print("teacher id", t_id, "student id", s_id)

    ok = book_slot(conn, "teacher", t_id, 9, 11, course_id=1)
    print("teacher booked 9-11:", ok)
    ok2 = book_slot(conn, "student", s_id, 10, 12, course_id=1)
    print("student booked 10-12 (should conflict):", ok2)

    print("bookings for teacher:", get_connection(db_url).cursor().execute("SELECT * FROM bookings").fetchall())


if __name__ == "__main__":
    main()

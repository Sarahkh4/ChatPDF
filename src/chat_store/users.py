import sqlite3
import uuid

from fastapi import HTTPException, status

from src.chat_store.database import connect, now, row_to_dict


def create_user(email: str, password_hash: str):
    user = {
        "id": str(uuid.uuid4()),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "created_at": now(),
    }
    try:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, password_hash, created_at)
                VALUES (:id, :email, :password_hash, :created_at)
                """,
                user,
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from exc

    user.pop("password_hash")
    return user


def get_user_by_email(email: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return row_to_dict(row)


def get_user(user_id: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return row_to_dict(row)

import uuid

from fastapi import HTTPException, status

from src.chat_store.database import connect, now, row_to_dict


def create_chat(user_id: str, title: str | None = None):
    timestamp = now()
    chat = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title.strip() if title and title.strip() else "New chat",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, user_id, title, created_at, updated_at)
            VALUES (:id, :user_id, :title, :created_at, :updated_at)
            """,
            chat,
        )
    return chat


def list_chats(user_id: str):
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                chats.id,
                chats.user_id,
                chats.title,
                chats.created_at,
                chats.updated_at,
                COUNT(documents.id) AS document_count
            FROM chats
            LEFT JOIN documents ON documents.chat_id = chats.id
            WHERE chats.user_id = ?
            GROUP BY chats.id
            ORDER BY chats.updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_chat_for_user(user_id: str, chat_id: str):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM chats
            WHERE id = ? AND user_id = ?
            """,
            (chat_id, user_id),
        ).fetchone()

    chat = row_to_dict(row)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    return chat


def touch_chat(user_id: str, chat_id: str):
    get_chat_for_user(user_id, chat_id)
    with connect() as conn:
        conn.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (now(), chat_id, user_id),
        )

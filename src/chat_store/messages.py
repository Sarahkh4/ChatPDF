import uuid

from src.chat_store.chats import get_chat_for_user, touch_chat
from src.chat_store.database import connect, now, row_to_dict


def create_message(user_id: str, chat_id: str, role: str, content: str):
    get_chat_for_user(user_id, chat_id)
    message = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "created_at": now(),
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, user_id, chat_id, role, content, created_at)
            VALUES (:id, :user_id, :chat_id, :role, :content, :created_at)
            """,
            message,
        )
    touch_chat(user_id, chat_id)
    return message


def list_messages(user_id: str, chat_id: str):
    get_chat_for_user(user_id, chat_id)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE user_id = ? AND chat_id = ?
            ORDER BY created_at ASC
            """,
            (user_id, chat_id),
        ).fetchall()
    return [row_to_dict(row) for row in rows]

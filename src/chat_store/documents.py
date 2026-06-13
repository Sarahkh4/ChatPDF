from fastapi import HTTPException, status

from src.chat_store.chats import get_chat_for_user, touch_chat
from src.chat_store.database import connect, now, row_to_dict


def create_document(
    user_id: str,
    chat_id: str,
    document_id: str,
    filename: str,
    file_hash: str,
    stored_filename: str,
    total_chunks: int,
):
    get_chat_for_user(user_id, chat_id)
    document = {
        "id": document_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "filename": filename,
        "file_hash": file_hash,
        "stored_filename": stored_filename,
        "total_chunks": total_chunks,
        "created_at": now(),
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, user_id, chat_id, filename, file_hash, stored_filename, total_chunks, created_at
            )
            VALUES (
                :id, :user_id, :chat_id, :filename, :file_hash, :stored_filename, :total_chunks, :created_at
            )
            """,
            document,
        )
    touch_chat(user_id, chat_id)
    return document


def list_documents(user_id: str, chat_id: str):
    get_chat_for_user(user_id, chat_id)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, file_hash, total_chunks, created_at
            FROM documents
            WHERE user_id = ? AND chat_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, chat_id),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_document_by_hash(user_id: str, chat_id: str, file_hash: str):
    get_chat_for_user(user_id, chat_id)
    with connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM documents
            WHERE user_id = ? AND chat_id = ? AND file_hash = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, chat_id, file_hash),
        ).fetchone()
    return row_to_dict(row)


def get_document_for_user(user_id: str, chat_id: str, document_id: str):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ? AND user_id = ? AND chat_id = ?
            """,
            (document_id, user_id, chat_id),
        ).fetchone()

    document = row_to_dict(row)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


def delete_document_record(user_id: str, chat_id: str, document_id: str):
    document = get_document_for_user(user_id, chat_id, document_id)
    with connect() as conn:
        conn.execute(
            """
            DELETE FROM documents
            WHERE id = ? AND user_id = ? AND chat_id = ?
            """,
            (document_id, user_id, chat_id),
        )
    touch_chat(user_id, chat_id)
    return document

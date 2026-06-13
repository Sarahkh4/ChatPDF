from fastapi import APIRouter, Depends, File, UploadFile

from schema.rag import ChatCreateRequest, QuestionRequest
from src.auth import get_current_user_id
from src.chat_store import (
    create_chat,
    create_message,
    get_chat_for_user,
    list_chats,
    list_documents,
    list_messages,
    touch_chat,
)
from src.document_service import delete_document_from_chat, upload_document_to_chat
from src.logging_config import get_logger
from src.rag import ask_question


router = APIRouter(prefix="/chats", tags=["chats"])
logger = get_logger(__name__)


@router.post("")
def create_new_chat(
    request: ChatCreateRequest,
    user_id: str = Depends(get_current_user_id),
):
    chat = create_chat(user_id=user_id, title=request.title)
    logger.info(
        "Chat created | user_id=%s | chat_id=%s | title=%s",
        user_id,
        chat["id"],
        chat["title"],
    )
    return {"chat": chat}


@router.get("")
def get_chats(user_id: str = Depends(get_current_user_id)):
    chats = list_chats(user_id)
    logger.info("Chat list requested | user_id=%s | chat_count=%s", user_id, len(chats))
    return {"chats": chats}


@router.get("/{chat_id}")
def get_chat(chat_id: str, user_id: str = Depends(get_current_user_id)):
    chat = get_chat_for_user(user_id=user_id, chat_id=chat_id)
    documents = list_documents(user_id=user_id, chat_id=chat_id)
    messages = list_messages(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Chat opened | user_id=%s | chat_id=%s | document_count=%s | message_count=%s",
        user_id,
        chat_id,
        len(documents),
        len(messages),
    )
    return {
        "chat": chat,
        "documents": documents,
        "messages": messages,
    }


@router.post("/{chat_id}/upload")
def upload_pdf(
    chat_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    logger.info(
        "PDF upload started | user_id=%s | chat_id=%s | filename=%s",
        user_id,
        chat_id,
        file.filename,
    )
    document = upload_document_to_chat(
        user_id=user_id,
        chat_id=chat_id,
        file=file,
    )
    logger.info(
        "PDF upload completed | user_id=%s | chat_id=%s | document_id=%s | filename=%s | chunks=%s | already_exists=%s",
        user_id,
        chat_id,
        document["id"],
        document["filename"],
        document["total_chunks"],
        document.get("already_exists", False),
    )
    return {
        "message": "PDF already exists in this chat"
        if document.get("already_exists")
        else "PDF uploaded for this chat",
        "chat_id": chat_id,
        "document": document,
    }


@router.post("/{chat_id}/ask")
def ask(
    chat_id: str,
    request: QuestionRequest,
    user_id: str = Depends(get_current_user_id),
):
    get_chat_for_user(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Question asked | user_id=%s | chat_id=%s | question_preview=%s",
        user_id,
        chat_id,
        _preview(request.question),
    )
    answer = ask_question(
        user_id=user_id,
        chat_id=chat_id,
        question=request.question,
    )
    create_message(
        user_id=user_id,
        chat_id=chat_id,
        role="user",
        content=request.question,
    )
    create_message(
        user_id=user_id,
        chat_id=chat_id,
        role="assistant",
        content=answer.get("final_answer", ""),
    )
    touch_chat(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Question answered | user_id=%s | chat_id=%s | source=%s | answer_preview=%s",
        user_id,
        chat_id,
        answer.get("source"),
        _preview(answer.get("final_answer", "")),
    )
    return answer


@router.get("/{chat_id}/documents")
def get_chat_documents(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
):
    documents = list_documents(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Document list requested | user_id=%s | chat_id=%s | document_count=%s",
        user_id,
        chat_id,
        len(documents),
    )
    return {"documents": documents}


@router.delete("/{chat_id}/documents/{document_id}")
def delete_document(
    chat_id: str,
    document_id: str,
    user_id: str = Depends(get_current_user_id),
):
    logger.info(
        "Document delete started | user_id=%s | chat_id=%s | document_id=%s",
        user_id,
        chat_id,
        document_id,
    )
    document = delete_document_from_chat(
        user_id=user_id,
        chat_id=chat_id,
        document_id=document_id,
    )
    logger.info(
        "Document delete completed | user_id=%s | chat_id=%s | document_id=%s | filename=%s",
        user_id,
        chat_id,
        document_id,
        document["filename"],
    )
    return {
        "message": "Document and its vectors deleted successfully",
        "document_id": document_id,
        "filename": document["filename"],
    }


def _preview(value: str, max_length: int = 120):
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length]}..."

import hashlib
import os
import uuid

from fastapi import UploadFile

from src.chat_store import (
    create_document,
    delete_document_record,
    get_document_by_hash,
    get_chat_for_user,
    get_document_for_user,
)
from src.chunking import chunk_documents
from src.loader import load_pdf
from src.logging_config import get_logger
from src.semantic_search_cache import clear_semantic_cache
from src.vector_store import delete_document_vectors, save_to_vector_db


UPLOAD_DIR = "uploads"
logger = get_logger(__name__)


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.info("Upload directory ready | path=%s", UPLOAD_DIR)


def upload_document_to_chat(user_id: str, chat_id: str, file: UploadFile):
    get_chat_for_user(user_id=user_id, chat_id=chat_id)
    ensure_upload_dir()

    original_filename = os.path.basename(file.filename)
    document_id = str(uuid.uuid4())
    stored_filename = f"{user_id}_{chat_id}_{document_id}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    file_hash = _save_file_and_hash(file, file_path)
    logger.info(
        "PDF file saved | user_id=%s | chat_id=%s | document_id=%s | file_hash=%s | path=%s",
        user_id,
        chat_id,
        document_id,
        file_hash,
        file_path,
    )

    existing_document = get_document_by_hash(
        user_id=user_id,
        chat_id=chat_id,
        file_hash=file_hash,
    )
    if existing_document:
        os.remove(file_path)
        existing_document["already_exists"] = True
        logger.info(
            "Duplicate PDF upload reused existing document | user_id=%s | chat_id=%s | existing_document_id=%s | file_hash=%s",
            user_id,
            chat_id,
            existing_document["id"],
            file_hash,
        )
        return existing_document

    documents = load_pdf(file_path)
    chunks = chunk_documents(documents)
    logger.info(
        "PDF processed | user_id=%s | chat_id=%s | document_id=%s | pages=%s | chunks=%s",
        user_id,
        chat_id,
        document_id,
        len(documents),
        len(chunks),
    )

    for i, chunk in enumerate(chunks):
        chunk.metadata["user_id"] = user_id
        chunk.metadata["chat_id"] = chat_id
        chunk.metadata["document_id"] = document_id
        chunk.metadata["filename"] = original_filename
        chunk.metadata["chunk_index"] = i

    save_to_vector_db(chunks)
    logger.info(
        "Document vectors saved | user_id=%s | chat_id=%s | document_id=%s | chunks=%s",
        user_id,
        chat_id,
        document_id,
        len(chunks),
    )
    document = create_document(
        user_id=user_id,
        chat_id=chat_id,
        document_id=document_id,
        filename=original_filename,
        file_hash=file_hash,
        stored_filename=stored_filename,
        total_chunks=len(chunks),
    )
    document["already_exists"] = False
    clear_semantic_cache(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Semantic cache cleared after upload | user_id=%s | chat_id=%s",
        user_id,
        chat_id,
    )

    return document


def delete_document_from_chat(user_id: str, chat_id: str, document_id: str):
    document = get_document_for_user(
        user_id=user_id,
        chat_id=chat_id,
        document_id=document_id,
    )
    file_path = os.path.join(UPLOAD_DIR, document["stored_filename"])

    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(
            "PDF file removed | user_id=%s | chat_id=%s | document_id=%s | path=%s",
            user_id,
            chat_id,
            document_id,
            file_path,
        )
    else:
        logger.warning(
            "PDF file missing during delete | user_id=%s | chat_id=%s | document_id=%s | path=%s",
            user_id,
            chat_id,
            document_id,
            file_path,
        )

    delete_document_vectors(
        user_id=user_id,
        chat_id=chat_id,
        document_id=document_id,
    )
    logger.info(
        "Document vectors deleted | user_id=%s | chat_id=%s | document_id=%s",
        user_id,
        chat_id,
        document_id,
    )
    delete_document_record(
        user_id=user_id,
        chat_id=chat_id,
        document_id=document_id,
    )
    logger.info(
        "Document database record deleted | user_id=%s | chat_id=%s | document_id=%s",
        user_id,
        chat_id,
        document_id,
    )
    clear_semantic_cache(user_id=user_id, chat_id=chat_id)
    logger.info(
        "Semantic cache cleared after delete | user_id=%s | chat_id=%s",
        user_id,
        chat_id,
    )

    return document


def _save_file_and_hash(file: UploadFile, file_path: str):
    hasher = hashlib.sha256()
    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            hasher.update(chunk)
            buffer.write(chunk)
    return hasher.hexdigest()

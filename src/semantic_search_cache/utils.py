import hashlib
import re

import numpy as np

from src.embeddings import get_embeddings
from src.semantic_search_cache.config import PREFIX, STOP_WORDS


embedding_model = None


def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = get_embeddings()
    return embedding_model


def to_vector_blob(vector):
    return np.array(vector, dtype=np.float32).tobytes()


def normalize_question(question: str):
    return re.sub(r"\s+", " ", question.strip().lower())


def question_tokens(question: str):
    tokens = re.findall(r"[a-z0-9]+", normalize_question(question))
    return {token for token in tokens if token not in STOP_WORDS}


def exact_cache_key(user_id: str, chat_id: str, question: str):
    question_hash = hashlib.sha256(
        normalize_question(question).encode("utf-8")
    ).hexdigest()
    return f"{PREFIX}exact:{user_id}:{chat_id}:{question_hash}"


def decode_cache_doc(cache_doc: dict):
    cached_question = cache_doc.get(b"question", b"")
    cached_answer = cache_doc.get(b"answer", b"")

    if isinstance(cached_question, bytes):
        cached_question = cached_question.decode("utf-8")
    if isinstance(cached_answer, bytes):
        cached_answer = cached_answer.decode("utf-8")

    return cached_question, cached_answer


def escape_tag(value: str):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("-", "\\-")
        .replace("_", "\\_")
        .replace(" ", "\\ ")
        .replace(".", "\\.")
        .replace("/", "\\/")
        .replace("@", "\\@")
        .replace(":", "\\:")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )

import time

import redis
from redis.commands.search.query import Query

from src.semantic_search_cache.config import (
    INDEX_NAME,
    PREFIX,
    SEMANTIC_CACHE_TTL_SECONDS,
    SIMILARITY_THRESHOLD,
    redis_client,
)
from src.semantic_search_cache.index import create_cache_index
from src.semantic_search_cache.lexical import search_lexical_cache
from src.semantic_search_cache.utils import (
    decode_cache_doc,
    escape_tag,
    exact_cache_key,
    get_embedding_model,
    to_vector_blob,
)


def search_semantic_cache(question: str, user_id: str, chat_id: str):
    try:
        create_cache_index()
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache unavailable: {exc}")
        return {
            "hit": False,
            "question_embedding": get_embedding_model().embed_query(question),
        }

    exact_match_result = search_exact_cache(question, user_id, chat_id)
    if exact_match_result:
        return exact_match_result

    lexical_match = search_lexical_cache(question, user_id, chat_id)
    if lexical_match:
        return {
            "hit": True,
            **lexical_match,
        }

    try:
        question_vector = get_embedding_model().embed_query(question)
    except Exception as exc:
        print(f"Semantic cache embedding failed: {exc}")
        return {
            "hit": False,
            "question_embedding": None,
        }

    return search_vector_cache(
        question_vector=question_vector,
        user_id=user_id,
        chat_id=chat_id,
    )


def save_semantic_cache(
    question: str,
    question_embedding,
    answer: str,
    user_id: str,
    chat_id: str,
    filename: str = "",
):
    try:
        create_cache_index()
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache unavailable; answer was not cached: {exc}")
        return False

    cache_id = exact_cache_key(user_id, chat_id, question)
    mapping = {
        "user_id": user_id,
        "chat_id": chat_id,
        "question": question,
        "answer": answer,
        "filename": filename,
        "created_at": int(time.time()),
    }

    if question_embedding is not None:
        mapping["question_embedding"] = to_vector_blob(question_embedding)

    try:
        redis_client.hset(cache_id, mapping=mapping)
        redis_client.expire(cache_id, SEMANTIC_CACHE_TTL_SECONDS)
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache save failed: {exc}")
        return False

    print(
        f"Saved semantic cache entry: {cache_id} "
        f"(expires in {SEMANTIC_CACHE_TTL_SECONDS} seconds)"
    )
    return True


def clear_semantic_cache(user_id: str, chat_id: str):
    patterns = [
        f"{PREFIX}{user_id}:{chat_id}:*",
        f"{PREFIX}exact:{user_id}:{chat_id}:*",
    ]
    try:
        keys = []
        for pattern in patterns:
            keys.extend(redis_client.keys(pattern))
        if keys:
            redis_client.delete(*keys)
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache clear failed: {exc}")


def search_exact_cache(question: str, user_id: str, chat_id: str):
    exact_key = exact_cache_key(user_id, chat_id, question)
    try:
        exact_match = redis_client.hgetall(exact_key)
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache exact lookup failed: {exc}")
        exact_match = {}

    if not exact_match:
        return None

    cached_question, cached_answer = decode_cache_doc(exact_match)
    if not cached_answer:
        return None

    print(f"Semantic cache exact hit: {exact_key}")
    return {
        "hit": True,
        "matched_question": cached_question,
        "answer": cached_answer,
        "similarity_score": 1.0,
    }


def search_vector_cache(question_vector, user_id: str, chat_id: str):
    vector_blob = to_vector_blob(question_vector)
    user_tag = escape_tag(user_id)
    chat_tag = escape_tag(chat_id)

    query = (
        Query(
            f"(@user_id:{{{user_tag}}} @chat_id:{{{chat_tag}}})=>[KNN 1 @question_embedding $vec AS vector_distance]"
        )
        .sort_by("vector_distance")
        .return_fields(
            "question",
            "answer",
            "filename",
            "vector_distance",
        )
        .dialect(2)
    )

    try:
        results = redis_client.ft(INDEX_NAME).search(
            query,
            query_params={"vec": vector_blob},
        )
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache search failed: {exc}")
        return {
            "hit": False,
            "question_embedding": question_vector,
        }

    print(f"Semantic cache search returned {len(results.docs)} result(s)")

    if len(results.docs) == 0:
        return {
            "hit": False,
            "question_embedding": question_vector,
        }

    doc = results.docs[0]
    distance = float(doc.vector_distance)
    similarity = 1 - distance

    if similarity >= SIMILARITY_THRESHOLD:
        print(f"Semantic cache hit with similarity {similarity:.3f}")
        return {
            "hit": True,
            "matched_question": doc.question.decode()
            if isinstance(doc.question, bytes)
            else doc.question,
            "answer": doc.answer.decode()
            if isinstance(doc.answer, bytes)
            else doc.answer,
            "similarity_score": similarity,
        }

    print(f"Semantic cache miss; best similarity was {similarity:.3f}")
    return {
        "hit": False,
        "question_embedding": question_vector,
    }

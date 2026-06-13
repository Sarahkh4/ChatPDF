from difflib import SequenceMatcher

import redis

from src.semantic_search_cache.config import (
    LEXICAL_SIMILARITY_THRESHOLD,
    PREFIX,
    TOKEN_OVERLAP_THRESHOLD,
    redis_client,
)
from src.semantic_search_cache.utils import (
    decode_cache_doc,
    normalize_question,
    question_tokens,
)


def search_lexical_cache(question: str, user_id: str, chat_id: str):
    pattern = f"{PREFIX}exact:{user_id}:{chat_id}:*"
    try:
        keys = redis_client.keys(pattern)
    except redis.exceptions.RedisError as exc:
        print(f"Semantic cache lexical lookup failed: {exc}")
        return None

    best_match = None
    best_score = 0.0

    for key in keys:
        try:
            cache_doc = redis_client.hgetall(key)
        except redis.exceptions.RedisError:
            continue

        cached_question, cached_answer = decode_cache_doc(cache_doc)
        if not cached_question or not cached_answer:
            continue

        score, common_count, token_overlap = question_similarity(
            question,
            cached_question,
        )
        if score > best_score:
            best_score = score
            best_match = {
                "matched_question": cached_question,
                "answer": cached_answer,
                "similarity_score": score,
                "common_count": common_count,
                "token_overlap": token_overlap,
            }

    is_text_match = (
        best_match
        and best_score >= LEXICAL_SIMILARITY_THRESHOLD
        and best_match["token_overlap"] >= TOKEN_OVERLAP_THRESHOLD
    )
    is_token_match = (
        best_match
        and best_match["common_count"] >= 2
        and best_match["token_overlap"] >= TOKEN_OVERLAP_THRESHOLD
    )

    if best_match and (is_text_match or is_token_match):
        print(f"Semantic cache lexical hit with similarity {best_score:.3f}")
        best_match.pop("common_count")
        best_match.pop("token_overlap")
        return best_match

    if best_match:
        print(f"Semantic cache lexical miss; best similarity was {best_score:.3f}")

    return None


def question_similarity(question: str, cached_question: str):
    normalized_question = normalize_question(question)
    normalized_cached = normalize_question(cached_question)
    text_similarity = SequenceMatcher(
        None,
        normalized_question,
        normalized_cached,
    ).ratio()

    tokens = question_tokens(question)
    cached_tokens = question_tokens(cached_question)
    if not tokens or not cached_tokens:
        return text_similarity, 0, 0.0

    common_tokens = tokens & cached_tokens
    token_overlap = len(common_tokens) / min(len(tokens), len(cached_tokens))
    return max(text_similarity, token_overlap), len(common_tokens), token_overlap

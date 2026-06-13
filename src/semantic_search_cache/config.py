import os

import redis
from dotenv import load_dotenv

from utils.contant import SEMANTIC_CACHE_TTL_SECONDS


load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

INDEX_NAME = "idx:semantic_cache:v2"
PREFIX = "cache:"
VECTOR_DIM = 384
SIMILARITY_THRESHOLD = 0.70
LEXICAL_SIMILARITY_THRESHOLD = 0.82
TOKEN_OVERLAP_THRESHOLD = 0.80

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "can",
    "could",
    "do",
    "does",
    "explain",
    "for",
    "from",
    "give",
    "how",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "please",
    "tell",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
}

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=False,
    socket_connect_timeout=2,
    socket_timeout=2,
)

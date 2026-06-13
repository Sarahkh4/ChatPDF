import redis
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType

from src.semantic_search_cache.config import INDEX_NAME, PREFIX, VECTOR_DIM, redis_client


def create_cache_index():
    try:
        redis_client.ping()
        redis_client.ft(INDEX_NAME).info()
        return
    except redis.exceptions.ResponseError:
        pass

    schema = [
        TagField("user_id"),
        TagField("chat_id"),
        TextField("question"),
        TextField("answer"),
        TextField("filename"),
        NumericField("created_at"),
        VectorField(
            "question_embedding",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIM,
                "DISTANCE_METRIC": "COSINE",
            },
        ),
    ]

    definition = IndexDefinition(
        prefix=[PREFIX],
        index_type=IndexType.HASH,
    )

    redis_client.ft(INDEX_NAME).create_index(
        fields=schema,
        definition=definition,
    )

from src.llm import generate_answer
from src.logging_config import get_logger
from src.semantic_search_cache import search_semantic_cache, save_semantic_cache
from src.vector_store import load_vector_db
from utils.contant import MMR_LAMBDA_MULT, RETRIEVAL_FETCH_K, RETRIEVAL_TOP_K


logger = get_logger(__name__)
NOT_FOUND_ANSWER = "I could not find this information in the document."


def ask_question(question: str, user_id: str, chat_id: str):
    cache_result = search_semantic_cache(
        question=question,
        user_id=user_id,
        chat_id=chat_id,
    )

    if cache_result["hit"]:
        logger.info(
            "RAG cache hit | user_id=%s | chat_id=%s | similarity=%s",
            user_id,
            chat_id,
            cache_result["similarity_score"],
        )
        return {
            "question": question,
            "source": "semantic_search_cache",
            "matched_question": cache_result["matched_question"],
            "similarity_score": cache_result["similarity_score"],
            "final_answer": cache_result["answer"],
        }

    results = retrieve_relevant_chunks(
        question=question,
        user_id=user_id,
        chat_id=chat_id,
    )

    if not results:
        logger.warning(
            "RAG retrieval returned no chunks | user_id=%s | chat_id=%s",
            user_id,
            chat_id,
        )

    context = "\n\n---\n\n".join(
        format_context_chunk(index, doc)
        for index, doc in enumerate(results, start=1)
    )

    prompt = f"""
You are a helpful AI assistant for answering questions from uploaded PDFs.

Use ONLY the provided context.
If the answer is not present in the context, say:
"{NOT_FOUND_ANSWER}"

When possible, include the relevant page number or file name from the context.

Context:
{context}

Question:
{question}
"""

    answer = generate_answer(prompt)

    filenames = sorted(
        {
            doc.metadata.get("filename", "")
            for doc in results
            if doc.metadata.get("filename")
        }
    )

    if results and not answer.strip().startswith(NOT_FOUND_ANSWER):
        save_semantic_cache(
            question=question,
            question_embedding=cache_result["question_embedding"],
            answer=answer,
            user_id=user_id,
            chat_id=chat_id,
            filename=", ".join(filenames),
        )
    else:
        logger.info(
            "RAG answer not cached | user_id=%s | chat_id=%s | reason=no_retrieval_or_not_found",
            user_id,
            chat_id,
        )

    return {
        "question": question,
        "source": "rag",
        "user_id": user_id,
        "chat_id": chat_id,
        "retrieved_chunks": [
            doc.page_content for doc in results
        ],
        "retrieved_metadata": [
            doc.metadata for doc in results
        ],
        "final_answer": answer,
    }


def retrieve_relevant_chunks(question: str, user_id: str, chat_id: str):
    vector_db = load_vector_db()
    metadata_filter = {
        "$and": [
            {"user_id": {"$eq": user_id}},
            {"chat_id": {"$eq": chat_id}},
        ]
    }

    try:
        results = vector_db.max_marginal_relevance_search(
            question,
            k=RETRIEVAL_TOP_K,
            fetch_k=RETRIEVAL_FETCH_K,
            lambda_mult=MMR_LAMBDA_MULT,
            filter=metadata_filter,
        )
        retrieval_strategy = "mmr"
    except Exception as exc:
        logger.warning(
            "MMR retrieval failed; falling back to similarity search | user_id=%s | chat_id=%s | error=%s",
            user_id,
            chat_id,
            exc,
        )
        results = vector_db.similarity_search(
            question,
            k=RETRIEVAL_TOP_K,
            filter=metadata_filter,
        )
        retrieval_strategy = "similarity"

    logger.info(
        "RAG retrieved chunks | user_id=%s | chat_id=%s | strategy=%s | chunks=%s | top_k=%s | fetch_k=%s",
        user_id,
        chat_id,
        retrieval_strategy,
        len(results),
        RETRIEVAL_TOP_K,
        RETRIEVAL_FETCH_K,
    )

    for index, doc in enumerate(results, start=1):
        logger.info(
            "RAG chunk selected | rank=%s | user_id=%s | chat_id=%s | filename=%s | page=%s | chunk_index=%s | chars=%s",
            index,
            user_id,
            chat_id,
            doc.metadata.get("filename"),
            doc.metadata.get("page"),
            doc.metadata.get("chunk_index"),
            len(doc.page_content),
        )

    return results


def format_context_chunk(index, doc):
    filename = doc.metadata.get("filename", "unknown file")
    page = doc.metadata.get("page")
    page_label = f"page {page + 1}" if isinstance(page, int) else "unknown page"

    return (
        f"[Chunk {index} | {filename} | {page_label}]\n"
        f"{doc.page_content}"
    )

from src.vector_store import load_vector_db
from src.llm import generate_answer

def ask_question(question: str):

    vector_db = load_vector_db()

    results = vector_db.similarity_search(
        question,
        k=3
    )

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    prompt = f"""
You are a helpful AI assistant.

Answer ONLY from the provided context.

If the answer is not present in the context,
say: "I could not find this information in the document."

Context:
{context}

Question:
{question}
"""

    answer = generate_answer(prompt)

    return {
        "question": question,
        "retrieved_chunks": [
            doc.page_content for doc in results
        ],
        "final_answer": answer
    }
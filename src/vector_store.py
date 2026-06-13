from langchain_chroma import Chroma
from src.embeddings import get_embeddings

VECTOR_DB_DIR = "vector_db"

# def save_to_vector_db(chunks):
    
#     vector_db = Chroma.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         persist_directory=VECTOR_DB_DIR
#     )

#     return vector_db

def save_to_vector_db(chunks):
    vector_db = load_vector_db()  # load existing
    vector_db.add_documents(chunks)  # append
    return vector_db

def load_vector_db():
    
    vector_db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=get_embeddings()
    )

    return vector_db

def delete_document_vectors(user_id: str, chat_id: str, document_id: str):
    vector_db = load_vector_db()

    vector_db._collection.delete(
        where={
            "$and": [
                {"user_id": {"$eq": user_id}},
                {"chat_id": {"$eq": chat_id}},
                {"document_id": {"$eq": document_id}},
            ]
        }
    )
    

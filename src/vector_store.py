from langchain_chroma import Chroma
from src.embeddings import get_embedding_model

VECTOR_DB_DIR = "vector_db"

embeddings = get_embedding_model()

def save_to_vector_db(chunks):
    
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )

    return vector_db


def load_vector_db():
    
    vector_db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings
    )

    return vector_db
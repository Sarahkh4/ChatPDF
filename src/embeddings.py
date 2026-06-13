from langchain_huggingface import HuggingFaceEmbeddings

embeddings = None

def get_embedding_model():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return embeddings


def get_embeddings():
    global embeddings
    if embeddings is None:
        embeddings = get_embedding_model()
    return embeddings


from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.contant import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(documents)

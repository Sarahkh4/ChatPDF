from fastapi import FastAPI, UploadFile, File
import os
import shutil
from src.loader import load_pdf
from src.chunking import chunk_documents
from src.vector_store import save_to_vector_db
from src.vector_store import delete_document_vectors
from schema.rag import QuestionRequest
from src.rag import ask_question

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "ChatPDF RAG API is running"}


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    documents = load_pdf(file_path)

    chunks = chunk_documents(documents)
    #
    for chunk in chunks:
        chunk.metadata["filename"] = file.filename

    save_to_vector_db(chunks)

    return {
        "message": "PDF uploaded, processed, and stored in vector DB",
        "filename": file.filename,
        "total_pages": len(documents),
        "total_chunks": len(chunks)
    }


@app.post("/ask")
def ask(request: QuestionRequest):
    response = ask_question(request.question)
    return response

@app.get("/documents")
def list_documents():
    files = os.listdir(UPLOAD_DIR)

    return {
        "documents": files
    }

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return {"message": "Document not found"}

    os.remove(file_path)

    delete_document_vectors(filename)

    return {
        "message": "Document and its vectors deleted successfully",
        "filename": filename
    }
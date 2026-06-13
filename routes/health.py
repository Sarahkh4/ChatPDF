from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def home():
    return {"message": "ChatPDF RAG API is running"}

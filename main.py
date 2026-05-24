from fastapi import FastAPI, UploadFile, File
import os
import shutil

app = FastAPI()

upload_folder = "uploads"

os.makedirs(upload_folder, exist_ok=True)

@app.get("/")
def home():
    return {"message": "ChatPDF RAG API is running"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):

    file_location = os.path.join(upload_folder, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "message": "File uploaded successfully"}
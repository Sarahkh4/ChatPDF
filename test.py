from src.embeddings import get_embedding_model
import os
import shutil

upload_folder = "uploads"

os.makedirs(upload_folder, exist_ok=True)
file_location = os.path.join(upload_folder, file.filename)

with open(file_location, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
get_embedding_model()
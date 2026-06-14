# ChatPDF RAG Application

ChatPDF is a full-stack Retrieval-Augmented Generation application that lets users sign up, log in, create multiple chats, upload PDFs inside each chat, and ask questions grounded in those documents.

The project started as a simple FastAPI RAG API where `user_id` and `chat_id` were manually passed in the URL. It has since grown into a ChatGPT-like authenticated application with JWT auth, persistent chat history, document management, semantic answer caching, a React frontend, and Docker support.

## Features

- JWT authentication with signup and login
- ChatGPT-like React dashboard
- Multiple chats per user
- PDF upload per chat
- Document list inside each chat
- Delete document and remove its ChromaDB vectors
- Persistent chat history after refresh
- SQLite storage for users, chats, messages, and document metadata
- ChromaDB vector storage for document chunks
- Redis semantic cache for repeated or similar questions
- 7-day Redis cache TTL for cached answers
- Duplicate PDF detection per chat using SHA-256 file hashes
- RAG retrieval with MMR for better chunk diversity
- Backend action logging for user activity
- Dockerized backend, frontend, Redis, persistent volumes, and model cache

## Tech Stack

Backend:

- FastAPI
- SQLite
- ChromaDB
- Redis Stack
- LangChain
- HuggingFace sentence-transformer embeddings
- OpenAI-compatible chat model API

Frontend:

- React
- Vite
- Tailwind CSS
- React Router
- Lucide icons
- Nginx for Docker production serving

Infrastructure:

- Docker
- Docker Compose
- RedisInsight through Redis Stack

## Project Structure

```text
.
|-- main.py
|-- routes/
|   |-- auth.py
|   |-- chats.py
|   `-- health.py
|-- schema/
|   `-- rag.py
|-- src/
|   |-- auth.py
|   |-- chunking.py
|   |-- document_service.py
|   |-- embeddings.py
|   |-- loader.py
|   |-- llm.py
|   |-- logging_config.py
|   |-- rag.py
|   |-- vector_store.py
|   |-- chat_store/
|   |   |-- database.py
|   |   |-- users.py
|   |   |-- chats.py
|   |   |-- documents.py
|   |   `-- messages.py
|   `-- semantic_search_cache/
|       |-- config.py
|       |-- index.py
|       |-- lexical.py
|       |-- service.py
|       `-- utils.py
|-- utils/
|   `-- contant.py
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- api.js
|   |   |-- main.jsx
|   |   |-- styles.css
|   |   `-- pages/
|   |       |-- LoginPage.jsx
|   |       `-- SignupPage.jsx
|   |-- Dockerfile
|   `-- nginx.conf
|-- Dockerfile
|-- docker-compose.yml
`-- requirements.txt
```

## How The App Works

1. A user signs up or logs in.
2. The backend returns a JWT token.
3. The frontend stores the token in `localStorage`.
4. Every protected request sends:

```http
Authorization: Bearer <token>
```

5. The user creates or selects a chat.
6. PDFs are uploaded inside that selected chat.
7. The backend loads the PDF, chunks it, embeds the chunks, and stores vectors in ChromaDB.
8. When the user asks a question:
   - Redis semantic cache is checked first.
   - If there is no cache hit, ChromaDB retrieves relevant chunks.
   - The LLM answers using only the retrieved context.
   - The answer is saved in Redis for future similar questions.
   - The user question and assistant answer are saved in SQLite.

## Storage

SQLite stores:

- Users
- Chats
- Documents metadata
- Chat messages

PDF files are stored in:

```text
uploads/
```

ChromaDB vectors are stored in:

```text
vector_db/
```

Redis stores:

- Semantic answer cache
- Question embeddings for cached answers
- Previous question and answer text
- `user_id`, `chat_id`, filename, and creation time

Redis cached answers expire after 7 days.

The constants are defined in:

```text
utils/contant.py
```

```python
SEMANTIC_CACHE_TTL_SECONDS = 60 * 60 * 24 * 7

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

RETRIEVAL_TOP_K = 8
RETRIEVAL_FETCH_K = 24
MMR_LAMBDA_MULT = 0.65
```

## RAG Pipeline

The RAG code is mainly in:

- `src/loader.py`: loads PDF pages
- `src/chunking.py`: splits pages into chunks
- `src/embeddings.py`: loads HuggingFace embeddings
- `src/vector_store.py`: saves and loads ChromaDB vectors
- `src/rag.py`: retrieves context and generates answers
- `src/semantic_search_cache/`: caches previous answers in Redis

Current embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This model is relatively small and is downloaded at runtime when embeddings are first needed. Docker stores it in a persistent HuggingFace cache volume so it does not need to be downloaded again after every restart.

## Duplicate PDF Handling

The app computes a SHA-256 hash for every uploaded PDF.

If the same user uploads the same PDF into the same chat again:

- The existing document record is reused.
- No new chunks are created.
- No new embeddings are generated.
- No duplicate ChromaDB vectors are stored.

This prevents wasting disk space on duplicate vectors.

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY="your-api-key"
OPENAI_BASE_URL="your-openai-compatible-base-url"
```

Do not commit real API keys.

## Run Locally Without Docker

Start Redis first:

```powershell
docker compose up redis
```

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

Backend:

```text
http://127.0.0.1:8000
```

## Run With Docker

Build and run the entire app:

```powershell
docker compose up --build
```

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

RedisInsight:

```text
http://localhost:8001
```

Docker volumes:

- `app_data`: SQLite database
- `uploads_data`: uploaded PDFs
- `vector_data`: ChromaDB vectors
- `redis_data`: Redis data
- `huggingface_cache`: HuggingFace model cache

## API Overview

Auth:

```text
POST /auth/register
POST /auth/login
GET  /me
```

Chats:

```text
GET  /chats
POST /chats
GET  /chats/{chat_id}
```

Documents:

```text
POST   /chats/{chat_id}/upload
GET    /chats/{chat_id}/documents
DELETE /chats/{chat_id}/documents/{document_id}
```

RAG:

```text
POST /chats/{chat_id}/ask
```

## Logging

The backend logs user actions in the terminal:

- Register attempts
- Login attempts and failures
- Chat creation
- Chat opening
- PDF uploads
- PDF processing and vector saving
- Questions asked
- Answers generated
- Document deletion
- Cache clearing

Sensitive values like passwords and JWT tokens are not logged.

## Major Challenges Solved

### 1. Manual `user_id` and `chat_id`

The project originally required users to manually pass `user_id` and `chat_id` in endpoints. This was replaced with JWT authentication. The backend now gets the user from the token, and users select chats through the frontend.

### 2. Chat History Disappearing On Refresh

At first, messages were only stored in React state. Refreshing the page wiped them. A `messages` table was added to SQLite, and `GET /chats/{chat_id}` now returns saved messages.

### 3. Document Deletion

The frontend originally had no way to delete a document. A delete button was added, and the backend now removes:

- PDF file
- SQLite document record
- ChromaDB vectors
- Redis semantic cache for that chat

### 4. Duplicate Vector Storage

Uploading the same PDF repeatedly would create duplicate vectors. The app now hashes each file and reuses the existing document in the same chat.

### 5. Weak RAG Retrieval

The first RAG version used small 500-character chunks and retrieved only 3 chunks. This often missed relevant information. The app now uses:

- Larger chunks
- More overlap
- MMR retrieval
- More retrieved context
- Retrieval logging

### 6. Redis Cache Never Expired

Semantic cache entries originally stayed forever. A 7-day TTL was added.

### 7. Bad Answers Could Be Cached

The app originally cached answers even when the model said it could not find the answer. Now weak "not found" answers are not cached.

### 8. Backend Became Too Large

`main.py` originally contained most routes and logic. The app was refactored into route modules and service modules.

### 9. Semantic Cache File Became Too Large

The Redis semantic cache code was decomposed into:

- config
- index setup
- lexical matching
- service functions
- utility functions

### 10. Dockerization

The app was dockerized with separate backend, frontend, and Redis services. Persistent volumes were added so user data, vectors, uploaded files, Redis data, and model cache survive container restarts.

## Important Notes

If you changed chunking settings after uploading PDFs, existing vectors still use the old chunking. Delete and re-upload those PDFs to rebuild vectors.

The HuggingFace model is not downloaded during Docker image build. It downloads at runtime the first time embeddings are needed, then stays cached in the Docker volume.

The file name `utils/contant.py` follows the current project request. If desired later, it can be renamed to `constants.py` for spelling consistency.

## Verification Commands

Backend compile check:

```powershell
.\.venv\Scripts\python.exe -m compileall main.py routes schema src utils
```

Frontend build:

```powershell
cd frontend
npm run build
```

Docker compose validation:

```powershell
docker compose config
```

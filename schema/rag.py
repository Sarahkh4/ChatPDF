from pydantic import BaseModel


class AuthRequest(BaseModel):
    email: str
    password: str


class ChatCreateRequest(BaseModel):
    title: str | None = None


class QuestionRequest(BaseModel):
    question: str


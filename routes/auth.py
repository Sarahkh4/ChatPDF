from fastapi import APIRouter, Depends, HTTPException, status

from schema.rag import AuthRequest
from src.auth import create_access_token, get_current_user_id, hash_password, verify_password
from src.chat_store import create_user, get_user, get_user_by_email
from src.logging_config import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.post("/auth/register")
def register(request: AuthRequest):
    logger.info("Register attempt | email=%s", request.email)
    user = create_user(
        email=request.email,
        password_hash=hash_password(request.password),
    )
    access_token = create_access_token(user["id"])
    logger.info("User registered | user_id=%s | email=%s", user["id"], user["email"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/auth/login")
def login(request: AuthRequest):
    logger.info("Login attempt | email=%s", request.email)
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["password_hash"]):
        logger.warning("Login failed | email=%s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user["id"])
    user.pop("password_hash")
    logger.info("Login successful | user_id=%s | email=%s", user["id"], user["email"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    logger.info("Profile requested | user_id=%s", user_id)
    return {"user": get_user(user_id)}

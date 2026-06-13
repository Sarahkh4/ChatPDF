import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

llm = init_chat_model(
    model = "gpt-4o-mini",
    model_provider = "openai",
    api_key = api_key,
    base_url = base_url,
)

def generate_answer(prompt: str):
    response = llm.invoke(prompt)
    return response.content

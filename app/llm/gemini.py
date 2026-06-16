import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

def get_model(temperature=0):
    return init_chat_model(
        "gemini-2.5-flash-lite",
        # "llama-3.1-8b-instant",
        # model_provider="groq",
        model_provider="google_genai",
        temperature=temperature,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def get_gemini_model() -> ChatGoogleGenerativeAI:
    """
    Create and return the configured Gemini chat model.
    """

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )
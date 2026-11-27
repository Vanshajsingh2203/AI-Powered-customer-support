from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    APP_NAME : str = "Customer Support AI"
    DEBUG : bool = False
    DATABASE_URL : str
    TEST_DATABASE_URL: str | None = None
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    model_config = SettingsConfigDict(
        env_file= APP_DIR /".env",
        extra = "ignore"
    )
    
settings = Settings()
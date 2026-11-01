from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    APP_NAME : str = "Customer Support AI"
    DEBUG : bool = False
    DATABASE_URL : str
    
    model_config = SettingsConfigDict(
        env_file= APP_DIR /".env",
        extra = "ignore"
    )
    
settings = Settings()
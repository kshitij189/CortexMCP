"""
Application configuration using Pydantic Settings.
Reads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ─── Database ───
    DATABASE_URL: str = "postgresql://cortex:cortex_secret@localhost:5432/cortexmcp"

    # ─── Redis ───
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── JWT Auth ───
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ─── CORS ───
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ─── AI API Keys ───
    TAVILY_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    SERPER_API_KEY: str = ""

    # ─── ChromaDB ───
    CHROMADB_PATH: str = "./chroma_data"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

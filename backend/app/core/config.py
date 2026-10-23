import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(os.path.join(backend_dir, ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "BimaGyan - AI Insurance Platform India"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration (read strictly from environment; no hardcoded credentials)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/insurance_db")
    DATABASE_DIRECT_URL: Optional[str] = os.getenv("DATABASE_DIRECT_URL", None)
    
    # LLM & RAG Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "hybrid") # hybrid, gemini, ollama, openai
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "Qwen3-4B-Instruct-2507")
    
    # Upload storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Admin API key for protected endpoints
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY", None)

settings = Settings()

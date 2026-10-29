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
    
    # LLM & RAG Configuration (Cloudflare Workers AI / Edge Inference)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "bimagyan")
    
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


    # -- Hugging Face (fine-tuned BimaGyan model) ----------------------------
    # After fine-tuning on Kaggle, push the merged model to HF Hub and set:
    #   HF_API_TOKEN      = your HF read/write token (hf_...)
    #   HF_INFERENCE_URL  = https://api-inference.huggingface.co/models/<user>/<repo>-merged
    #   HF_MODEL_REPO     = <user>/<repo>  (used by upload / retrain scripts)
    HF_API_TOKEN: Optional[str] = os.getenv("HF_API_TOKEN", None)
    HF_INFERENCE_URL: Optional[str] = os.getenv("HF_INFERENCE_URL", None)
    HF_MODEL_REPO: Optional[str] = os.getenv("HF_MODEL_REPO", None)

    # -- Kaggle API credentials (for dataset upload & notebook retraining) ---
    KAGGLE_USERNAME: Optional[str] = os.getenv("KAGGLE_USERNAME", None)
    KAGGLE_KEY: Optional[str] = os.getenv("KAGGLE_KEY", None)

settings = Settings()

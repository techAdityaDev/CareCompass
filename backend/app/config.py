# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CareCompass"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    
    # Data paths
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"
    MODEL_DIR: Path = Path(__file__).parent.parent / "models"
    
    # Safety thresholds
    RED_FLAG_RECALL_TARGET: float = 1.0  # 100% on training set
    MAX_FOLLOW_UPS: int = 3
    CONFIDENCE_THRESHOLD: float = 0.75
    
    # Matching weights (baseline from README)
    MATCH_WEIGHTS: dict = {
        "language": 0.35,
        "proximity": 0.30,
        "skill": 0.20,
        "rating": 0.15,
    }
    
    # TinyFish
    TINYFISH_API_KEY: str = ""
    TINYFISH_TIMEOUT: float = 8.0
    
    # External APIs (optional)
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    
    # Default location (Delhi NCR centre)
    DEFAULT_LAT: float = 28.6139
    DEFAULT_LNG: float = 77.2090
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
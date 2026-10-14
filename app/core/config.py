from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PriorityCare (MEDI-DISPATCH AI)"
    VERSION: str = "1.0.0-RELEASE"
    API_V1_STR: str = "/api/v1"
    
    # Database URL: uses SQLite by default for zero-setup local execution,
    # or PostgreSQL when DATABASE_URL is provided in environment
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./prioritycare.db")
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Operational Sector Defaults (Perambalur / Trichy, Tamil Nadu)
    DEFAULT_CENTER_LAT: float = 11.234123
    DEFAULT_CENTER_LON: float = 78.874123
    
    # Deduplication thresholds
    DEDUP_RADIUS_METERS: float = 500.0
    DEDUP_TIME_WINDOW_SECONDS: int = 1200  # 20 minutes
    
    # Routing parameters
    URBAN_DETOUR_FACTOR: float = 1.3
    PEAK_HOURS_MULTIPLIER: float = 1.4

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()

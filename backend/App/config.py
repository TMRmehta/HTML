import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    
    # CORS Settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:8080",
        "http://0.0.0.0:8080",
        "https://www.oncosight.org",
        "https://cure-query-hub.vercel.app"
    ]
    
    
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

# Create settings instance
settings = Settings()

# JWT Configuration
JWT_CONFIG = {
    "SECRET_KEY": settings.SECRET_KEY,
    "ALGORITHM": settings.ALGORITHM,
    "ACCESS_TOKEN_EXPIRE_MINUTES": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    "REFRESH_TOKEN_EXPIRE_DAYS": settings.REFRESH_TOKEN_EXPIRE_DAYS,
}
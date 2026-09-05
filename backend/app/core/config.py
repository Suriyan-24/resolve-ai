import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ResolveAI"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "dev_secret_key_change_in_production_123456789"
    
    DATABASE_URL: str = "sqlite:///./resolve_ai_dev.db"
    
    RAZORPAY_KEY_ID: str = "rzp_test_mock12345678"
    RAZORPAY_KEY_SECRET: str = "mock_secret_key_12345678"
    RAZORPAY_WEBHOOK_SECRET: str = "whsec_mock_test_12345"
    
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = "mock_key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

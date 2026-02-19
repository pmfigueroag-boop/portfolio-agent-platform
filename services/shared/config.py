import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio Agent Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "admin")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "portfolio_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        import urllib.parse
        encoded_user = urllib.parse.quote_plus(self.POSTGRES_USER)
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{encoded_user}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MinIO / S3
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = False
    
    # Security - NO DEFAULTS (Fail Fast)
    API_KEY_SECRET: str = Field(..., min_length=32, description="Must be set in .env")
    JWT_SECRET: str = Field(..., min_length=32, description="Must be set in .env")

    # Financial Thresholds
    @property
    def DECIMAL_THRESHOLDS(self) -> dict:
        return {
            "BUY": float(os.getenv("THRESHOLD_BUY", "0.20")),
            "SELL": float(os.getenv("THRESHOLD_SELL", "-0.15")),
            "STRONG_BUY": float(os.getenv("THRESHOLD_STRONG_BUY", "0.40")),
            "STRONG_SELL": float(os.getenv("THRESHOLD_STRONG_BUY", "0.40")),
            "STRONG_SELL": float(os.getenv("THRESHOLD_STRONG_SELL", "-0.30"))
        }

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

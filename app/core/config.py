from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://loanuser:loanpass@localhost:3306/loandb"
    SECRET_KEY: str = "dev-secret-key-change-in-production-must-be-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LoanPortal"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

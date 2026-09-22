"""
config.py
Loads environment variables and exposes app-wide settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:password@localhost:5432/postgres"
    )

    # JWT
    SECRET_KEY: str = "change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin approval workflow
    DEVELOPER_EMAIL: str = ""
    APPROVAL_TOKEN_EXPIRE_MINUTES: int = 1440
    BACKEND_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:8080"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    # LLM fallback
    USE_LLM_FALLBACK: bool = True
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENAI_MODEL: str = "gemini-2.5-flash"

    # App
    APP_NAME: str = "College Enquiry Chatbot"
    DEBUG: bool = True

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url

    class Config:
        env_file = ".env"


settings = Settings()
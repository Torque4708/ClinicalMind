from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://clinicalmind:clinicalmind@localhost:5432/clinicalmind"
    )
    GROQ_API_KEY: str = Field(default="")
    SECRET_KEY: str = Field(default="changeme-in-production-secret-key-32chars")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")
    BACKEND_URL: str = Field(default="http://localhost:8000")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

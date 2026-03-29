from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Asynchronous Document Processing API"
    MONGODB_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    RATE_LIMIT_PER_SEC: int = 10
    APP_DATABASE_NAME: str = "document_processing"

    class Config:
        env_file = ".env"

settings = Settings()

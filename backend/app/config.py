from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Anomaly"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://anomaly:anomaly@localhost:5432/anomaly"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    jwt_secret: str = "change-me"
    cors_origins: str = "http://localhost:3000"
    embedding_dimensions: int = 768

@lru_cache
def get_settings(): return Settings()
settings = get_settings()

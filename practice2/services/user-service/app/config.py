from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://caluser:calpass@postgres:5432/calendar_db"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "changeme32byteshexstringhere!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    service_port: int = 8001


settings = Settings()

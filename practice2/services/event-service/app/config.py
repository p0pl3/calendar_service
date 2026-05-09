from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://caluser:calpass@postgres:5432/calendar_db"
    rabbitmq_url: str = "amqp://rabbituser:rabbitpass@rabbitmq:5672/"
    user_service_url: str = "http://user-service:8001"
    secret_key: str = "changeme32byteshexstringhere!!"
    algorithm: str = "HS256"
    service_port: int = 8002


settings = Settings()

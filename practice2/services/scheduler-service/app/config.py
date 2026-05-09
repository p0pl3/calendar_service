from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://caluser:calpass@postgres:5432/calendar_db"
    redis_url: str = "redis://redis:6379/1"
    rabbitmq_url: str = "amqp://rabbituser:rabbitpass@rabbitmq:5672/"


settings = Settings()

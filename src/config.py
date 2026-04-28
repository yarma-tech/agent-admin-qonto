from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://agent_qonto:agent_qonto@localhost:5432/agent_qonto"
    redis_url: str = "redis://localhost:6379/0"
    telegram_bot_token: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    webhook_base_url: str = "https://example.com"


settings = Settings()

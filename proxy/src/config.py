from pydantic_settings import BaseSettings, SettingsConfigDict


class ProxySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    qonto_organization_slug: str
    qonto_secret_key: str
    shared_token: str
    central_ws_url: str = ""


settings = ProxySettings()

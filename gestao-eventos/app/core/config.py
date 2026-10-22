from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Sistema de Gestão de Eventos"
    DATABASE_URL: str = "sqlite:///./database.db"
    SQL_ECHO: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
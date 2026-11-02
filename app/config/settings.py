import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Configuration Settings."""

    app_name: str = "ShopEase Product Service"
    app_version: str = "1.0.0"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8003
    api_prefix: str = "/api/products"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached settings instance."""
    return Settings()

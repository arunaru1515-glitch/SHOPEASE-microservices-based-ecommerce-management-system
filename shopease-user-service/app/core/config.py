import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "ShopEase-User-Service"
    APP_ENV: str = "development"
    APP_PORT: int = 8002

    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "shopease_user"
    DB_PASSWORD: str = "shopease_password"
    DB_NAME: str = "shopease_user_db"
    DATABASE_URL: str | None = None

    # JWT Settings (Shared with Authentication Microservice)
    JWT_SECRET_KEY: str = "supersecretjwtkey_change_in_production_1234567890!@#$%"
    JWT_ALGORITHM: str = "HS256"

    # Auth Microservice URL
    AUTH_SERVICE_URL: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_database_url(self) -> str:
        """Returns the configured or constructed SQLAlchemy database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()


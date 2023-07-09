from pydantic import BaseSettings


class Settings(BaseSettings):
    port: int = 80
    ENVIRONMENT: str
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int = 900
    SESSION_EXPIRE_MINUTES: int = 24 * 60 * 30

    REDIS_URL: str

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore


def get_settings() -> Settings:
    return settings


# TODO: Add setting as dependency injection for routes

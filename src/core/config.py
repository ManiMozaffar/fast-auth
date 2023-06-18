from pydantic import BaseSettings


class Settings(BaseSettings):
    port: int = 80
    ENVIRONMENT: str
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int = 900

    REDIS_URL: str

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore

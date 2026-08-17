from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "API da Plataforma de Avaliação de Funcionários"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/employee_evaluation"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""Central, validated application settings loaded from environment variables."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads values from the environment and from a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    groq_api_key: SecretStr
    groq_model: str = "llama-3.3-70b-versatile"
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        """SQLAlchemy-style URL, used later by LangChain's PGVector."""
        password = quote_plus(self.postgres_password.get_secret_value())
        return (
            f"postgresql+psycopg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Create Settings once and reuse it everywhere."""
    return Settings()

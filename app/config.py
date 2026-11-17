from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables prefixed with `API_`."""

    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", extra="ignore")

    title: str = "SIPOSM practice API"
    version: str = "1.0.0"
    environment: str = "demo"
    data_dir: Path = Path(__file__).parent / "data"
    cors_origins: list[str] = ["*"]
    token_ttl_seconds: int = Field(default=3600, gt=0)
    demo_username: str = "johndoe"
    demo_password: SecretStr = SecretStr("johndoe123")


@lru_cache
def get_settings() -> Settings:
    return Settings()

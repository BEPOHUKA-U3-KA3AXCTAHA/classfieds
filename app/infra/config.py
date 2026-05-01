from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = "dev-secret"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    default_lang: str = "me"
    supported_langs: str = "me,ru,en"

    anthropic_api_key: str = ""
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    telegram_session: str = "scraper"

    @property
    def langs(self) -> list[str]:
        return [s.strip() for s in self.supported_langs.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

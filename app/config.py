from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: str = ""
    admin_ids: str = ""
    webapp_url: str = ""
    dev_mode: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./ncoin.db"
    channel_id: str = ""
    channel_url: str = ""
    # Railway автоматически прокидывает публичный домен — используем как fallback,
    # чтобы кнопка Play/админка работали без ручной установки WEBAPP_URL.
    railway_public_domain: str = ""

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def web_url(self) -> str:
        """Публичный HTTPS-адрес Web App: WEBAPP_URL (можно без https://) или домен Railway."""
        raw = self.webapp_url.strip()
        if raw:
            if not raw.startswith("http"):
                raw = "https://" + raw
            return raw.rstrip("/")
        if self.railway_public_domain:
            return "https://" + self.railway_public_domain.strip().rstrip("/")
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

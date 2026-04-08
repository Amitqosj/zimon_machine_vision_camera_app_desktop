import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_title: str = "ZIMON API"
    secret_key: str = os.environ.get("ZIMON_JWT_SECRET", "change-me-in-production-use-long-random-string")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = os.environ.get(
        "ZIMON_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    recovery_secret_key: str = os.environ.get("ZIMON_RECOVERY_SECRET", "")
    recovery_allow_ips: str = os.environ.get("ZIMON_RECOVERY_ALLOW_IPS", "")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def recovery_ip_list(self) -> list[str]:
        return [o.strip() for o in self.recovery_allow_ips.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

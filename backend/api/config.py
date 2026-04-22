import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_root = Path(__file__).resolve().parents[2]
_backend = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv

    load_dotenv(_root / ".env")
    load_dotenv(_backend / ".env", override=True)
except ImportError:
    pass


def _default_api_host() -> str:
    if os.environ.get("ZIMON_API_HOST"):
        return os.environ["ZIMON_API_HOST"]
    # When PORT is set (e.g. some hosts), bind on all interfaces.
    if os.environ.get("PORT"):
        return "0.0.0.0"
    return "127.0.0.1"


def _default_api_port() -> int:
    raw = os.environ.get("PORT") or os.environ.get("ZIMON_API_PORT", "8010")
    return int(raw)


# Default local: 127.0.0.1:8010. With PORT set: 0.0.0.0:$PORT. Match `VITE_API_URL` on the frontend.
API_HOST = _default_api_host()
API_PORT = _default_api_port()


class Settings(BaseSettings):
    api_title: str = "ZIMON API"
    secret_key: str = os.environ.get("ZIMON_JWT_SECRET", "change-me-in-production-use-long-random-string")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = os.environ.get(
        "ZIMON_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5180",
    )
    recovery_secret_key: str = os.environ.get("ZIMON_RECOVERY_SECRET", "dscxvfbfrertdrer46534ewdsdwe3e454fef")
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

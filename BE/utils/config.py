"""환경변수 기반 설정 로더. API Key는 코드에 하드코딩하지 않는다."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# 레포 루트 .env
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # CLOVA Studio
    clova_api_key: str
    clova_apigw_api_key: str  # deprecated gateway key (legacy)
    clova_request_id: str
    clova_model: str
    clova_base_url: str
    clova_max_tokens: int
    clova_temperature: float

    # NAVER Maps (NCP Application)
    naver_map_client_id: str
    naver_map_client_secret: str
    naver_openapi_client_id: str
    naver_openapi_client_secret: str

    # TourAPI
    tour_api_key: str
    tour_api_base_url: str
    tour_api_mobile_app: str

    # DB
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_url: str  # optional full SQLAlchemy URL override
    sqlite_path: str

    # App
    default_region: str
    app_env: str
    http_timeout_sec: float
    tour_api_retries: int
    allow_stub_without_keys: bool


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        clova_api_key=os.getenv("CLOVA_API_KEY", "").strip(),
        clova_apigw_api_key=os.getenv("CLOVA_APIGW_API_KEY", "").strip(),
        clova_request_id=os.getenv("CLOVA_REQUEST_ID", "").strip(),
        clova_model=os.getenv("CLOVA_MODEL", "HCX-003").strip() or "HCX-003",
        clova_base_url=os.getenv(
            "CLOVA_BASE_URL",
            "https://clovastudio.stream.ntruss.com",
        ).rstrip("/"),
        clova_max_tokens=int(os.getenv("CLOVA_MAX_TOKENS", "1024")),
        clova_temperature=float(os.getenv("CLOVA_TEMPERATURE", "0.5")),
        naver_map_client_id=os.getenv("NAVER_MAP_CLIENT_ID", "").strip(),
        naver_map_client_secret=os.getenv("NAVER_MAP_CLIENT_SECRET", "").strip(),
        naver_openapi_client_id=os.getenv("NAVER_OPENAPI_CLIENT_ID", "").strip(),
        naver_openapi_client_secret=os.getenv(
            "NAVER_OPENAPI_CLIENT_SECRET", ""
        ).strip(),
        tour_api_key=os.getenv("TOUR_API_KEY", "").strip(),
        tour_api_base_url=os.getenv(
            "TOUR_API_BASE_URL",
            "https://apis.data.go.kr/B551011/KorService1",
        ).rstrip("/"),
        tour_api_mobile_app=os.getenv("TOUR_API_MOBILE_APP", "LocalMuseAI"),
        db_host=os.getenv("DB_HOST", "").strip(),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_name=os.getenv("DB_NAME", "localmuse"),
        db_user=os.getenv("DB_USER", "").strip(),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_url=os.getenv("DATABASE_URL", "").strip(),
        sqlite_path=os.getenv(
            "SQLITE_PATH",
            str(_ROOT / "data" / "localmuse.sqlite3"),
        ),
        default_region=os.getenv("DEFAULT_REGION", "서울"),
        app_env=os.getenv("APP_ENV", "development"),
        http_timeout_sec=float(os.getenv("HTTP_TIMEOUT_SEC", "10")),
        tour_api_retries=int(os.getenv("TOUR_API_RETRIES", "2")),
        allow_stub_without_keys=_bool_env("ALLOW_STUB_WITHOUT_KEYS", True),
    )


def clear_settings_cache() -> None:
    """테스트용: 설정 캐시 초기화."""
    get_settings.cache_clear()

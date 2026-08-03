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
    # CLOVA
    clova_api_key: str
    clova_apigw_api_key: str
    clova_request_id: str

    # NAVER Maps
    naver_map_client_id: str
    naver_map_client_secret: str
    naver_openapi_client_id: str
    naver_openapi_client_secret: str

    # TourAPI
    tour_api_key: str

    # DB
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # App
    default_region: str
    app_env: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        clova_api_key=os.getenv("CLOVA_API_KEY", ""),
        clova_apigw_api_key=os.getenv("CLOVA_APIGW_API_KEY", ""),
        clova_request_id=os.getenv("CLOVA_REQUEST_ID", ""),
        naver_map_client_id=os.getenv("NAVER_MAP_CLIENT_ID", ""),
        naver_map_client_secret=os.getenv("NAVER_MAP_CLIENT_SECRET", ""),
        naver_openapi_client_id=os.getenv("NAVER_OPENAPI_CLIENT_ID", ""),
        naver_openapi_client_secret=os.getenv("NAVER_OPENAPI_CLIENT_SECRET", ""),
        tour_api_key=os.getenv("TOUR_API_KEY", ""),
        db_host=os.getenv("DB_HOST", ""),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_name=os.getenv("DB_NAME", "localmuse"),
        db_user=os.getenv("DB_USER", ""),
        db_password=os.getenv("DB_PASSWORD", ""),
        default_region=os.getenv("DEFAULT_REGION", "서울"),
        app_env=os.getenv("APP_ENV", "development"),
    )

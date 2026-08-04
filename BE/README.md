# BE — Backend (Python Service Layer)

LocalMuse AI의 **비즈니스 로직 · 외부 API · DB** 레이어입니다.  
MVP에서는 별도 HTTP 서버 없이 Streamlit 프로세스에서 직접 import 합니다. (PRD: Backend = Streamlit)

## 역할 (PRD)

| 모듈 | 책임 |
|------|------|
| `services/tourapi.py` | 한국관광공사 TourAPI — 관광지·음식점·문화시설·Overview |
| `services/clova.py` | CLOVA Studio Chat Completions — 코스·추천 이유·지역 스토리 (JSON) |
| `services/maps.py` | NAVER Maps — Geocoding, Reverse Geocoding, Marker/Polyline payload |
| `services/course.py` | `generate_course()` 오케스트레이션 (AI Workflow) |
| `database/` | SQLite(로컬) / NCP Cloud DB(MySQL) — User·Course·Location·History |
| `models/` | 도메인 모델 + Pydantic 입출력 스키마 |
| `utils/` | config, regions, retry, json_extract |

## AI Workflow (고정)

```text
사용자 입력
  → TourAPI (장소 리스트, 재시도)
  → (선택) detailCommon overview 보강
  → Prompt 생성
  → CLOVA Studio (JSON)
  → 실패 시 Fallback 코스
  → Maps 좌표 보강 + route payload
  → DB 저장 (실패해도 결과는 반환)
  → Streamlit(FE) 출력
```

## 공개 API

```python
from BE.services.course import generate_course

result = generate_course(
    location="성수",
    purpose="3시간 혼자 감성 카페와 산책",
    time="3시간",
    transport="도보",
    save=True,
)
# result: title, story, places, route, route_note, source, course_id, message?
```

| Function | 설명 |
|----------|------|
| `generate_course(...)` | 전체 파이프라인 |
| `tourapi.get_location(...)` | TourAPI 후보 조회 |
| `clova.complete_course_json(...)` | AI 코스 JSON |
| `clova.generate_story(...)` | 지역 스토리 |
| `maps.geocode` / `reverse_geocode` | 좌표 ↔ 주소 |
| `maps.build_route_payload` | 지도용 markers/polyline |

## 환경변수

루트 `.env.example` 참고.

| Key | 용도 |
|-----|------|
| `TOUR_API_KEY` | 공공데이터포털 TourAPI 인증키 |
| `CLOVA_API_KEY` | CLOVA Studio API Key (`Bearer`) |
| `CLOVA_MODEL` | 기본 `HCX-003` |
| `NAVER_MAP_CLIENT_ID` / `SECRET` | NCP Maps Geocoding |
| `DB_HOST` 등 | NCP Cloud DB (없으면 SQLite) |
| `SQLITE_PATH` | 로컬 SQLite 경로 |
| `ALLOW_STUB_WITHOUT_KEYS` | 키 없을 때 스텁 허용 (기본 true) |

## CLI

```bash
python -m BE health                # 연동/DB 상태
python -m BE health --probe        # 실호출 스모크 (Tour/CLOVA/Maps)
python -m BE e2e                   # 성수 PRD 시나리오 E2E + verdict
python -m BE course 성수 "감성 카페"  # 코스 스모크
./scripts/e2e_seongsu.sh
```

## 로컬 실행 / 테스트

```bash
# 레포 루트
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 스모크 (키 없이 스텁)
python -c "from BE.services.course import generate_course; print(generate_course('성수','감성 카페','3시간','도보')['title'])"

# 단위 테스트
./scripts/run_tests.sh
# 또는
pytest -q
```

## 구조

```text
BE/
├── services/
│   ├── clova.py
│   ├── tourapi.py
│   ├── maps.py
│   └── course.py
├── database/
│   ├── connection.py
│   ├── repository.py
│   └── schema.sql
├── models/
│   ├── entities.py
│   └── schemas.py
└── utils/
    ├── config.py
    ├── regions.py
    ├── retry.py
    └── json_extract.py
```

## 규칙

- API Key는 환경변수만 사용 (`.env` / NCP 시크릿).
- Prompt 응답은 **JSON 고정**.
- 외부 연동은 이 레이어에만 둔다.
- Future 기능(여행일기, 취향 학습 등) 구현 금지.

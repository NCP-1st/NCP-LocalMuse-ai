# BE — Backend (Python Service Layer)

LocalMuse AI의 **비즈니스 로직 · 외부 API · DB** 레이어입니다.  
MVP에서는 별도 HTTP 서버 없이 Streamlit 프로세스에서 직접 import 합니다. (PRD: Backend = Streamlit)

## 역할 (PRD)

| 모듈 | 책임 |
|------|------|
| `services/tourapi.py` | 한국관광공사 TourAPI — 관광지·음식점·문화시설·Overview |
| `services/clova.py` | CLOVA Studio — 코스·추천 이유·지역 스토리 (JSON 출력) |
| `services/maps.py` | NAVER Maps — Geocoding, Marker, Polyline 보조 |
| `services/course.py` | `generate_course()` 오케스트레이션 (AI Workflow) |
| `database/` | NCP Cloud DB — User / Course / Location / History |
| `models/` | 도메인 모델 |
| `utils/` | 설정, 공통 유틸 |

## AI Workflow (고정)

```text
사용자 입력
  → TourAPI (장소 리스트)
  → Prompt 생성
  → CLOVA Studio
  → 추천 결과
  → Streamlit(FE) 출력
```

## 공개 함수 (Service API)

| Function | 설명 |
|----------|------|
| `generate_course(location, purpose, time, transport)` | → course, story, route |
| `get_location(...)` | TourAPI 장소 조회 |
| `generate_story(...)` | AI 추천 이유/스토리 |

## 구조

```text
BE/
├── __init__.py
├── services/
│   ├── clova.py
│   ├── tourapi.py
│   ├── maps.py
│   └── course.py
├── database/
├── models/
├── utils/
└── README.md
```

## 규칙

- API Key는 환경변수만 사용 (`.env` / NCP 시크릿).
- Prompt 응답은 **JSON 고정**.
- 외부 연동은 이 레이어에만 둔다. FE에서 직접 HTTP 호출하지 않는다.
- Future 기능(여행일기, 취향 학습 등) 구현 금지.

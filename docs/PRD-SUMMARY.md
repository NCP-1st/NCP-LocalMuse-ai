# LocalMuse AI — PRD Summary

> 본 문서는 **LocalMuse AI PRD Part 1·2**의 개발용 요약이다.  
> 기술 스택 변경, MVP 범위 변경, Future 기능 구현은 **금지**한다.  
> 상세 기획·기술 명세는 원본 PRD(Part 1, Part 2)를 따른다.

| Item | Content |
|------|---------|
| Project | LocalMuse AI |
| Version | 1.0 |
| Target | NIPA–NAVER Cloud Sovereign AI PBL |
| Platform | PC Web |
| Document sources | PRD Part 1 (Planning & Functional Spec), PRD Part 2 (Technical Architecture) |

---

## 1. One-liner

AI가 사용자의 **취향과 현재 상황**을 분석하여 **가장 적합한 로컬 여행 코스**를 추천하는 AI 기반 여행 큐레이션 플랫폼.

---

## 2. Problem → Solution

| Problem | Description |
|---------|-------------|
| 검색 중심 | “오늘 분위기 좋은 곳” 같은 의도는 검색하기 어렵다 |
| 동선 직접 계획 | 카페 → 전시 → 산책 → 식당을 사용자가 직접 연결해야 한다 |
| 추천 이유 부재 | 별점만 있고 “왜 지금 가야 하는지” 설명이 없다 |

**Solution:** 자연어 요청 + 현재 위치·목적·시간·이동수단 + 한국관광공사 TourAPI + NAVER Maps를 종합 분석하여 **여행 코스 · 이동 동선 · 추천 이유 · 지역 스토리**를 생성한다.

---

## 3. MVP Goal & Success Criteria

| Item | Content |
|------|---------|
| MVP Goal | 자연어 한 줄 입력 → 장소 **3~5개** 추천 + 네이버 지도 **최적 동선** 표시 |
| Success Criteria | **3분 이내** 여행 코스 생성 |
| Response target | **10초 이내** (NFR 목표) |

---

## 4. Scope

### Included (MVP)

- AI 여행 코스 생성
- NAVER Maps 기반 동선
- CLOVA Studio 추천 이유
- 지역 스토리 생성
- 한국관광공사 관광 데이터(TourAPI) 활용

### Excluded (Future — 구현 금지)

- AI 여행일기
- 사진 저장
- AI 취향 학습
- 지역 행사 추천
- 회원 간 공유
- 실시간 채팅

---

## 5. Target Users (Personas)

1. **대학생 (22)** — 혼자 카페 탐방, 사진, 반나절 여행  
2. **직장인 (30)** — 주말 데이트, 짧은 일정, 자동차 이동  
3. **관광객** — 처음 방문한 지역, 명소 쉽게 파악  

---

## 6. User Journey / Flow

```
서비스 접속 → 현재 위치 허용 → 자연어(여행 목적) 입력
  → AI 여행 코스 생성 → 네이버 지도 출력 → 장소 상세/설명 확인 → 여행 시작
```

**Demo input example**

> 성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘.

---

## 7. MVP Features

### Feature 1 — AI 여행 코스 생성

| | |
|--|--|
| **Input** | 현재 위치, 목적, 시간, 이동수단 |
| **Output** | 장소 3~5개, 방문 순서, 예상 이동시간, 예상 소요시간 |
| **Flow** | 사용자 입력 → CLOVA Studio → TourAPI 장소 검색 → 추천 장소 선정 → 최종 코스 생성 |

### Feature 2 — 네이버 지도 기반 이동 동선

- Marker, 장소 카드, 이동 동선(Polyline), 현재 위치 표시  
- 예: 현재 위치 → 카페 → 전시 → 산책 → 식당  

### Feature 3 — AI 추천 이유 및 지역 스토리

사용자가 **왜 추천되었는지** 이해할 수 있어야 한다.

---

## 8. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | 자연어 입력 | High |
| FR-02 | AI 코스 생성 | High |
| FR-03 | 지도 출력 | High |
| FR-04 | 장소 상세 보기 | High |
| FR-05 | 지역 스토리 생성 | High |

---

## 9. Non-Functional Requirements

- PC Web 환경 지원
- 응답 시간 10초 이내 (목표)
- Streamlit 기반 단일 애플리케이션
- 직관적인 UI
- MVP 중심 구현
- **모바일 최적화는 범위 제외**

---

## 10. Tech Stack (고정)

| Category | Technology |
|----------|------------|
| Frontend | Streamlit |
| Backend | Streamlit (MVP) |
| Language | Python 3.11 |
| AI | NAVER CLOVA Studio |
| Map | NAVER Maps API |
| Tourism Data | 한국관광공사 TourAPI |
| Cloud | NAVER Cloud Platform |
| Database | NCP Cloud DB |
| Network | VPC, ACG, NCP Server |

**허용 스택만 사용.** 그 외 프레임워크/클라우드/LLM 교체 금지.

---

## 11. System Architecture

```
User
  │
Streamlit UI  (로그인 · 검색 · 지도 · 결과)
  │
Business Logic
  ├── NAVER Maps API     (Marker, Polyline, 현재 위치, Geo/Reverse Geo)
  ├── CLOVA Studio       (코스 · 추천 이유 · 지역 스토리)
  ├── 한국관광공사 TourAPI (관광지 · 음식점 · 문화시설 · Overview)
  └── NCP Cloud DB       (User · Course · Location · History)
```

### NCP

- **VPC** — 프로젝트 전용 네트워크  
- **ACG** — HTTP / HTTPS / SSH 허용  
- **Server** — Streamlit · Python 실행  
- **Cloud DB** — User, Course, Location, History  

---

## 12. AI Workflow (고정)

```
사용자 입력
  → TourAPI (장소 리스트)
  → Prompt 생성
  → CLOVA Studio
  → 추천 결과
  → Streamlit 출력
```

**Prompt 규칙:** JSON 출력 고정.  
예시 역할: 여행 큐레이터 — 현재 위치와 관광 데이터를 참고해 3~5개 장소를 추천하고 JSON으로 출력.

---

## 13. Data Model

| Entity | Fields |
|--------|--------|
| **User** | id, nickname, created_at |
| **Location** | id, name, address, latitude, longitude, category |
| **Course** | id, user_id, title |
| **CourseLocation** | course_id, location_id, sequence |

---

## 14. API Surface (Service Layer)

| Function | Role |
|----------|------|
| `generate_course(location, purpose, time, transport)` | → course, story, route |
| `get_location()` | TourAPI 장소 조회 |
| `generate_story()` | AI 추천 이유 생성 |

---

## 15. Folder Structure

레포는 **FE / BE** 로 분리한다. (MVP: Streamlit이 BE를 직접 import)

```text
FE/                     # Streamlit UI
├── app.py
├── pages/
├── components/
└── assets/

BE/                     # Service layer · DB · models
├── services/
│   ├── clova.py
│   ├── tourapi.py
│   ├── maps.py
│   └── course.py       # generate_course 오케스트레이션
├── database/
├── models/
└── utils/
```

---

## 16. Conventions

| Area | Rule |
|------|------|
| Python | PEP 8 |
| Streamlit | 페이지 단위 구성 |
| Prompt | JSON 출력 고정 |
| API | Service Layer 분리 |
| Secrets | API Key → 환경변수 |
| DB | 외부 접근 차단 |
| Transport | HTTPS |

---

## 17. Error Handling

| Failure | Fallback |
|---------|----------|
| 위치 권한 거부 | 기본 지역 **서울** |
| TourAPI 실패 | 재시도 → 안내 메시지 |
| CLOVA 실패 | Fallback Prompt |
| 지도 실패 | 텍스트 추천만 제공 |

---

## 18. Deployment

```
Developer → Git → NCP Server → Python → Streamlit → Browser
```

---

## 19. Context Switching Rules (절대)

새로운 기여자·AI 어시스턴트는 **이 문서와 PRD**를 기준으로 개발한다.

1. **기술 스택 변경 금지**
2. **MVP 범위 변경 금지**
3. **Future 기능 구현 금지**

---

## 20. Demo Scenario (Acceptance Sketch)

1. 서비스 실행  
2. 현재 위치 허용  
3. 입력: `"성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘."`  
4. TourAPI로 후보 장소 구성  
5. CLOVA Studio가 코스·추천 이유 생성  
6. 네이버 지도에 경로·추천 장소 표시  
7. 장소별 설명 확인 후 여행 시작  

# LocalMuse AI

**AI가 사용자의 취향과 현재 상황을 분석하여 가장 적합한 로컬 여행 코스를 추천하는 AI 기반 여행 큐레이션 플랫폼**

| | |
|--|--|
| **Organization Repo** | [NCP-1st/NCP-LocalMuse-ai](https://github.com/NCP-1st/NCP-LocalMuse-ai) |
| **Version** | 1.0 (MVP) |
| **Platform** | PC Web |
| **Target Program** | NIPA–NAVER Cloud Sovereign AI PBL |
| **Cloud** | NAVER Cloud Platform (NCP) |

> 기획·기능 명세는 **PRD Part 1**, 기술 아키텍처·개발 규칙은 **PRD Part 2**를 따른다.  
> 개발용 압축 요약: [`docs/PRD-SUMMARY.md`](./docs/PRD-SUMMARY.md)

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [문제 정의](#2-문제-정의)
3. [솔루션](#3-솔루션)
4. [목표 & 성공 기준](#4-목표--성공-기준)
5. [범위 (In / Out)](#5-범위-in--out)
6. [타깃 사용자](#6-타깃-사용자)
7. [사용자 여정 & 플로우](#7-사용자-여정--플로우)
8. [MVP 기능 명세](#8-mvp-기능-명세)
9. [기능 / 비기능 요구사항](#9-기능--비기능-요구사항)
10. [기술 스택](#10-기술-스택)
11. [시스템 아키텍처](#11-시스템-아키텍처)
12. [NCP 인프라](#12-ncp-인프라)
13. [외부 API 활용](#13-외부-api-활용)
14. [AI 워크플로우](#14-ai-워크플로우)
15. [데이터 모델](#15-데이터-모델)
16. [서비스 API 명세](#16-서비스-api-명세)
17. [프로젝트 구조](#17-프로젝트-구조)
18. [개발 컨벤션](#18-개발-컨벤션)
19. [에러 처리](#19-에러-처리)
20. [보안](#20-보안)
21. [배포](#21-배포)
22. [데모 시나리오](#22-데모-시나리오)
23. [협업 가이드](#23-협업-가이드)
24. [Future (구현 금지)](#24-future-구현-금지)
25. [Context Switching 규칙](#25-context-switching-규칙)

---

## 1. 프로젝트 개요

### 1.1 프로젝트명

**LocalMuse AI**

### 1.2 한 줄 정의

AI가 사용자의 **취향**과 **현재 상황**을 분석하여, 오늘에 가장 적합한 **로컬 여행 코스**를 생성하는 서비스.

### 1.3 배경

기존 지도 서비스는 다음 기능은 뛰어나다.

- 장소 검색
- 리뷰 확인
- 길찾기

그러나 사용자는 여전히 스스로 결정해야 한다.

> “오늘 어디를 가야 하지?”

특히 **혼자 여행**, **데이트**, **짧은 반나절 여행**에서는 장소 하나가 아니라 **하나의 코스**가 필요하다.

LocalMuse AI는 AI가 다음을 분석한다.

- 사용자의 목적
- 현재 위치
- 이용 가능 시간
- 이동수단

그리고 **“오늘 가장 적합한 여행 코스”**를 생성한다.

---

## 2. 문제 정의

| # | Problem | 설명 |
|---|---------|------|
| 1 | **검색 중심 서비스** | 사용자는 “성수 카페”, “을지로 맛집”처럼 검색어를 알아야 한다. “오늘 분위기 좋은 곳” 같은 의도형 요청은 검색하기 어렵다. |
| 2 | **동선을 직접 계획** | 카페 → 전시 → 산책 → 식당을 사용자가 직접 연결해야 한다. |
| 3 | **추천 이유 부재** | “카페 A ★★★★★”처럼 점수만 있고, **왜 지금 가야 하는지** 설명하지 않는다. |

---

## 3. 솔루션

LocalMuse AI는 사용자의 **자연어 요청**을 이해하고 다음 정보를 종합 분석한다.

- 현재 위치
- 여행 목적
- 이용 가능 시간
- 이동수단
- 한국관광공사 관광 데이터 (TourAPI)
- NAVER Maps 위치 정보

**최종 산출물**

| 산출물 | 설명 |
|--------|------|
| 여행 코스 | 방문할 장소 3~5개와 순서 |
| 이동 동선 | 지도 위 Marker + Polyline |
| 추천 이유 | 장소별 “왜 지금 여기인지” |
| 지역 스토리 | 동네·골목·공간의 맥락 설명 |

---

## 4. 목표 & 성공 기준

### MVP Goal

사용자가 **자연어 한 줄**만 입력하면,

1. AI가 **3~5개** 장소를 추천하고  
2. 네이버 지도에 **최적 동선**을 표시한다.

### Success Criteria

| 지표 | 목표 |
|------|------|
| 코스 생성 완료 | **3분 이내** |
| 시스템 응답 (NFR) | **10초 이내** (목표) |

---

## 5. 범위 (In / Out)

### Included (MVP에서 구현)

- AI 여행 코스 생성
- NAVER Maps 기반 이동 동선
- CLOVA Studio 기반 추천 이유
- 지역 스토리 생성
- 한국관광공사 TourAPI 관광 데이터 활용
- (기술 명세) 사용자·검색기록·추천 결과 저장 (NCP Cloud DB)

### Excluded (MVP 범위 밖 — Future)

다음 기능은 **구현하지 않는다.**

- AI 여행일기
- 사진 저장
- AI 취향 학습
- 지역 행사 추천
- 회원 간 공유 기능
- 실시간 채팅
- 모바일 최적화 (NFR: PC Web 전용)

---

## 6. 타깃 사용자

| Persona | 특징 |
|---------|------|
| **대학생 (22)** | 혼자 카페 탐방, 사진 촬영 선호, 반나절 여행 |
| **직장인 (30)** | 주말 데이트, 짧은 일정, 자동차 이동 |
| **관광객** | 처음 방문한 지역, 지역 명소를 쉽게 알고 싶음 |

---

## 7. 사용자 여정 & 플로우

### User Journey (예시)

```text
오늘 서울 성수에서 3시간 동안 혼자 여행하고 싶다
        ↓
   서비스 접속
        ↓
  현재 위치 허용
        ↓
    자연어 입력
        ↓
  AI 여행 코스 생성
        ↓
   네이버 지도 출력
        ↓
   장소 설명 확인
        ↓
     여행 시작
```

### User Flow

```text
Start
  → 현재 위치 허용
  → 여행 목적 입력
  → AI 요청
  → 여행 코스 생성
  → 지도 출력
  → 장소 상세 확인
  → 종료
```

---

## 8. MVP 기능 명세

### Feature 1 — AI 여행 코스 생성

| 항목 | 내용 |
|------|------|
| **목적** | 자연어 요청을 분석하여 여행 코스 생성 |
| **입력** | 현재 위치, 목적, 시간, 이동수단 |
| **입력 예시** | `"성수에서 3시간 동안 혼자 감성 카페 위주로 추천해줘."` |
| **출력** | 장소 3~5개, 방문 순서, 예상 이동시간, 예상 소요시간 |

**Feature Flow**

```text
사용자 입력
  → CLOVA Studio
  → TourAPI 장소 검색
  → 추천 장소 선정
  → 최종 코스 생성
```

> 구현 시 기술 명세(Part 2)의 **권장 AI Workflow**는  
> `입력 → TourAPI → Prompt → CLOVA → 결과 → Streamlit` 순서를 기준으로 한다.  
> (후보 장소를 먼저 모은 뒤 LLM이 코스를 구성)

### Feature 2 — 네이버 지도 기반 이동 동선

| 항목 | 내용 |
|------|------|
| **목적** | 추천 장소를 직관적으로 확인 |
| **기능** | Marker 표시, 장소 카드, 이동 동선 표시, 현재 위치 표시 |
| **출력 예** | 현재 위치 → 카페 → 전시 → 산책 → 식당 |

### Feature 3 — AI 추천 이유 및 지역 스토리

사용자는 **왜 추천되었는지** 이해할 수 있어야 한다.

**예시**

> “이 카페는 성수의 오래된 공장 건물을 리모델링한 공간으로, 조용한 분위기에서 휴식을 취하기 좋습니다.”

> “이 골목은 오래전부터 수제화 거리로 유명하며 현재는 다양한 편집숍과 카페가 함께 형성되어 있습니다.”

---

## 9. 기능 / 비기능 요구사항

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | 자연어 입력 | High |
| FR-02 | AI 코스 생성 | High |
| FR-03 | 지도 출력 | High |
| FR-04 | 장소 상세 보기 | High |
| FR-05 | 지역 스토리 생성 | High |

### Non-Functional Requirements

- PC Web 환경 지원
- 응답 시간 **10초 이내** (목표)
- **Streamlit** 기반 단일 애플리케이션
- 직관적인 UI
- MVP 중심 구현
- **모바일 최적화는 범위 제외**

---

## 10. 기술 스택

PRD Part 2 기준 — **아래 스택만 사용한다. 변경 금지.**

| Category | Technology |
|----------|------------|
| Frontend | Streamlit |
| Backend | Streamlit (MVP) |
| Language | **Python 3.11** |
| AI | NAVER **CLOVA Studio** |
| Map | **NAVER Maps API** |
| Tourism Data | 한국관광공사 **TourAPI** |
| Database | **NCP Cloud DB** |
| Cloud | **NAVER Cloud Platform** |
| Network | VPC, ACG, NCP Server |

---

## 11. 시스템 아키텍처

```text
                 User
                   │
             Streamlit UI
        (로그인 · 검색 · 지도 · 결과)
                   │
            Business Logic
                   │
     ┌─────────────┼─────────────┬──────────────┐
     │             │             │              │
NAVER Maps   CLOVA Studio   TourAPI      NCP Cloud DB
  Marker      코스 생성      관광지         User
  Polyline    추천 이유      음식점         Course
  현재 위치   지역 스토리    문화시설       Location
  GeoCoding                  Overview       History
```

### 컴포넌트 역할

| Component | Role |
|-----------|------|
| **Streamlit** | UI — 로그인, 검색, 지도 출력, 결과 출력 |
| **CLOVA Studio** | AI — 여행 코스, 추천 이유, 지역 스토리 생성 |
| **NAVER Maps** | 지도 — Marker, Polyline, 현재 위치 |
| **TourAPI** | 장소 데이터 — 관광지, 음식점, 문화시설, 여행지 Overview |
| **Cloud DB** | 저장 — 사용자, 검색기록, 추천 결과 |

---

## 12. NCP 인프라

```text
Internet
    ↓
   VPC          ← 프로젝트 전용 네트워크
    ↓
  Server        ← Streamlit / Python 실행
    ↓
 Cloud DB       ← User · Course · Location · History
```

### ACG (보안 그룹)

허용 포트/프로토콜:

- HTTP
- HTTPS
- SSH

---

## 13. 외부 API 활용

### 13.1 NAVER Maps API

| 기능 | 설명 |
|------|------|
| Geocoding | 주소 → 좌표 |
| Reverse Geocoding | 좌표 → 주소 |
| Marker | 추천 장소 표시 |
| Polyline | 이동 경로 표시 |
| 현재 위치 | GPS 기반 |

### 13.2 한국관광공사 TourAPI

| 구분 | 용도 |
|------|------|
| Tourist Spot | 관광지 |
| Restaurant | 음식점 |
| Culture | 문화시설 |
| Overview | 여행지 정보 |

**사용 이유:** 네이버 지도는 지도 기능은 뛰어나지만 관광 정보가 충분하지 않다. TourAPI로 **공공 관광 데이터**를 보완한다.

### 13.3 CLOVA Studio

| | |
|--|--|
| **역할** | AI 추천 |
| **입력** | 현재 위치, 시간, 여행 목적, 이동수단 (+ TourAPI 후보) |
| **출력** | 추천 코스, 추천 이유, 지역 스토리 |

**예시 Prompt (개념)**

```text
당신은 여행 큐레이터입니다.
사용자의 현재 위치와 관광 데이터를 참고하여
3~5개의 장소를 추천하세요.
JSON으로 출력하세요.
```

> Prompt는 **JSON 출력 고정** (개발 컨벤션).

---

## 14. AI 워크플로우

```text
사용자 입력
    ↓
TourAPI          ← 장소 리스트 수집
    ↓
Prompt 생성
    ↓
CLOVA Studio     ← 코스 · 이유 · 스토리
    ↓
추천 결과
    ↓
Streamlit 출력   ← 카드 + 지도
```

---

## 15. 데이터 모델

```text
User
  id
  nickname
  created_at

Location
  id
  name
  address
  latitude
  longitude
  category

Course
  id
  user_id
  title

CourseLocation
  course_id
  location_id
  sequence
```

관계 요약: **User 1 — N Course**, **Course N — M Location** (중간 테이블 `CourseLocation` + 방문 순서 `sequence`).

---

## 16. 서비스 API 명세

Service Layer에 분리하여 구현한다.

| Function | Input | Output / Role |
|----------|--------|----------------|
| `generate_course()` | `location`, `purpose`, `time`, `transport` | `course`, `story`, `route` |
| `get_location()` | (지역·카테고리 등) | TourAPI 장소 조회 |
| `generate_story()` | (장소·맥락) | AI 추천 이유·스토리 생성 |

---

## 17. 프로젝트 구조

협업 기준: 레포를 **`FE/`(프론트) · `BE/`(백엔드 서비스 레이어)** 로 분리한다.  
MVP에서는 별도 API 서버 없이 Streamlit이 `BE` 모듈을 직접 import 한다. (PRD: Backend = Streamlit)

```text
.
├── FE/                         # Frontend (Streamlit UI)
│   ├── app.py                  # 진입점 · 메인 플로우
│   ├── pages/                  # multipage 확장
│   ├── components/             # 지도 · 코스 카드 등 UI 조각
│   ├── assets/
│   └── README.md
├── BE/                         # Backend (Service Layer · DB · Models)
│   ├── services/
│   │   ├── clova.py            # CLOVA Studio
│   │   ├── tourapi.py          # 한국관광공사 TourAPI
│   │   ├── maps.py             # NAVER Maps
│   │   └── course.py           # generate_course() 오케스트레이션
│   ├── database/               # NCP Cloud DB
│   ├── models/                 # User · Location · Course · CourseLocation
│   ├── utils/                  # config 등
│   └── README.md
├── docs/
│   └── PRD-SUMMARY.md
├── requirements.txt
├── .env.example
└── README.md
```

### 로컬 실행

```bash
pip install -r requirements.txt
cp .env.example .env   # API 키 입력
streamlit run FE/app.py
```

---

## 18. 개발 컨벤션

| 영역 | 규칙 |
|------|------|
| Python | **PEP 8** |
| Streamlit | **페이지 단위** 구성 |
| Prompt | **JSON 출력 고정** |
| API 연동 | **Service Layer 분리** (`services/`) |
| 시크릿 | API Key는 **환경변수** (코드·Git 커밋 금지) |

---

## 19. 에러 처리

| 상황 | 대응 |
|------|------|
| 위치 권한 거부 | 기본 지역 **서울** |
| TourAPI 실패 | **재시도** → 안내 메시지 |
| CLOVA 실패 | **Fallback Prompt** |
| 지도 실패 | **텍스트 추천**만 제공 |

---

## 20. 보안

- API Key → **환경변수** 저장
- Cloud DB → **외부 접근 차단**
- 통신 → **HTTPS** 사용
- ACG로 필요한 포트만 개방 (HTTP / HTTPS / SSH)

---

## 21. 배포

```text
Developer
    ↓
   Git          (본 조직 레포 브랜치 협업)
    ↓
 NCP Server
    ↓
  Python 3.11
    ↓
 Streamlit
    ↓
  Browser (PC Web)
```

---

## 22. 데모 시나리오

1. 사용자가 서비스를 실행한다.  
2. 현재 위치를 허용한다.  
3. 다음을 입력한다.  
   > `"성수에서 3시간 동안 혼자 감성 카페와 산책 코스를 추천해줘."`  
4. AI가 한국관광공사 **TourAPI** 데이터를 참고하여 후보 장소를 구성한다.  
5. **CLOVA Studio**가 사용자 요청에 맞는 코스와 추천 이유를 생성한다.  
6. **네이버 지도**에 이동 경로와 추천 장소가 표시된다.  
7. 사용자는 장소별 설명을 확인하며 여행을 시작한다.  

---

## 23. 협업 가이드

조직 공개 레포 **NCP-1st/NCP-LocalMuse-ai**에서 **브랜치 기반**으로 협업한다.

### 브랜치 전략 (권장)

| Branch | 용도 |
|--------|------|
| `main` | 배포·데모 기준 (직접 커밋 최소화) |
| `feature/<topic>` | 기능 개발 |
| `fix/<topic>` | 버그 수정 |
| `chore/<topic>` | 설정·문서·인프라 |
| `docs/<topic>` | 문서 전용 |

### 작업 흐름

```text
1. main 최신화
2. feature 브랜치 생성
3. 커밋 · push
4. Pull Request → main
5. 검토자(@jinhgit) 승인 후 머지
```

### PR · 머지 정책

| 항목 | 설정 |
|------|------|
| **자동 머지 (Auto-merge)** | 비활성 — PR이 올라와도 자동으로 머지되지 않음 |
| **main 직접 push** | 브랜치 보호로 제한 (PR 경유) |
| **필수 승인** | 최소 **1명** Approve |
| **Code Owner 리뷰** | 필수 — [`.github/CODEOWNERS`](./.github/CODEOWNERS) 기준 **@jinhgit** |
| **stale review** | 새 push 시 기존 승인 무효화 (`dismiss_stale_reviews`) |

팀원이 PR을 올리면 CODEOWNERS에 따라 **검토자 `@jinhgit`에게 리뷰 요청**이 갑니다.  
승인 전에는 `main`에 머지할 수 없습니다. (관리자 계정은 GitHub 설정상 예외 가능)

### 로컬 클론

```bash
git clone https://github.com/NCP-1st/NCP-LocalMuse-ai.git
cd NCP-LocalMuse-ai
```

### 문서

| 문서 | 설명 |
|------|------|
| [docs/PRD-SUMMARY.md](./docs/PRD-SUMMARY.md) | PRD Part 1·2 개발용 요약 (AI/기여자 공통 컨텍스트) |
| 원본 PRD Part 1 | Project Planning & Functional Specification |
| 원본 PRD Part 2 | Technical Architecture & Development Specification |

---

## 24. Future (구현 금지)

MVP 완료 이후 검토 가능. **현재 스프린트에서는 구현하지 않는다.**

- AI 여행일기  
- 사진 저장  
- AI 취향 학습  
- 지역 행사 추천  

---

## 25. Context Switching 규칙

새로운 기여자 및 AI(Code Assistant)는 **이 README와 [`docs/PRD-SUMMARY.md`](./docs/PRD-SUMMARY.md)** 를 기준으로 개발한다.

| 규칙 | 설명 |
|------|------|
| **기술 스택 변경 금지** | Streamlit / Python 3.11 / CLOVA / Maps / TourAPI / NCP 고정 |
| **MVP 범위 변경 금지** | Included만 구현 |
| **Future 기능 구현 금지** | 여행일기·사진·취향학습·행사 추천 등 보류 |

---

## License / 프로그램

NIPA–NAVER Cloud Sovereign AI PBL 학습·데모 목적 프로젝트.

---

*Document aligned with LocalMuse AI PRD Part 1 & Part 2 (Version 1.0).*

# FE — Frontend (Streamlit)

LocalMuse AI의 **PC Web UI** 레이어입니다.

## 역할 (PRD)

| 화면/모듈 | FR | 설명 |
|-----------|----|------|
| 자연어 입력 폼 | FR-01 | 위치·목적·시간·이동수단 |
| 코스 결과 | FR-02 | AI 코스 제목·순서·시간 |
| 지도 동선 | FR-03 | Marker / Polyline (`st.map` + NAVER Maps skeleton) |
| 장소 카드 | FR-04 | 상세·추천 이유 |
| 지역 스토리 | FR-05 | 코스 맥락 설명 |
| 저장 코스 | — | DB 조회 |
| 시스템 상태 | — | 키/DB 헬스 |

## 구조

```text
FE/
├── app.py                 # 홈 · 코스 추천 메인 플로우
├── pages/
│   ├── 2_저장_코스.py
│   └── 3_시스템_상태.py
├── components/
│   ├── hero.py
│   ├── input_form.py
│   ├── place_card.py
│   ├── course_panel.py
│   ├── map_view.py
│   └── styles.py
├── lib/
│   ├── bootstrap.py       # repo root → sys.path
│   └── session.py         # session_state
├── assets/
│   └── styles.css
└── README.md
```

## 실행

레포 루트에서:

```bash
pip install -r requirements.txt
cp .env.example .env   # 키 입력 (없어도 스텁 동작)

# 방법 1
./scripts/run_app.sh

# 방법 2
export PYTHONPATH=.
streamlit run FE/app.py
```

> `FE/` 가 패키지로 import 되므로 **반드시 레포 루트**에서 실행하세요.

## 규칙

- UI만 담당. 외부 API·DB 는 `BE.services` / `BE.database` 경유.
- API Key 하드코딩 금지.
- 모바일 최적화는 MVP 범위 밖 (PC Web).

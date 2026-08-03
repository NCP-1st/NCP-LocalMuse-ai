# FE — Frontend (Streamlit)

LocalMuse AI의 **PC Web UI** 레이어입니다.

## 역할 (PRD)

- 현재 위치 허용 / 기본 지역(서울) 폴백
- 자연어 여행 목적 입력
- AI 코스 결과 카드 출력
- NAVER Maps 기반 Marker · Polyline · 현재 위치 표시
- 장소 상세 · 추천 이유 · 지역 스토리 확인

## 실행

레포 루트에서:

```bash
# 의존성 (최초 1회)
pip install -r requirements.txt

# 환경변수
cp .env.example .env   # 키 입력

# Streamlit 실행
streamlit run FE/app.py
```

## 구조

```text
FE/
├── app.py              # 진입점 · 메인 플로우
├── pages/              # Streamlit multipage (확장용)
├── components/         # UI 조각 (지도, 코스 카드 등)
├── assets/             # 정적 리소스
└── README.md
```

## 규칙

- UI/인터랙션만 담당한다. 외부 API·DB 호출은 `BE/services` 를 통해서만 수행한다.
- 모바일 최적화는 MVP 범위 밖 (PC Web).
- API Key를 프론트 코드에 하드코딩하지 않는다.

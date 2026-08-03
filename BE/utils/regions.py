"""
한국관광공사 TourAPI 지역 코드 매핑.

areaCode (광역):
  1 서울, 2 인천, 3 대전, 4 대구, 5 광주, 6 부산, 7 울산, 8 세종,
  31 경기, 32 강원, 33 충북, 34 충남, 35 경북, 36 경남, 37 전북, 38 전남, 39 제주
"""

from __future__ import annotations

import re

# 긴 키워드를 먼저 매칭하기 위해 길이 순 정렬 전제
_AREA_KEYWORDS: list[tuple[str, int]] = [
    ("서울특별시", 1),
    ("부산광역시", 6),
    ("대구광역시", 4),
    ("인천광역시", 2),
    ("광주광역시", 5),
    ("대전광역시", 3),
    ("울산광역시", 7),
    ("세종특별자치시", 8),
    ("제주특별자치도", 39),
    ("경기도", 31),
    ("강원특별자치도", 32),
    ("강원도", 32),
    ("충청북도", 33),
    ("충북", 33),
    ("충청남도", 34),
    ("충남", 34),
    ("전북특별자치도", 37),
    ("전라북도", 37),
    ("전북", 37),
    ("전라남도", 38),
    ("전남", 38),
    ("경상북도", 35),
    ("경북", 35),
    ("경상남도", 36),
    ("경남", 36),
    ("제주도", 39),
    ("제주", 39),
    ("서울", 1),
    ("부산", 6),
    ("대구", 4),
    ("인천", 2),
    ("광주", 5),
    ("대전", 3),
    ("울산", 7),
    ("세종", 8),
    ("경기", 31),
    ("강원", 32),
]

# 서울 주요 권역 → 키워드 검색 보조 (areaCode 는 서울=1)
SEOUL_DISTRICTS = {
    "성수",
    "성동",
    "홍대",
    "연남",
    "합정",
    "이태원",
    "한남",
    "강남",
    "역삼",
    "삼성",
    "잠실",
    "송파",
    "종로",
    "광화문",
    "명동",
    "을지로",
    "동대문",
    "연신내",
    "망원",
    "상수",
    "북촌",
    "서촌",
    "익선",
    "성북",
    "혜화",
    "건대",
    "왕십리",
    "여의도",
    "마포",
    "용산",
    "영등포",
}


def resolve_area_code(region: str) -> int | None:
    """지역 문자열에서 TourAPI areaCode 를 추정. 모르면 None."""
    text = (region or "").strip()
    if not text:
        return 1  # PRD 기본: 서울

    for key, code in _AREA_KEYWORDS:
        if key in text:
            return code

    # 성수 등 서울 동네만 적힌 경우
    for d in SEOUL_DISTRICTS:
        if d in text:
            return 1

    return None


def extract_search_keyword(region: str, purpose: str | None = None) -> str:
    """
    TourAPI searchKeyword 용 짧은 검색어.
    자연어 목적 전체를 넣으면 매칭이 약해지므로 핵심 토큰을 뽑는다.
    """
    region = (region or "").strip()
    purpose = (purpose or "").strip()

    # 지역명에서 짧은 핵심 (성수, 홍대 등)
    for d in sorted(SEOUL_DISTRICTS, key=len, reverse=True):
        if d in region or d in purpose:
            return d

    for key, _ in _AREA_KEYWORDS:
        if key in region:
            # "서울특별시" → 너무 넓으면 purpose 토큰 사용
            break

    # purpose 에서 불용어 제거 후 2~3글자 이상 토큰
    stop = {
        "동안",
        "혼자",
        "같이",
        "추천",
        "해줘",
        "해주세요",
        "코스",
        "여행",
        "위주",
        "으로",
        "에서",
        "시간",
        "정도",
        "오늘",
        "내일",
        "주말",
        "데이트",
        "싶은",
        "싶어",
        "하고",
        "하는",
        "있는",
        "같은",
    }
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", purpose)
    useful = [t for t in tokens if len(t) >= 2 and t not in stop]
    if useful:
        # 감성, 카페, 산책 등 앞쪽 핵심
        return " ".join(useful[:3])

    if region:
        return region.split()[0]
    return "관광"


def content_type_name(content_type_id: str | int | None) -> str:
    mapping = {
        "12": "관광지",
        "14": "문화시설",
        "15": "행사",
        "25": "여행코스",
        "28": "레포츠",
        "32": "숙박",
        "38": "쇼핑",
        "39": "음식점",
    }
    if content_type_id is None:
        return "기타"
    return mapping.get(str(content_type_id), "기타")

# Icon Convention — Linear SVG Only

## 규칙 (필수)

1. **이모지(emoji) 사용 금지** — UI, `page_icon`, toast, 버튼 라벨, 문서 장식 포함  
2. 시각 장식·상태는 **선형 SVG** 만 사용 (`FE/components/icons.py`)  
3. 스타일: stroke 기반, fill 없음, `currentColor`, round cap/join  
4. 새 아이콘이 필요하면 `_PATHS` 에 path 를 추가하고 `icon("name")` 으로 사용  

## 사용법

```python
from FE.components.icons import icon, icon_text, icon_heading, status_icon

# 인라인
st.markdown(f"{icon('compass')} LocalMuse", unsafe_allow_html=True)

# 아이콘 + 텍스트
st.markdown(icon_text("map-pin", address), unsafe_allow_html=True)

# 제목
st.markdown(icon_heading("save", "저장 코스", level=1), unsafe_allow_html=True)

# 상태
st.markdown(status_icon(True) + " TourAPI", unsafe_allow_html=True)
```

## Streamlit 제약

| API | 처리 |
|-----|------|
| `st.set_page_config(page_icon=...)` | 이모지 대신 텍스트/`None` (브라우저 탭) |
| `st.toast(..., icon=...)` | `icon` 인자 생략 (이모지 전용 슬롯) |

## 등록된 이름 (일부)

`compass`, `map`, `map-pin`, `check`, `check-circle`, `x`, `x-circle`, `alert`,  
`circle`, `zap`, `save`, `clock`, `walk`, `message`, `activity`, `database`,  
`route`, `chevron-right`, `list`, `spark`, `refresh`, `play`

## 금지 예

```python
# BAD
st.title("🧭 LocalMuse")
st.button("⚡ 데모")
page_icon="💾"
```

```python
# GOOD
st.markdown(icon_heading("compass", "LocalMuse", level=1), unsafe_allow_html=True)
st.button("데모 실행")  # 라벨은 텍스트, 옆 제목에만 SVG
```

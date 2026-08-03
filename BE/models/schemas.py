"""Pydantic 스키마 — Service API 입출력 계약."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CourseRequest(BaseModel):
    location: str = Field(..., description="현재 위치 / 지역")
    purpose: str = Field(..., description="여행 목적 자연어")
    time: str = Field(..., description="이용 가능 시간")
    transport: str = Field(..., description="이동수단")
    user_id: Optional[int] = None
    save: bool = Field(default=True, description="DB 저장 여부")
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class PlaceItem(BaseModel):
    name: str
    category: str = "-"
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    duration: str = ""
    travel_time: str = ""
    reason: str = ""
    content_id: Optional[str] = None
    image: Optional[str] = None


class RoutePayload(BaseModel):
    markers: list[dict[str, Any]] = Field(default_factory=list)
    polyline: list[list[float]] = Field(default_factory=list)
    available: bool = False
    current: Optional[dict[str, float]] = None


class CourseResponse(BaseModel):
    title: Optional[str] = None
    story: Optional[str] = None
    places: list[PlaceItem] = Field(default_factory=list)
    route: Optional[RoutePayload] = None
    route_note: Optional[str] = None
    source: Optional[str] = None
    course_id: Optional[int] = None
    message: Optional[str] = None
    candidates_count: int = 0

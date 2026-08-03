"""
PRD 데이터 모델.

User          id, nickname, created_at
Location      id, name, address, latitude, longitude, category
Course        id, user_id, title
CourseLocation course_id, location_id, sequence
History       id, user_id, query_json, result_json, created_at  (검색/추천 기록)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    id: Optional[int]
    nickname: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Location:
    id: Optional[int]
    name: str
    address: str
    latitude: float
    longitude: float
    category: str


@dataclass
class Course:
    id: Optional[int]
    user_id: Optional[int]
    title: str
    story: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class CourseLocation:
    course_id: int
    location_id: int
    sequence: int
    duration: Optional[str] = None
    travel_time: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class History:
    id: Optional[int]
    user_id: Optional[int]
    query_json: str
    result_json: str
    created_at: datetime = field(default_factory=utcnow)

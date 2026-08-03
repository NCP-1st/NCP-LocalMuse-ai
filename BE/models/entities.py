"""
PRD 데이터 모델.

User          id, nickname, created_at
Location      id, name, address, latitude, longitude, category
Course        id, user_id, title
CourseLocation course_id, location_id, sequence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    nickname: str
    created_at: datetime = field(default_factory=datetime.utcnow)


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


@dataclass
class CourseLocation:
    course_id: int
    location_id: int
    sequence: int

"""Prompt templates for CLOVA Studio."""

from BE.prompts.course import (
    SYSTEM_CURATOR,
    SYSTEM_JSON_STRICT,
    build_course_user_prompt,
    build_strict_retry_suffix,
)

__all__ = [
    "SYSTEM_CURATOR",
    "SYSTEM_JSON_STRICT",
    "build_course_user_prompt",
    "build_strict_retry_suffix",
]

"""UI components."""

from FE.components.course_panel import render_course_result
from FE.components.hero import render_hero
from FE.components.input_form import TripFormData, render_sidebar_form
from FE.components.map_view import render_map
from FE.components.place_card import render_place_card
from FE.components.styles import inject_styles

__all__ = [
    "inject_styles",
    "render_hero",
    "render_sidebar_form",
    "TripFormData",
    "render_course_result",
    "render_place_card",
    "render_map",
]

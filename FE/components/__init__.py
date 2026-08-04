"""UI components."""

from FE.components.course_panel import render_course_result
from FE.components.demo_panel import render_demo_panel
from FE.components.hero import render_hero
from FE.components.icons import icon, icon_heading, icon_text, status_icon
from FE.components.input_form import TripFormData, render_sidebar_form
from FE.components.integration_banner import render_integration_banner
from FE.components.map_view import render_map
from FE.components.pipeline_status import render_stage_timeline, run_course_with_stage_ui
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
    "render_integration_banner",
    "render_demo_panel",
    "run_course_with_stage_ui",
    "render_stage_timeline",
    "icon",
    "icon_text",
    "icon_heading",
    "status_icon",
]

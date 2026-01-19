"""
Routers Package - API Endpoints
================================

This package contains all API routers:
- idea: Project idea input and understanding
- planning: Feature trade-offs, flows, tech stack, viva guide
- flowcharts: Mermaid diagram generation
- export: PDF and image export
- projects: Saved project blueprints (read-only)
"""

from app.routers.idea import router as idea_router
from app.routers.planning import router as planning_router
from app.routers.flowcharts import router as flowcharts_router
from app.routers.export import router as export_router
from app.routers.projects import router as projects_router

__all__ = [
    "idea_router",
    "planning_router",
    "flowcharts_router",
    "export_router",
    "projects_router",
]

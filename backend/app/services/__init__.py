"""
Services Package - Core Business Logic
=======================================

This package contains all the service classes that power
the AI Project Planner:

- llm_service: Handles multi-provider AI communication (Gemini → OpenAI → Groq)
- validation_service: Validates inputs, blocks code requests
- planner_service: Orchestrates all planning operations
- project_service: Persists projects to Firebase Firestore
- normalizer: Ensures AI outputs are properly structured
"""

from app.services.llm_service import llm_service, LLMService
from app.services.validation_service import validation_service, ValidationService
from app.services.planner_service import planner_service, PlannerService
from app.services.project_service import project_service, ProjectService
from app.services.normalizer import normalize_blueprint, map_to_frontend_format, get_fallback_blueprint

__all__ = [
    "llm_service",
    "LLMService",
    "validation_service",
    "ValidationService",
    "planner_service",
    "PlannerService",
    "project_service",
    "ProjectService",
    "normalize_blueprint",
    "map_to_frontend_format",
    "get_fallback_blueprint",
]


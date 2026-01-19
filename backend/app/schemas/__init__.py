"""
Schemas Package - All data models for the AI Project Planner
=============================================================

This package contains Pydantic models that define:
- What data the API accepts (request schemas)
- What data the API returns (response schemas)
- The structure of the project blueprint

Import from here for cleaner code:
    from app.schemas import IdeaInput, Blueprint, APIResponse
"""

# Idea-related schemas
from app.schemas.idea import (
    PlanningMode,
    IdeaInput,
    IdeaExpanded,
    ClarifyingQuestion,
    StudentAnswer,
)

# Blueprint-related schemas
from app.schemas.blueprint import (
    FeasibilityLevel,
    IdeaEvaluation,
    FeatureTradeOff,
    FeatureCategory,
    Feature,
    SystemFlowStep,
    SystemFlow,
    TechStackItem,
    ArchitectureOverview,
    VivaQuestion,
    VivaGuide,
    Pitch,
    Blueprint,
)

# Response schemas
from app.schemas.response import (
    APIResponse,
    ErrorDetail,
    HealthResponse,
    CodeGenerationRefusal,
)

# Make all schemas available at package level
__all__ = [
    # Idea
    "PlanningMode",
    "IdeaInput",
    "IdeaExpanded",
    "ClarifyingQuestion",
    "StudentAnswer",
    # Blueprint
    "FeasibilityLevel",
    "IdeaEvaluation",
    "FeatureTradeOff",
    "FeatureCategory",
    "Feature",
    "SystemFlowStep",
    "SystemFlow",
    "TechStackItem",
    "ArchitectureOverview",
    "VivaQuestion",
    "VivaGuide",
    "Pitch",
    "Blueprint",
    # Response
    "APIResponse",
    "ErrorDetail",
    "HealthResponse",
    "CodeGenerationRefusal",
]

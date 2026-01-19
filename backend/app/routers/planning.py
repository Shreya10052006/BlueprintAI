"""
Planning Router - Endpoints for Project Planning Operations
============================================================

This router handles all endpoints related to:
- Feature trade-off analysis
- System flow generation
- Tech stack recommendations
- Architecture explanations
- Viva preparation guides
- Project pitches

These endpoints help students plan their project systematically.
"""

from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas import APIResponse
from app.services import planner_service

# Create the router
router = APIRouter(
    prefix="/api/planning",
    tags=["Project Planning"]
)


# =============================================================================
# REQUEST MODELS
# =============================================================================

class BlueprintRequest(BaseModel):
    """Request model for unified blueprint generation."""
    idea: str = Field(..., min_length=10, description="Project idea or finalized summary")
    mode: str = Field(default="QUICK_BLUEPRINT", description="QUICK_BLUEPRINT or INTERACTIVE_FINALIZED")


class RevisionRequest(BaseModel):
    """Request model for revision-based regeneration."""
    updated_summary: dict = Field(..., description="Updated summary from revision")


# =============================================================================
# UNIFIED BLUEPRINT ENDPOINT (NEW)
# =============================================================================

@router.post(
    "/generate-blueprint",
    response_model=APIResponse,
    summary="Generate complete blueprint in single call",
    description="""
    🚀 NEW: Unified endpoint that generates ALL blueprint sections in ONE call.
    
    Replaces 10+ sequential API calls with a single request.
    Uses provider cascade (Gemini → GPT → Groq) for reliability.
    
    Returns complete blueprint with:
    - Summary
    - Features
    - Feasibility
    - System Flow
    - Tech Stack
    - Comparison
    - Viva Guide
    - Pitch
    - Diagrams (Mermaid)
    """
)
async def generate_blueprint(request: BlueprintRequest):
    """
    Generate complete project blueprint in a single AI call.
    
    This is the new primary endpoint that should be used instead
    of calling individual section endpoints sequentially.
    """
    result = await planner_service.generate_full_blueprint(
        summary_text=request.idea,
        mode=request.mode
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="The AI service is temporarily unavailable. Please try again in a moment.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's your complete project blueprint!",
        data={
            "blueprint": result["blueprint"],
            "provider_used": result.get("provider_used")  # For debugging, not shown to users
        }
    )


@router.post(
    "/regenerate-blueprint",
    response_model=APIResponse,
    summary="Regenerate blueprint after revision",
    description="""
    Regenerates the entire blueprint after a revision request.
    
    For reliability, this regenerates all sections rather than
    attempting partial updates.
    """
)
async def regenerate_blueprint(request: RevisionRequest):
    """
    Regenerate blueprint after revision changes.
    """
    result = await planner_service.regenerate_after_revision(
        updated_summary=request.updated_summary
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="The AI service is temporarily unavailable. Please try again in a moment.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Your blueprint has been regenerated with the changes!",
        data={
            "blueprint": result["blueprint"],
            "provider_used": result.get("provider_used")
        }
    )


# =============================================================================
# LEGACY ENDPOINTS (Kept for backwards compatibility)
# =============================================================================

@router.post(
    "/tradeoffs",
    response_model=APIResponse,
    summary="Analyze feature trade-offs",
    description="""
    Explains what adding a feature really costs.
    
    For every feature, shows:
    - Complexity impact
    - Time impact  
    - Architecture changes needed
    - Recommendation (include or skip)
    
    This teaches real engineering thinking!
    """
)
async def analyze_tradeoffs(
    project_summary: str,
    feature: str
):
    """
    Explain the trade-offs of adding a specific feature.
    
    This is one of the UNIQUE aspects of this system.
    It teaches students that features have hidden costs.
    """
    if not project_summary or len(project_summary) < 10:
        return APIResponse(
            success=False,
            message="Please provide a brief project summary.",
            data=None,
            errors=["Project summary must be at least 10 characters"]
        )
    
    if not feature or len(feature) < 3:
        return APIResponse(
            success=False,
            message="Please specify which feature to analyze.",
            data=None,
            errors=["Feature name must be at least 3 characters"]
        )
    
    result = await planner_service.analyze_feature_tradeoff(project_summary, feature)
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't analyze the feature trade-offs.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message=f"Here's what adding '{feature}' really means:",
        data={
            "feature_analyzed": feature,
            "analysis": result["data"]
        }
    )


@router.post(
    "/flow",
    response_model=APIResponse,
    summary="Generate system flow",
    description="""
    Creates a step-by-step flow of how the system works.
    
    Example output:
    User → Login → Input Data → Processing → Output
    
    Perfect for documentation and viva explanations.
    """
)
async def generate_flow(
    project_summary: str,
    features: List[str]
):
    """
    Generate a clear system flow for documentation.
    
    This flow can be used directly in:
    - Project reports
    - Presentations
    - Viva explanations
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    if not features:
        return APIResponse(
            success=False,
            message="Please list at least one feature.",
            data=None,
            errors=["At least one feature is required"]
        )
    
    result = await planner_service.generate_system_flow(project_summary, features)
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate the system flow.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's how your system works, step by step:",
        data={
            "flow": result["data"]
        }
    )


@router.post(
    "/tech-stack",
    response_model=APIResponse,
    summary="Get tech stack recommendations",
    description="""
    Recommends appropriate technologies based on:
    - Project requirements
    - Student skill level
    - Project timeline
    
    Each recommendation includes WHY it's suitable.
    """
)
async def recommend_tech_stack(
    project_summary: str,
    features: List[str]
):
    """
    Recommend technologies suitable for this project and skill level.
    
    We prioritize:
    - Beginner-friendly technologies
    - Well-documented options
    - Technologies commonly taught in colleges
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.recommend_tech_stack(project_summary, features or [])
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate tech stack recommendations.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here are the recommended technologies for your project:",
        data=result["data"]
    )


@router.post(
    "/architecture",
    response_model=APIResponse,
    summary="Generate architecture explanation",
    description="""
    Explains system architecture in simple terms.
    
    Includes:
    - High-level overview
    - Main modules
    - Data flow explanation
    - Diagram description
    """
)
async def explain_architecture(
    project_summary: str,
    features: List[str],
    tech_stack: List[dict]
):
    """
    Generate a clear architecture explanation.
    
    This helps students:
    - Understand how parts fit together
    - Explain architecture in viva
    - Plan implementation order
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.explain_architecture(
        project_summary,
        tech_stack or [],
        features or []
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate architecture explanation.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's how your system architecture works:",
        data={
            "architecture": result["data"]
        }
    )


@router.post(
    "/viva-guide",
    response_model=APIResponse,
    summary="Generate viva preparation guide",
    description="""
    Creates everything a student needs to face viva confidently.
    
    Includes:
    - How to explain each part of the project
    - Common viva questions with answers
    - Why examiners ask each question
    """
)
async def generate_viva_guide(
    project_summary: str,
    features: List[str],
    tech_stack: str = "",
    architecture: str = ""
):
    """
    Generate a comprehensive viva preparation guide.
    
    This is GOLD for nervous students.
    It tells them exactly what to expect.
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.generate_viva_guide(
        project_summary,
        features or [],
        tech_stack,
        architecture
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate viva guide.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's your complete viva preparation guide:",
        data={
            "viva_guide": result["data"]
        }
    )


@router.post(
    "/pitch",
    response_model=APIResponse,
    summary="Generate project pitches",
    description="""
    Creates ready-to-use project pitches.
    
    Includes:
    - 30-second pitch (quick intro)
    - 1-minute pitch (detailed)
    - Key points to remember
    """
)
async def generate_pitch(
    project_summary: str,
    problem: str = "",
    features: List[str] = [],
    unique_aspects: str = ""
):
    """
    Generate professional project pitches.
    
    These can be used for:
    - Project reviews
    - Hackathon presentations
    - Demo days
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.generate_pitch(
        project_summary,
        problem or project_summary,
        features or [],
        unique_aspects or "Innovative approach to solving the problem"
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate pitches.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here are your project pitches:",
        data={
            "pitch": result["data"]
        }
    )


@router.post(
    "/features",
    response_model=APIResponse,
    summary="Generate feature breakdown",
    description="""
    Creates a detailed breakdown of all app features.
    
    For each feature:
    - What it does
    - Why it exists
    - How it helps users
    - Limitations (if any)
    """
)
async def generate_features(
    project_summary: str,
    problem: str = ""
):
    """
    Generate detailed feature breakdown for the project.
    
    This helps students understand and explain each feature
    without getting into implementation details.
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.generate_features(
        project_summary,
        problem or project_summary
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate feature breakdown.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's your feature breakdown:",
        data={
            "features": result["data"]
        }
    )


@router.post(
    "/comparison",
    response_model=APIResponse,
    summary="Generate comparison with existing solutions",
    description="""
    Analyzes the student's idea against existing solutions.
    
    Includes:
    - Existing solutions for the same problem
    - Unique aspects of the student's approach
    - Why this project is still valuable
    - Summary insight for viva defense
    """
)
async def generate_comparison(
    project_summary: str,
    features: List[str] = [],
    problem: str = ""
):
    """
    Generate comparison analysis for the student's project idea.
    
    This helps students answer: "This already exists — why did you build it?"
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.generate_comparison(
        project_summary,
        features or [],
        problem or project_summary
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate comparison analysis.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's how your project compares to existing solutions:",
        data={
            "comparison": result["data"]
        }
    )


@router.post(
    "/hackathon-viva",
    response_model=APIResponse,
    summary="Generate extended viva and hackathon guide",
    description="""
    Comprehensive preparation for viva AND hackathon presentations.
    
    Includes:
    - Standard viva questions with answers
    - Hackathon-specific questions
    - Key points to emphasize
    """
)
async def generate_hackathon_viva(
    project_summary: str,
    features: List[str] = [],
    tech_stack: str = "",
    unique_aspects: str = ""
):
    """
    Generate extended viva guide with hackathon-specific questions.
    
    Prepares students for both academic viva and hackathon pitching.
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    result = await planner_service.generate_hackathon_viva(
        project_summary,
        features or [],
        tech_stack,
        unique_aspects or "Innovative approach to solving the problem"
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't generate hackathon viva guide.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's your extended viva and hackathon guide:",
        data={
            "hackathon_viva": result["data"]
        }
    )

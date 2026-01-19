"""
Revision Router - Endpoints for Post-Generation Changes
========================================================

This router handles changes requested after the blueprint
has been generated. It ensures:
- Summary is updated first (source of truth)
- Only affected sections are regenerated
- No unauthorized feature additions
- Decision traceability is maintained
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from pydantic import BaseModel
from app.schemas import APIResponse
from app.services import planner_service


# Request models
class RevisionRequest(BaseModel):
    current_summary: Dict[str, Any]
    change_request: str


# Change propagation map
CHANGE_PROPAGATION = {
    "feature": ["features", "feasibility", "flow", "diagrams", "pitch", "comparison"],
    "tech": ["techStack", "architecture", "vivaGuide"],
    "scope": ["summary", "features", "feasibility", "flow", "techStack", "diagrams", "comparison", "vivaGuide", "pitch"],
    "wording": ["summary", "pitch"]
}


# Create the router
router = APIRouter(
    prefix="/api/revision",
    tags=["Post-Generation Revision"]
)


@router.post(
    "/apply",
    response_model=APIResponse,
    summary="Apply a change to the blueprint",
    description="""
    Processes a user's change request after blueprint generation.
    
    This endpoint:
    1. Interprets what the user wants to change
    2. Updates the summary first (source of truth)
    3. Determines which sections need regeneration
    4. Returns the updated summary and affected sections
    
    The frontend should then regenerate ONLY the affected sections.
    This prevents blind regeneration of the entire blueprint.
    """
)
async def apply_revision(request: RevisionRequest):
    """
    Apply a post-generation change to the project.
    
    The summary is always updated first as the source of truth.
    Only sections affected by the change type are marked for regeneration.
    """
    if not request.current_summary:
        return APIResponse(
            success=False,
            message="Current summary is required.",
            data=None,
            errors=["Cannot apply changes without existing summary"]
        )
    
    if not request.change_request or len(request.change_request.strip()) < 5:
        return APIResponse(
            success=False,
            message="Please describe what you want to change.",
            data=None,
            errors=["Change request must be at least 5 characters"]
        )
    
    result = await planner_service.apply_revision(
        current_summary=request.current_summary,
        change_request=request.change_request.strip()
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="Couldn't process the change request.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    # Get change type and affected sections
    change_type = result["data"].get("change_type", "feature")
    sections_to_regenerate = CHANGE_PROPAGATION.get(change_type, [])
    
    # Also include any sections explicitly mentioned by AI
    ai_suggested_sections = result["data"].get("sections_affected", [])
    for section in ai_suggested_sections:
        if section not in sections_to_regenerate:
            sections_to_regenerate.append(section)
    
    return APIResponse(
        success=True,
        message=f"Change applied: {result['data'].get('change_description', 'Summary updated')}",
        data={
            "updated_summary": result["data"].get("updated_summary", {}),
            "change_type": change_type,
            "change_description": result["data"].get("change_description", ""),
            "sections_to_regenerate": sections_to_regenerate
        }
    )


@router.get(
    "/propagation-map",
    response_model=APIResponse,
    summary="Get change propagation rules",
    description="""
    Returns the mapping of change types to affected sections.
    Useful for frontend to understand what gets regenerated.
    """
)
async def get_propagation_map():
    """
    Return the change propagation rules.
    
    This helps the frontend understand which sections
    will be affected by different types of changes.
    """
    return APIResponse(
        success=True,
        message="Propagation map retrieved",
        data={
            "propagation_map": CHANGE_PROPAGATION,
            "change_types": list(CHANGE_PROPAGATION.keys())
        }
    )

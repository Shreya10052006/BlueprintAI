"""
Projects Router - Endpoints for Saved Project Blueprints
=========================================================

This router handles read-only access to saved projects:
- GET /api/projects - List all projects
- GET /api/projects/{id} - Get a specific project

All persistence is handled via Firebase Firestore.
This data is accessed ONLY from the backend.
"""

from fastapi import APIRouter, Path
from typing import Optional
from app.schemas import APIResponse
from app.services import project_service
from app.utils import is_firebase_available

# Create the router
router = APIRouter(
    prefix="/api/projects",
    tags=["Saved Projects"]
)


@router.get(
    "",
    response_model=APIResponse,
    summary="List all saved projects",
    description="""
    Retrieve all project blueprints saved to the database.
    
    Returns a list of projects ordered by creation date (newest first).
    Maximum 50 projects are returned.
    
    Note: This requires Firebase to be configured.
    """
)
async def list_projects(limit: int = 50):
    """
    Get all saved project blueprints.
    
    This endpoint is useful for:
    - Viewing past project plans
    - Referencing previous work
    - Demonstrating the system's outputs
    """
    if not is_firebase_available():
        return APIResponse(
            success=False,
            message="Database not configured.",
            data=None,
            errors=[
                "Firebase is not set up.",
                "Projects can still be generated but won't be saved."
            ]
        )
    
    projects = await project_service.get_all_projects(limit=limit)
    
    return APIResponse(
        success=True,
        message=f"Found {len(projects)} saved project(s)",
        data={
            "projects": projects,
            "count": len(projects)
        }
    )


@router.get(
    "/{project_id}",
    response_model=APIResponse,
    summary="Get a specific project by ID",
    description="""
    Retrieve a single project blueprint by its document ID.
    
    Use this to view the complete details of a previously
    generated blueprint.
    """
)
async def get_project(
    project_id: str = Path(..., description="The project document ID")
):
    """
    Get a specific project by ID.
    
    Returns the complete project document including:
    - Original idea input
    - Planning mode used
    - Complete blueprint
    - Mermaid diagrams
    - Creation timestamp
    """
    if not is_firebase_available():
        return APIResponse(
            success=False,
            message="Database not configured.",
            data=None,
            errors=["Firebase is not set up."]
        )
    
    project = await project_service.get_project_by_id(project_id)
    
    if project is None:
        return APIResponse(
            success=False,
            message="Project not found.",
            data=None,
            errors=[f"No project exists with ID: {project_id}"]
        )
    
    return APIResponse(
        success=True,
        message="Project retrieved successfully",
        data={
            "project": project
        }
    )

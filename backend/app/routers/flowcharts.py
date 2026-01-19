"""
Flowcharts Router - Endpoints for Diagram Generation
=====================================================

This router handles Mermaid.js flowchart generation:
- User flow diagrams
- Tech stack diagrams
- Architecture diagrams

All diagrams are designed to be:
- Clean and professional
- Print-friendly (white background)
- Easy to export
"""

from fastapi import APIRouter
from typing import List
from app.schemas import APIResponse
from app.utils import mermaid_generator

# Create the router
router = APIRouter(
    prefix="/api/flowcharts",
    tags=["Flowcharts & Diagrams"]
)


@router.post(
    "/user-flow",
    response_model=APIResponse,
    summary="Generate user flow diagram",
    description="""
    Creates a Mermaid.js flowchart showing the user journey.
    
    Shows how a user interacts with the system from start to finish.
    Perfect for documentation and presentations.
    """
)
async def generate_user_flow(
    project_summary: str,
    features: List[str]
):
    """
    Generate a user flow flowchart.
    
    The output is Mermaid.js syntax that can be rendered
    in the frontend or exported as an image.
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
    
    result = await mermaid_generator.generate_user_flow(project_summary, features)
    
    if not result["success"]:
        # Use fallback if AI generation fails
        simple_steps = [f"Start", f"Login", f"Use {features[0]}", f"View Results", f"Logout"]
        fallback_code = mermaid_generator.create_simple_user_flow(simple_steps)
        
        return APIResponse(
            success=True,
            message="Generated a basic user flow (AI generation unavailable):",
            data={
                "mermaid_code": fallback_code,
                "is_fallback": True
            }
        )
    
    return APIResponse(
        success=True,
        message="Here's your user flow diagram:",
        data={
            "mermaid_code": result["mermaid_code"],
            "is_fallback": False
        }
    )


@router.post(
    "/tech-stack",
    response_model=APIResponse,
    summary="Generate tech stack diagram",
    description="""
    Creates a Mermaid.js diagram showing technology architecture.
    
    Shows how different technologies connect:
    Frontend → Backend → Database → Services
    """
)
async def generate_tech_stack_diagram(
    project_summary: str,
    tech_stack: List[dict]
):
    """
    Generate a tech stack architecture diagram.
    
    This visually shows how the chosen technologies work together.
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    if not tech_stack:
        return APIResponse(
            success=False,
            message="Please provide the tech stack first.",
            data=None,
            errors=["Tech stack is required. Generate it using /api/planning/tech-stack"]
        )
    
    result = await mermaid_generator.generate_tech_stack_diagram(project_summary, tech_stack)
    
    if not result["success"]:
        # Use fallback
        fallback_code = mermaid_generator.create_simple_tech_stack(tech_stack)
        
        return APIResponse(
            success=True,
            message="Generated a basic tech stack diagram (AI generation unavailable):",
            data={
                "mermaid_code": fallback_code,
                "is_fallback": True
            }
        )
    
    return APIResponse(
        success=True,
        message="Here's your tech stack diagram:",
        data={
            "mermaid_code": result["mermaid_code"],
            "is_fallback": False
        }
    )


@router.post(
    "/architecture",
    response_model=APIResponse,
    summary="Generate architecture diagram",
    description="""
    Creates a Mermaid.js diagram of the system architecture.
    
    Shows all major modules and how they interact.
    """
)
async def generate_architecture_diagram(
    project_summary: str,
    modules: List[str],
    data_flow: str
):
    """
    Generate a system architecture diagram.
    
    This shows the big picture of how the system is organized.
    """
    if not project_summary:
        return APIResponse(
            success=False,
            message="Please provide a project summary.",
            data=None,
            errors=["Project summary is required"]
        )
    
    if not modules:
        return APIResponse(
            success=False,
            message="Please list the system modules.",
            data=None,
            errors=["At least one module is required. Generate architecture using /api/planning/architecture first"]
        )
    
    result = await mermaid_generator.generate_architecture_diagram(
        project_summary,
        modules,
        data_flow or "Data flows from user input through processing to output"
    )
    
    if not result["success"]:
        # Create a simple fallback
        fallback_code = mermaid_generator.create_simple_user_flow(modules[:5])
        
        return APIResponse(
            success=True,
            message="Generated a basic architecture diagram (AI generation unavailable):",
            data={
                "mermaid_code": fallback_code,
                "is_fallback": True
            }
        )
    
    return APIResponse(
        success=True,
        message="Here's your architecture diagram:",
        data={
            "mermaid_code": result["mermaid_code"],
            "is_fallback": False
        }
    )

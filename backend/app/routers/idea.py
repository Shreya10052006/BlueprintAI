"""
Idea Router - Endpoints for Project Idea Input & Understanding
===============================================================

This router handles all endpoints related to:
- Accepting a new project idea
- Expanding the idea into structured form
- Evaluating idea feasibility

These are typically the first steps a student takes.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from app.schemas import (
    IdeaInput, IdeaExpanded, IdeaEvaluation,
    APIResponse, ClarifyingQuestion, StudentAnswer,
    PlanningMode
)
from app.services import planner_service, validation_service

# Create the router with a prefix and tags for API docs
router = APIRouter(
    prefix="/api/idea",
    tags=["Idea Input & Understanding"]
)


@router.post(
    "",
    response_model=APIResponse,
    summary="Submit a new project idea",
    description="""
    This is the starting point for students.
    
    They submit their raw idea (even if vague!) and choose a planning mode:
    - **interactive**: AI asks questions, student makes decisions
    - **ai_only**: AI makes all decisions, student reviews the plan
    """
)
async def submit_idea(idea: IdeaInput):
    """
    Accept a new project idea from a student.
    
    This endpoint:
    1. Validates the idea is reasonable
    2. Checks for code generation requests (and refuses them!)
    3. Returns clarifying questions (interactive) or expands immediately (ai_only)
    """
    # Validate the idea first
    is_valid, error_msg, suggestion = validation_service.validate_idea(idea.raw_idea)
    
    if not is_valid:
        # Return a helpful error, not a crash
        return APIResponse(
            success=False,
            message=error_msg,
            data=None,
            errors=[suggestion] if suggestion else None
        )
    
    # Clean up the input
    cleaned_idea = validation_service.sanitize_input(idea.raw_idea)
    
    if idea.mode == PlanningMode.INTERACTIVE:
        # Generate clarifying questions for interactive mode
        result = await planner_service.generate_clarifying_questions(cleaned_idea)
        
        if not result["success"]:
            return APIResponse(
                success=False,
                message="We couldn't generate questions. Please try again.",
                data=None,
                errors=[result.get("error", "Unknown error")]
            )
        
        return APIResponse(
            success=True,
            message="Great idea! Let's understand it better. Answer these questions:",
            data={
                "mode": "interactive",
                "raw_idea": cleaned_idea,
                "questions": result["data"].get("questions", [])
            }
        )
    else:
        # AI_ONLY mode: Expand the idea directly
        result = await planner_service.expand_idea(cleaned_idea)
        
        if not result["success"]:
            return APIResponse(
                success=False,
                message="We couldn't understand your idea. Please try rephrasing.",
                data=None,
                errors=[result.get("error", "Unknown error")]
            )
        
        return APIResponse(
            success=True,
            message="We've understood your idea! Here's the structured version:",
            data={
                "mode": "ai_only",
                "raw_idea": cleaned_idea,
                "expanded": result["data"]
            }
        )


@router.post(
    "/understand",
    response_model=APIResponse,
    summary="Expand idea into structured form",
    description="""
    Takes a raw idea and transforms it into a clear, structured understanding.
    
    Output includes:
    - Problem statement
    - Target users
    - Objectives
    - Scope
    - Educational explanations
    """
)
async def understand_idea(idea: IdeaInput):
    """
    Transform a vague idea into structured understanding.
    
    This is valuable because most students have ideas but
    don't know how to articulate them clearly.
    """
    # Validate first
    is_valid, error_msg, suggestion = validation_service.validate_idea(idea.raw_idea)
    
    if not is_valid:
        return APIResponse(
            success=False,
            message=error_msg,
            data=None,
            errors=[suggestion] if suggestion else None
        )
    
    cleaned_idea = validation_service.sanitize_input(idea.raw_idea)
    
    # Expand the idea
    result = await planner_service.expand_idea(cleaned_idea)
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="We had trouble understanding your idea.",
            data=None,
            errors=[result.get("error", "Please try rephrasing your idea")]
        )
    
    return APIResponse(
        success=True,
        message="Here's what we understand from your idea:",
        data={
            "original_idea": cleaned_idea,
            "expanded": result["data"]
        }
    )


@router.post(
    "/evaluate",
    response_model=APIResponse,
    summary="Evaluate idea feasibility",
    description="""
    Provides an honest evaluation of the project idea.
    
    Output includes:
    - Strengths (what works well)
    - Risks (potential challenges)
    - Feasibility level (High/Medium/Low)
    - Explanation of the evaluation
    
    No numeric scores - just clear, helpful explanations.
    """
)
async def evaluate_idea(
    idea: IdeaInput,
    expanded_details: Optional[dict] = None
):
    """
    Evaluate an idea's feasibility for a college student.
    
    This helps students understand if their idea is realistic
    BEFORE they invest time implementing it.
    """
    # Validate
    is_valid, error_msg, suggestion = validation_service.validate_idea(idea.raw_idea)
    
    if not is_valid:
        return APIResponse(
            success=False,
            message=error_msg,
            data=None,
            errors=[suggestion] if suggestion else None
        )
    
    cleaned_idea = validation_service.sanitize_input(idea.raw_idea)
    
    # Evaluate the idea
    result = await planner_service.evaluate_idea(cleaned_idea, expanded_details)
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="We couldn't complete the evaluation.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Here's our honest evaluation of your idea:",
        data={
            "original_idea": cleaned_idea,
            "evaluation": result["data"]
        }
    )


@router.post(
    "/answer",
    response_model=APIResponse,
    summary="Submit answers to clarifying questions",
    description="""
    In interactive mode, students answer questions to refine their idea.
    This endpoint accepts those answers and continues the planning process.
    """
)
async def submit_answers(
    raw_idea: str,
    answers: list[StudentAnswer]
):
    """
    Process student answers to clarifying questions.
    
    This builds a more complete understanding of what the student wants.
    """
    # Validate the original idea
    is_valid, error_msg, suggestion = validation_service.validate_idea(raw_idea)
    
    if not is_valid:
        return APIResponse(
            success=False,
            message=error_msg,
            data=None,
            errors=[suggestion] if suggestion else None
        )
    
    # Combine idea with answers for better expansion
    answers_text = "\n".join([
        f"Q: {a.question_id} - A: {a.answer}" 
        for a in answers
    ])
    
    enhanced_idea = f"{raw_idea}\n\nStudent's clarifications:\n{answers_text}"
    
    # Now expand with the additional context
    result = await planner_service.expand_idea(enhanced_idea)
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="We had trouble processing your answers.",
            data=None,
            errors=[result.get("error", "Please try again")]
        )
    
    return APIResponse(
        success=True,
        message="Thanks for the clarifications! Here's your refined idea:",
        data={
            "original_idea": raw_idea,
            "answers_received": len(answers),
            "expanded": result["data"]
        }
    )

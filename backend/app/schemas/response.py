"""
Response Schemas - Standardized API response structures
========================================================

All API responses follow a consistent format so the frontend
always knows what to expect. This makes error handling easier
and provides clear feedback to students.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, List


class APIResponse(BaseModel):
    """
    Standard wrapper for all API responses.
    
    Every endpoint returns this structure, making it easy for
    the frontend to handle responses consistently.
    
    Example success response:
        {
            "success": true,
            "message": "Idea analyzed successfully",
            "data": { ... },
            "errors": null
        }
    
    Example error response:
        {
            "success": false,
            "message": "We couldn't understand your idea",
            "data": null,
            "errors": ["Please provide more details about what you want to build"]
        }
    """
    success: bool = Field(
        ...,
        description="Did the operation complete successfully?"
    )
    message: str = Field(
        ...,
        description="Human-readable status message"
    )
    data: Optional[Any] = Field(
        default=None,
        description="The actual response data (if successful)"
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="List of error messages (if failed)"
    )


class ErrorDetail(BaseModel):
    """
    Detailed error information for troubleshooting.
    
    Note: Stack traces are NEVER shown to users.
    Errors are always explained in student-friendly language.
    """
    code: str = Field(
        ...,
        description="Error code for reference (e.g., 'IDEA_TOO_VAGUE')"
    )
    message: str = Field(
        ...,
        description="Student-friendly explanation of what went wrong"
    )
    suggestion: str = Field(
        default="",
        description="How the student can fix this issue"
    )


class HealthResponse(BaseModel):
    """
    Response for the /health endpoint.
    
    This tells us if the server is running and if the AI
    service is available.
    """
    status: str = Field(
        default="healthy",
        description="Overall system status"
    )
    api_key_configured: bool = Field(
        ...,
        description="Is the Gemini API key set up?"
    )
    message: str = Field(
        default="",
        description="Additional status information"
    )


class CodeGenerationRefusal(BaseModel):
    """
    Response when a student asks for code generation.
    
    This system is a MENTOR, not a developer.
    We politely refuse code requests and redirect to planning.
    """
    refused: bool = Field(default=True)
    reason: str = Field(
        default="This system helps you plan and understand your project, not generate code.",
        description="Why we can't generate code"
    )
    what_we_can_help_with: List[str] = Field(
        default=[
            "Understanding your project idea",
            "Evaluating feasibility",
            "Explaining feature trade-offs",
            "Creating system flow diagrams",
            "Preparing for viva questions",
            "Writing project pitches"
        ],
        description="What this system CAN help with"
    )
    encouragement: str = Field(
        default="Understanding your project deeply will make implementation much easier!",
        description="Encouraging message for the student"
    )

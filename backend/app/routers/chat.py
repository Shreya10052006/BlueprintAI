"""
Chat Router - Endpoints for Interactive Planning Conversations
===============================================================

This router handles the interactive planning mode where students
chat with an AI mentor to refine their project idea before
generating the full blueprint.

Key principles:
- Chat is for discussion and exploration
- Draft summary evolves but is NOT final until explicitly confirmed
- The AI acts as a mentor, not a decision-maker
"""

from fastapi import APIRouter
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.schemas import APIResponse
from app.services import planner_service


# Request/Response models
class ChatMessage(BaseModel):
    role: str  # "user" or "ai"
    content: str


class ChatRequest(BaseModel):
    raw_idea: str
    chat_history: List[ChatMessage] = []
    user_message: str


# Create the router
router = APIRouter(
    prefix="/api/chat",
    tags=["Interactive Planning"]
)


@router.post(
    "/message",
    response_model=APIResponse,
    summary="Send a message in interactive planning",
    description="""
    Continues the interactive planning conversation.
    
    The AI mentor will:
    - Respond conversationally
    - Ask clarifying questions
    - Suggest options without deciding
    - Update the draft summary as understanding evolves
    
    The draft summary is NOT final until the user clicks
    "Finalize & Generate Blueprint".
    """
)
async def send_chat_message(request: ChatRequest):
    """
    Process a student's message in interactive planning mode.
    
    This is the core of the mentor-style conversation.
    The AI helps the student think through their idea.
    """
    if not request.raw_idea or len(request.raw_idea) < 10:
        return APIResponse(
            success=False,
            message="Please provide your initial project idea.",
            data=None,
            errors=["Original idea is required for context"]
        )
    
    if not request.user_message or len(request.user_message.strip()) < 2:
        return APIResponse(
            success=False,
            message="Please enter a message.",
            data=None,
            errors=["Message cannot be empty"]
        )
    
    # Convert pydantic models to dicts for service
    history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
    
    result = await planner_service.generate_chat_response(
        raw_idea=request.raw_idea,
        chat_history=history,
        user_message=request.user_message.strip()
    )
    
    if not result["success"]:
        return APIResponse(
            success=False,
            message="I couldn't generate a response. Please try again.",
            data=None,
            errors=[result.get("error", "Unknown error")]
        )
    
    return APIResponse(
        success=True,
        message="Response generated",
        data={
            "ai_response": result["data"].get("ai_response", ""),
            "draft_summary": result["data"].get("draft_summary", {}),
            "is_ready_to_finalize": result["data"].get("is_ready_to_finalize", False),
            "suggested_next_question": result["data"].get("suggested_next_question")
        }
    )


@router.post(
    "/start",
    response_model=APIResponse,
    summary="Start an interactive planning session",
    description="""
    Initializes a new interactive planning session.
    
    Returns the AI mentor's greeting and initial thoughts
    based on the raw idea provided.
    """
)
async def start_chat_session(raw_idea: str):
    """
    Begin a new interactive planning session.
    
    The AI greets the student and starts the conversation.
    """
    if not raw_idea or len(raw_idea) < 10:
        return APIResponse(
            success=False,
            message="Please provide your project idea first.",
            data=None,
            errors=["Idea must be at least 10 characters"]
        )
    
    # Generate initial response with empty history
    result = await planner_service.generate_chat_response(
        raw_idea=raw_idea,
        chat_history=[],
        user_message="I want to start planning this project. Can you help me refine my idea?"
    )
    
    if not result["success"]:
        # Fallback greeting if AI fails
        return APIResponse(
            success=True,
            message="Session started",
            data={
                "ai_response": f"Great! I'd love to help you plan this project: \"{raw_idea}\"\n\nLet's start by understanding what you want to build. Can you tell me more about who will use this and what problem it solves?",
                "draft_summary": {
                    "problem_statement": raw_idea,
                    "target_users": "",
                    "main_features": [],
                    "scope_notes": "Not yet defined"
                },
                "is_ready_to_finalize": False
            }
        )
    
    return APIResponse(
        success=True,
        message="Session started",
        data=result["data"]
    )

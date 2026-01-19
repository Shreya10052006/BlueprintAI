"""
Mentor Chat Router - Fast Chat Mode for BlueprintAI
====================================================

Provides a separate, fast chat endpoint for mentor conversations.
Uses Groq LLaMA 3.1 70B directly (no cascade) for:
- Speed: 1-3 second responses
- Concise answers: 2-4 sentences
- Mentor-like tone

This endpoint is ISOLATED from blueprint generation to:
- Prevent quota contention
- Enable faster responses
- Keep chat traffic separate

Uses a separate API key (GROQ_CHAT_API_KEY) if available,
otherwise falls back to the primary GROQ_API_KEY.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import os
import httpx
from dotenv import load_dotenv

from app.schemas import APIResponse

# Load environment variables
load_dotenv()

# Create the router
router = APIRouter(
    prefix="/api/mentor-chat",
    tags=["Mentor Chat"]
)

# Configuration - use separate key if available, else fall back to main key
GROQ_CHAT_API_KEY = os.getenv("GROQ_CHAT_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Fast chat settings (optimized for speed and conciseness)
FAST_CHAT_CONFIG = {
    "model": "llama-3.1-70b-versatile",
    "temperature": 0.25,  # Lower = more focused
    "max_tokens": 200,     # Short responses
    "top_p": 0.9
}

# System prompt for mentor chat
MENTOR_SYSTEM_PROMPT = """You are a friendly project mentor for college students.

Your responses should be:
- CONCISE: 2-4 sentences maximum
- HELPFUL: Give clear, actionable guidance
- ENCOURAGING: Positive but honest tone
- FOCUSED: Answer only what was asked

You help with:
- Project understanding questions
- Tech stack clarifications
- Viva preparation tips
- General project guidance

NEVER provide code. NEVER give long explanations.
Keep it short, direct, and mentor-like."""


class MentorChatRequest(BaseModel):
    """Request model for mentor chat."""
    message: str = Field(..., min_length=1, max_length=500, description="User's question")
    context: Optional[str] = Field(None, description="Optional project context")


class MentorChatResponse(BaseModel):
    """Response model for mentor chat."""
    response: str
    response_time_ms: int


@router.post(
    "/message",
    response_model=APIResponse,
    summary="Send a message to the mentor",
    description="""
    Fast mentor chat for quick questions and clarifications.
    
    Features:
    - Responses in 1-3 seconds
    - Concise, mentor-like answers (2-4 sentences)
    - Separate from blueprint generation
    
    Use this for:
    - Quick clarifications
    - Viva preparation tips
    - Understanding explanations
    - Project guidance
    """
)
async def send_mentor_message(request: MentorChatRequest):
    """
    Send a message to the AI mentor and get a quick response.
    """
    import time
    start_time = time.time()
    
    # Check if API key is configured
    if not GROQ_CHAT_API_KEY or GROQ_CHAT_API_KEY == "YOUR_API_KEY_HERE":
        return APIResponse(
            success=False,
            message="Mentor chat is not configured. Please add GROQ_API_KEY or GROQ_CHAT_API_KEY to your .env file.",
            data=None,
            errors=["Missing API key configuration"]
        )
    
    # Build the prompt
    user_message = request.message.strip()
    if request.context:
        user_message = f"Project context: {request.context}\n\nQuestion: {user_message}"
    
    try:
        # Call Groq directly (no cascade - speed is priority)
        response = await call_groq_fast(user_message)
        
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        if response["success"]:
            return APIResponse(
                success=True,
                message="",
                data={
                    "response": response["content"],
                    "response_time_ms": response_time_ms
                }
            )
        else:
            return APIResponse(
                success=False,
                message="Mentor chat is temporarily unavailable.",
                data=None,
                errors=[response.get("error", "Unknown error")]
            )
            
    except Exception as e:
        return APIResponse(
            success=False,
            message="Something went wrong with the mentor chat.",
            data=None,
            errors=[str(e)]
        )


async def call_groq_fast(message: str) -> dict:
    """
    Call Groq with fast chat settings.
    
    Optimized for:
    - Speed (shorter timeout, small max_tokens)
    - Conciseness (lower temperature)
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_CHAT_API_KEY}"
        }
        
        payload = {
            "model": FAST_CHAT_CONFIG["model"],
            "messages": [
                {
                    "role": "system",
                    "content": MENTOR_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": FAST_CHAT_CONFIG["temperature"],
            "max_tokens": FAST_CHAT_CONFIG["max_tokens"],
            "top_p": FAST_CHAT_CONFIG["top_p"]
        }
        
        # Shorter timeout for fast responses
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return {
                        "success": True,
                        "content": content.strip()
                    }
                else:
                    return {
                        "success": False,
                        "error": "Empty response from Groq"
                    }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "error": "Too many requests. Please wait a moment."
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

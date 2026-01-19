"""
AI Project Planner - Main Application Entry Point
===================================================

This is the starting point for the FastAPI backend.

To run the server:
    cd backend
    uvicorn app.main:app --reload --port 8000

Then open http://localhost:8000/docs for the API documentation.

-------------------------------------------------------------
IMPORTANT: This system is a project MENTOR, not a code generator.
All LLM interactions focus on planning, explanation, and education.
-------------------------------------------------------------
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routers import (
    idea_router,
    planning_router,
    flowcharts_router,
    export_router,
    projects_router,
)
from app.routers.chat import router as chat_router
from app.routers.revision import router as revision_router
from app.routers.mentor_chat import router as mentor_chat_router

# Import services to check status
from app.services import llm_service
from app.utils import is_firebase_available

# Create the FastAPI application
app = FastAPI(
    title="AI Project Planner for Students",
    description="""
    ## 🎓 A Project Planning Mentor for College Students
    
    This system helps students transform vague project ideas into 
    clear, explainable, presentation-ready blueprints.
    
    ### What This System Does ✅
    - Expands vague ideas into structured problem statements
    - Evaluates feasibility honestly
    - Explains feature trade-offs
    - Generates system flows and diagrams
    - Prepares students for viva
    - Creates project pitches
    
    ### What This System Does NOT Do ❌
    - Generate programming code
    - Create SQL queries
    - Build applications automatically
    
    **This is intentional.** Understanding your project deeply 
    before coding leads to better results!
    """,
    version="1.0.0",
    contact={
        "name": "Student Project Support",
    }
)

# Configure CORS for frontend access
# Supports both local development and production deployment
ALLOWED_ORIGINS = [
    "http://localhost:8080",      # Local dev frontend
    "http://localhost:3000",      # Alternative local dev
    "http://127.0.0.1:8080",      # Local dev frontend
]

# Add production frontend URL from environment (set in Render)
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
if FRONTEND_URL:
    ALLOWED_ORIGINS.append(FRONTEND_URL)
else:
    # Default Vercel domain - TODO: Update with your actual Vercel URL
    ALLOWED_ORIGINS.append("https://blueprintai.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================
# We never show stack traces to users - only friendly messages

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch any unhandled exception and return a friendly message.
    
    Students shouldn't see scary error messages or stack traces.
    """
    # Log the actual error for debugging (in production, use proper logging)
    print(f"❌ Error: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Oops! Something went wrong on our end.",
            "data": None,
            "errors": [
                "Please try again in a moment.",
                "If this keeps happening, the AI service might be temporarily unavailable."
            ]
        }
    )


# ============================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================

@app.get(
    "/health",
    tags=["System Status"],
    summary="Check if the server is running"
)
async def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        {"status": "healthy"} if the server is running
    """
    llm_status = llm_service.get_status()
    
    return {
        "status": "healthy",
        "api_key_configured": llm_status["configured"],
        "message": llm_status["message"]
    }


@app.get(
    "/",
    tags=["System Status"],
    summary="Welcome message"
)
async def root():
    """
    Root endpoint - shows a welcome message.
    """
    return {
        "message": "Welcome to the AI Project Planner for Students! 🎓",
        "description": "This system helps you plan your project, not build it.",
        "docs": "Visit /docs for the full API documentation",
        "important": "We help you UNDERSTAND and PLAN. We don't generate code."
    }


@app.get(
    "/api/status",
    tags=["System Status"],
    summary="Get detailed system status"
)
async def system_status():
    """
    Get detailed status of all system components.
    """
    llm_status = llm_service.get_status()
    
    return {
        "success": True,
        "message": "System status retrieved",
        "data": {
            "server": "running",
            "llm_service": llm_status,
            "version": "1.0.0",
            "endpoints_available": {
                "idea": ["/api/idea", "/api/idea/understand", "/api/idea/evaluate"],
                "planning": ["/api/planning/tradeoffs", "/api/planning/flow", 
                           "/api/planning/tech-stack", "/api/planning/architecture",
                           "/api/planning/viva-guide", "/api/planning/pitch"],
                "flowcharts": ["/api/flowcharts/user-flow", "/api/flowcharts/tech-stack",
                              "/api/flowcharts/architecture"],
                "export": ["/api/export/blueprint", "/api/export/flowchart",
                          "/api/export/formats"],
                "projects": ["/api/projects", "/api/projects/{id}"]
            },
            "firebase_available": is_firebase_available()
        }
    }


# ============================================================
# REGISTER ROUTERS
# ============================================================

app.include_router(idea_router)
app.include_router(planning_router)
app.include_router(flowcharts_router)
app.include_router(export_router)
app.include_router(projects_router)
app.include_router(chat_router)
app.include_router(revision_router)
app.include_router(mentor_chat_router)


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
async def startup_event():
    """
    Called when the server starts.
    
    Checks configuration and prints helpful messages.
    """
    print("\n" + "=" * 60)
    print("🎓 AI PROJECT PLANNER FOR STUDENTS")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("\n⚠️  WARNING: GEMINI_API_KEY not configured!")
        print("   The system will run in DEMO MODE.")
        print("   To enable full AI features:")
        print("   1. Create a .env file in the backend folder")
        print("   2. Add: GEMINI_API_KEY=your_actual_key")
        print("   3. Get your key from: https://aistudio.google.com/app/apikey")
    else:
        print("\n✅ Gemini API key configured")
    
    # Check Firebase
    if is_firebase_available():
        print("✅ Firebase Firestore connected")
    else:
        print("⚠️  Firebase not configured - projects won't be saved")
    
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("\n" + "=" * 60 + "\n")


# ============================================================
# APP PACKAGE INIT (for importing)
# ============================================================
# The app can be imported as: from app.main import app

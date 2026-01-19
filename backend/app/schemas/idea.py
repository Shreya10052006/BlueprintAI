"""
Idea Schemas - Data models for project idea input and expansion
===============================================================

These schemas define the structure of data that flows through
the idea-related endpoints. Think of these as "blueprints" for
what the data should look like.

Why use schemas?
- They validate input automatically
- They document what data is expected
- They make errors clear and helpful
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PlanningMode(str, Enum):
    """
    Two ways a student can use this system:
    
    INTERACTIVE: Student answers AI's questions, makes decisions
    AI_ONLY: AI makes all decisions, student just reviews
    """
    INTERACTIVE = "interactive"
    AI_ONLY = "ai_only"


class IdeaInput(BaseModel):
    """
    What the student provides when starting a new project plan.
    
    Example:
        {
            "raw_idea": "I want to make an attendance tracking app",
            "mode": "interactive"
        }
    """
    raw_idea: str = Field(
        ...,  # ... means this field is required
        min_length=10,  # Idea must be at least 10 characters
        max_length=2000,  # Keep ideas reasonable
        description="The student's project idea in their own words",
        examples=["I want to make an attendance tracking app using face recognition"]
    )
    mode: PlanningMode = Field(
        default=PlanningMode.INTERACTIVE,
        description="How the student wants to plan: interactive or let AI decide"
    )


class IdeaExpanded(BaseModel):
    """
    The structured version of a vague idea, extracted by AI.
    
    This transforms "I want an attendance app" into a clear,
    structured understanding that can be explained in viva.
    """
    problem_statement: str = Field(
        ...,
        description="Clear statement of what problem this project solves"
    )
    target_users: List[str] = Field(
        ...,
        description="Who will use this system? (e.g., students, teachers, admin)"
    )
    objectives: List[str] = Field(
        ...,
        description="What the project aims to achieve (3-5 clear goals)"
    )
    scope: str = Field(
        ...,
        description="What is included and excluded from this project"
    )
    
    # Educational explanation fields
    what_this_means: str = Field(
        default="",
        description="Simple explanation of the expanded idea"
    )
    why_this_matters: str = Field(
        default="",
        description="Why understanding this is important for the student"
    )


class ClarifyingQuestion(BaseModel):
    """
    A question the AI asks to understand the idea better.
    Used in interactive mode.
    """
    question_id: str = Field(..., description="Unique ID for this question")
    question_text: str = Field(..., description="The question to ask the student")
    context: str = Field(
        default="",
        description="Why this question helps (for student understanding)"
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="Suggested answers, if applicable"
    )


class StudentAnswer(BaseModel):
    """
    A student's answer to a clarifying question.
    """
    question_id: str = Field(..., description="Which question this answers")
    answer: str = Field(..., description="The student's answer")

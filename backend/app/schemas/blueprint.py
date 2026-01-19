"""
Blueprint Schemas - Data models for the complete project blueprint
===================================================================

These schemas define the structure of all planning outputs:
- Idea evaluation (strengths, risks, feasibility)
- Feature analysis and trade-offs
- System flow
- Complete blueprint

Each schema includes educational fields to help students
understand what they're seeing and why it matters.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class FeasibilityLevel(str, Enum):
    """
    How feasible is this project for a college student?
    
    Note: We use text levels, not numeric scores.
    Why? Because "High feasibility" is more meaningful
    than "8.5/10" for a nervous student.
    """
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IdeaEvaluation(BaseModel):
    """
    Honest evaluation of a project idea.
    
    This helps students understand if their idea is realistic
    BEFORE they start implementing. Much better than finding
    out mid-project that something is too hard!
    """
    strengths: List[str] = Field(
        ...,
        description="What works well about this idea"
    )
    risks: List[str] = Field(
        ...,
        description="Potential challenges to be aware of"
    )
    feasibility_level: FeasibilityLevel = Field(
        ...,
        description="Overall feasibility for a college project"
    )
    feasibility_explanation: str = Field(
        ...,
        description="Why this feasibility level was assigned"
    )
    
    # Educational fields
    what_this_means: str = Field(default="")
    why_this_matters: str = Field(default="")


class FeatureTradeOff(BaseModel):
    """
    Analysis of what adding/removing a feature really means.
    
    This teaches students that in real engineering, every
    feature has a cost. There's no such thing as "just add this".
    """
    feature_name: str = Field(
        ...,
        description="Name of the feature being analyzed"
    )
    complexity_impact: str = Field(
        ...,
        description="How does this affect project complexity?"
    )
    time_impact: str = Field(
        ...,
        description="How much extra development time is needed?"
    )
    architecture_impact: str = Field(
        ...,
        description="What changes are needed in system design?"
    )
    recommendation: str = Field(
        ...,
        description="Should this feature be included? Why?"
    )
    
    # Educational explanation
    what_this_means: str = Field(default="")


class FeatureCategory(str, Enum):
    """Categories for organizing features logically."""
    CORE = "Core"           # Must-have features
    ADVANCED = "Advanced"   # Nice-to-have features
    ADMIN = "Admin"         # Administrative features


class Feature(BaseModel):
    """A single feature with its category and explanation."""
    name: str
    description: str
    category: FeatureCategory
    why_included: str = Field(
        default="",
        description="Why this feature is part of the project"
    )


class SystemFlowStep(BaseModel):
    """One step in the system's operation flow."""
    step_number: int
    action: str = Field(..., description="What happens at this step")
    actor: str = Field(..., description="Who/what performs this action")
    explanation: str = Field(
        default="",
        description="Simple explanation of this step"
    )


class SystemFlow(BaseModel):
    """
    Step-by-step explanation of how the system works.
    
    Example: User → Login → Input Idea → AI Analysis → Blueprint Output
    
    This is exactly what students need for documentation and viva.
    """
    flow_title: str
    steps: List[SystemFlowStep]
    summary: str = Field(
        default="",
        description="One-paragraph summary of the entire flow"
    )


class TechStackItem(BaseModel):
    """A technology recommendation with justification."""
    category: str = Field(
        ...,
        description="What role does this play? (frontend, backend, database, etc.)"
    )
    technology: str = Field(
        ...,
        description="Name of the recommended technology"
    )
    justification: str = Field(
        ...,
        description="Why this technology is suitable for this project"
    )
    skill_level: str = Field(
        default="Beginner-friendly",
        description="What skill level is needed?"
    )


class ArchitectureOverview(BaseModel):
    """High-level explanation of system architecture."""
    overview: str = Field(
        ...,
        description="Simple explanation of how parts work together"
    )
    modules: List[str] = Field(
        ...,
        description="Main modules/components in the system"
    )
    data_flow: str = Field(
        ...,
        description="How data moves through the system"
    )
    diagram_description: str = Field(
        default="",
        description="Text description of architecture diagram"
    )


class VivaQuestion(BaseModel):
    """A viva question with its suggested answer."""
    question: str
    suggested_answer: str
    why_asked: str = Field(
        default="",
        description="Why examiners commonly ask this"
    )


class VivaGuide(BaseModel):
    """
    Everything a student needs to prepare for viva.
    
    This section is GOLD for nervous students. It tells them
    exactly what to expect and how to answer confidently.
    """
    project_overview_explanation: str
    problem_statement_explanation: str
    architecture_explanation: str
    unique_feature_explanation: str
    common_questions: List[VivaQuestion]


class Pitch(BaseModel):
    """Project pitches for different time limits."""
    thirty_second_pitch: str
    one_minute_pitch: str
    key_points: List[str] = Field(
        default=[],
        description="Bullet points to remember"
    )


class Blueprint(BaseModel):
    """
    The COMPLETE project blueprint - the main output of this system.
    
    This contains everything a student needs to:
    - Understand their project fully
    - Explain it confidently in viva
    - Start implementation with clarity
    - Create documentation
    """
    # Project Identity
    project_title: str
    project_subtitle: str
    abstract: str
    
    # Understanding
    idea_summary: str
    expanded_idea: Optional["IdeaExpanded"] = None
    evaluation: Optional[IdeaEvaluation] = None
    
    # Features
    features: List[Feature] = Field(default=[])
    feature_tradeoffs: List[FeatureTradeOff] = Field(default=[])
    
    # Technical Design
    system_flow: Optional[SystemFlow] = None
    tech_stack: List[TechStackItem] = Field(default=[])
    architecture: Optional[ArchitectureOverview] = None
    
    # Flowcharts (Mermaid syntax)
    user_flow_mermaid: str = Field(default="")
    tech_stack_mermaid: str = Field(default="")
    
    # Presentation
    viva_guide: Optional[VivaGuide] = None
    pitch: Optional[Pitch] = None
    
    # Metadata
    limitations: List[str] = Field(default=[])
    future_scope: List[str] = Field(default=[])
    
    class Config:
        # Allow the model to be built in stages
        validate_assignment = True


# Import for forward reference resolution
from app.schemas.idea import IdeaExpanded
Blueprint.model_rebuild()

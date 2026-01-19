"""
Blueprint Normalizer - Safe Output Processing Layer
====================================================

This module ensures all AI responses are properly structured
before reaching the UI, regardless of which provider generated them.

RESPONSIBILITIES:
1. Ensure all expected keys exist
2. Fill missing strings with safe defaults
3. Replace missing arrays with empty arrays
4. Prevent undefined access in UI
5. Make Gemini / GPT / Groq outputs interchangeable

IMPORTANT:
- ALL AI blueprint responses must pass through normalize_blueprint()
- UI must consume ONLY normalized output
"""

from typing import Dict, Any, List


def normalize_blueprint(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw blueprint from any AI provider.
    
    Ensures all expected keys exist with safe defaults.
    This is the critical layer that makes provider switching invisible to the UI.
    
    Args:
        raw: Raw blueprint dict from AI (may be partial or malformed)
    
    Returns:
        Fully normalized blueprint with all required keys
    """
    if not raw or not isinstance(raw, dict):
        return get_fallback_blueprint()
    
    return {
        "summary": _normalize_summary(raw.get("summary", {})),
        "features": _normalize_features(raw.get("features", {})),
        "feasibility": _normalize_feasibility(raw.get("feasibility", {})),
        "system_flow": _normalize_system_flow(raw.get("system_flow", {})),
        "tech_stack": _normalize_tech_stack(raw.get("tech_stack", {})),
        "comparison": _normalize_comparison(raw.get("comparison", {})),
        "viva": _normalize_viva(raw.get("viva", {})),
        "pitch": _normalize_pitch(raw.get("pitch", {})),
        "diagrams": _normalize_diagrams(raw.get("diagrams", {}))
    }


def _safe_string(value: Any, default: str = "Not provided by AI") -> str:
    """Ensure value is a non-empty string."""
    if value and isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _safe_list(value: Any, default: List = None) -> List:
    """Ensure value is a list."""
    if default is None:
        default = []
    if isinstance(value, list):
        return value
    return default


def _normalize_summary(data: Dict) -> Dict:
    """Normalize the summary section."""
    if not isinstance(data, dict):
        data = {}
    
    return {
        "problem_statement": _safe_string(data.get("problem_statement")),
        "target_users": _safe_list(data.get("target_users"), ["Users"]),
        "objectives": _safe_list(data.get("objectives"), ["Complete the project"]),
        "scope": _safe_string(data.get("scope"), "Defined by project requirements"),
        "what_this_means": _safe_string(data.get("what_this_means"), "This section explains your project's purpose"),
        "why_this_matters": _safe_string(data.get("why_this_matters"), "Understanding this helps you explain your project clearly")
    }


def _normalize_features(data: Dict) -> Dict:
    """Normalize the features section."""
    if not isinstance(data, dict):
        data = {}
    
    features_list = data.get("features", [])
    if not isinstance(features_list, list):
        features_list = []
    
    normalized_features = []
    for f in features_list:
        if isinstance(f, dict):
            normalized_features.append({
                "feature_name": _safe_string(f.get("feature_name"), "Feature"),
                "what_it_does": _safe_string(f.get("what_it_does"), "Provides functionality to users"),
                "why_it_exists": _safe_string(f.get("why_it_exists"), "Addresses a user need"),
                "how_it_helps": _safe_string(f.get("how_it_helps"), "Improves user experience"),
                "limitations": _safe_string(f.get("limitations"), "None specified")
            })
    
    # Ensure at least one feature
    if not normalized_features:
        normalized_features = [{
            "feature_name": "Core Feature",
            "what_it_does": "Provides the main functionality",
            "why_it_exists": "To solve the core problem",
            "how_it_helps": "Delivers value to users",
            "limitations": "Specific limitations depend on implementation"
        }]
    
    return {"features": normalized_features}


def _normalize_feasibility(data: Dict) -> Dict:
    """Normalize the feasibility section."""
    if not isinstance(data, dict):
        data = {}
    
    level = data.get("feasibility_level", "Medium")
    if level not in ["High", "Medium", "Low"]:
        level = "Medium"
    
    return {
        "feasibility_level": level,
        "feasibility_explanation": _safe_string(data.get("feasibility_explanation"), "This project is achievable for a college student"),
        "strengths": _safe_list(data.get("strengths"), ["Good educational value"]),
        "risks": _safe_list(data.get("risks"), ["Time management is important"]),
        "why_this_matters": _safe_string(data.get("why_this_matters"), "Knowing feasibility helps you plan realistically")
    }


def _normalize_system_flow(data: Dict) -> Dict:
    """Normalize the system flow section."""
    if not isinstance(data, dict):
        data = {}
    
    steps = data.get("steps", [])
    if not isinstance(steps, list):
        steps = []
    
    normalized_steps = []
    for i, step in enumerate(steps):
        if isinstance(step, dict):
            normalized_steps.append({
                "step_number": step.get("step_number", i + 1),
                "actor": _safe_string(step.get("actor"), "User"),
                "action": _safe_string(step.get("action"), "Performs action"),
                "explanation": _safe_string(step.get("explanation"), "Part of the workflow")
            })
    
    # Ensure at least basic steps
    if not normalized_steps:
        normalized_steps = [
            {"step_number": 1, "actor": "User", "action": "Opens application", "explanation": "Entry point"},
            {"step_number": 2, "actor": "System", "action": "Processes request", "explanation": "Core processing"},
            {"step_number": 3, "actor": "System", "action": "Returns result", "explanation": "Output to user"}
        ]
    
    return {
        "flow_title": _safe_string(data.get("flow_title"), "System Flow"),
        "steps": normalized_steps,
        "summary": _safe_string(data.get("summary"), "This flow shows how users interact with the system")
    }


def _normalize_tech_stack(data: Dict) -> Dict:
    """Normalize the tech stack section."""
    if not isinstance(data, dict):
        data = {}
    
    # Handle primary stack
    primary = data.get("primary_stack", [])
    if not isinstance(primary, list):
        primary = []
    
    normalized_primary = []
    for item in primary:
        if isinstance(item, dict):
            normalized_primary.append({
                "category": _safe_string(item.get("category"), "General"),
                "technology": _safe_string(item.get("technology"), "Technology"),
                "justification": _safe_string(item.get("justification"), "Suitable for this project"),
                "skill_level": _safe_string(item.get("skill_level"), "Beginner-friendly")
            })
    
    # Handle backup stack
    backup = data.get("backup_stack", [])
    if not isinstance(backup, list):
        backup = []
    
    normalized_backup = []
    for item in backup:
        if isinstance(item, dict):
            normalized_backup.append({
                "category": _safe_string(item.get("category"), "General"),
                "technology": _safe_string(item.get("technology"), "Alternative"),
                "why_backup": _safe_string(item.get("why_backup"), "Alternative option if needed")
            })
    
    # Ensure at least basic stack
    if not normalized_primary:
        normalized_primary = [
            {"category": "Frontend", "technology": "HTML/CSS/JavaScript", "justification": "Universal web technologies", "skill_level": "Beginner-friendly"},
            {"category": "Backend", "technology": "Python or Node.js", "justification": "Common choices for web apps", "skill_level": "Beginner-friendly"},
            {"category": "Database", "technology": "MySQL or MongoDB", "justification": "Well-documented options", "skill_level": "Beginner-friendly"}
        ]
    
    return {
        "primary_stack": normalized_primary,
        "backup_stack": normalized_backup
    }


def _normalize_comparison(data: Dict) -> Dict:
    """Normalize the comparison section."""
    if not isinstance(data, dict):
        data = {}
    
    # Handle existing solutions
    solutions = data.get("existing_solutions", [])
    if not isinstance(solutions, list):
        solutions = []
    
    normalized_solutions = []
    for sol in solutions:
        if isinstance(sol, dict):
            normalized_solutions.append({
                "solution_name": _safe_string(sol.get("solution_name"), "Existing Solution"),
                "what_it_does": _safe_string(sol.get("what_it_does"), "Provides similar functionality"),
                "limitations": _safe_string(sol.get("limitations"), "May not fit specific needs")
            })
    
    return {
        "existing_solutions": normalized_solutions,
        "unique_aspects": _safe_list(data.get("unique_aspects"), ["Custom solution for specific needs"]),
        "why_this_project_is_still_valuable": _safe_list(
            data.get("why_this_project_is_still_valuable") or data.get("why_still_valuable"), 
            ["Learning experience", "Tailored to specific requirements"]
        ),
        "summary_insight": _safe_string(
            data.get("summary_insight"), 
            "Even though similar systems exist, this project provides valuable learning and customization opportunities."
        )
    }


def _normalize_viva(data: Dict) -> Dict:
    """Normalize the viva preparation section."""
    if not isinstance(data, dict):
        data = {}
    
    # Handle common questions
    common_qs = data.get("common_questions", [])
    if not isinstance(common_qs, list):
        common_qs = []
    
    normalized_common = []
    for q in common_qs:
        if isinstance(q, dict):
            normalized_common.append({
                "question": _safe_string(q.get("question"), "Question"),
                "suggested_answer": _safe_string(q.get("suggested_answer"), "Provide a clear, concise answer"),
                "why_asked": _safe_string(q.get("why_asked"), "To assess your understanding")
            })
    
    # Handle hackathon questions
    hackathon_qs = data.get("hackathon_questions", [])
    if not isinstance(hackathon_qs, list):
        hackathon_qs = []
    
    normalized_hackathon = []
    for q in hackathon_qs:
        if isinstance(q, dict):
            normalized_hackathon.append({
                "question": _safe_string(q.get("question"), "Question"),
                "suggested_response": _safe_string(q.get("suggested_response"), "Provide a confident response"),
                "key_points": _safe_list(q.get("key_points"), ["Focus on value delivered"])
            })
    
    # Ensure at least one question each
    if not normalized_common:
        normalized_common = [
            {"question": "Why did you choose this project?", "suggested_answer": "It solves a real problem I observed", "why_asked": "Tests motivation"},
            {"question": "What challenges did you face?", "suggested_answer": "Learning new technologies and time management", "why_asked": "Tests problem-solving"}
        ]
    
    if not normalized_hackathon:
        normalized_hackathon = [
            {"question": "What makes this unique?", "suggested_response": "Tailored to specific user needs", "key_points": ["User focus", "Practical value"]}
        ]
    
    return {
        "project_overview_explanation": _safe_string(data.get("project_overview_explanation"), "This project solves a real problem using modern technology"),
        "problem_statement_explanation": _safe_string(data.get("problem_statement_explanation"), "The problem affects users in their daily workflow"),
        "architecture_explanation": _safe_string(data.get("architecture_explanation"), "The system uses a standard three-tier architecture"),
        "unique_feature_explanation": _safe_string(data.get("unique_feature_explanation"), "What makes this project special is its focus on the user experience"),
        "common_questions": normalized_common,
        "hackathon_questions": normalized_hackathon
    }


def _normalize_pitch(data: Dict) -> Dict:
    """Normalize the pitch section."""
    if not isinstance(data, dict):
        data = {}
    
    return {
        "thirty_second_pitch": _safe_string(
            data.get("thirty_second_pitch"), 
            "This project solves a real problem by providing an efficient digital solution. It saves time, reduces errors, and improves the user experience."
        ),
        "one_minute_pitch": _safe_string(
            data.get("one_minute_pitch"),
            "Every day, users face challenges with manual processes. This project automates those processes, providing a faster, more reliable solution. Built with modern technologies, it's designed to be user-friendly and scalable. The system is ideal for educational or organizational settings where efficiency matters."
        ),
        "key_points": _safe_list(data.get("key_points"), ["Solves real problem", "Saves time", "User-friendly"])
    }


def _normalize_diagrams(data: Dict) -> Dict:
    """Normalize the diagrams section."""
    if not isinstance(data, dict):
        data = {}
    
    # Provide sensible Mermaid defaults
    default_user_flow = """flowchart TD
    A[User Opens App] --> B{Login Required?}
    B -->|Yes| C[Login Page]
    B -->|No| D[Dashboard]
    C --> E[Enter Credentials]
    E --> F{Valid?}
    F -->|No| C
    F -->|Yes| D
    D --> G[Use Features]
    G --> H[Complete Task]"""
    
    default_tech_stack = """flowchart LR
    subgraph Frontend
        A[Web Interface]
    end
    subgraph Backend
        B[API Server]
    end
    subgraph Database
        C[(Data Storage)]
    end
    A -->|HTTP| B
    B -->|Queries| C"""
    
    return {
        "user_flow_mermaid": _safe_string(data.get("user_flow_mermaid"), default_user_flow),
        "tech_stack_mermaid": _safe_string(data.get("tech_stack_mermaid"), default_tech_stack)
    }


def get_fallback_blueprint() -> Dict[str, Any]:
    """
    Return a complete fallback blueprint when AI completely fails.
    
    This ensures the UI never crashes, even if all providers are down.
    """
    return {
        "summary": _normalize_summary({}),
        "features": _normalize_features({}),
        "feasibility": _normalize_feasibility({}),
        "system_flow": _normalize_system_flow({}),
        "tech_stack": _normalize_tech_stack({}),
        "comparison": _normalize_comparison({}),
        "viva": _normalize_viva({}),
        "pitch": _normalize_pitch({}),
        "diagrams": _normalize_diagrams({})
    }


def map_to_frontend_format(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map normalized blueprint to the format expected by existing frontend.
    
    This handles the key naming differences between the new master prompt
    output and what the existing UI expects.
    
    Args:
        normalized: Output from normalize_blueprint()
    
    Returns:
        Dict matching existing appState.blueprint structure
    """
    return {
        # Summary → expandedIdea mapping (for backward compat)
        "expandedIdea": {
            "problem_statement": normalized["summary"]["problem_statement"],
            "target_users": normalized["summary"]["target_users"],
            "objectives": normalized["summary"]["objectives"],
            "scope": normalized["summary"]["scope"],
            "what_this_means": normalized["summary"]["what_this_means"],
            "why_this_matters": normalized["summary"]["why_this_matters"]
        },
        
        # Direct mappings to blueprint object
        "evaluation": normalized["feasibility"],
        "featuresDetailed": normalized["features"],
        "systemFlow": normalized["system_flow"],
        
        # Tech stack - need to map to old format
        "techStack": normalized["tech_stack"]["primary_stack"],
        "techStackExtended": {
            "primary_stack": normalized["tech_stack"]["primary_stack"],
            "alternatives": normalized["tech_stack"]["backup_stack"]
        },
        
        # Comparison
        "comparison": normalized["comparison"],
        
        # Viva guide - map to old format
        "vivaGuide": {
            "project_overview_explanation": normalized["viva"]["project_overview_explanation"],
            "problem_statement_explanation": normalized["viva"]["problem_statement_explanation"],
            "architecture_explanation": normalized["viva"]["architecture_explanation"],
            "unique_feature_explanation": normalized["viva"]["unique_feature_explanation"],
            "common_questions": normalized["viva"]["common_questions"]
        },
        "hackathonViva": {
            "viva_questions": normalized["viva"]["common_questions"],
            "hackathon_questions": normalized["viva"]["hackathon_questions"]
        },
        
        # Pitch
        "pitch": normalized["pitch"],
        
        # Diagrams
        "userFlowMermaid": normalized["diagrams"]["user_flow_mermaid"],
        "techStackMermaid": normalized["diagrams"]["tech_stack_mermaid"]
    }

"""
Planner Service - Core Project Planning Logic
==============================================

This is the brain of the planning system. It uses the LLM service
to generate all planning content: idea expansion, evaluation,
trade-offs, flows, viva guides, and pitches.

All prompts are carefully designed to:
1. NEVER ask for code
2. Use simple, student-friendly language
3. Include educational context
4. Be explainable in viva
"""

import json
from typing import Dict, List, Optional, Any
from app.services.llm_service import llm_service
from app.schemas import (
    IdeaExpanded, IdeaEvaluation, FeatureTradeOff,
    SystemFlow, SystemFlowStep, TechStackItem,
    ArchitectureOverview, VivaGuide, VivaQuestion, Pitch,
    Feature, FeatureCategory, FeasibilityLevel
)


class PlannerService:
    """
    Service for generating project planning content.
    
    This service orchestrates all planning operations:
    - Takes user input
    - Sends appropriate prompts to the LLM
    - Parses and structures the responses
    - Returns clean, usable data
    """
    
    # ===========================================
    # PROMPT TEMPLATES
    # ===========================================
    # These are carefully crafted to produce planning content,
    # never code. Each prompt is educational in nature.
    
    EXPAND_IDEA_PROMPT = """You are a helpful project mentor for college students.

A student has shared their project idea. Your job is to help them understand it better by expanding it into a structured format.

STUDENT'S IDEA: {idea}

Please analyze this idea and provide:

1. **Problem Statement**: A clear 2-3 sentence statement of what problem this project solves
2. **Target Users**: List of people who would use this system (e.g., students, teachers, administrators)
3. **Objectives**: 3-5 clear, achievable goals for this project
4. **Scope**: What IS included in this project, and what is NOT included (to keep it manageable)
5. **What This Means**: A simple explanation a beginner would understand
6. **Why This Matters**: Why understanding this structure is important for the student

Remember:
- Use simple language suitable for 1st/2nd year students
- Be realistic about what's achievable in a college project
- Focus on planning, not implementation details

Respond in JSON format with keys: problem_statement, target_users (array), objectives (array), scope, what_this_means, why_this_matters"""

    EVALUATE_IDEA_PROMPT = """You are an honest project mentor for college students.

A student wants to know if their project idea is feasible. Be honest but encouraging.

PROJECT IDEA: {idea}
EXPANDED DETAILS: {details}

Please evaluate this idea and provide:

1. **Strengths**: 3-5 things that work well about this idea
2. **Risks**: 3-5 potential challenges or risks to be aware of
3. **Feasibility Level**: High, Medium, or Low (for a college student project)
4. **Feasibility Explanation**: Why you gave this rating, in simple terms
5. **What This Means**: Simple explanation of the evaluation
6. **Why This Matters**: Why knowing feasibility early is important

Be honest:
- If something is too complex for beginners, say so kindly
- If something is very achievable, be encouraging
- Don't just list generic risks - be specific to THIS project

Respond in JSON format with keys: strengths (array), risks (array), feasibility_level (High/Medium/Low), feasibility_explanation, what_this_means, why_this_matters"""

    FEATURE_TRADEOFF_PROMPT = """You are a project mentor helping a student understand feature trade-offs.

The student wants to add this feature to their project and needs to understand its impact.

PROJECT: {project_summary}
FEATURE TO ANALYZE: {feature}

Explain the trade-offs of adding this feature:

1. **Complexity Impact**: How does this affect overall project complexity?
2. **Time Impact**: How much extra development time will this need?
3. **Architecture Impact**: What changes to the system design are required?
4. **Recommendation**: Should they include it? Why or why not?
5. **What This Means**: Simple summary for a beginner

Be realistic:
- Consider a typical college student's skill level
- Consider typical project timelines (2-3 months)
- If it's too advanced, suggest simpler alternatives

Respond in JSON format with keys: feature_name, complexity_impact, time_impact, architecture_impact, recommendation, what_this_means"""

    SYSTEM_FLOW_PROMPT = """You are a project mentor helping a student document their system's workflow.

PROJECT: {project_summary}
KEY FEATURES: {features}

Create a clear, step-by-step system flow that shows how a user would interact with this system.

Provide:
1. **Flow Title**: A clear name for this flow
2. **Steps**: 6-10 numbered steps, each with:
   - Step number
   - Actor (who performs this action - User, System, Admin, etc.)
   - Action (what happens)
   - Explanation (why this step matters)
3. **Summary**: One paragraph explaining the entire flow

Make it:
- Simple enough for a beginner to understand
- Detailed enough to use in documentation
- Logical and realistic

Respond in JSON format with keys: flow_title, steps (array of objects with step_number, actor, action, explanation), summary"""

    TECH_STACK_PROMPT = """You are a project mentor recommending technologies for a college student's project.

PROJECT: {project_summary}
KEY FEATURES: {features}
STUDENT LEVEL: Beginner to Intermediate (1st/2nd year college)

Recommend a simple, appropriate tech stack:

For each technology, provide:
1. **Category**: What it's for (Frontend, Backend, Database, etc.)
2. **Technology**: Specific technology name
3. **Justification**: Why this is suitable (keep it simple!)
4. **Skill Level**: Is this beginner-friendly?

Guidelines:
- Prefer well-documented, popular technologies
- Consider what students typically learn in college
- Avoid overly complex or new technologies
- Keep the stack minimal - don't over-engineer

Respond in JSON format with keys: tech_stack (array of objects with category, technology, justification, skill_level)"""

    ARCHITECTURE_PROMPT = """You are a project mentor explaining system architecture to a college student.

PROJECT: {project_summary}
TECH STACK: {tech_stack}
FEATURES: {features}

Explain the architecture in simple terms:

1. **Overview**: 2-3 sentence explanation of how the system is organized
2. **Modules**: List the main modules/components (5-7 max)
3. **Data Flow**: How does data move through the system?
4. **Diagram Description**: Describe what an architecture diagram would show

Remember:
- Use simple language - imagine explaining to someone who's never built a system before
- Focus on the "what" and "why", not the "how to code it"
- This should be explainable in a viva

Respond in JSON format with keys: overview, modules (array), data_flow, diagram_description"""

    VIVA_GUIDE_PROMPT = """You are a project mentor helping a student prepare for their project viva.

PROJECT: {project_summary}
FEATURES: {features}
TECH STACK: {tech_stack}
ARCHITECTURE: {architecture}

Create a comprehensive viva preparation guide:

1. **Project Overview Explanation**: How to explain the project in 30 seconds
2. **Problem Statement Explanation**: How to explain the problem being solved
3. **Architecture Explanation**: How to explain the technical design simply
4. **Unique Feature Explanation**: How to highlight what makes this project special
5. **Common Questions**: 5-7 questions examiners typically ask, with:
   - The question
   - A suggested answer
   - Why examiners ask this

Write in a way that:
- Builds confidence
- Uses simple language
- Could be memorized and explained naturally
- Shows understanding, not just memorization

Respond in JSON format with keys: project_overview_explanation, problem_statement_explanation, architecture_explanation, unique_feature_explanation, common_questions (array of objects with question, suggested_answer, why_asked)"""

    PITCH_PROMPT = """You are a project mentor helping a student create compelling project pitches.

PROJECT: {project_summary}
PROBLEM: {problem}
KEY FEATURES: {features}
UNIQUE ASPECTS: {unique_aspects}

Create two pitches:

1. **30-Second Pitch**: Quick, memorable, gets attention
2. **1-Minute Pitch**: More detailed, covers problem-solution-impact
3. **Key Points**: 4-5 bullet points to remember

The pitches should:
- Sound natural and confident
- Be appropriate for a student (not corporate)
- Highlight the problem solved
- Mention key features briefly
- End with impact or future potential

Respond in JSON format with keys: thirty_second_pitch, one_minute_pitch, key_points (array)"""

    FEATURES_PROMPT = """You are a project mentor helping a student understand their app's features.

PROJECT SUMMARY: {project_summary}
PROBLEM BEING SOLVED: {problem}

List all major features of this application. For EACH feature, explain:

1. **Feature Name**: Clear, descriptive name
2. **What It Does**: Simple explanation of the functionality
3. **Why It Exists**: The user problem or need it addresses
4. **How It Helps Students**: Practical benefit for the target users
5. **Limitations**: Any constraints or edge cases (if applicable)

Guidelines:
- Focus on WHAT the feature does, NOT how it's implemented
- Use simple language for 1st/2nd year students
- Be specific to THIS project, not generic features
- Include 5-8 main features

Respond in JSON format with key: features (array of objects with feature_name, what_it_does, why_it_exists, how_it_helps, limitations)"""

    COMPARISON_PROMPT = """You are a project mentor helping a student understand how their idea compares to existing solutions.

STUDENT'S PROJECT IDEA: {project_summary}
KEY FEATURES: {features}
PROBLEM BEING SOLVED: {problem}

Help the student understand their project in context:

**SECTION A - Existing Solutions**
Identify 2-4 existing real-world systems that solve a SIMILAR problem to the student's idea.
For EACH existing solution, provide:
- Solution name/type (generic, not branded)
- What it does (core functionality)
- Common features found in such systems
- Limitations or gaps (especially for students, small scale, college use)

**SECTION B - How the Student's Idea is Different**
Based on the student's features and approach, explain:
- Unique aspects in the student's idea
- Improvements over existing solutions
- Why this project is still worth building

**SECTION C - Summary Insight**
Provide a confident conclusion the student can use to answer:
"This already exists — why did you build it?"

Rules:
- Be factual and neutral about existing solutions
- No criticism or negative tone
- Focus on the STUDENT'S IDEA, not any platform
- This is for learning, not market analysis

Respond in JSON format with keys: 
- existing_solutions (array of objects with solution_name, what_it_does, common_features, limitations)
- unique_aspects (array of strings)
- why_still_valuable (array of strings)
- summary_insight (string - confident conclusion for viva)"""

    HACKATHON_VIVA_PROMPT = """You are a project mentor preparing a student for viva AND hackathon presentations.

PROJECT: {project_summary}
FEATURES: {features}
TECH STACK: {tech_stack}
UNIQUE ASPECTS: {unique_aspects}

Create comprehensive preparation material:

**PART A - Standard Viva Questions** (5-7 questions)
For each question, provide:
- The question examiners typically ask
- A suggested answer (understanding-based, not memorized)
- Why examiners ask this

Include questions like:
- Why did you choose this problem?
- What are the limitations?
- How can this be improved?
- Why this tech stack?

**PART B - Hackathon-Specific Questions** (5-7 questions)
Questions commonly asked at hackathons:
- What makes your solution unique?
- How is this scalable?
- What did you learn building this?
- What would you do with more time/resources?
- How does AI help here responsibly?
- Who are your users and how did you validate the need?
- What's your biggest technical challenge and how did you solve it?

For each, provide:
- The question
- A suggested response approach
- Key points to emphasize

Rules:
- Focus on understanding, not memorization
- Answers should sound natural
- Build confidence, not scripts

Respond in JSON format with keys:
- viva_questions (array of objects with question, suggested_answer, why_asked)
- hackathon_questions (array of objects with question, suggested_response, key_points)"""

    TECH_STACK_EXTENDED_PROMPT = """You are a project mentor recommending and explaining technologies for a college student's project.

PROJECT: {project_summary}
KEY FEATURES: {features}
STUDENT LEVEL: Beginner to Intermediate (1st/2nd year college)

For EACH technology, provide comprehensive explanation:

**PRIMARY TECHNOLOGY STACK**
For each category (Frontend, Backend, Database, AI/LLM, etc.), provide:
- Technology name
- What it is (simple 1-2 sentence explanation)
- Why it's used in this project (specific reason)
- What role it plays (how it fits in the system)
- Skill level required (Beginner/Intermediate)

**BACKUP / ALTERNATIVE OPTIONS**
For each critical technology, also suggest:
- One alternative option
- When to consider switching (e.g., cost, availability, skill)
- Brief comparison

Categories to cover:
- Frontend framework
- Backend framework  
- Database
- AI/LLM service
- Diagram generation
- Hosting (if applicable)

Rules:
- Use well-documented, popular technologies
- Prefer what students typically learn in college
- Keep it minimal - don't over-engineer
- Explain in simple terms
- Backups are conceptual, not migration guides

Respond in JSON format with keys:
- primary_stack (array of objects with category, technology, what_it_is, why_used, role, skill_level)
- alternatives (array of objects with category, primary, alternative, when_to_switch)"""

    CHAT_MENTOR_PROMPT = """You are a helpful project mentor for college students.
You are helping the student clarify and refine their project idea through conversation.

STUDENT'S ORIGINAL IDEA: {raw_idea}

CONVERSATION SO FAR:
{chat_history}

STUDENT'S LATEST MESSAGE: {user_message}

Guidelines:
- Respond conversationally and encouragingly
- Ask clarifying questions when the idea is vague
- Suggest options WITHOUT deciding for the student
- Explain trade-offs in simple terms
- Do NOT finalize scope or features unless the student explicitly confirms
- Do NOT say "your blueprint is ready" or similar
- Keep responses concise (2-4 sentences typically)

Based on the conversation, also maintain a DRAFT SUMMARY that evolves as you learn more.
This is NOT final - just to track understanding.

Respond in JSON format with keys:
- ai_response (your conversational response to the student)
- draft_summary (object with: problem_statement, target_users, main_features (array), scope_notes)
- is_ready_to_finalize (boolean - true only if student has confirmed enough details)
- suggested_next_question (optional - what to explore next)"""

    REVISION_PROMPT = """You are revising a project summary based on student feedback.

CURRENT PROJECT SUMMARY:
Problem Statement: {problem_statement}
Target Users: {target_users}
Main Features: {features}
Scope: {scope}

STUDENT'S REQUESTED CHANGE:
{change_request}

Your task:
1. Interpret what the student wants to change
2. Revise the summary to reflect ONLY these changes
3. Do NOT introduce new features or ideas unless explicitly requested
4. Keep the rest of the summary intact

Also determine the CHANGE TYPE:
- "feature" = adding, removing, or modifying features
- "tech" = changing technology choices
- "scope" = expanding or reducing overall scope
- "wording" = minor text adjustments only

Respond in JSON format with keys:
- updated_summary (object with: problem_statement, target_users, main_features, scope_notes)
- change_type (one of: feature, tech, scope, wording)
- change_description (brief explanation of what was changed)
- sections_affected (array of section names that need regeneration)"""

    # ===========================================
    # MASTER BLUEPRINT PROMPT (SINGLE-CALL)
    # ===========================================
    # This prompt generates ALL 9 blueprint sections in ONE response.
    # Used for Quick Blueprint mode and post-Interactive finalization.
    
    MASTER_BLUEPRINT_PROMPT = """You are a helpful AI project mentor for college students.
Your role is to help students plan and explain software projects clearly.
This is a planning task only — do NOT generate code.

STUDENT CONTEXT
Mode: {mode}

Project Idea / Finalized Summary:
{summary_text}

OUTPUT FORMAT (MANDATORY)

Respond ONLY with valid JSON.
Do NOT include markdown code blocks (no ```).
Do NOT include explanations outside JSON.
Return raw JSON only.

Generate a COMPLETE project blueprint with ALL of the following sections.
Each section must be thorough but beginner-friendly.
Use simple language suitable for 1st/2nd year college students.

Return exactly this structure:

{{
  "summary": {{
    "problem_statement": "Clear 2-3 sentence statement of the problem this project solves",
    "target_users": ["User type 1", "User type 2"],
    "objectives": ["Objective 1", "Objective 2", "Objective 3"],
    "scope": "What IS and is NOT included in this project",
    "what_this_means": "Simple explanation for beginners",
    "why_this_matters": "Why understanding this is important"
  }},
  "features": {{
    "features": [
      {{
        "feature_name": "Clear feature name",
        "what_it_does": "Simple explanation of functionality",
        "why_it_exists": "The user need it addresses",
        "how_it_helps": "Practical benefit for users",
        "limitations": "Any constraints (or 'None' if minimal)"
      }}
    ]
  }},
  "feasibility": {{
    "feasibility_level": "High or Medium or Low",
    "feasibility_explanation": "Why this rating, in simple terms",
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "risks": ["Risk 1", "Risk 2", "Risk 3"],
    "why_this_matters": "Why knowing feasibility early is important"
  }},
  "system_flow": {{
    "flow_title": "Clear name for this flow",
    "steps": [
      {{
        "step_number": 1,
        "actor": "User or System or Admin",
        "action": "What happens at this step",
        "explanation": "Why this step matters"
      }}
    ],
    "summary": "One paragraph explaining the entire flow"
  }},
  "tech_stack": {{
    "primary_stack": [
      {{
        "category": "Frontend or Backend or Database or etc",
        "technology": "Specific technology name",
        "justification": "Why this is suitable",
        "skill_level": "Beginner-friendly or Intermediate"
      }}
    ],
    "backup_stack": [
      {{
        "category": "Category name",
        "technology": "Alternative technology",
        "why_backup": "When to consider switching"
      }}
    ]
  }},
  "comparison": {{
    "existing_solutions": [
      {{
        "solution_name": "Generic name (not branded)",
        "what_it_does": "Core functionality",
        "limitations": "Gaps especially for students"
      }}
    ],
    "unique_aspects": ["What makes this project different 1", "Aspect 2"],
    "why_this_project_is_still_valuable": ["Reason 1", "Reason 2"],
    "summary_insight": "Confident conclusion for viva: why build this even though similar exists"
  }},
  "viva": {{
    "project_overview_explanation": "How to explain project in 30 seconds",
    "problem_statement_explanation": "How to explain the problem being solved",
    "architecture_explanation": "How to explain technical design simply",
    "unique_feature_explanation": "What makes this project special",
    "common_questions": [
      {{
        "question": "Question examiners typically ask",
        "suggested_answer": "Natural, understanding-based answer",
        "why_asked": "Why examiners ask this"
      }}
    ],
    "hackathon_questions": [
      {{
        "question": "Hackathon-style question",
        "suggested_response": "Confident response approach",
        "key_points": ["Key point 1", "Key point 2"]
      }}
    ]
  }},
  "pitch": {{
    "thirty_second_pitch": "Quick, memorable pitch that gets attention",
    "one_minute_pitch": "Detailed pitch covering problem-solution-impact",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"]
  }},
  "diagrams": {{
    "user_flow_mermaid": "Mermaid flowchart TD syntax showing user journey - plain text only, no backticks",
    "tech_stack_mermaid": "Mermaid flowchart LR syntax showing tech architecture - plain text only, no backticks"
  }}
}}

GUIDELINES:
- Generate 5-8 features
- Generate 6-10 system flow steps
- Generate 5-7 viva questions
- Generate 3-5 hackathon questions
- Include 2-4 existing solutions for comparison
- Tech stack should have 4-6 primary technologies
- Mermaid diagrams should start with 'flowchart TD' or 'flowchart LR' - NO markdown code blocks around them
- All explanations should be simple enough for beginners
- Focus on WHAT and WHY, never on HOW to code it
- Tone: Mentor helping a student, not authority lecturing"""

    def __init__(self):
        """Initialize the planner service."""
        self.llm = llm_service
        # Import normalizer for full blueprint generation
        from app.services.normalizer import normalize_blueprint, map_to_frontend_format
        self.normalize_blueprint = normalize_blueprint
        self.map_to_frontend_format = map_to_frontend_format
    
    # ===========================================
    # NEW: SINGLE-CALL BLUEPRINT GENERATION
    # ===========================================
    
    async def generate_full_blueprint(
        self,
        summary_text: str,
        mode: str = "QUICK_BLUEPRINT"
    ) -> Dict[str, Any]:
        """
        Generate complete blueprint in a single LLM call.
        
        This is the new unified generation method that replaces
        10+ sequential API calls with ONE call.
        
        Args:
            summary_text: Raw idea (quick mode) or finalized summary (interactive mode)
            mode: "QUICK_BLUEPRINT" or "INTERACTIVE_FINALIZED"
        
        Returns:
            Dict with:
            - success: bool
            - blueprint: Normalized blueprint object (matches frontend structure)
            - provider_used: Which AI provider was used
            - error: Error message if failed
        """
        prompt = self.MASTER_BLUEPRINT_PROMPT.format(
            mode=mode,
            summary_text=summary_text
        )
        
        result = await self.llm.generate_json_with_fallback(
            prompt, 
            temperature=0.7, 
            max_tokens=8192
        )
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate blueprint"),
                "provider_used": result.get("provider_used")
            }
        
        # Normalize the raw output to ensure all keys exist
        raw_blueprint = result["content"]
        
        # Handle case where content is string (JSON parse failed earlier)
        if isinstance(raw_blueprint, str):
            try:
                raw_blueprint = json.loads(raw_blueprint)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "AI response was not valid JSON",
                    "provider_used": result.get("provider_used")
                }
        
        normalized = self.normalize_blueprint(raw_blueprint)
        frontend_format = self.map_to_frontend_format(normalized)
        
        return {
            "success": True,
            "blueprint": frontend_format,
            "normalized": normalized,  # Keep normalized version too
            "provider_used": result.get("provider_used")
        }
    
    async def regenerate_after_revision(
        self,
        updated_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Regenerate full blueprint after a revision request.
        
        For reliability with free providers, we regenerate the entire
        blueprint rather than attempting partial updates.
        
        Args:
            updated_summary: The revised summary from apply_revision()
        
        Returns:
            Full blueprint generation result
        """
        # Build summary text from updated summary
        summary_text = f"""
Problem Statement: {updated_summary.get('problem_statement', '')}
Target Users: {', '.join(updated_summary.get('target_users', []) if isinstance(updated_summary.get('target_users'), list) else [updated_summary.get('target_users', '')])}
Main Features: {', '.join(updated_summary.get('main_features', []))}
Scope: {updated_summary.get('scope_notes', '')}
"""
        
        return await self.generate_full_blueprint(
            summary_text=summary_text.strip(),
            mode="REVISION_REGENERATION"
        )
    
    async def expand_idea(self, raw_idea: str) -> Dict[str, Any]:
        """
        Transform a vague idea into a structured understanding.
        
        Args:
            raw_idea: The student's raw project idea
        
        Returns:
            Structured idea with problem statement, users, objectives, scope
        """
        prompt = self.EXPAND_IDEA_PROMPT.format(idea=raw_idea)
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to expand idea")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def evaluate_idea(
        self, 
        raw_idea: str, 
        expanded_details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate an idea's strengths, risks, and feasibility.
        
        Args:
            raw_idea: The original idea
            expanded_details: Previously expanded details (optional)
        
        Returns:
            Evaluation with strengths, risks, and feasibility level
        """
        details_str = json.dumps(expanded_details) if expanded_details else "Not available yet"
        
        prompt = self.EVALUATE_IDEA_PROMPT.format(
            idea=raw_idea,
            details=details_str
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to evaluate idea")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def analyze_feature_tradeoff(
        self,
        project_summary: str,
        feature: str
    ) -> Dict[str, Any]:
        """
        Explain the trade-offs of adding a feature.
        
        Args:
            project_summary: Brief description of the project
            feature: The feature to analyze
        
        Returns:
            Trade-off analysis with impacts and recommendation
        """
        prompt = self.FEATURE_TRADEOFF_PROMPT.format(
            project_summary=project_summary,
            feature=feature
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to analyze feature")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_system_flow(
        self,
        project_summary: str,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a step-by-step system flow.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
        
        Returns:
            System flow with numbered steps
        """
        prompt = self.SYSTEM_FLOW_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features)
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate system flow")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def recommend_tech_stack(
        self,
        project_summary: str,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Recommend appropriate technologies for the project.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
        
        Returns:
            Tech stack recommendations with justifications
        """
        prompt = self.TECH_STACK_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features)
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to recommend tech stack")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def explain_architecture(
        self,
        project_summary: str,
        tech_stack: List[Dict],
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Generate architecture explanation.
        
        Args:
            project_summary: Brief description of the project
            tech_stack: Recommended technologies
            features: List of key features
        
        Returns:
            Architecture overview with modules and data flow
        """
        tech_stack_str = ", ".join([t.get("technology", str(t)) for t in tech_stack])
        
        prompt = self.ARCHITECTURE_PROMPT.format(
            project_summary=project_summary,
            tech_stack=tech_stack_str,
            features=", ".join(features)
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to explain architecture")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_viva_guide(
        self,
        project_summary: str,
        features: List[str],
        tech_stack: str,
        architecture: str
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive viva preparation guide.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
            tech_stack: Tech stack summary
            architecture: Architecture overview
        
        Returns:
            Viva guide with explanations and Q&A
        """
        prompt = self.VIVA_GUIDE_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features),
            tech_stack=tech_stack,
            architecture=architecture
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate viva guide")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_pitch(
        self,
        project_summary: str,
        problem: str,
        features: List[str],
        unique_aspects: str
    ) -> Dict[str, Any]:
        """
        Generate 30-second and 1-minute pitches.
        
        Args:
            project_summary: Brief description of the project
            problem: The problem being solved
            features: List of key features
            unique_aspects: What makes this project special
        
        Returns:
            Two pitches and key points
        """
        prompt = self.PITCH_PROMPT.format(
            project_summary=project_summary,
            problem=problem,
            features=", ".join(features),
            unique_aspects=unique_aspects
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate pitch")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_clarifying_questions(self, raw_idea: str) -> Dict[str, Any]:
        """
        Generate questions to better understand the idea.
        
        Used in interactive mode to gather more details.
        
        Args:
            raw_idea: The student's initial idea
        
        Returns:
            List of clarifying questions
        """
        prompt = f"""You are a project mentor helping a student clarify their project idea.

STUDENT'S IDEA: {raw_idea}

Generate 3-5 clarifying questions to better understand what they want to build.

For each question, provide:
1. **question_id**: Unique ID (q1, q2, etc.)
2. **question_text**: The question to ask
3. **context**: Why this question helps (brief)
4. **options**: Suggested answers if applicable (null if open-ended)

Questions should:
- Be simple and non-intimidating
- Help define scope and features
- Understand constraints (time, skill level)
- Be answerable by a beginner student

Respond in JSON format with key: questions (array of question objects)"""
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate questions")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }

    async def generate_features(
        self,
        project_summary: str,
        problem: str
    ) -> Dict[str, Any]:
        """
        Generate detailed feature breakdown for the project.
        
        Args:
            project_summary: Brief description of the project
            problem: The problem being solved
        
        Returns:
            List of features with explanations
        """
        prompt = self.FEATURES_PROMPT.format(
            project_summary=project_summary,
            problem=problem
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate features")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_comparison(
        self,
        project_summary: str,
        features: List[str],
        problem: str
    ) -> Dict[str, Any]:
        """
        Generate comparison with existing solutions and uniqueness analysis.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
            problem: The problem being solved
        
        Returns:
            Existing solutions, unique aspects, and summary insight
        """
        prompt = self.COMPARISON_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features),
            problem=problem
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate comparison")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def generate_hackathon_viva(
        self,
        project_summary: str,
        features: List[str],
        tech_stack: str,
        unique_aspects: str
    ) -> Dict[str, Any]:
        """
        Generate extended viva guide with hackathon-specific questions.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
            tech_stack: Tech stack summary
            unique_aspects: What makes this project special
        
        Returns:
            Viva questions and hackathon questions with answers
        """
        prompt = self.HACKATHON_VIVA_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features),
            tech_stack=tech_stack,
            unique_aspects=unique_aspects
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate hackathon viva guide")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }
    
    async def recommend_tech_stack_extended(
        self,
        project_summary: str,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Recommend technologies with explanations and backup alternatives.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
        
        Returns:
            Primary tech stack with explanations and alternatives
        """
        prompt = self.TECH_STACK_EXTENDED_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features)
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to recommend extended tech stack")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }

    async def generate_chat_response(
        self,
        raw_idea: str,
        chat_history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """
        Generate a conversational mentor response for interactive planning.
        
        Args:
            raw_idea: The student's original project idea
            chat_history: List of previous messages [{role, content}]
            user_message: The student's latest message
        
        Returns:
            AI response, updated draft summary, and readiness status
        """
        # Format chat history for prompt
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in chat_history
        ]) if chat_history else "(No previous messages)"
        
        prompt = self.CHAT_MENTOR_PROMPT.format(
            raw_idea=raw_idea,
            chat_history=history_text,
            user_message=user_message
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate response")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }

    async def apply_revision(
        self,
        current_summary: Dict[str, Any],
        change_request: str
    ) -> Dict[str, Any]:
        """
        Apply a user's change request to the project summary.
        
        Args:
            current_summary: The current project summary
            change_request: What the user wants to change
        
        Returns:
            Updated summary, change type, and affected sections
        """
        prompt = self.REVISION_PROMPT.format(
            problem_statement=current_summary.get("problem_statement", ""),
            target_users=current_summary.get("target_users", ""),
            features=", ".join(current_summary.get("main_features", [])),
            scope=current_summary.get("scope_notes", ""),
            change_request=change_request
        )
        
        result = await self.llm.generate_json(prompt)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to apply revision")
            }
        
        return {
            "success": True,
            "data": result["content"]
        }


# Create a singleton instance
planner_service = PlannerService()

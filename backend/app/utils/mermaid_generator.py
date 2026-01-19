"""
Mermaid Generator - Flowchart Diagram Generation
=================================================

This utility generates Mermaid.js syntax for flowcharts.
Mermaid is a text-based diagramming tool that renders
beautiful diagrams from simple text descriptions.

All diagrams are designed to be:
- Clean and readable
- Print-friendly (white background)
- Easy to export as images
"""

from typing import List, Dict, Optional
from app.services.llm_service import llm_service


class MermaidGenerator:
    """
    Generate Mermaid.js diagrams for project documentation.
    
    What is Mermaid?
    Mermaid is a JavaScript library that renders diagrams from text.
    Instead of drawing diagrams, you describe them in a simple syntax.
    
    Example:
        flowchart TD
            A[Start] --> B[Process]
            B --> C[End]
    
    This renders as a top-to-bottom flowchart with three boxes.
    """
    
    USER_FLOW_PROMPT = """You are helping create a Mermaid.js flowchart for a student's project.

PROJECT: {project_summary}
FEATURES: {features}

Create a USER FLOW flowchart showing how a user interacts with the system.

Requirements:
- Use Mermaid flowchart syntax (flowchart TD for top-down)
- Include 8-12 nodes showing the user journey
- Use descriptive node labels
- Include decision points (diamond shapes) where appropriate
- Keep it simple and readable

Example syntax:
flowchart TD
    A[User Opens App] --> B{{Login Required?}}
    B -->|Yes| C[Show Login Page]
    B -->|No| D[Show Dashboard]

Rules:
- Start with 'flowchart TD' on its own line
- Use [Square] for actions, {{Diamond}} for decisions
- Use -->|Label| for labeled connections
- Keep node text short (2-4 words)
- No colors or special styling (will be added in frontend)

Respond with ONLY the Mermaid code, no explanation."""

    TECH_STACK_PROMPT = """You are helping create a Mermaid.js diagram showing technology architecture.

PROJECT: {project_summary}
TECH STACK:
{tech_stack}

Create a TECH STACK DIAGRAM showing how the technologies connect.

Requirements:
- Use Mermaid flowchart syntax
- Show Frontend → Backend → Database flow
- Include external services if applicable
- Use subgraphs to group related technologies

Example syntax:
flowchart LR
    subgraph Frontend
        A[React App]
    end
    subgraph Backend
        B[Node.js API]
    end
    subgraph Database
        C[(MongoDB)]
    end
    A -->|HTTP Requests| B
    B -->|Queries| C

Rules:
- Start with 'flowchart LR' (left to right) on its own line
- Use subgraphs to organize by layer
- Use [()] for databases
- Keep labels short
- Show data flow direction with arrows

Respond with ONLY the Mermaid code, no explanation."""

    ARCHITECTURE_PROMPT = """You are helping create a Mermaid.js architecture diagram.

PROJECT: {project_summary}
MODULES: {modules}
DATA FLOW: {data_flow}

Create an ARCHITECTURE DIAGRAM showing system components and their interactions.

Requirements:
- Use Mermaid flowchart syntax
- Show all major modules
- Indicate data flow between components
- Group related components

Rules:
- Start with 'flowchart TB' (top to bottom)
- Use subgraphs for layers (Presentation, Business, Data)
- Keep it readable - max 15 nodes
- Show clear data flow direction

Respond with ONLY the Mermaid code, no explanation."""

    def __init__(self):
        """Initialize the Mermaid generator."""
        self.llm = llm_service
    
    async def generate_user_flow(
        self,
        project_summary: str,
        features: List[str]
    ) -> Dict:
        """
        Generate a user flow flowchart.
        
        Args:
            project_summary: Brief description of the project
            features: List of key features
        
        Returns:
            Dict with 'success' and 'mermaid_code'
        """
        prompt = self.USER_FLOW_PROMPT.format(
            project_summary=project_summary,
            features=", ".join(features)
        )
        
        result = await self.llm.generate(prompt, temperature=0.5)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate user flow diagram")
            }
        
        # Clean up the response
        mermaid_code = self._clean_mermaid_code(result["content"])
        
        return {
            "success": True,
            "mermaid_code": mermaid_code
        }
    
    async def generate_tech_stack_diagram(
        self,
        project_summary: str,
        tech_stack: List[Dict]
    ) -> Dict:
        """
        Generate a tech stack architecture diagram.
        
        Args:
            project_summary: Brief description of the project
            tech_stack: List of technology recommendations
        
        Returns:
            Dict with 'success' and 'mermaid_code'
        """
        # Format tech stack for the prompt
        tech_stack_str = "\n".join([
            f"- {t.get('category', 'Unknown')}: {t.get('technology', str(t))}"
            for t in tech_stack
        ])
        
        prompt = self.TECH_STACK_PROMPT.format(
            project_summary=project_summary,
            tech_stack=tech_stack_str
        )
        
        result = await self.llm.generate(prompt, temperature=0.5)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate tech stack diagram")
            }
        
        mermaid_code = self._clean_mermaid_code(result["content"])
        
        return {
            "success": True,
            "mermaid_code": mermaid_code
        }
    
    async def generate_architecture_diagram(
        self,
        project_summary: str,
        modules: List[str],
        data_flow: str
    ) -> Dict:
        """
        Generate a system architecture diagram.
        
        Args:
            project_summary: Brief description of the project
            modules: List of system modules
            data_flow: Description of data flow
        
        Returns:
            Dict with 'success' and 'mermaid_code'
        """
        prompt = self.ARCHITECTURE_PROMPT.format(
            project_summary=project_summary,
            modules=", ".join(modules),
            data_flow=data_flow
        )
        
        result = await self.llm.generate(prompt, temperature=0.5)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate architecture diagram")
            }
        
        mermaid_code = self._clean_mermaid_code(result["content"])
        
        return {
            "success": True,
            "mermaid_code": mermaid_code
        }
    
    def _clean_mermaid_code(self, content: str) -> str:
        """
        Clean up LLM response to extract valid Mermaid code.
        
        Removes markdown code blocks, extra whitespace, etc.
        """
        # Remove markdown code blocks
        if "```mermaid" in content:
            content = content.split("```mermaid")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # Clean up whitespace
        content = content.strip()
        
        # Ensure it starts with a valid Mermaid declaration
        valid_starts = ["flowchart", "graph", "sequenceDiagram", "classDiagram"]
        if not any(content.startswith(start) for start in valid_starts):
            # Try to find and extract the flowchart portion
            for start in valid_starts:
                if start in content:
                    idx = content.index(start)
                    content = content[idx:]
                    break
        
        return content
    
    def create_simple_user_flow(self, steps: List[str]) -> str:
        """
        Create a simple user flow from a list of steps.
        
        This is a fallback for when LLM is unavailable.
        
        Args:
            steps: List of step descriptions
        
        Returns:
            Mermaid code for the flowchart
        """
        if not steps:
            return "flowchart TD\n    A[Start] --> B[End]"
        
        lines = ["flowchart TD"]
        
        # Create nodes
        for i, step in enumerate(steps):
            node_id = chr(65 + i)  # A, B, C, etc.
            # Clean step text for Mermaid
            clean_step = step.replace('"', "'").replace("[", "(").replace("]", ")")
            lines.append(f"    {node_id}[{clean_step}]")
        
        # Create connections
        for i in range(len(steps) - 1):
            from_id = chr(65 + i)
            to_id = chr(65 + i + 1)
            lines.append(f"    {from_id} --> {to_id}")
        
        return "\n".join(lines)
    
    def create_simple_tech_stack(self, tech_stack: List[Dict]) -> str:
        """
        Create a simple tech stack diagram from a list of technologies.
        
        This is a fallback for when LLM is unavailable.
        
        Args:
            tech_stack: List of tech stack items
        
        Returns:
            Mermaid code for the diagram
        """
        # Group by category
        groups = {}
        for tech in tech_stack:
            category = tech.get("category", "Other")
            if category not in groups:
                groups[category] = []
            groups[category].append(tech.get("technology", "Unknown"))
        
        lines = ["flowchart LR"]
        
        # Create subgraphs for each category
        prev_category = None
        for category, techs in groups.items():
            safe_category = category.replace(" ", "_")
            lines.append(f"    subgraph {safe_category}[{category}]")
            for tech in techs:
                safe_tech = tech.replace(" ", "_").replace(".", "_")
                lines.append(f"        {safe_tech}[{tech}]")
            lines.append("    end")
            
            # Connect to previous category
            if prev_category:
                safe_prev = prev_category.replace(" ", "_")
                lines.append(f"    {safe_prev} --> {safe_category}")
            prev_category = category
        
        return "\n".join(lines)


# Create a singleton instance
mermaid_generator = MermaidGenerator()

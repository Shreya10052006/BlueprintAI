"""
LLM Service - Free-Only Provider Cascade for BlueprintAI
=========================================================

This service handles all communication with AI providers.

PROVIDER CASCADE (ALL FREE):
1. Gemini 2.5 Flash (Primary - Google free tier)
2. Groq LLaMA 3.1 70B (Secondary - free, fast)
3. OpenRouter DeepSeek V3:free (Tertiary - ~50 req/day emergency fallback)

IMPORTANT DESIGN DECISIONS:
1. All providers use REST API for reliability
2. DeepSeek is ONLY used when Gemini AND Groq both fail
3. DeepSeek is quota-limited (~50 req/day) - treated as emergency fallback
4. ONLY generates planning content - NEVER code
5. All providers return same format via normalization layer
"""

import os
import json
import httpx
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up file-based logging for diagnostics
_log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'llm_debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(message)s',
    handlers=[
        logging.FileHandler(_log_path, mode='w'),  # 'w' to overwrite each time
        logging.StreamHandler()  # Also print to console
    ]
)
_logger = logging.getLogger('llm_service')

# =============================================================================
# CONFIGURATION
# =============================================================================

# API Keys (from environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# API Endpoints
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Provider order for cascade (STRICT - do not change order)
PROVIDER_ORDER = ["gemini", "groq", "openrouter"]

# Check if we're in demo mode (no API keys at all)
def _has_valid_key(key: str) -> bool:
    """Check if an API key is valid (not empty or placeholder)."""
    return key and key.strip() and key != "YOUR_API_KEY_HERE"


IS_DEMO_MODE = not any([
    _has_valid_key(GEMINI_API_KEY),
    _has_valid_key(GROQ_API_KEY),
    _has_valid_key(OPENROUTER_API_KEY)
])


# =============================================================================
# LLM SERVICE CLASS
# =============================================================================

class LLMService:
    """
    Service for interacting with multiple FREE AI providers.
    
    Provider cascade (all free tier):
    1. Gemini 2.5 Flash - Primary, generous free tier
    2. Groq LLaMA 3.1 70B - Secondary, fast and free
    3. OpenRouter DeepSeek V3:free - Tertiary, ~50 req/day emergency fallback
    
    Automatic failover on:
    - HTTP 429 (rate limit)
    - HTTP 401/403 (auth error)
    - Timeout
    - Empty/invalid response
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.providers = self._build_provider_list()
        self.is_demo_mode = IS_DEMO_MODE
        
        if self.is_demo_mode:
            print("⚠️  LLM Service running in DEMO MODE (no API keys configured)")
            print("   Configure at least one API key in .env for full functionality:")
            print("   - GEMINI_API_KEY (primary - free)")
            print("   - GROQ_API_KEY (secondary - free)")
            print("   - OPENROUTER_API_KEY (tertiary - DeepSeek free)")
        else:
            print(f"✅ LLM Service initialized with {len(self.providers)} provider(s): {', '.join(self.providers)}")
    
    def _build_provider_list(self) -> List[str]:
        """Build list of available providers based on configured keys."""
        available = []
        if _has_valid_key(GEMINI_API_KEY):
            available.append("gemini")
        if _has_valid_key(GROQ_API_KEY):
            available.append("groq")
        if _has_valid_key(OPENROUTER_API_KEY):
            available.append("openrouter")
        return available
    
    # =========================================================================
    # MAIN ENTRY POINTS
    # =========================================================================
    
    async def generate_with_fallback(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Generate content using provider cascade.
        
        Tries providers in order: Gemini → Groq → OpenRouter DeepSeek
        Automatically fails over on error.
        
        Args:
            prompt: The planning prompt (never ask for code!)
            temperature: Creativity level (0.7 is good for planning)
            max_tokens: Maximum response length (8192 for large blueprint)
        
        Returns:
            Dict with:
            - success: bool
            - content: str (the generated text)
            - provider_used: str (gemini | groq | openrouter)
            - error: str (if all failed)
        """
        # In demo mode, return mock responses
        if self.is_demo_mode:
            demo_response = self._get_demo_response(prompt)
            demo_response["provider_used"] = "demo"
            return demo_response
        
        # Try each available provider in order
        errors = []
        for provider in self.providers:
            print(f"🔄 Trying provider: {provider}...")
            
            try:
                if provider == "gemini":
                    result = await self._call_gemini(prompt, temperature, max_tokens)
                elif provider == "groq":
                    result = await self._call_groq(prompt, temperature, max_tokens)
                elif provider == "openrouter":
                    result = await self._call_openrouter(prompt, temperature, max_tokens)
                else:
                    continue
                
                if result["success"]:
                    print(f"✅ Provider {provider} succeeded")
                    result["provider_used"] = provider
                    return result
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"⚠️  Provider {provider} failed: {error_msg}")
                    errors.append(f"{provider}: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Provider {provider} exception: {error_msg}")
                errors.append(f"{provider}: {error_msg}")
        
        # All providers failed
        print("❌ All providers failed")
        return {
            "success": False,
            "content": None,
            "provider_used": None,
            "error": "AI services are temporarily busy. Please try again later.",
            "error_details": errors  # Internal only, not shown to users
        }
    
    async def generate_json_with_fallback(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Generate content and parse as JSON.
        
        Used when we need structured data back from the AI.
        Wraps generate_with_fallback with JSON parsing.
        """
        # Add JSON instruction to prompt
        json_prompt = prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown code blocks, no explanation, just the raw JSON object."
        
        result = await self.generate_with_fallback(json_prompt, temperature, max_tokens)
        
        if not result["success"]:
            return result
        
        try:
            # Try to extract JSON from the response
            content = result["content"]
            
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
            
            # Try to find JSON object boundaries
            content = content.strip()
            if not content.startswith("{"):
                # Try to find the first {
                start_idx = content.find("{")
                if start_idx != -1:
                    content = content[start_idx:]
            
            parsed = json.loads(content)
            return {
                "success": True,
                "content": parsed,
                "provider_used": result.get("provider_used")
            }
        except json.JSONDecodeError as e:
            # Return raw content if JSON parsing fails
            return {
                "success": True,
                "content": result["content"],
                "provider_used": result.get("provider_used"),
                "warning": f"Response was not valid JSON, returning raw text. Parse error: {str(e)}"
            }
    
    # =========================================================================
    # BACKWARDS COMPATIBILITY - Keep old method signatures working
    # =========================================================================
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate content from AI (backwards compatible).
        
        This method maintains the old signature for existing code.
        Internally uses the new cascade system.
        """
        return await self.generate_with_fallback(prompt, temperature, max_tokens)
    
    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate JSON content (backwards compatible).
        
        This method maintains the old signature for existing code.
        Internally uses the new cascade system.
        """
        return await self.generate_json_with_fallback(prompt, temperature, max_tokens)
    
    # =========================================================================
    # PROVIDER-SPECIFIC IMPLEMENTATIONS
    # =========================================================================
    
    async def _call_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Call Gemini 2.5 Flash via REST API.
        
        Primary provider - generous free tier.
        """
        try:
            headers = {
                "Content-Type": "application/json; charset=utf-8"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                    headers=headers,
                    json=payload
                )
                
                # VERBOSE LOGGING: Capture exact status and error
                status = response.status_code
                body_snippet = response.text[:200] if response.text else "(empty)"
                
                if status == 200:
                    data = response.json()
                    content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if content:
                        print(f"✅ Gemini | status={status} | reason=success")
                        return {
                            "success": True,
                            "content": content
                        }
                    else:
                        print(f"⚠️ Gemini | status={status} | reason=empty_response")
                        return {
                            "success": False,
                            "error": "Empty response from Gemini"
                        }
                elif status == 429:
                    print(f"⚠️ Gemini | status={status} | reason=rate_limit | body={body_snippet}")
                    return {
                        "success": False,
                        "error": "Rate limited (429)"
                    }
                elif status in [401, 403]:
                    print(f"⚠️ Gemini | status={status} | reason=auth_failed | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"Authentication failed ({status})"
                    }
                else:
                    print(f"⚠️ Gemini | status={status} | reason=http_error | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"HTTP {status}"
                    }
                    
        except httpx.TimeoutException:
            print(f"⚠️ Gemini | status=TIMEOUT | reason=90s_timeout")
            return {
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"⚠️ Gemini | status=EXCEPTION | reason={str(e)[:100]}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_groq(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Call Groq LLaMA 3.1 70B via REST API.
        
        Secondary provider - fast and free.
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
            
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI project mentor for college students. Your role is to help students plan and explain software projects clearly. This is a planning task only — do NOT generate code."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": min(max_tokens, 8000)  # Groq limit
            }
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    GROQ_API_URL,
                    headers=headers,
                    json=payload
                )
                
                # VERBOSE LOGGING: Capture exact status and error
                status = response.status_code
                body_snippet = response.text[:200] if response.text else "(empty)"
                
                if status == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        print(f"✅ Groq | status={status} | reason=success")
                        return {
                            "success": True,
                            "content": content
                        }
                    else:
                        print(f"⚠️ Groq | status={status} | reason=empty_response")
                        return {
                            "success": False,
                            "error": "Empty response from Groq"
                        }
                elif status == 429:
                    print(f"⚠️ Groq | status={status} | reason=rate_limit | body={body_snippet}")
                    return {
                        "success": False,
                        "error": "Rate limited (429)"
                    }
                elif status in [401, 403]:
                    print(f"⚠️ Groq | status={status} | reason=auth_failed | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"Authentication failed ({status})"
                    }
                else:
                    print(f"⚠️ Groq | status={status} | reason=http_error | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"HTTP {status}"
                    }
                    
        except httpx.TimeoutException:
            print(f"⚠️ Groq | status=TIMEOUT | reason=90s_timeout")
            return {
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"⚠️ Groq | status=EXCEPTION | reason={str(e)[:100]}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_openrouter(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Call OpenRouter DeepSeek V3:free via REST API.
        
        Tertiary provider - EMERGENCY FALLBACK ONLY.
        Quota-limited: ~50 requests per day.
        
        ONLY called when Gemini AND Groq both fail.
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://blueprintai.app",  # Required by OpenRouter
                "X-Title": "BlueprintAI"  # Optional, shows in OpenRouter dashboard
            }
            
            payload = {
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI project mentor for college students. Your role is to help students plan and explain software projects clearly. This is a planning task only — do NOT generate code."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": min(max_tokens, 8000)
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for DeepSeek
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                )
                
                # VERBOSE LOGGING: Capture exact status and error
                status = response.status_code
                body_snippet = response.text[:200] if response.text else "(empty)"
                
                if status == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        print(f"✅ OpenRouter | status={status} | reason=success")
                        print("[WARN] DeepSeek V3 fallback used (quota-limited provider)")
                        return {
                            "success": True,
                            "content": content
                        }
                    else:
                        print(f"⚠️ OpenRouter | status={status} | reason=empty_response")
                        return {
                            "success": False,
                            "error": "Empty response from DeepSeek"
                        }
                elif status == 429:
                    print(f"⚠️ OpenRouter | status={status} | reason=quota_exceeded | body={body_snippet}")
                    return {
                        "success": False,
                        "error": "DeepSeek quota exceeded (429)"
                    }
                elif status == 402:
                    print(f"⚠️ OpenRouter | status={status} | reason=payment_required | body={body_snippet}")
                    return {
                        "success": False,
                        "error": "Payment required (402)"
                    }
                elif status in [401, 403]:
                    print(f"⚠️ OpenRouter | status={status} | reason=auth_failed | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"Authentication failed ({status})"
                    }
                else:
                    print(f"⚠️ OpenRouter | status={status} | reason=http_error | body={body_snippet}")
                    return {
                        "success": False,
                        "error": f"HTTP {status}"
                    }
                    
        except httpx.TimeoutException:
            print(f"⚠️ OpenRouter | status=TIMEOUT | reason=120s_timeout")
            return {
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"⚠️ OpenRouter | status=EXCEPTION | reason={str(e)[:100]}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =========================================================================
    # DEMO MODE RESPONSES
    # =========================================================================
    
    def _get_demo_response(self, prompt: str) -> Dict[str, Any]:
        """
        Return demo responses when no API key is configured.
        
        This allows the system to be demonstrated without a real API key.
        The responses show what the system would typically generate.
        """
        prompt_lower = prompt.lower()
        
        # Detect what type of content is being requested
        if "master" in prompt_lower or "blueprint" in prompt_lower or "full" in prompt_lower:
            # Return full master blueprint demo
            return {
                "success": True,
                "content": json.dumps(self._get_demo_blueprint()),
                "is_demo": True
            }
        elif "problem statement" in prompt_lower or "expand" in prompt_lower:
            return {
                "success": True,
                "content": json.dumps({
                    "problem_statement": "Students often spend valuable time manually tracking attendance, which is error-prone and time-consuming. A digital attendance system would automate this process, saving time and improving accuracy.",
                    "target_users": ["Students", "Teachers", "Administrators"],
                    "objectives": [
                        "Automate the attendance tracking process",
                        "Reduce manual errors in attendance records",
                        "Provide easy access to attendance history",
                        "Generate attendance reports automatically"
                    ],
                    "scope": "This project covers a web-based attendance system for a single institution. Mobile app development and biometric integration are outside the current scope.",
                    "what_this_means": "Your project will help educational institutions move from paper-based attendance to a digital system that saves time and reduces errors.",
                    "why_this_matters": "Understanding your problem statement clearly is essential for explaining your project confidently in any review."
                }),
                "is_demo": True
            }
        else:
            # Generic demo response
            return {
                "success": True,
                "content": "This is a demo response. Please configure at least one API key in the .env file for full AI functionality. The system supports: GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY (all free!).",
                "is_demo": True
            }
    
    def _get_demo_blueprint(self) -> Dict:
        """Return a complete demo blueprint for testing."""
        return {
            "summary": {
                "problem_statement": "Students and teachers struggle with manual attendance tracking, leading to errors and wasted time.",
                "target_users": ["Students", "Teachers", "Administrators"],
                "objectives": [
                    "Automate attendance marking",
                    "Reduce manual errors",
                    "Generate reports automatically",
                    "Track attendance history"
                ],
                "scope": "Web-based attendance system for a single educational institution",
                "what_this_means": "This project replaces paper-based attendance with a digital solution",
                "why_this_matters": "Understanding scope helps you stay focused and explain your project clearly"
            },
            "features": {
                "features": [
                    {
                        "feature_name": "User Authentication",
                        "what_it_does": "Allows different users to log in securely",
                        "why_it_exists": "To protect student data and ensure only authorized access",
                        "how_it_helps": "Teachers can only see their classes, students can only see their records",
                        "limitations": "Requires password reset mechanism for forgotten passwords"
                    },
                    {
                        "feature_name": "Attendance Marking",
                        "what_it_does": "Teachers can mark present/absent for each student",
                        "why_it_exists": "Core functionality that replaces manual roll call",
                        "how_it_helps": "Saves 5-10 minutes per class",
                        "limitations": "Requires internet connectivity"
                    }
                ]
            },
            "feasibility": {
                "feasibility_level": "High",
                "feasibility_explanation": "Uses standard web technologies taught in most colleges",
                "strengths": ["Clear requirements", "Well-documented technologies", "Real-world application"],
                "risks": ["Security implementation", "Database design", "Time management"],
                "why_this_matters": "Knowing feasibility helps you plan realistically"
            },
            "system_flow": {
                "flow_title": "Attendance Marking Flow",
                "steps": [
                    {"step_number": 1, "actor": "User", "action": "Opens application", "explanation": "Entry point"},
                    {"step_number": 2, "actor": "System", "action": "Shows login page", "explanation": "Security first"},
                    {"step_number": 3, "actor": "Teacher", "action": "Enters credentials", "explanation": "Authentication"},
                    {"step_number": 4, "actor": "System", "action": "Validates and shows dashboard", "explanation": "Role-based access"},
                    {"step_number": 5, "actor": "Teacher", "action": "Selects class", "explanation": "Choose which class to mark"},
                    {"step_number": 6, "actor": "System", "action": "Shows student list", "explanation": "Display markable students"},
                    {"step_number": 7, "actor": "Teacher", "action": "Marks attendance", "explanation": "Core action"},
                    {"step_number": 8, "actor": "System", "action": "Saves and confirms", "explanation": "Persistence and feedback"}
                ],
                "summary": "Simple 8-step flow from login to confirmation"
            },
            "tech_stack": {
                "primary_stack": [
                    {"category": "Frontend", "technology": "React", "justification": "Component-based, well-documented", "skill_level": "Intermediate"},
                    {"category": "Backend", "technology": "Node.js + Express", "justification": "JavaScript throughout the stack", "skill_level": "Beginner-friendly"},
                    {"category": "Database", "technology": "MongoDB", "justification": "Flexible schema, easy to learn", "skill_level": "Beginner-friendly"}
                ],
                "backup_stack": [
                    {"category": "Frontend", "technology": "Vue.js", "why_backup": "Simpler learning curve if React is too complex"},
                    {"category": "Backend", "technology": "Python Flask", "why_backup": "If JavaScript backend is challenging"}
                ]
            },
            "comparison": {
                "existing_solutions": [
                    {"solution_name": "Google Forms", "what_it_does": "Basic data collection", "limitations": "No role-based access, no reports"},
                    {"solution_name": "Enterprise ERP systems", "what_it_does": "Full institution management", "limitations": "Too complex and expensive for single use case"}
                ],
                "unique_aspects": ["Focused on college use case", "Student-friendly interface", "Built-in report generation"],
                "why_this_project_is_still_valuable": ["Learning experience", "Customizable for specific needs", "No licensing costs"],
                "summary_insight": "While attendance systems exist, this project provides hands-on learning while creating something tailored to your institution's specific needs."
            },
            "viva": {
                "project_overview_explanation": "This is a web-based attendance system that helps teachers mark attendance digitally and generate reports automatically.",
                "problem_statement_explanation": "Manual attendance wastes 5-10 minutes per class and is prone to errors. Our system automates this completely.",
                "architecture_explanation": "We use a three-tier architecture: React frontend talks to Node.js backend, which stores data in MongoDB.",
                "unique_feature_explanation": "Automatic report generation sets us apart from simple digital forms.",
                "common_questions": [
                    {"question": "Why did you choose this tech stack?", "suggested_answer": "React for reusable components, Node.js for JavaScript consistency, MongoDB for flexible data storage.", "why_asked": "Tests if you made informed choices"},
                    {"question": "What are the limitations?", "suggested_answer": "Requires internet, no offline mode, single institution only.", "why_asked": "Tests honesty and self-awareness"}
                ],
                "hackathon_questions": [
                    {"question": "What makes this unique?", "suggested_response": "Built specifically for college context with student-friendly design", "key_points": ["Focus on UX", "Report generation", "Role-based access"]}
                ]
            },
            "pitch": {
                "thirty_second_pitch": "Teachers spend 5-10 minutes every class on attendance. Our digital system does it in 30 seconds with zero errors and automatic reports.",
                "one_minute_pitch": "Imagine never losing an attendance register again. Our system lets teachers mark attendance with a few clicks, generates reports instantly, and gives students transparency into their records. Built with modern web technologies, it's designed specifically for college environments.",
                "key_points": ["Saves time", "Eliminates errors", "Automatic reports", "Role-based access"]
            },
            "diagrams": {
                "user_flow_mermaid": "flowchart TD\n    A[User Opens App] --> B{Logged In?}\n    B -->|No| C[Login Page]\n    B -->|Yes| D[Dashboard]\n    C --> E[Enter Credentials]\n    E --> F{Valid?}\n    F -->|No| C\n    F -->|Yes| D\n    D --> G[Select Class]\n    G --> H[Mark Attendance]\n    H --> I[Save & Confirm]",
                "tech_stack_mermaid": "flowchart LR\n    subgraph Frontend\n        A[React App]\n    end\n    subgraph Backend\n        B[Node.js API]\n    end\n    subgraph Database\n        C[(MongoDB)]\n    end\n    A -->|HTTP| B\n    B -->|Queries| C"
            }
        }
    
    # =========================================================================
    # STATUS METHODS
    # =========================================================================
    
    def is_available(self) -> bool:
        """Check if the LLM service is properly configured."""
        return not self.is_demo_mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the LLM service."""
        return {
            "configured": not self.is_demo_mode,
            "demo_mode": self.is_demo_mode,
            "providers_available": self.providers,
            "provider_count": len(self.providers),
            "cascade_order": ["Gemini 2.5 Flash", "Groq LLaMA 3.1 70B", "OpenRouter DeepSeek V3:free"],
            "message": f"Cascade active with {len(self.providers)} provider(s)" if not self.is_demo_mode else "Running in demo mode - configure API keys for full features"
        }


# Create a singleton instance
llm_service = LLMService()

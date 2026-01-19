"""
Validation Service - Input Validation & Code Generation Prevention
===================================================================

This service is responsible for:
1. Validating user inputs before processing
2. Detecting and refusing code generation requests
3. Sanitizing inputs for safety

This is a KEY component that makes our system a MENTOR, not a developer.
"""

import re
from typing import Tuple, List, Optional
from app.schemas.response import CodeGenerationRefusal


class ValidationService:
    """
    Service for validating inputs and preventing code generation.
    
    Why this matters:
    - Ensures the system stays true to its educational purpose
    - Protects against malicious inputs
    - Provides helpful feedback instead of errors
    """
    
    # Patterns that suggest a user wants code, not planning
    CODE_REQUEST_PATTERNS = [
        r'\bgenerate\s+code\b',
        r'\bwrite\s+(the\s+)?code\b',
        r'\bcreate\s+(the\s+)?code\b',
        r'\bgive\s+me\s+(the\s+)?code\b',
        r'\bshow\s+me\s+(the\s+)?code\b',
        r'\bcode\s+for\b',
        r'\bsource\s+code\b',
        r'\bimplementation\s+code\b',
        r'\bprogramming\s+code\b',
        r'\bhtml\s+code\b',
        r'\bcss\s+code\b',
        r'\bjavascript\s+code\b',
        r'\bpython\s+code\b',
        r'\bjava\s+code\b',
        r'\bsql\s+queries?\b',
        r'\bwrite\s+.*\s+function\b',
        r'\bwrite\s+.*\s+class\b',
        r'\bwrite\s+.*\s+script\b',
        r'\bdownload\s+.*\s+code\b',
        r'\bexport\s+.*\s+code\b',
        r'\bgenerate\s+.*\s+script\b',
    ]
    
    # Minimum requirements for a valid idea
    MIN_IDEA_LENGTH = 10
    MAX_IDEA_LENGTH = 2000
    
    def __init__(self):
        """Initialize the validation service."""
        # Compile regex patterns for efficiency
        self.code_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.CODE_REQUEST_PATTERNS
        ]
    
    def validate_idea(self, raw_idea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate a project idea input.
        
        Args:
            raw_idea: The raw idea text from the user
        
        Returns:
            Tuple of (is_valid, error_message, suggestion)
        """
        # Remove excessive whitespace
        cleaned = " ".join(raw_idea.split())
        
        # Check length
        if len(cleaned) < self.MIN_IDEA_LENGTH:
            return (
                False,
                "Your idea is too short for us to understand.",
                "Please describe your project in at least one complete sentence. "
                "For example: 'I want to build an app that helps students track their attendance.'"
            )
        
        if len(cleaned) > self.MAX_IDEA_LENGTH:
            return (
                False,
                "Your idea is too long to process at once.",
                "Please summarize your main idea in a few sentences. "
                "You can add more details during the interactive planning phase."
            )
        
        # Check for code generation requests
        is_code_request, matched_phrase = self._detect_code_request(cleaned)
        if is_code_request:
            return (
                False,
                f"It looks like you're asking for code generation ('{matched_phrase}').",
                "This system helps you PLAN and UNDERSTAND your project, not write code. "
                "Try describing what your project should DO instead. "
                "For example: 'A system that tracks student attendance' instead of 'Code for attendance system'."
            )
        
        # Check for gibberish or random characters
        if self._is_gibberish(cleaned):
            return (
                False,
                "We couldn't understand your input.",
                "Please enter a real project idea in plain English. "
                "Describe what problem you want to solve or what you want to build."
            )
        
        return (True, None, None)
    
    def _detect_code_request(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if the text is asking for code generation.
        
        Returns:
            Tuple of (is_code_request, matched_phrase)
        """
        for pattern in self.code_patterns:
            match = pattern.search(text)
            if match:
                return (True, match.group(0))
        return (False, None)
    
    def _is_gibberish(self, text: str) -> bool:
        """
        Check if text appears to be random characters or gibberish.
        
        Simple heuristics:
        - Too many consecutive consonants
        - Very few vowels
        - Too many special characters
        """
        # Remove spaces and count character types
        no_spaces = text.replace(" ", "").lower()
        
        if len(no_spaces) == 0:
            return True
        
        # Count vowels
        vowels = sum(1 for c in no_spaces if c in "aeiou")
        vowel_ratio = vowels / len(no_spaces)
        
        # Very few vowels suggests gibberish
        if vowel_ratio < 0.1 and len(no_spaces) > 10:
            return True
        
        # Too many special characters
        special = sum(1 for c in no_spaces if not c.isalnum())
        if special / len(no_spaces) > 0.3:
            return True
        
        return False
    
    def get_code_refusal_response(self) -> CodeGenerationRefusal:
        """
        Get a friendly refusal response for code generation requests.
        
        This is returned when a user asks for code instead of planning.
        """
        return CodeGenerationRefusal(
            refused=True,
            reason=(
                "This system is designed to help you PLAN and UNDERSTAND your project, "
                "not to write code for you. This is intentional! Understanding your project "
                "deeply before coding leads to better results and makes viva much easier."
            ),
            what_we_can_help_with=[
                "Turning your vague idea into a clear problem statement",
                "Evaluating if your idea is feasible",
                "Explaining what features will cost in terms of time and complexity",
                "Creating system flow diagrams",
                "Recommending a tech stack with explanations",
                "Preparing you for viva questions",
                "Writing project pitches"
            ],
            encouragement=(
                "Once you understand your project blueprint completely, "
                "you'll find the actual coding much easier! Plus, you'll be "
                "able to explain every decision in your viva with confidence. 💪"
            )
        )
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input for safe processing.
        
        - Removes excessive whitespace
        - Strips leading/trailing spaces
        - Limits length
        """
        # Normalize whitespace
        cleaned = " ".join(text.split())
        
        # Limit length
        if len(cleaned) > self.MAX_IDEA_LENGTH:
            cleaned = cleaned[:self.MAX_IDEA_LENGTH]
        
        return cleaned.strip()
    
    def validate_feature_list(self, features: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a list of features.
        
        Ensures features are reasonable strings, not code snippets.
        """
        for feature in features:
            if len(feature) > 500:
                return (False, f"Feature description too long: '{feature[:50]}...'")
            
            # Check if feature looks like code
            code_indicators = ["()", ";", "=>", "function", "def ", "class ", "{", "}"]
            if any(ind in feature for ind in code_indicators):
                return (
                    False, 
                    f"Feature '{feature[:50]}...' looks like code. Please describe features in plain English."
                )
        
        return (True, None)


# Create a singleton instance
validation_service = ValidationService()

"""
Utils Package - Utility Functions
==================================

Helper functions and utilities used across the application.
"""

from app.utils.mermaid_generator import mermaid_generator, MermaidGenerator
from app.utils.firebase_client import get_firestore, is_firebase_available, PROJECTS_COLLECTION

__all__ = [
    "mermaid_generator",
    "MermaidGenerator",
    "get_firestore",
    "is_firebase_available",
    "PROJECTS_COLLECTION",
]

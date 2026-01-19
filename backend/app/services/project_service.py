"""
Project Service - Firestore Persistence for Blueprints
========================================================

This service handles saving and retrieving project blueprints
from Firebase Firestore.

Key Design:
- Read/write operations are backend-only
- Graceful fallback if Firebase is not configured
- Minimal data storage (only essential fields)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from app.utils.firebase_client import get_firestore, is_firebase_available, PROJECTS_COLLECTION


class ProjectService:
    """
    Service for persisting project blueprints to Firestore.
    
    All methods gracefully handle the case where Firebase
    is not configured - they return None or empty lists
    instead of crashing.
    """
    
    def __init__(self):
        """Initialize the project service."""
        pass  # Firestore client is obtained on-demand
    
    async def save_project(
        self,
        idea_input: str,
        mode: str,
        blueprint: Dict[str, Any],
        user_flow_mermaid: str = "",
        tech_stack_mermaid: str = ""
    ) -> Optional[str]:
        """
        Save a project blueprint to Firestore.
        
        Args:
            idea_input: The original idea text from the student
            mode: Planning mode ('interactive' or 'ai_only')
            blueprint: The complete blueprint dictionary
            user_flow_mermaid: Mermaid code for user flow diagram
            tech_stack_mermaid: Mermaid code for tech stack diagram
        
        Returns:
            The document ID if saved successfully, None otherwise
        """
        db = get_firestore()
        
        if db is None:
            print("⚠️  Project not saved - Firebase not configured")
            return None
        
        try:
            # Prepare the document with only essential fields
            doc_data = {
                "ideaInput": idea_input,
                "mode": mode,
                "blueprint": {
                    "projectTitle": blueprint.get("projectTitle", ""),
                    "projectSubtitle": blueprint.get("projectSubtitle", ""),
                    "ideaSummary": blueprint.get("ideaSummary", ""),
                    "evaluation": blueprint.get("evaluation"),
                    "features": blueprint.get("features", []),
                    "systemFlow": blueprint.get("systemFlow"),
                    "techStack": blueprint.get("techStack", []),
                    "architecture": blueprint.get("architecture"),
                    "vivaGuide": blueprint.get("vivaGuide"),
                    "pitch": blueprint.get("pitch"),
                },
                "mermaidDiagrams": {
                    "userFlow": user_flow_mermaid,
                    "techStack": tech_stack_mermaid
                },
                "createdAt": datetime.utcnow().isoformat()
            }
            
            # Add to Firestore
            doc_ref = db.collection(PROJECTS_COLLECTION).add(doc_data)
            
            # doc_ref is a tuple: (timestamp, DocumentReference)
            doc_id = doc_ref[1].id
            
            print(f"✅ Project saved to Firestore: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Failed to save project: {str(e)}")
            return None
    
    async def get_all_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all projects from Firestore.
        
        Args:
            limit: Maximum number of projects to return
        
        Returns:
            List of project documents with their IDs
        """
        db = get_firestore()
        
        if db is None:
            return []
        
        try:
            # Query projects, ordered by creation date (newest first)
            projects_ref = db.collection(PROJECTS_COLLECTION)
            query = projects_ref.order_by("createdAt", direction="DESCENDING").limit(limit)
            
            docs = query.stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                project_data["id"] = doc.id
                projects.append(project_data)
            
            return projects
            
        except Exception as e:
            print(f"❌ Failed to fetch projects: {str(e)}")
            return []
    
    async def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single project by its ID.
        
        Args:
            project_id: The Firestore document ID
        
        Returns:
            The project document or None if not found
        """
        db = get_firestore()
        
        if db is None:
            return None
        
        try:
            doc_ref = db.collection(PROJECTS_COLLECTION).document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                project_data = doc.to_dict()
                project_data["id"] = doc.id
                return project_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to fetch project {project_id}: {str(e)}")
            return None


# Create a singleton instance
project_service = ProjectService()

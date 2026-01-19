"""
Firebase Client - Firestore Database Connection
=================================================

This utility handles Firebase initialization and provides
a singleton Firestore client for the entire application.

IMPORTANT:
- Firebase is used ONLY from the backend (FastAPI)
- NO Firebase SDK in the frontend
- Credentials are read from environment variable
- This is for PERSISTENCE only, not auth
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase Admin SDK
_firestore_client = None
_firebase_initialized = False


def _initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK safely.
    
    Returns True if initialization succeeded, False otherwise.
    Does NOT crash the app if Firebase is unavailable.
    """
    global _firebase_initialized
    
    if _firebase_initialized:
        return True
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Get the service account path from environment
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")
        
        if not service_account_path or service_account_path == "YOUR_PATH_HERE":
            print("⚠️  Firebase: FIREBASE_SERVICE_ACCOUNT not configured")
            print("   Projects will NOT be saved to database")
            return False
        
        # Check if the file exists
        if not os.path.exists(service_account_path):
            print(f"⚠️  Firebase: Service account file not found at: {service_account_path}")
            return False
        
        # Initialize Firebase Admin
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        
        _firebase_initialized = True
        print("✅ Firebase: Initialized successfully")
        return True
        
    except Exception as e:
        print(f"⚠️  Firebase: Initialization failed - {str(e)}")
        return False


def get_firestore():
    """
    Get the Firestore client singleton.
    
    Returns None if Firebase is not configured.
    This allows the app to work even without Firebase.
    
    Usage:
        db = get_firestore()
        if db:
            db.collection('projects').add(data)
    """
    global _firestore_client
    
    if _firestore_client is not None:
        return _firestore_client
    
    if not _initialize_firebase():
        return None
    
    try:
        from firebase_admin import firestore
        _firestore_client = firestore.client()
        return _firestore_client
    except Exception as e:
        print(f"⚠️  Firebase: Could not get Firestore client - {str(e)}")
        return None


def is_firebase_available() -> bool:
    """
    Check if Firebase is configured and available.
    
    Use this before attempting database operations.
    """
    return get_firestore() is not None


# Collection names (constants for consistency)
PROJECTS_COLLECTION = "projects"

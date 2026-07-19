"""
Firebase initialization module for PokeMath.

This module centralizes the initialization of Firebase Admin SDK 
to ensure consistent access to Firestore and Auth services.
"""

import firebase_admin
from firebase_admin import auth, firestore

# Global clients to be used across the application
_firestore_client = None
_auth_client = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Use Application Default Credentials in every environment. Cloud Run obtains
    short-lived credentials from its service account; local development uses
    credentials created by ``gcloud auth application-default login``.
    
    Returns:
        Tuple of (firestore_client, auth_instance)
    """
    global _firestore_client, _auth_client
    
    # Return existing clients if already initialized
    if _firestore_client is not None and _auth_client is not None:
        return _firestore_client, _auth_client
    
    # Check if Firebase is already initialized
    if firebase_admin._apps:
        firebase_admin._apps[0]
    else:
        try:
            firebase_admin.initialize_app()
            print("Firebase Admin SDK initialized successfully")
        except Exception as e:
            raise RuntimeError(
                "Failed to initialize Firebase with Application Default "
                "Credentials. For local development, run "
                "`gcloud auth application-default login`."
            ) from e
    
    # Get clients
    _firestore_client = firestore.client()
    _auth_client = auth
    
    return _firestore_client, _auth_client

def get_firestore_client():
    """
    Get the Firestore client.
    
    Returns:
        Firestore client instance
    """
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client

def get_auth_client():
    """
    Get the Auth client.
    
    Returns:
        Auth client instance
    """
    global _auth_client
    if _auth_client is None:
        initialize_firebase()
    return _auth_client

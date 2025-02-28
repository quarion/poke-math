"""
Firebase initialization module for PokeMath.

This module centralizes the initialization of Firebase Admin SDK 
to ensure consistent access to Firestore and Auth services.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Global clients to be used across the application
_firestore_client = None
_auth_client = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    In Cloud Run with a service account, this will use Application Default Credentials.
    In development, it will look for a credentials file.
    
    Returns:
        Tuple of (firestore_client, auth_instance)
    """
    global _firestore_client, _auth_client
    
    # Return existing clients if already initialized
    if _firestore_client is not None and _auth_client is not None:
        return _firestore_client, _auth_client
    
    # Check if Firebase is already initialized
    if firebase_admin._apps:
        app = firebase_admin._apps[0]
    else:
        # Initialize Firebase Admin SDK
        cred = None
        
        # In Cloud Run with the service account, use Application Default Credentials
        if os.environ.get('K_SERVICE') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                cred = credentials.ApplicationDefault()
                print("Using Application Default Credentials for Firebase")
            except Exception as e:
                print(f"Error getting ApplicationDefault credentials: {e}")
        
        # If not in Cloud Run or ADC not available, try service account file
        if not cred:
            try:
                # Try multiple locations for the credentials file
                possible_paths = [
                    'firebase-credentials.json',                                       # Root dir
                    os.path.join(os.path.dirname(__file__), 'firebase-credentials.json'),  # Current dir
                    os.path.join(os.path.dirname(__file__), '..', '..', 'firebase-credentials.json') # Project root
                ]
                
                # Use FIREBASE_SERVICE_ACCOUNT env var if available
                if os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
                    possible_paths.insert(0, os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
                
                # Try each path
                for path in possible_paths:
                    if os.path.exists(path):
                        cred = credentials.Certificate(path)
                        print(f"Using Firebase credentials file: {path}")
                        break
            except Exception as e:
                print(f"Error loading service account credentials: {e}")
        
        # If still no credentials, raise error
        if not cred:
            raise RuntimeError(
                "Firebase credentials not found. Either set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable, provide a firebase-credentials.json file, or "
                "run in Cloud Run with the proper service account."
            )
        
        # Initialize the app
        try:
            app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firebase: {e}")
    
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
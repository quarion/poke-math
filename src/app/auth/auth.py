"""
Authentication module for PokeMath.

This module handles user authentication using Firebase Authentication,
including Google sign-in and guest user functionality.
"""

import os
import uuid
from typing import Dict, Any, Optional, Tuple, Callable
from datetime import datetime
from flask import session, redirect, url_for, request
from functools import wraps
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('firebase-credentials.json')
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization error: {e}")

class AuthManager:
    """
    Manages user authentication and session data.
    """
    
    @staticmethod
    def create_guest_user() -> str:
        """
        Create a guest user with a unique ID.
        
        Returns:
            str: The generated guest user ID
        """
        guest_id = f"guest_{uuid.uuid4()}"
        session['user_id'] = guest_id
        session['auth_type'] = 'guest'
        session['authenticated'] = True
        session['display_name'] = None
        return guest_id
    
    @staticmethod
    def set_user_name(name: str) -> None:
        """
        Set the user's display name in the session.
        
        Args:
            name: The user's display name
        """
        session['display_name'] = name
    
    @staticmethod
    def get_user_name() -> Optional[str]:
        """
        Get the user's display name from the session.
        
        Returns:
            The user's display name or None if not set
        """
        return session.get('display_name')
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if the user is authenticated.
        
        Returns:
            True if the user is authenticated, False otherwise
        """
        return session.get('authenticated', False)
    
    @staticmethod
    def is_guest() -> bool:
        """
        Check if the user is a guest.
        
        Returns:
            True if the user is a guest, False otherwise
        """
        return session.get('auth_type') == 'guest'
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """
        Get the user ID from the session.
        
        Returns:
            The user ID or None if not set
        """
        return session.get('user_id')
    
    @staticmethod
    def logout() -> None:
        """
        Log the user out by clearing the session.
        """
        # Keep some session data like CSRF token
        csrf_token = session.get('csrf_token')
        
        # Clear the session
        session.clear()
        
        # Restore CSRF token if it existed
        if csrf_token:
            session['csrf_token'] = csrf_token
    
    @staticmethod
    def verify_google_token(id_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify a Google ID token and extract user information.
        
        Args:
            id_token: The Google ID token to verify
            
        Returns:
            Tuple of (success, user_data)
            - success: True if verification succeeded, False otherwise
            - user_data: Dictionary of user data if successful, None otherwise
        """
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information
            user_data = {
                'user_id': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture')
            }
            
            return True, user_data
        except Exception as e:
            print(f"Token verification error: {e}")
            return False, None
    
    @staticmethod
    def login_with_google(id_token: str) -> bool:
        """
        Log in a user with a Google ID token.
        
        Args:
            id_token: The Google ID token to verify
            
        Returns:
            True if login succeeded, False otherwise
        """
        success, user_data = AuthManager.verify_google_token(id_token)
        
        if success and user_data:
            # Set session data
            session['user_id'] = user_data['user_id']
            session['auth_type'] = 'google'
            session['authenticated'] = True
            session['email'] = user_data.get('email')
            session['display_name'] = user_data.get('name')
            session['picture'] = user_data.get('picture')
            session['login_time'] = datetime.now().isoformat()
            
            return True
        
        return False
    
    @staticmethod
    def login_required(f: Callable) -> Callable:
        """
        Decorator to require login for routes.
        
        Args:
            f: The view function to decorate
            
        Returns:
            The decorated function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AuthManager.is_authenticated():
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function 
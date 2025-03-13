"""
Authentication module for PokeMath.

This module handles user authentication using Firebase Authentication,
including Google sign-in and guest user functionality.
"""

import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from flask import redirect, request, session, url_for
from flask_wtf.csrf import generate_csrf

from ..firebase.firebase_init import get_auth_client


class AuthManager:
    """
    Manages user authentication and session data.
    
    Features:
    - Google authentication using Firebase
    - Guest user authentication
    - Guest account persistence using cookies (30 days)
    - Session management
    """
    
    # Cookie name for storing guest ID
    GUEST_COOKIE_NAME = 'pokemath_guest_id'
    # Cookie expiration in days
    GUEST_COOKIE_EXPIRY = 30
    
    @staticmethod
    def create_guest_user() -> str:
        """
        Create a guest user with a unique ID or reuse an existing guest ID from cookies.
        
        Returns:
            str: The guest user ID
        """
        # Check if there's an existing guest ID in cookies
        existing_guest_id = request.cookies.get(AuthManager.GUEST_COOKIE_NAME)
        
        if existing_guest_id and existing_guest_id.startswith('guest_'):
            # Reuse the existing guest ID
            guest_id = existing_guest_id
        else:
            # Generate a new guest ID
            guest_id = f"guest_{uuid.uuid4()}"
        
        # Store in session
        session['user_id'] = guest_id
        session['auth_type'] = 'guest'
        session['authenticated'] = True
        session['display_name'] = None
        
        # The cookie will be set in the response
        return guest_id
    
    @staticmethod
    def set_guest_cookie(response) -> None:
        """
        Set a persistent cookie with the guest ID.
        
        Args:
            response: Flask response object
        """
        if session.get('auth_type') == 'guest' and session.get('user_id'):
            # Calculate expiry time in seconds (days * 24 hours * 60 minutes * 60 seconds)
            max_age = AuthManager.GUEST_COOKIE_EXPIRY * 24 * 60 * 60
            
            # Set the cookie
            response.set_cookie(
                AuthManager.GUEST_COOKIE_NAME,
                session['user_id'],
                max_age=max_age,
                httponly=True,
                samesite='Lax'
            )

    
    @staticmethod
    def is_authenticated() -> bool:
        return session.get('authenticated', False)
    
    @staticmethod
    def is_guest() -> bool:
        return session.get('auth_type') == 'guest'
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        return session.get('user_id')
    
    @staticmethod
    def logout() -> None:
        """
        Log the user out by clearing the session.
        """
        # Keep some session data like CSRF token
        csrf_token = session.get('csrf_token')
        
        # Remember if this was a guest account
        was_guest = session.get('auth_type') == 'guest'
        session.get('user_id') if was_guest else None
        
        # Clear the session
        session.clear()
        
        # Restore CSRF token if it existed
        if csrf_token:
            session['csrf_token'] = csrf_token
            
        # Ensure CSRF token is preserved for Flask-WTF
        generate_csrf()
    
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
            decoded_token = get_auth_client().verify_id_token(id_token)
            
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
            # Store Google name separately instead of as display_name
            # This allows users to choose their own game display name
            session['google_name'] = user_data.get('name')
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
from flask import session as flask_session
from typing import Dict, Any
from .storage_interface import UserStorageInterface

class FlaskSessionStorage(UserStorageInterface):
    """Stores user data in Flask session."""
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Load data from Flask session.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            The user data from Flask session or an empty dict if not found
        """
        return flask_session.get('session_state', {})
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Save data to Flask session.
        
        Args:
            user_id: The unique identifier for the user (not used for Flask session)
            data: The data to save to Flask session
        """
        flask_session['session_state'] = data
        
    def user_exists(self, user_id: str) -> bool:
        """
        Check if user data exists in session.
        
        Args:
            user_id: The unique identifier for the user (not used for Flask session)
            
        Returns:
            True if the session state exists, False otherwise
        """
        return 'session_state' in flask_session 
from typing import Dict, Set, Any, Optional, List
from flask import session as flask_session
import uuid
from datetime import datetime

from src.app.storage.storage_interface import UserStorageInterface
from src.app.storage.flask_session_storage import FlaskSessionStorage
from src.app.auth.auth import AuthManager

class SessionState:
    """
    Represents the user-specific session state that needs to be persisted.
    This contains only the data that varies per user and needs to be stored.
    """
    def __init__(self):
        self.solved_quizzes: Set[str] = set()
        self.variable_mappings: Dict[str, Dict[str, str]] = {}
        self.quiz_attempts: List[Dict[str, Any]] = []  # New field for quiz attempts
        self.user_name: Optional[str] = None  # Added for storing user's Pokemon-style name
    
    def reset(self):
        """Reset the session state."""
        self.solved_quizzes.clear()
        self.variable_mappings.clear()
        self.quiz_attempts.clear()
        # Don't clear user_name on reset - that should persist
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session state to a dictionary for serialization."""
        return {
            'solved_quizzes': list(self.solved_quizzes),
            'variable_mappings': self.variable_mappings,
            'quiz_attempts': self.quiz_attempts,
            'user_name': self.user_name
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore the session state from a dictionary."""
        self.solved_quizzes = set(data.get('solved_quizzes', []))
        self.variable_mappings = data.get('variable_mappings', {})
        self.quiz_attempts = data.get('quiz_attempts', [])
        self.user_name = data.get('user_name')

class SessionManager:
    """
    Manages quiz session persistence and state.
    Uses a storage implementation to persist data.
    """
    
    def __init__(self, storage: Optional[UserStorageInterface] = None, user_id: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            storage: Storage implementation. Defaults to FlaskSessionStorage.
            user_id: User ID. If not provided, will be loaded from Flask session
                    or a new one will be generated.
        """
        self.storage = storage or FlaskSessionStorage()
        # Use AuthManager to get user_id if available
        self.user_id = user_id or AuthManager.get_user_id() or self._get_or_create_user_id()
        self.state = SessionState()
        self._load_state()
    
    def _get_or_create_user_id(self) -> str:
        """
        Get existing user ID from Flask session or create a new one.
        
        Returns:
            User ID string
        """
        if 'user_id' not in flask_session:
            # Create a guest user if no user ID exists
            return AuthManager.create_guest_user()
        return flask_session['user_id']
    
    def _load_state(self):
        """Load state from storage."""
        data = self.storage.load_user_data(self.user_id)
        if 'session_state' in data:
            self.state.from_dict(data['session_state'])
            
        # Sync user name with AuthManager if available
        if AuthManager.get_user_name() and not self.state.user_name:
            self.state.user_name = AuthManager.get_user_name()
        elif self.state.user_name and not AuthManager.get_user_name():
            AuthManager.set_user_name(self.state.user_name)
    
    def _save_state(self):
        """Save state to storage."""
        self.storage.save_user_data(self.user_id, {
            'session_state': self.state.to_dict()
        })
    
    def reset(self):
        """Reset the session state."""
        self.state.reset()
        self._save_state()
    
    def mark_quiz_solved(self, quiz_id: str):
        """
        Mark a quiz as solved.
        
        Args:
            quiz_id: The ID of the quiz
        """
        self.state.solved_quizzes.add(quiz_id)
        self._save_state()
    
    def is_quiz_solved(self, quiz_id: str) -> bool:
        """
        Check if a quiz is solved.
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            True if the quiz is solved, False otherwise
        """
        return quiz_id in self.state.solved_quizzes
    
    @property
    def solved_quizzes(self) -> Set[str]:
        """
        Get the set of solved quizzes.
        
        Returns:
            Set of quiz IDs that have been solved
        """
        return self.state.solved_quizzes
    
    def get_variable_mappings(self, quiz_id: str) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz.
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            Dictionary of variable mappings or empty dict if not found
        """
        return self.state.variable_mappings.get(quiz_id, {})
    
    def set_variable_mappings(self, quiz_id: str, mappings: Dict[str, str]):
        """
        Set variable mappings for a quiz.
        
        Args:
            quiz_id: The ID of the quiz
            mappings: Dictionary of variable mappings
        """
        self.state.variable_mappings[quiz_id] = mappings
        self._save_state()
    
    def has_variable_mappings(self, quiz_id: str) -> bool:
        """
        Check if variable mappings exist for a quiz.
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            True if mappings exist, False otherwise
        """
        return quiz_id in self.state.variable_mappings
    
    @classmethod
    def load_from_flask_session(cls, storage: Optional[UserStorageInterface] = None) -> 'SessionManager':
        """
        Load session manager using user_id from Flask session.
        If no user_id exists, a new one is created.
        
        Args:
            storage: Optional storage implementation
            
        Returns:
            SessionManager instance
        """
        # Create session manager with specified storage and user ID from Flask session
        return cls(storage=storage)
    
    def save_session(self):
        """
        Save user_id to Flask session and state to storage.
        """
        flask_session['user_id'] = self.user_id
        self._save_state()
    
    # User name management methods
    
    def set_user_name(self, name: str):
        """
        Set the user's Pokemon-style name.
        
        Args:
            name: The user's Pokemon-style name
        """
        self.state.user_name = name
        # Also update in AuthManager for session consistency
        AuthManager.set_user_name(name)
        self._save_state()
    
    def get_user_name(self) -> Optional[str]:
        """
        Get the user's Pokemon-style name.
        
        Returns:
            The user's name or None if not set
        """
        return self.state.user_name
    
    # Quiz attempts methods
    
    def add_quiz_attempt(self, quiz_id: str, quiz_data: Dict[str, Any], score: int, total: int, completed: bool):
        """
        Record a quiz attempt with full quiz data.
        
        Args:
            quiz_id: The ID of the quiz
            quiz_data: Complete quiz data including equations, variables, solutions
            score: Number of points earned
            total: Total number of possible points
            completed: Whether the quiz was fully completed
        """
        # Check if an attempt already exists for this quiz
        existing_attempt_index = self.find_quiz_attempt_index(quiz_id)
        
        if existing_attempt_index != -1:
            # Update the existing attempt instead of creating a new one
            self.state.quiz_attempts[existing_attempt_index].update({
                'timestamp': datetime.now().isoformat(),
                'score': score,
                'total': total,
                'completed': completed,
                'quiz_data': quiz_data,
            })
        else:
            # Create a new attempt if none exists
            self.state.quiz_attempts.append({
                'quiz_id': quiz_id,
                'timestamp': datetime.now().isoformat(),
                'score': score,
                'total': total,
                'completed': completed,
                'quiz_data': quiz_data,  # Store complete quiz data for restoration
            })
        self._save_state()
    
    def find_quiz_attempt_index(self, quiz_id: str) -> int:
        """
        Find the index of an existing quiz attempt by quiz_id.
        
        Args:
            quiz_id: The ID of the quiz to find
            
        Returns:
            Index of the attempt or -1 if not found
        """
        for i, attempt in enumerate(self.state.quiz_attempts):
            if attempt.get('quiz_id') == quiz_id:
                return i
        return -1
    
    def get_quiz_attempts(self) -> List[Dict[str, Any]]:
        """
        Get all quiz attempts.
        
        Returns:
            List of quiz attempt dictionaries
        """
        return self.state.quiz_attempts
    
    def remove_quiz_attempt(self, timestamp: str):
        """
        Remove a quiz attempt by timestamp.
        
        Args:
            timestamp: The timestamp string of the attempt to remove
        """
        self.state.quiz_attempts = [
            attempt for attempt in self.state.quiz_attempts 
            if attempt.get('timestamp') != timestamp
        ]
        self._save_state() 
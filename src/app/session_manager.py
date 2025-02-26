from typing import Dict, Set, Any
from flask import session as flask_session

class SessionState:
    """
    Represents the user-specific session state that needs to be persisted.
    This contains only the data that varies per user and needs to be stored.
    """
    def __init__(self):
        self.solved_quizzes: Set[str] = set()
        self.variable_mappings: Dict[str, Dict[str, str]] = {}
    
    def reset(self):
        """Reset the session state."""
        self.solved_quizzes.clear()
        self.variable_mappings.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session state to a dictionary for serialization."""
        return {
            'solved_quizzes': list(self.solved_quizzes),
            'variable_mappings': self.variable_mappings
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore the session state from a dictionary."""
        self.solved_quizzes = set(data.get('solved_quizzes', []))
        self.variable_mappings = data.get('variable_mappings', {})

class SessionManager:
    """
    Manages quiz session persistence and state.
    This class is responsible only for persisting user-specific session data.
    
    This class can be replaced with a different implementation (e.g., database persistence)
    without affecting the core quiz logic.
    """
    
    def __init__(self):
        """
        Initialize the session manager.
        """
        # User-specific session state (persisted per session)
        self.state = SessionState()
    
    def reset(self):
        """Reset the session state."""
        self.state.reset()
    
    def mark_quiz_solved(self, quiz_id: str):
        """Mark a quiz as solved."""
        self.state.solved_quizzes.add(quiz_id)
    
    def is_quiz_solved(self, quiz_id: str) -> bool:
        """Check if a quiz is solved."""
        return quiz_id in self.state.solved_quizzes
    
    @property
    def solved_quizzes(self) -> Set[str]:
        """Get the set of solved quizzes."""
        return self.state.solved_quizzes
    
    def get_variable_mappings(self, quiz_id: str) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz.
        """
        return self.state.variable_mappings.get(quiz_id, {})
    
    def set_variable_mappings(self, quiz_id: str, mappings: Dict[str, str]):
        """
        Set variable mappings for a quiz.
        """
        self.state.variable_mappings[quiz_id] = mappings
    
    def has_variable_mappings(self, quiz_id: str) -> bool:
        """
        Check if variable mappings exist for a quiz.
        """
        return quiz_id in self.state.variable_mappings
    
    @classmethod
    def load_from_flask_session(cls) -> 'SessionManager':
        """
        Load session manager from Flask session.
        If no session data exists, a new session manager is created.
        """
        manager = cls()
        
        # Initialize session data if it doesn't exist
        if 'session_state' not in flask_session:
            flask_session['session_state'] = manager.state.to_dict()
            return manager
        
        # Load existing session data
        manager.state.from_dict(flask_session['session_state'])
        return manager
    
    def save_to_flask_session(self):
        """
        Save session manager state to Flask session.
        """
        flask_session['session_state'] = self.state.to_dict() 
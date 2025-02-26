from typing import Dict, Set

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
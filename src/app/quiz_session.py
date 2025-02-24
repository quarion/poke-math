from typing import Dict, Set
from src.app.quiz_data import QuizData
from src.app.session_manager import SessionManager

class QuizSession:
    """
    Class representing a quiz session.
    This is a thin wrapper around SessionManager for backward compatibility.
    
    In a future version, this class could be removed and SessionManager
    could be used directly in the application.
    """
    def __init__(self, session_manager: SessionManager):
        """Initialize with a session manager."""
        self.session_manager = session_manager
    
    @classmethod
    def create_new(cls, quiz_data: QuizData) -> 'QuizSession':
        """Create a new quiz session."""
        return cls(
            session_manager=SessionManager(quiz_data)
        )
    
    def get_quiz_state(self, quiz_id: str):
        """Get the current state of a quiz."""
        return self.session_manager.get_quiz_state(quiz_id)
    
    def check_answers(self, quiz_id: str, user_answers: Dict[str, int]):
        """Check the user's answers for a quiz."""
        return self.session_manager.check_answers(quiz_id, user_answers)
    
    def reset(self):
        """Reset the session state."""
        self.session_manager.reset()
    
    @property
    def solved_quizzes(self) -> Set[str]:
        """Get the set of solved quizzes."""
        return self.session_manager.solved_quizzes 
from typing import Dict, Set, Any, Optional, List
from flask import session as flask_session
import uuid
from datetime import datetime

from src.app.storage.storage_interface import UserStorageInterface
from src.app.storage.flask_session_storage import FlaskSessionStorage
from src.app.auth.auth import AuthManager
from src.app.game.models import SessionState, QuizData, QuizAttempt

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
            self.state = SessionState.from_dict(data['session_state'])
            
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
    
    @classmethod
    def load_from_storage(cls, storage: Optional[UserStorageInterface] = None) -> 'SessionManager':
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
    
    def get_quiz_attempts(self) -> List[QuizAttempt]:
        """
        Get all quiz attempts.
        
        Returns:
            List of quiz attempt objects
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
            if attempt.timestamp != timestamp
        ]
        self._save_state()
    
    def find_quiz_attempt(self, quiz_id: str) -> Optional[QuizAttempt]:
        """
        Find a quiz attempt by quiz_id.
        
        Args:
            quiz_id: The ID of the quiz to find
            
        Returns:
            QuizAttempt if found, None otherwise
        """
        for attempt in self.state.quiz_attempts:
            if attempt.quiz_id == quiz_id:
                return attempt
        return None
        
    # Unified quiz data methods
    
    def save_quiz_data(self, quiz_id: str, quiz_data_dict: Dict[str, Any], is_random: bool = False):
        """
        Save quiz data for both random and regular quizzes.
        
        Args:
            quiz_id: The ID of the quiz
            quiz_data_dict: Complete quiz data including equations, variables, solutions
            is_random: Whether this is a randomly generated quiz
        """
        # Convert dictionary to QuizData object
        quiz_data_dict['is_random'] = is_random
        quiz_data_dict['quiz_id'] = quiz_id
        quiz_data = QuizData.from_dict(quiz_data_dict)
        
        # Find existing attempt for this quiz or create a new one
        attempt = self.find_quiz_attempt(quiz_id)
        
        if not attempt:
            # Create a new attempt record
            attempt = QuizAttempt(
                quiz_id=quiz_id,
                quiz_data=quiz_data,
                timestamp=datetime.now().isoformat(),
                user_answers={}
            )
            self.state.quiz_attempts.append(attempt)
        else:
            # Update existing attempt's quiz data
            attempt.quiz_data = quiz_data
            attempt.timestamp = datetime.now().isoformat()
        
        self._save_state()
    
    def get_quiz_data(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quiz data for any quiz by ID.
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            Quiz data dictionary or None if not found
        """
        attempt = self.find_quiz_attempt(quiz_id)
        
        if attempt:
            return attempt.quiz_data.to_dict()
        return None
    
    def save_quiz_answers(self, quiz_id: str, user_answers: Dict[str, int]):
        """
        Save user answers for any quiz.
        
        Args:
            quiz_id: The ID of the quiz
            user_answers: Dictionary of user-provided answers {var: value}
        """
        attempt = self.find_quiz_attempt(quiz_id)
        
        if attempt:
            attempt.user_answers = user_answers
            attempt.timestamp = datetime.now().isoformat()
            self._save_state()
        
    def get_quiz_answers(self, quiz_id: str) -> Dict[str, int]:
        """
        Get user answers for any quiz.
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            Dictionary of user answers or empty dict if not found
        """
        attempt = self.find_quiz_attempt(quiz_id)
        
        if attempt:
            return attempt.user_answers
        return {} 
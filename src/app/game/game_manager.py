from typing import Dict, Set, Optional, Any, Tuple
import uuid
import random
from src.app.game.game_config import GameConfig
from src.app.game.session_manager import SessionManager
from src.app.game.quiz_engine import check_quiz_answers, get_display_variables


class GameManager:
    """
    Manager orchestrating the game and holding the game configuration
    """

    def __init__(self, game_config: GameConfig, session_manager: SessionManager):
        """
        Initialize with game configuration and session manager.
        
        Args:
            game_config: The shared game configuration
            session_manager: The session manager for persisting user state
        """
        self.game_config = game_config
        self.session_manager = session_manager

    @classmethod
    def initialize_from_session(cls, quiz_data: GameConfig, session_manager: Optional[SessionManager] = None) -> 'GameManager':
        """
        Create a new quiz session.
        
        Args:
            quiz_data: The game configuration
            session_manager: Optional session manager. If not provided, one will be loaded from Flask session.
        
        Returns:
            A new GameManager instance
        """
        if session_manager is None:
            session_manager = SessionManager.load_from_storage()
            
        return cls(
            game_config=quiz_data,
            session_manager=session_manager
        )

    def save_session(self):
        """Save the current session state."""
        self.session_manager.save_session()

    def get_quiz_state(self, quiz_id: str) -> Optional[Dict]:
        """
        Get the current state of a quiz.
        Returns None if quiz not found.
        """
        quiz = self.game_config.quizzes_by_id.get(quiz_id)
        if not quiz:
            return None

        # Generate display variables using the quiz_engine module
        display_vars = get_display_variables(self.game_config, {})

        return {
            'quiz': quiz,
            'image_mapping': display_vars,
            'is_solved': self.session_manager.is_quiz_solved(quiz_id)
        }

    def check_answers(self, quiz_id: str, user_answers: Dict[str, int]):
        """Check the user's answers for a quiz."""
        quiz = self.game_config.quizzes_by_id.get(quiz_id)
        if not quiz:
            return {'error': 'Quiz not found'}

        # Use the quiz_engine module to check answers
        all_correct, correct_answers, all_answered = check_quiz_answers(
            quiz,
            user_answers
        )

        # Only mark as solved if all answers are correct and all questions were answered
        if all_correct and all_answered:
            self.session_manager.mark_quiz_solved(quiz_id)

        # Count how many answers are correct
        correct_count = sum(1 for is_correct in correct_answers.values() if is_correct)
        total_count = len(correct_answers)
        
        return {
            'correct': all_correct and all_answered,
            'correct_answers': correct_answers,
            'next_quiz_id': quiz.next_quiz_id,
            'all_answered': all_answered,
            'correct_count': correct_count,
            'total_count': total_count
        }

    def reset(self):
        """Reset the session state."""
        self.session_manager.reset()

    @property
    def solved_quizzes(self) -> Set[str]:
        """Get the set of solved quizzes."""
        return self.session_manager.solved_quizzes

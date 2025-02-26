from typing import Dict, Set
from src.app.game_config import GameConfig
from src.app.session_manager import SessionManager
from src.app.quiz_engine import check_quiz_answers


class GameManager:
    """
    Thin manager orchestrating the game
    """

    def __init__(self, session_manager: SessionManager):
        """Initialize with a session manager."""
        self.session_manager = session_manager

    @classmethod
    def start_session(cls, quiz_data: GameConfig) -> 'GameManager':
        """Create a new quiz session."""
        return cls(
            session_manager=SessionManager(quiz_data)
        )

    def get_quiz_state(self, quiz_id: str):
        """Get the current state of a quiz."""
        return self.session_manager.get_quiz_state(quiz_id)

    def check_answers(self, quiz_id: str, user_answers: Dict[str, int]):
        """Check the user's answers for a quiz."""
        quiz = self.session_manager.game_config.quizzes_by_id.get(quiz_id)
        if not quiz:
            return {'error': 'Quiz not found'}

        # Use the quiz_engine module to check answers
        all_correct, correct_answers = check_quiz_answers(
            quiz,
            user_answers
        )

        if all_correct:
            self.session_manager.mark_quiz_solved(quiz_id)

        return {
            'correct': all_correct,
            'correct_answers': correct_answers,
            'next_quiz_id': quiz.next_quiz_id
        }

    def reset(self):
        """Reset the session state."""
        self.session_manager.reset()

    @property
    def solved_quizzes(self) -> Set[str]:
        """Get the set of solved quizzes."""
        return self.session_manager.solved_quizzes

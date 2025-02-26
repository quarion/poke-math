from typing import Dict, Set, Optional
from src.app.game_config import GameConfig
from src.app.session_manager import SessionManager
from src.app.quiz_engine import check_quiz_answers, create_variable_mappings, get_display_variables


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
    def start_session(cls, quiz_data: GameConfig) -> 'GameManager':
        """Create a new quiz session."""
        return cls(
            game_config=quiz_data,
            session_manager=SessionManager.load_from_flask_session()
        )

    def save_session(self):
        """Save the current session state."""
        self.session_manager.save_to_flask_session()

    def get_quiz_state(self, quiz_id: str) -> Optional[Dict]:
        """
        Get the current state of a quiz, including any variable mappings.
        Returns None if quiz not found.
        """
        quiz = self.game_config.quizzes_by_id.get(quiz_id)
        if not quiz:
            return None

        # Get or create variable mappings for this quiz
        mappings = self.get_or_create_variable_mappings(quiz_id)
        
        # Get display variables using the quiz_engine module
        display_vars = get_display_variables(
            self.game_config,
            mappings
        )

        return {
            'quiz': quiz,
            'pokemon_vars': display_vars,
            'is_solved': self.session_manager.is_quiz_solved(quiz_id),
            'variable_mappings': mappings
        }

    def get_or_create_variable_mappings(self, quiz_id: str) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz or create new ones if they don't exist.
        """
        # Check if mappings already exist in the session
        if not self.session_manager.has_variable_mappings(quiz_id):
            quiz = self.game_config.quizzes_by_id.get(quiz_id)
            if not quiz:
                return {}
                
            # Use the quiz_engine module to create mappings
            mappings = create_variable_mappings(
                quiz, 
                self.game_config.pokemons
            )
            
            # Store the mappings in the session
            self.session_manager.set_variable_mappings(quiz_id, mappings)
            return mappings
            
        return self.session_manager.get_variable_mappings(quiz_id)

    def check_answers(self, quiz_id: str, user_answers: Dict[str, int]):
        """Check the user's answers for a quiz."""
        quiz = self.game_config.quizzes_by_id.get(quiz_id)
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

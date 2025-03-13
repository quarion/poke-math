from typing import Dict, Optional, Set

from src.app.game.game_config import GameConfig
from src.app.game.progression_manager import ProgressionManager
from src.app.game.quiz_engine import check_quiz_answers, get_display_variables
from src.app.game.session_manager import SessionManager


class GameManager:
    """
    Orchestrates game state and configuration.
    
    Manages quiz sessions, user progress, and coordinates between
    the game configuration and session storage.
    """

    def __init__(self, game_config: GameConfig, session_manager: SessionManager):
        self.game_config = game_config
        self.session_manager = session_manager

    @classmethod
    def initialize_from_session(cls, quiz_data: GameConfig,
                                session_manager: Optional[SessionManager] = None) -> 'GameManager':
        """Create a new GameManager with optional session manager."""
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
        """Get the state of a specific quiz."""
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

    def add_xp_and_handle_level_up(self, xp_amount: int) -> bool:
        """
        Add XP to the player and handle level-ups.
        
        Args:
            xp_amount: Amount of XP to add
            
        Returns:
            True if player leveled up, False otherwise
        """
        # Get current level and XP from session
        current_state = self.session_manager.get_level_and_xp()
        current_level = current_state['level']
        current_xp = current_state['xp']

        # Add XP to current amount
        current_xp += xp_amount

        # Use ProgressionManager to process level-up logic
        result = ProgressionManager.process_level_up(current_level, current_xp)

        # Update session with new level and XP
        self.session_manager.update_level_and_xp(result['level'], result['xp'])

        return result['leveled_up']

    def calculate_adventure_rewards(self, caught_pokemon, difficulty):
        """
        Calculate rewards for completing an adventure.
        
        Args:
            caught_pokemon: List of caught Pokémon IDs
            difficulty: Adventure difficulty level
            
        Returns:
            Dictionary with XP reward and whether player leveled up
        """
        # Calculate XP reward using ProgressionManager
        xp_reward = ProgressionManager.calculate_xp_reward(
            caught_pokemon,
            difficulty,
            self.game_config
        )

        # Add XP and handle level-up
        leveled_up = self.add_xp_and_handle_level_up(xp_reward)

        return {
            'xp_reward': xp_reward,
            'leveled_up': leveled_up
        }

    def get_player_level_info(self):
        """
        Get player level information.
        
        Returns:
            Dictionary with level, current XP, and XP needed for next level
        """
        # Get current level and XP from session
        current_state = self.session_manager.get_level_and_xp()

        # Use ProgressionManager to get level info
        return ProgressionManager.get_level_info(
            current_state['level'],
            current_state['xp']
        )

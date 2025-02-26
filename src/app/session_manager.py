from typing import Dict, Set, Optional
from src.app.game_config import GameConfig, Quiz
from src.app.quiz_engine import create_variable_mappings, get_display_variables

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
    This class separates the session state (user-specific data) from the
    application data (quiz definitions).
    
    This class can be replaced with a different implementation (e.g., database persistence)
    without affecting the core quiz logic.
    """
    
    def __init__(self, game_config: GameConfig):
        """
        Initialize with quiz data.
        
        Args:
            game_config: The shared quiz data (not persisted per session)
        """
        # Shared application data (not persisted per session)
        self.game_config = game_config
        
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
    
    def get_or_create_variable_mappings(self, quiz_id: str) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz or create new ones if they don't exist.
        """
        if quiz_id not in self.state.variable_mappings:
            quiz = self.game_config.quizzes_by_id.get(quiz_id)
            if not quiz:
                return {}
                
            # Use the quiz_engine module to create mappings
            self.state.variable_mappings[quiz_id] = create_variable_mappings(
                quiz, 
                self.game_config.pokemons
            )
            
        return self.state.variable_mappings[quiz_id]
    
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
            'is_solved': self.is_quiz_solved(quiz_id),
            'variable_mappings': mappings
        } 
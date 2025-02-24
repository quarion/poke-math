from typing import Dict, Set, Optional
from src.app.quiz_data import QuizData, Quiz
from src.app.quiz_engine import create_variable_mappings, check_quiz_answers, get_display_variables

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
    
    def __init__(self, quiz_data: QuizData):
        """
        Initialize with quiz data.
        
        Args:
            quiz_data: The shared quiz data (not persisted per session)
        """
        # Shared application data (not persisted per session)
        self.quiz_data = quiz_data
        
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
            quiz = self.quiz_data.quizzes_by_id.get(quiz_id)
            if not quiz:
                return {}
                
            # Use the quiz_engine module to create mappings
            self.state.variable_mappings[quiz_id] = create_variable_mappings(
                quiz, 
                self.quiz_data.pokemons
            )
            
        return self.state.variable_mappings[quiz_id]
    
    def get_quiz_state(self, quiz_id: str) -> Optional[Dict]:
        """
        Get the current state of a quiz, including any variable mappings.
        Returns None if quiz not found.
        """
        quiz = self.quiz_data.quizzes_by_id.get(quiz_id)
        if not quiz:
            return None

        # Get or create variable mappings for this quiz
        mappings = self.get_or_create_variable_mappings(quiz_id)
        
        # Get display variables using the quiz_engine module
        display_vars = get_display_variables(
            quiz,
            self.quiz_data,
            mappings
        )

        return {
            'quiz': quiz,
            'pokemon_vars': display_vars,
            'is_solved': self.is_quiz_solved(quiz_id),
            'variable_mappings': mappings
        }
    
    def check_answers(self, quiz_id: str, user_answers: Dict[str, int]) -> Dict:
        """
        Check the user's answers for a quiz.
        Returns a dictionary with the results.
        """
        quiz = self.quiz_data.quizzes_by_id.get(quiz_id)
        if not quiz:
            return {'error': 'Quiz not found'}

        # Get variable mappings
        mappings = self.get_or_create_variable_mappings(quiz_id)
        
        # Use the quiz_engine module to check answers
        all_correct, correct_answers = check_quiz_answers(
            quiz, 
            user_answers,
            mappings
        )
        
        if all_correct:
            self.mark_quiz_solved(quiz_id)

        return {
            'correct': all_correct,
            'correct_answers': correct_answers,
            'next_quiz_id': quiz.next_quiz_id
        } 
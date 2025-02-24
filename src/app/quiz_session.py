from dataclasses import dataclass
from typing import Dict, Optional, Set
import random
from src.app.quiz_data import QuizData, Quiz

@dataclass
class QuizSession:
    quiz_data: QuizData
    solved_quizzes: Set[str]
    variable_mappings: Dict[str, Dict[str, str]]  # quiz_id -> {variable -> pokemon}

    @classmethod
    def create_new(cls, quiz_data: QuizData) -> 'QuizSession':
        """Create a new quiz session."""
        return cls(
            quiz_data=quiz_data,
            solved_quizzes=set(),
            variable_mappings={}
        )

    def get_quiz_state(self, quiz_id: str) -> Optional[Dict]:
        """
        Get the current state of a quiz, including any variable mappings.
        Returns None if quiz not found.
        """
        quiz = self.quiz_data.quizzes_by_id.get(quiz_id)
        if not quiz:
            return None

        # Get or create variable mappings for this quiz
        mappings = self._get_or_create_variable_mappings(quiz)
        
        # Create display variables dictionary
        display_vars = {
            name: pokemon.image_path 
            for name, pokemon in self.quiz_data.pokemons.items()
        }
        
        # Add any special variable mappings
        for var, pokemon_name in mappings.items():
            display_vars[var] = self.quiz_data.pokemons[pokemon_name].image_path

        return {
            'quiz': quiz,
            'pokemon_vars': display_vars,
            'is_solved': quiz_id in self.solved_quizzes,
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

        # Map variable names to their actual values
        mappings = self._get_or_create_variable_mappings(quiz)
        mapped_answers = {}
        
        for var, value in user_answers.items():
            # If it's a special variable (x, y, z), we need to check against the answer directly
            if var in mappings:
                mapped_answers[var] = int(value)
            else:
                # For regular Pokemon variables, use them as is
                mapped_answers[var] = int(value)

        # Check each answer
        correct_answers = {
            var: mapped_answers.get(var, 0) == answer
            for var, answer in quiz.answer.values.items()
        }

        all_correct = all(correct_answers.values())
        if all_correct:
            self.solved_quizzes.add(quiz_id)

        return {
            'correct': all_correct,
            'correct_answers': correct_answers,
            'next_quiz_id': quiz.next_quiz_id
        }

    def _get_or_create_variable_mappings(self, quiz: Quiz) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz or create new ones if they don't exist.
        """
        if quiz.id not in self.variable_mappings:
            # Find all special variables used in the equations
            special_vars = {'x', 'y', 'z'}
            used_vars = set()
            for eq in quiz.equations:
                for var in special_vars:
                    if f'{{{var}}}' in eq:
                        used_vars.add(var)

            # Create new mappings if needed
            if used_vars:
                available_pokemon = list(self.quiz_data.pokemons.keys())
                random.shuffle(available_pokemon)
                self.variable_mappings[quiz.id] = {
                    var: available_pokemon.pop()
                    for var in used_vars
                }
            else:
                self.variable_mappings[quiz.id] = {}

        return self.variable_mappings[quiz.id]

    def reset(self):
        """Reset the session state."""
        self.solved_quizzes.clear()
        self.variable_mappings.clear() 
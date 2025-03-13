"""
View Models
----------
This module contains view model classes used to pass data to templates.
These classes provide a strongly-typed interface between the application and views.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QuizViewModel:
    """View model for quiz templates."""
    # Basic quiz information
    id: str
    title: str
    equations: List[str]
    variables: List[str]
    image_mapping: Dict[str, str]  # Variable name -> Pokemon image path

    # Optional fields with default values must come after required fields
    description: str = ""
    is_random: bool = False
    difficulty: Optional[Dict[str, Any]] = None
    next_quiz_id: Optional[str] = None
    has_next: bool = False

    def get_pokemon_image(self, variable: str) -> str:
        return self.image_mapping.get(variable, "default.png")

    def has_difficulty(self) -> bool:
        return self.difficulty is not None

    def replace_variables_with_images(self, equation: str) -> str:
        result = equation
        for var, img_path in self.image_mapping.items():
            img_tag = f'<img src="/static/images/{img_path}" class="pokemon-var" alt="{var}">'

            # Replace direct variable name using regex with word boundaries
            # This ensures we only replace standalone variables, not variables that are part of other words
            pattern = r'\b' + re.escape(var) + r'\b'
            result = re.sub(pattern, img_tag, result)

            # Also replace {var} placeholders
            placeholder = "{" + var + "}"
            result = result.replace(placeholder, img_tag)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert the view model to a dictionary for debugging."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'equations': self.equations,
            'variables': self.variables,
            'image_mapping': self.image_mapping,
            'is_random': self.is_random,
            'difficulty': self.difficulty,
            'next_quiz_id': self.next_quiz_id,
            'has_next': self.has_next
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"QuizViewModel(id={self.id}, title='{self.title}', variables={self.variables})"


@dataclass
class QuizResultViewModel:
    """View model for quiz results."""
    correct: bool
    correct_answers: Dict[str, bool]  # Variable name -> bool indicating if correct
    all_answered: bool
    correct_count: int
    total_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'correct': self.correct,
            'correct_answers': self.correct_answers,
            'all_answered': self.all_answered,
            'correct_count': self.correct_count,
            'total_count': self.total_count
        }

    def __str__(self) -> str:
        return f"QuizResultViewModel(correct={self.correct}, score={self.correct_count}/{self.total_count})"

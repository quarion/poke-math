"""
Models for quiz data and session state.
This module contains dataclasses for strongly typed quiz data structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime


@dataclass
class QuizData:
    """Strongly typed model for quiz data."""
    quiz_id: str
    title: str
    equations: List[str]
    solution: Dict[str, str]  # Variable name -> solution value
    image_mapping: Dict[str, str]  # Variable name -> Pokemon image path
    description: str = ""
    next_quiz_id: Optional[str] = None
    difficulty: Optional[Dict[str, Any]] = None
    is_random: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'quiz_id': self.quiz_id,
            'title': self.title,
            'equations': self.equations,
            'solution': self.solution,
            'image_mapping': self.image_mapping,
            'description': self.description,
            'next_quiz_id': self.next_quiz_id,
            'difficulty': self.difficulty,
            'is_random': self.is_random
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizData':
        """Create a QuizData instance from a dictionary."""
        return cls(
            quiz_id=data.get('quiz_id', ''),
            title=data.get('title', ''),
            equations=data.get('equations', []),
            solution=data.get('solution', {}),
            image_mapping=data.get('image_mapping', {}),
            description=data.get('description', ''),
            next_quiz_id=data.get('next_quiz_id'),
            difficulty=data.get('difficulty'),
            is_random=data.get('is_random', False)
        )


@dataclass
class QuizAttempt:
    """Strongly typed model for a quiz attempt."""
    quiz_id: str
    quiz_data: QuizData
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_answers: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'quiz_id': self.quiz_id,
            'quiz_data': self.quiz_data.to_dict(),
            'timestamp': self.timestamp,
            'user_answers': self.user_answers
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizAttempt':
        """Create a QuizAttempt instance from a dictionary."""
        quiz_data = QuizData.from_dict(data.get('quiz_data', {}))
        return cls(
            quiz_id=data.get('quiz_id', ''),
            quiz_data=quiz_data,
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            user_answers=data.get('user_answers', {})
        )


@dataclass
class SessionState:
    """Strongly typed model for session state."""
    solved_quizzes: Set[str] = field(default_factory=set)
    quiz_attempts: List[QuizAttempt] = field(default_factory=list)
    user_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'solved_quizzes': list(self.solved_quizzes),
            'quiz_attempts': [attempt.to_dict() for attempt in self.quiz_attempts],
            'user_name': self.user_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create a SessionState instance from a dictionary."""
        quiz_attempts = [
            QuizAttempt.from_dict(attempt_data)
            for attempt_data in data.get('quiz_attempts', [])
        ]
        return cls(
            solved_quizzes=set(data.get('solved_quizzes', [])),
            quiz_attempts=quiz_attempts,
            user_name=data.get('user_name')
        )

    def reset(self):
        """Reset the session state."""
        self.solved_quizzes.clear()
        self.quiz_attempts.clear()
        # Don't clear user_name on reset - that should persist 
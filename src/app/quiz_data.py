from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

@dataclass
class Pokemon:
    name: str
    image_path: str

@dataclass
class QuizAnswer:
    values: Dict[str, int]
    is_dynamic: bool = False
    relations: List[str] = None

@dataclass
class Quiz:
    id: str
    title: str
    description: str
    equations: List[str]
    answer: QuizAnswer
    section_id: str
    section_title: str
    display_number: int
    next_quiz_id: Optional[str] = None

@dataclass
class Section:
    id: str
    title: str
    description: str
    quizzes: List[Quiz]

@dataclass
class QuizData:
    pokemons: Dict[str, Pokemon]
    sections: List[Section]
    quizzes_by_id: Dict[str, Quiz]

def load_quiz_data(data_file: Path) -> QuizData:
    """
    Load and prepare quiz data from a JSON file.
    Returns a QuizData object containing all necessary information.
    """
    with open(data_file) as f:
        raw_data = json.load(f)

    # Prepare Pokemon data
    pokemons = {
        name: Pokemon(name=name, image_path=image_path)
        for name, image_path in raw_data['pokemons'].items()
    }

    # Prepare sections and quizzes
    sections = []
    quizzes_by_id = {}

    for section_data in raw_data['sections']:
        section_quizzes = []
        for idx, quiz_data in enumerate(section_data['quizzes'], 1):
            # Prepare answer data
            if isinstance(quiz_data['answer'], dict) and quiz_data['answer'].get('dynamic'):
                answer = QuizAnswer(
                    values={},  # Empty dict for dynamic answers
                    is_dynamic=True,
                    relations=quiz_data['answer']['relations']
                )
            else:
                answer = QuizAnswer(values=quiz_data['answer'])

            # Create quiz object
            quiz = Quiz(
                id=quiz_data['id'],
                title=quiz_data['title'],
                description=quiz_data['description'],
                equations=quiz_data['equations'],
                answer=answer,
                section_id=section_data['id'],
                section_title=section_data['title'],
                display_number=idx
            )
            section_quizzes.append(quiz)
            quizzes_by_id[quiz.id] = quiz

        # Create section object
        section = Section(
            id=section_data['id'],
            title=section_data['title'],
            description=section_data['description'],
            quizzes=section_quizzes
        )
        sections.append(section)

    # Set next_quiz_id for each quiz
    for section_idx, section in enumerate(sections):
        for quiz_idx, quiz in enumerate(section.quizzes):
            # If there's another quiz in this section
            if quiz_idx < len(section.quizzes) - 1:
                quiz.next_quiz_id = section.quizzes[quiz_idx + 1].id
            # If there's another section with quizzes
            elif section_idx < len(sections) - 1 and sections[section_idx + 1].quizzes:
                quiz.next_quiz_id = sections[section_idx + 1].quizzes[0].id

    return QuizData(
        pokemons=pokemons,
        sections=sections,
        quizzes_by_id=quizzes_by_id
    ) 
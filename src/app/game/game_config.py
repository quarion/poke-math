from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path

@dataclass
class Pokemon:
    name: str
    image_path: str
    tier: int = 1  # Default to tier 1 (common)

@dataclass
class QuizAnswer:
    values: Dict[str, int]

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
class GameConfig:
    pokemons: Dict[str, Pokemon]
    sections: List[Section]T
    quizzes_by_id: Dict[str, Quiz]

def load_pokemon_config(data_file: Path) -> Dict[str, Pokemon]:
    with open(data_file) as f:
        raw_data = json.load(f)

    pokemons = {}
    for name, pokemon_data in raw_data.items():
        pokemons[name] = Pokemon(
            name=name,
            image_path=pokemon_data.get('image_path', ''),
            tier=pokemon_data.get('tier', 1)
        )
    
    return pokemons

def load_game_config(data_file: Path, pokemon_file: Path) -> GameConfig:
    with open(data_file) as f:
        raw_data = json.load(f)
    
    # Load Pokemon data from separate file
    pokemons = load_pokemon_config(pokemon_file)

    # Prepare sections and quizzes
    sections = []
    quizzes_by_id = {}

    for section_data in raw_data['sections']:
        section_quizzes = []
        for idx, quiz_data in enumerate(section_data['quizzes'], 1):
            # Create quiz object with answer
            answer = QuizAnswer(values=quiz_data['answer'])
            
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

    return GameConfig(
        pokemons=pokemons,
        sections=sections,
        quizzes_by_id=quizzes_by_id
    )


def load_equation_difficulties(file_path: Path) -> List[Dict[str, Any]]:
    with open(file_path) as f:
        difficulties = json.load(f)
    return difficulties

"""
Unit tests for quiz data loading and structure.

Tests the loading and validation of quiz data from JSON files.
"""

from pathlib import Path

import pytest

from src.app.game.game_config import (
    GameConfig,
    Pokemon,
    Quiz,
    QuizAnswer,
    Section,
    load_game_config,
    load_pokemon_config,
)


@pytest.fixture
def test_data_path():
    return Path('tests/data/quizzes.json')

@pytest.fixture
def test_pokemon_data_path():
    return Path('tests/data/pokemons.json')

@pytest.fixture
def quiz_data(test_data_path, test_pokemon_data_path):
    return load_game_config(test_data_path, test_pokemon_data_path)

def test_load_quiz_data_structure(quiz_data):
    """Test if the quiz data is loaded with correct structure."""
    assert isinstance(quiz_data, GameConfig)
    assert isinstance(quiz_data.pokemons, dict)
    assert isinstance(quiz_data.sections, list)
    assert isinstance(quiz_data.quizzes_by_id, dict)

def test_pokemon_data_loading(quiz_data):
    """Test if Pokemon data is loaded correctly."""
    assert len(quiz_data.pokemons) == 4
    pikachu = quiz_data.pokemons['pikachu']
    assert isinstance(pikachu, Pokemon)
    assert pikachu.name == 'pikachu'
    assert pikachu.image_path == 'pikachu.png'
    assert pikachu.tier == 2  # Check tier value
    
    # Check other Pokémon
    assert 'bulbasaur' in quiz_data.pokemons
    assert 'charmander' in quiz_data.pokemons
    assert 'squirtle' in quiz_data.pokemons

def test_load_pokemon_config_function(test_pokemon_data_path):
    """Test if the load_pokemon_config function works correctly."""
    pokemons = load_pokemon_config(test_pokemon_data_path)
    assert len(pokemons) == 4
    assert isinstance(pokemons['pikachu'], Pokemon)
    assert pokemons['pikachu'].name == 'pikachu'
    assert pokemons['pikachu'].image_path == 'pikachu.png'
    assert pokemons['pikachu'].tier == 2

def test_section_structure(quiz_data):
    """Test if sections are structured correctly."""
    assert len(quiz_data.sections) == 1
    section = quiz_data.sections[0]
    
    assert isinstance(section, Section)
    assert section.id == 'test_section'
    assert section.title == 'Test Section'
    assert section.description == 'Section for testing'
    assert isinstance(section.quizzes, list)
    assert len(section.quizzes) == 2
    
    # Check if all quizzes in section are properly structured
    for quiz in section.quizzes:
        assert isinstance(quiz, Quiz)
        assert quiz.section_id == section.id
        assert quiz.section_title == section.title

def test_quiz_content(quiz_data):
    """Test if quiz content is loaded correctly."""
    # Test basic quiz
    basic_quiz = quiz_data.quizzes_by_id['test_basic']
    assert basic_quiz.title == 'Basic Test Quiz'
    assert len(basic_quiz.equations) == 1
    assert basic_quiz.equations[0] == '2 + {pikachu} = 5'
    
    # Test variable quiz
    var_quiz = quiz_data.quizzes_by_id['test_variables']
    assert var_quiz.title == 'Variable Test Quiz'
    assert len(var_quiz.equations) == 2
    assert '{x}' in var_quiz.equations[0]
    assert '{y}' in var_quiz.equations[0]
    assert '{z}' in var_quiz.equations[1]

def test_quiz_answers(quiz_data):
    """Test if quiz answers are structured correctly."""
    # Test basic quiz answers
    basic_quiz = quiz_data.quizzes_by_id['test_basic']
    assert isinstance(basic_quiz.answer, QuizAnswer)
    assert basic_quiz.answer.values == {'pikachu': 3}
    
    # Test variable quiz answers
    var_quiz = quiz_data.quizzes_by_id['test_variables']
    assert isinstance(var_quiz.answer, QuizAnswer)
    assert var_quiz.answer.values == {'x': 5, 'y': 5, 'z': 2}

def test_quiz_navigation(quiz_data):
    """Test if quiz navigation (next_quiz_id) is set up correctly."""
    basic_quiz = quiz_data.quizzes_by_id['test_basic']
    var_quiz = quiz_data.quizzes_by_id['test_variables']
    
    # Basic quiz should link to variable quiz
    assert basic_quiz.next_quiz_id == 'test_variables'
    # Variable quiz should have no next quiz
    assert var_quiz.next_quiz_id is None

def test_quiz_lookup(quiz_data):
    """Test if quizzes can be looked up by ID."""
    # Check if both quizzes are in the lookup dict
    assert 'test_basic' in quiz_data.quizzes_by_id
    assert 'test_variables' in quiz_data.quizzes_by_id
    
    # Check if the objects are the same as in sections
    section_quizzes = {quiz.id: quiz for quiz in quiz_data.sections[0].quizzes}
    assert quiz_data.quizzes_by_id['test_basic'] is section_quizzes['test_basic']
    assert quiz_data.quizzes_by_id['test_variables'] is section_quizzes['test_variables'] 
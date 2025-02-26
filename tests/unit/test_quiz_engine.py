"""
Unit tests for quiz engine functionality.

Tests the pure functions in the quiz_engine module that handle variable mappings
and answer checking logic.
"""

import pytest
from src.app.game.game_config import Quiz, QuizAnswer
from src.app.game.quiz_engine import create_variable_mappings, check_quiz_answers, get_display_variables

@pytest.fixture
def sample_quiz():
    """Fixture providing a sample quiz with variables."""
    return Quiz(
        id="test_quiz",
        title="Test Quiz",
        description="A test quiz with variables",
        equations=["{x} + {y} = 10", "{y} - {z} = 3"],
        answer=QuizAnswer(values={"x": 5, "y": 5, "z": 2}),
        section_id="test_section",
        section_title="Test Section",
        display_number=1
    )

@pytest.fixture
def sample_pokemon():
    """Fixture providing sample Pokemon data."""
    return {
        "pikachu": type("Pokemon", (), {"image_path": "pikachu.png"}),
        "bulbasaur": type("Pokemon", (), {"image_path": "bulbasaur.png"}),
        "charmander": type("Pokemon", (), {"image_path": "charmander.png"}),
        "squirtle": type("Pokemon", (), {"image_path": "squirtle.png"})
    }

def test_create_variable_mappings(sample_quiz, sample_pokemon):
    """Test creating variable mappings for a quiz."""
    # Test with a quiz that has variables
    mappings = create_variable_mappings(sample_quiz, sample_pokemon)
    assert len(mappings) == 3  # x, y, z
    
    # Check that all mappings are valid Pokemon
    valid_pokemon = set(sample_pokemon.keys())
    # Check all mappings are valid and unique Pokemon
    used_pokemon = set()
    for var, pokemon in mappings.items():
        assert pokemon in valid_pokemon
        assert pokemon not in used_pokemon, f"Pokemon {pokemon} used multiple times"
        used_pokemon.add(pokemon)
    
    # Test with a quiz that has no variables
    quiz_no_vars = Quiz(
        id="no_vars",
        title="No Variables",
        description="A quiz without variables",
        equations=["2 + {pikachu} = 5"],
        answer=QuizAnswer(values={"pikachu": 3}),
        section_id="test_section",
        section_title="Test Section",
        display_number=2
    )
    
    mappings = create_variable_mappings(quiz_no_vars, sample_pokemon)
    assert len(mappings) == 0

def test_check_quiz_answers(sample_quiz):
    """Test checking quiz answers."""
    # Test with correct answers
    correct_answers = {"x": 5, "y": 5, "z": 2}
    all_correct, correct_dict = check_quiz_answers(sample_quiz, correct_answers)
    assert all_correct is True
    assert all(correct_dict.values())
    
    # Test with some incorrect answers
    wrong_answers = {"x": 5, "y": 4, "z": 2}
    all_correct, correct_dict = check_quiz_answers(sample_quiz, wrong_answers)
    assert all_correct is False
    assert correct_dict["x"] is True
    assert correct_dict["y"] is False
    assert correct_dict["z"] is True
    
    # Test with missing answers
    incomplete_answers = {"x": 5, "z": 2}
    all_correct, correct_dict = check_quiz_answers(sample_quiz, incomplete_answers)
    assert all_correct is False
    assert correct_dict["y"] is False

def test_get_display_variables(sample_quiz, sample_pokemon, quiz_data):
    """Test getting display variables for a quiz."""
    # Create mappings
    mappings = {"x": "pikachu", "y": "bulbasaur", "z": "charmander"}
    
    # Test with a mock quiz_data object
    class MockQuizData:
        def __init__(self, pokemons):
            self.pokemons = pokemons
    
    mock_quiz_data = MockQuizData(sample_pokemon)
    
    # Get display variables
    display_vars = get_display_variables(mock_quiz_data, mappings)
    
    # Check that all Pokemon are included
    for pokemon, obj in sample_pokemon.items():
        assert display_vars[pokemon] == obj.image_path
    
    # Check that variables are mapped correctly
    assert display_vars["x"] == "pikachu.png"
    assert display_vars["y"] == "bulbasaur.png"
    assert display_vars["z"] == "charmander.png" 
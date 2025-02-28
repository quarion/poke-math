"""
Unit tests for quiz engine functionality.

Tests the pure functions in the quiz_engine module that handle answer checking logic
and display variables.
"""

import pytest
from src.app.game.game_config import Quiz, QuizAnswer
from src.app.game.quiz_engine import check_quiz_answers, get_display_variables

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

def test_check_quiz_answers(sample_quiz):
    """Test checking quiz answers."""
    # Test with correct answers
    correct_answers = {"x": 5, "y": 5, "z": 2}
    all_correct, correct_dict, all_answered = check_quiz_answers(sample_quiz, correct_answers)
    assert all_correct
    assert all(correct_dict.values())
    assert all_answered
    
    # Test with partially correct answers
    partial_answers = {"x": 5, "y": 4, "z": 2}
    all_correct, correct_dict, all_answered = check_quiz_answers(sample_quiz, partial_answers)
    assert not all_correct
    assert correct_dict["x"]
    assert not correct_dict["y"]
    assert correct_dict["z"]
    assert all_answered
    
    # Test with missing answers
    missing_answers = {"x": 5, "y": 5}
    all_correct, correct_dict, all_answered = check_quiz_answers(sample_quiz, missing_answers)
    assert not all_correct
    assert correct_dict["x"]
    assert correct_dict["y"]
    assert not correct_dict["z"]
    assert not all_answered

def test_get_display_variables(sample_pokemon):
    """Test getting display variables."""
    # Create a mock game config
    class MockGameConfig:
        def __init__(self, pokemons):
            self.pokemons = pokemons
    
    game_config = MockGameConfig(sample_pokemon)
    
    # Test with no image mapping
    display_vars = get_display_variables(game_config)
    assert len(display_vars) == 4
    assert display_vars["pikachu"] == "pikachu.png"
    assert display_vars["bulbasaur"] == "bulbasaur.png"
    
    # Test with image mapping
    image_mapping = {"x": "x.png", "y": "y.png"}
    display_vars = get_display_variables(game_config, image_mapping)
    assert len(display_vars) == 6  # 4 Pokemon + 2 mapped variables
    assert display_vars["x"] == "x.png"
    assert display_vars["y"] == "y.png"
    assert display_vars["pikachu"] == "pikachu.png" 
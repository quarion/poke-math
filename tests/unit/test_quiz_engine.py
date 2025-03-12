"""
Unit tests for quiz engine functionality.

Tests the pure functions in the quiz_engine module that handle answer checking logic
and display variables.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.app.game.game_config import Quiz, QuizAnswer, Pokemon
from src.app.game.quiz_engine import check_quiz_answers, get_display_variables, generate_random_quiz_data

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

@pytest.fixture
def mock_equation_generator():
    """Fixture providing a mock equation generator."""
    generator = MagicMock()
    
    # Create a mock quiz result
    mock_quiz = MagicMock()
    mock_quiz.solution.human_readable = {"x": 5, "y": 10, "z": 15}
    mock_quiz.equations = []
    
    # Add mock equations with formatted property
    eq1 = MagicMock()
    eq1.formatted = "{x} + {y} = 15"
    eq2 = MagicMock()
    eq2.formatted = "{y} - {z} = -5"
    mock_quiz.equations = [eq1, eq2]
    
    # Set up the generator to return our mock quiz
    generator.generate_equations.return_value = mock_quiz
    
    return generator

@pytest.fixture
def mock_game_config():
    """Fixture providing a mock game config with Pokemon of different tiers."""
    pokemons = {
        "rattata": Pokemon(name="Rattata", image_path="rattata.png", tier=1),
        "pidgey": Pokemon(name="Pidgey", image_path="pidgey.png", tier=1),
        "pikachu": Pokemon(name="Pikachu", image_path="pikachu.png", tier=2),
        "bulbasaur": Pokemon(name="Bulbasaur", image_path="bulbasaur.png", tier=2),
        "charizard": Pokemon(name="Charizard", image_path="charizard.png", tier=3),
        "blastoise": Pokemon(name="Blastoise", image_path="blastoise.png", tier=4),
        "mewtwo": Pokemon(name="Mewtwo", image_path="mewtwo.png", tier=5)
    }
    
    config = MagicMock()
    config.pokemons = pokemons
    return config

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

def test_generate_random_quiz_data_with_player_level(mock_game_config, mock_equation_generator):
    """Test that generate_random_quiz_data selects Pokemon based on player level."""
    # Test with player level 1 (should only get tier 1 Pokemon)
    difficulty = {'name': 'Easy', 'level': 1, 'params': {'min_value': 1, 'max_value': 10}}
    
    with patch('src.app.game.pokemon_selector.PokemonSelector.select_pokemon') as mock_select:
        # Mock the select_pokemon method to return specific Pokemon
        mock_select.return_value = ["rattata", "pidgey"]
        
        quiz_id, quiz_data = generate_random_quiz_data(
            mock_game_config, 
            difficulty, 
            mock_equation_generator,
            player_level=1
        )
        
        # Verify select_pokemon was called with correct parameters
        mock_select.assert_called_once_with(
            mock_game_config.pokemons, 
            1,  # player_level
            1,  # difficulty level
            count=3  # number of variables in the quiz
        )
        
        # Verify the quiz data structure
        assert quiz_id.startswith("random_")
        assert quiz_data['title'] == "Random Easy Quiz"
        assert len(quiz_data['equations']) == 2
        assert quiz_data['solution'] == {'x': '5', 'y': '10', 'z': '15'}
        assert len(quiz_data['image_mapping']) == 2  # Only 2 Pokemon were returned by mock

def test_generate_random_quiz_data_integration(mock_game_config, mock_equation_generator):
    """Integration test for generate_random_quiz_data with actual PokemonSelector."""
    # Test with different player levels
    difficulty = {'name': 'Medium', 'level': 3, 'params': {'min_value': 1, 'max_value': 20}}
    
    # Test with player level 1 (should only get tier 1 Pokemon)
    quiz_id, quiz_data = generate_random_quiz_data(
        mock_game_config, 
        difficulty, 
        mock_equation_generator,
        player_level=1
    )
    
    # Verify the quiz data structure
    assert quiz_id.startswith("random_")
    assert quiz_data['title'] == "Random Medium Quiz"
    
    # Check that all Pokemon in the image mapping are from tier 1
    for var, image_path in quiz_data['image_mapping'].items():
        # Find the Pokemon with this image path
        pokemon_name = None
        for name, pokemon in mock_game_config.pokemons.items():
            if pokemon.image_path == image_path:
                pokemon_name = name
                break
        
        assert pokemon_name is not None, f"Could not find Pokemon with image path {image_path}"
        assert mock_game_config.pokemons[pokemon_name].tier == 1, f"Expected tier 1 Pokemon, got {mock_game_config.pokemons[pokemon_name].tier}"
    
    # Test with player level 15 (should get tier 1-2 Pokemon)
    quiz_id, quiz_data = generate_random_quiz_data(
        mock_game_config, 
        difficulty, 
        mock_equation_generator,
        player_level=15
    )
    
    # Check that all Pokemon in the image mapping are from tier 1-2
    for var, image_path in quiz_data['image_mapping'].items():
        # Find the Pokemon with this image path
        pokemon_name = None
        for name, pokemon in mock_game_config.pokemons.items():
            if pokemon.image_path == image_path:
                pokemon_name = name
                break
        
        assert pokemon_name is not None, f"Could not find Pokemon with image path {image_path}"
        assert mock_game_config.pokemons[pokemon_name].tier <= 2, f"Expected tier 1-2 Pokemon, got {mock_game_config.pokemons[pokemon_name].tier}" 
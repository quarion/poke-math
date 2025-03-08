"""
Unit tests for Pokémon catching and XP rewards.
"""
import pytest
from unittest.mock import MagicMock

from src.app.game.session_manager import SessionManager
from src.app.game.game_config import Pokemon, GameConfig


def test_catch_pokemon(mock_session_manager):
    """Test catching a Pokémon and incrementing its count."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Reset state to ensure clean test
    session_manager.state.caught_pokemon = {}
    
    # Catch a Pokémon for the first time
    count = session_manager.catch_pokemon("pikachu")
    
    # Check that the Pokémon was caught
    assert count == 1
    assert session_manager.state.caught_pokemon["pikachu"] == 1
    
    # Catch the same Pokémon again
    count = session_manager.catch_pokemon("pikachu")
    
    # Check that the count was incremented
    assert count == 2
    assert session_manager.state.caught_pokemon["pikachu"] == 2


def test_get_caught_pokemon(mock_session_manager):
    """Test getting the caught Pokémon dictionary."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Reset state to ensure clean test
    session_manager.state.caught_pokemon = {
        "pikachu": 2,
        "bulbasaur": 1
    }
    
    # Get caught Pokémon
    caught_pokemon = session_manager.get_caught_pokemon()
    
    # Check that the caught Pokémon dictionary is correct
    assert caught_pokemon == {"pikachu": 2, "bulbasaur": 1}


def test_calculate_xp_reward(mock_session_manager):
    """Test calculating XP rewards for caught Pokémon and adventure completion."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Create a mock game config with Pokémon of different tiers
    pokemons = {
        "pikachu": Pokemon(name="Pikachu", image_path="pikachu.png", tier=2),
        "rattata": Pokemon(name="Rattata", image_path="rattata.png", tier=1),
        "mewtwo": Pokemon(name="Mewtwo", image_path="mewtwo.png", tier=5)
    }
    
    mock_game_config = MagicMock(spec=GameConfig)
    mock_game_config.pokemons = pokemons
    
    # Calculate XP reward for catching Pokémon of different tiers
    # Tier 1 (rattata) = 50 XP
    # Tier 2 (pikachu) = 100 XP
    # Tier 5 (mewtwo) = 800 XP
    # Difficulty 3 bonus = 50 * 3 = 150 XP
    # Total = 50 + 100 + 800 + 150 = 1100 XP
    xp_reward = session_manager.calculate_xp_reward(
        ["rattata", "pikachu", "mewtwo"],
        3,
        mock_game_config
    )
    
    # Check that the XP reward is correct
    assert xp_reward == 1100
    
    # Test with unknown Pokémon (should be ignored)
    xp_reward = session_manager.calculate_xp_reward(
        ["unknown", "pikachu"],
        1,
        mock_game_config
    )
    
    # Check that only the known Pokémon and difficulty bonus are counted
    # Tier 2 (pikachu) = 100 XP
    # Difficulty 1 bonus = 50 * 1 = 50 XP
    # Total = 100 + 50 = 150 XP
    assert xp_reward == 150
    
    # Test with empty caught Pokémon list (only difficulty bonus)
    xp_reward = session_manager.calculate_xp_reward(
        [],
        2,
        mock_game_config
    )
    
    # Check that only the difficulty bonus is counted
    # Difficulty 2 bonus = 50 * 2 = 100 XP
    assert xp_reward == 100 
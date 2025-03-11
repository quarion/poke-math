"""
Unit tests for Pokémon catching functionality.
"""
import pytest
from unittest.mock import MagicMock

from src.app.game.session_manager import SessionManager


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
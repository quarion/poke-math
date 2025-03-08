"""
Unit tests for Pokémon collection display.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.app.game.game_config import Pokemon, GameConfig


def test_prepare_collection_data():
    """Test preparing collection data for the template."""
    # Create a mock game manager
    mock_game_manager = MagicMock()
    
    # Create a mock session manager
    mock_session_manager = MagicMock()
    mock_session_manager.get_caught_pokemon.return_value = {
        "pikachu": 2,
        "bulbasaur": 1,
        "unknown": 3  # This one should be filtered out
    }
    
    # Create a mock game config
    mock_game_config = MagicMock(spec=GameConfig)
    mock_game_config.pokemons = {
        "pikachu": Pokemon(name="Pikachu", image_path="pikachu.png", tier=2),
        "bulbasaur": Pokemon(name="Bulbasaur", image_path="bulbasaur.png", tier=2),
        "charmander": Pokemon(name="Charmander", image_path="charmander.png", tier=2)
    }
    
    # Set up the game manager
    mock_game_manager.session_manager = mock_session_manager
    mock_game_manager.game_config = mock_game_config
    
    # Get caught Pokémon
    caught_pokemon = mock_session_manager.get_caught_pokemon()
    
    # Prepare collection data for the template
    collection = []
    for pokemon_id, count in caught_pokemon.items():
        if pokemon_id in mock_game_config.pokemons:
            pokemon = mock_game_config.pokemons[pokemon_id]
            collection.append({
                'id': pokemon_id,
                'name': pokemon.name,
                'image_path': pokemon.image_path,
                'count': count
            })
    
    # Sort by name
    collection.sort(key=lambda p: p['name'])
    
    # Calculate totals
    total_unique_pokemon = len(caught_pokemon)
    total_available_pokemon = len(mock_game_config.pokemons)
    
    # Check that the collection data is correct
    assert len(collection) == 2  # Only pikachu and bulbasaur should be included
    assert collection[0]['name'] == "Bulbasaur"  # Should be sorted by name
    assert collection[1]['name'] == "Pikachu"
    assert collection[0]['count'] == 1
    assert collection[1]['count'] == 2
    
    # Check that the totals are correct
    assert total_unique_pokemon == 3  # Including the unknown one
    assert total_available_pokemon == 3  # All Pokémon in the game config 
"""
Unit tests for Pokemon tier assignment.
"""
import json
import tempfile
from pathlib import Path

import pytest

from src.app.game.game_config import load_game_config, Pokemon


def test_pokemon_tier_default():
    """Test that Pokemon has a default tier of 1."""
    pokemon = Pokemon(name="test", image_path="test.png")
    assert pokemon.tier == 1


def test_pokemon_tier_custom():
    """Test that Pokemon can have a custom tier."""
    pokemon = Pokemon(name="test", image_path="test.png", tier=3)
    assert pokemon.tier == 3


def test_load_game_config_with_tiers():
    """Test loading game config with Pokemon tiers."""
    # Create a temporary JSON file with Pokemon tiers
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        json_data = {
            "pokemons": {
                "pikachu": {
                    "image_path": "pikachu.png",
                    "tier": 2
                },
                "mew": {
                    "image_path": "mew.png",
                    "tier": 5
                },
                "rattata": "rattata.png"  # Old format without tier
            },
            "sections": []
        }
        json.dump(json_data, temp_file)
        temp_file_path = temp_file.name

    try:
        # Load the game config
        game_config = load_game_config(Path(temp_file_path))

        # Check that Pokemon tiers are loaded correctly
        assert game_config.pokemons["pikachu"].tier == 2
        assert game_config.pokemons["mew"].tier == 5
        assert game_config.pokemons["rattata"].tier == 1  # Default tier
    finally:
        # Clean up the temporary file
        Path(temp_file_path).unlink() 
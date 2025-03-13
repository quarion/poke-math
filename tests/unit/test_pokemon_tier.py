"""
Unit tests for Pokemon tier assignment.
"""
import json
import tempfile
from pathlib import Path

from src.app.game.game_config import Pokemon, load_pokemon_config


def test_pokemon_tier_default():
    """Test that Pokemon has a default tier of 1."""
    pokemon = Pokemon(name="test", image_path="test.png")
    assert pokemon.tier == 1


def test_pokemon_tier_custom():
    """Test that Pokemon can have a custom tier."""
    pokemon = Pokemon(name="test", image_path="test.png", tier=3)
    assert pokemon.tier == 3


def test_load_pokemon_config_with_tiers():
    """Test loading Pokemon config with the new tier format."""
    # Create a temporary JSON file with Pokemon tiers in the new format
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        json_data = {
            "pokemons": {
                "pikachu": {
                    "image_path": "pikachu.png"
                },
                "mew": {
                    "image_path": "mew.png"
                },
                "rattata": {
                    "image_path": "rattata.png"
                }
            },
            "tiers": {
                "2": ["pikachu"],
                "5": ["mew"]
                # rattata not in any tier, should default to 1
            }
        }
        json.dump(json_data, temp_file)
        temp_file_path = temp_file.name

    try:
        # Load the Pokemon config
        pokemons = load_pokemon_config(Path(temp_file_path))

        # Check that Pokemon tiers are loaded correctly
        assert pokemons["pikachu"].tier == 2
        assert pokemons["mew"].tier == 5
        assert pokemons["rattata"].tier == 1  # Default tier
    finally:
        # Clean up the temporary file
        Path(temp_file_path).unlink() 
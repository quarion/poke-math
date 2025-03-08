"""
Unit tests for the PokemonSelector class.
"""
import pytest
from unittest.mock import MagicMock

from src.app.game.pokemon_selector import PokemonSelector
from src.app.game.game_config import Pokemon


def test_get_eligible_tiers():
    """Test that eligible tiers are correctly determined based on player level."""
    # Level 1-10 should only have tier 1
    assert PokemonSelector.get_eligible_tiers(1) == [1]
    assert PokemonSelector.get_eligible_tiers(10) == [1]
    
    # Level 11-20 should have tiers 1-2
    assert PokemonSelector.get_eligible_tiers(11) == [1, 2]
    assert PokemonSelector.get_eligible_tiers(20) == [1, 2]
    
    # Level 21-30 should have tiers 1-3
    assert PokemonSelector.get_eligible_tiers(21) == [1, 2, 3]
    assert PokemonSelector.get_eligible_tiers(30) == [1, 2, 3]
    
    # Level 31-40 should have tiers 1-4
    assert PokemonSelector.get_eligible_tiers(31) == [1, 2, 3, 4]
    assert PokemonSelector.get_eligible_tiers(40) == [1, 2, 3, 4]
    
    # Level 41+ should have all tiers
    assert PokemonSelector.get_eligible_tiers(41) == [1, 2, 3, 4, 5]
    assert PokemonSelector.get_eligible_tiers(50) == [1, 2, 3, 4, 5]


def test_calculate_adjusted_weight():
    """Test that weights are correctly adjusted based on tier and difficulty."""
    # Base weights: {1: 100, 2: 50, 3: 20, 4: 10, 5: 5}
    
    # At difficulty 1, weights should be the base weights
    assert PokemonSelector.calculate_adjusted_weight(1, 1) == 100
    assert PokemonSelector.calculate_adjusted_weight(2, 1) == 50
    assert PokemonSelector.calculate_adjusted_weight(5, 1) == 5
    
    # At higher difficulties, higher tiers should get more weight
    # Formula: W_T × (1 + (D-1)/6 × (T-1))
    
    # Tier 1 should always have the same weight regardless of difficulty
    assert PokemonSelector.calculate_adjusted_weight(1, 7) == 100
    
    # Tier 5 at difficulty 7 should have a significant boost
    # 5 * (1 + (7-1)/6 * (5-1)) = 5 * (1 + 1 * 4) = 5 * 5 = 25
    assert PokemonSelector.calculate_adjusted_weight(5, 7) == 25


def test_select_pokemon():
    """Test that Pokémon are selected based on level and difficulty."""
    # Create a set of test Pokémon
    pokemons = {
        "pikachu": Pokemon(name="Pikachu", image_path="pikachu.png", tier=2),
        "bulbasaur": Pokemon(name="Bulbasaur", image_path="bulbasaur.png", tier=2),
        "rattata": Pokemon(name="Rattata", image_path="rattata.png", tier=1),
        "mewtwo": Pokemon(name="Mewtwo", image_path="mewtwo.png", tier=5),
        "charizard": Pokemon(name="Charizard", image_path="charizard.png", tier=3)
    }
    
    # Test with level 1 (only tier 1 available)
    selected = PokemonSelector.select_pokemon(pokemons, player_level=1, difficulty=1, count=1)
    assert len(selected) == 1
    assert selected[0] == "rattata"  # Only tier 1 Pokémon
    
    # Test with level 15 (tiers 1-2 available)
    selected = PokemonSelector.select_pokemon(pokemons, player_level=15, difficulty=1, count=3)
    assert len(selected) == 3
    for pokemon in selected:
        assert pokemon in ["rattata", "pikachu", "bulbasaur"]
    
    # Test with level 50 (all tiers available)
    selected = PokemonSelector.select_pokemon(pokemons, player_level=50, difficulty=1, count=5)
    assert len(selected) == 5  # Should select all 5 Pokémon
    
    # Test with empty Pokémon list
    selected = PokemonSelector.select_pokemon({}, player_level=1, difficulty=1, count=1)
    assert len(selected) == 0


def test_select_pokemon_with_weights():
    """Test that Pokémon selection respects weights."""
    # Create a set of test Pokémon
    pokemons = {
        "rattata": Pokemon(name="Rattata", image_path="rattata.png", tier=1),
        "mewtwo": Pokemon(name="Mewtwo", image_path="mewtwo.png", tier=5)
    }
    
    # Mock random.choices to always return the first option (rattata)
    # This is to test that the weights are being calculated correctly
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("random.choices", lambda population, weights, k: [population[0]] * k)
        
        # At difficulty 1, rattata should be selected due to higher base weight
        selected = PokemonSelector.select_pokemon(pokemons, player_level=50, difficulty=1, count=1)
        assert selected[0] == "rattata"
        
        # Calculate expected weights
        rattata_weight = PokemonSelector.calculate_adjusted_weight(1, 1)  # 100
        mewtwo_weight = PokemonSelector.calculate_adjusted_weight(5, 1)   # 5
        
        # Verify weights are as expected
        assert rattata_weight == 100
        assert mewtwo_weight == 5 
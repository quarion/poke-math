"""
Unit tests for the PokemonSelector class.
"""

import pytest

from src.app.game.game_config import Pokemon
from src.app.game.pokemon_selector import PokemonSelector
from src.app.game.progression_config import TIER_BASE_WEIGHTS


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
    """Test that weights are correctly adjusted based on tier, difficulty, and player level."""
    # Tier 1 should always have the same weight regardless of difficulty and level
    base_weight_tier1 = TIER_BASE_WEIGHTS[1]
    assert PokemonSelector.calculate_adjusted_weight(1, 1, 1) == base_weight_tier1
    assert PokemonSelector.calculate_adjusted_weight(1, 7, 1) == base_weight_tier1
    assert PokemonSelector.calculate_adjusted_weight(1, 1, 50) == base_weight_tier1
    assert PokemonSelector.calculate_adjusted_weight(1, 7, 50) == base_weight_tier1
    
    # For higher tiers, test relative weights rather than specific values
    
    # 1. Difficulty effect: Higher difficulty should increase weight for higher tiers
    for tier in range(2, 6):
        if tier in TIER_BASE_WEIGHTS:
            low_difficulty_weight = PokemonSelector.calculate_adjusted_weight(tier, 1, 10)
            high_difficulty_weight = PokemonSelector.calculate_adjusted_weight(tier, 7, 10)
            assert high_difficulty_weight > low_difficulty_weight, f"Tier {tier} weight should increase with difficulty"
    
    # 2. Level effect: Higher player level should increase weight for higher tiers
    for tier in range(2, 6):
        if tier in TIER_BASE_WEIGHTS:
            low_level_weight = PokemonSelector.calculate_adjusted_weight(tier, 4, 10)
            high_level_weight = PokemonSelector.calculate_adjusted_weight(tier, 4, 50)
            assert high_level_weight > low_level_weight, f"Tier {tier} weight should increase with player level"
    
    # 3. Tier effect: Higher tiers should have higher weights at high difficulty/level
    weights_at_high_settings = [
        PokemonSelector.calculate_adjusted_weight(tier, 7, 50) 
        for tier in range(1, 6) if tier in TIER_BASE_WEIGHTS
    ]
    for i in range(1, len(weights_at_high_settings)):
        assert weights_at_high_settings[i] > weights_at_high_settings[i-1], "Higher tiers should have higher weights at high difficulty/level"


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
    # Create a set of test Pokémon with tiers that will be eligible at level 50
    pokemons = {
        "rattata": Pokemon(name="Rattata", image_path="rattata.png", tier=1),
        "pikachu": Pokemon(name="Pikachu", image_path="pikachu.png", tier=2)
    }
    
    # Test that weights are passed correctly to random.choices
    with pytest.MonkeyPatch.context() as mp:
        # Create a mock for random.choices that captures the weights parameter
        captured_weights = []
        def mock_choices(population, weights, k):
            captured_weights.append(weights)
            return [population[0]] * k
        
        mp.setattr("random.choices", mock_choices)
        
        # Call select_pokemon and verify weights were passed
        PokemonSelector.select_pokemon(pokemons, player_level=20, difficulty=3, count=1)
        
        # Verify that weights were passed to random.choices
        assert len(captured_weights) == 1
        assert len(captured_weights[0]) == 2  # Two Pokémon, two weights
        
        # Verify that weights are non-negative
        assert all(w > 0 for w in captured_weights[0]), "All weights should be positive" 
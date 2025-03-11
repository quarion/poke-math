"""
Test script to simulate player progression from Level 1 to 50.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.app.game.progression_manager import ProgressionManager
from src.app.game.game_config import Pokemon, GameConfig
from src.app.game.pokemon_selector import PokemonSelector
from src.app.game.progression_config import (
    BASE_XP,
    XP_MULTIPLIER,
    TIER_XP_REWARDS,
    TIER_BASE_WEIGHTS,
    TIER_UNLOCK_LEVELS
)


def test_xp_progression_curve():
    """Test the XP progression curve from Level 1 to 50."""
    # Calculate XP needed for each level
    xp_per_level = [ProgressionManager.calculate_xp_needed(level) for level in range(1, 51)]
    
    # Print XP needed for each level
    for level, xp in enumerate(xp_per_level, 1):
        print(f"Level {level}: {xp} XP")
    
    # Check that XP requirements increase with level
    for i in range(1, len(xp_per_level)):
        assert xp_per_level[i] > xp_per_level[i-1]
    
    # Check that the progression is reasonable
    # Level 10 should require less than 10x the XP of Level 1
    assert xp_per_level[9] < 10 * xp_per_level[0]
    # Level 50 should require less than 1000x the XP of Level 1
    assert xp_per_level[49] < 10000 * xp_per_level[0]


def test_pokemon_tier_distribution():
    """Test the distribution of Pokémon tiers at different player levels and difficulties."""
    # Create a set of test Pokémon
    pokemons = {
        f"pokemon_{i}": Pokemon(name=f"Pokemon {i}", image_path=f"pokemon_{i}.png", tier=(i % 5) + 1)
        for i in range(100)  # Create 100 Pokémon with tiers 1-5
    }
    
    # Test tier distribution at different player levels
    levels_to_test = [1, 10, 20, 30, 40, 50]
    difficulties_to_test = [1, 3, 5, 7]
    
    for level in levels_to_test:
        eligible_tiers = PokemonSelector.get_eligible_tiers(level)
        print(f"Level {level}: Eligible tiers {eligible_tiers}")
        
        # Store weighted averages for comparison
        weighted_avgs = {}
        
        for difficulty in difficulties_to_test:
            # Select 1000 Pokémon to get a good distribution
            selected = []
            for _ in range(10):  # Run 10 times to get 1000 Pokémon
                selected.extend(PokemonSelector.select_pokemon(pokemons, level, difficulty, count=100))
            
            # Count the tiers of selected Pokémon
            tier_counts = {}
            for pokemon_id in selected:
                tier = pokemons[pokemon_id].tier
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            # Print the distribution
            total = sum(tier_counts.values())
            print(f"  Difficulty {difficulty}: {', '.join([f'Tier {t}: {c} ({c/total:.1%})' for t, c in sorted(tier_counts.items())])}")
            
            # Check that only eligible tiers are selected
            for tier in tier_counts:
                assert tier in eligible_tiers
            
            # Calculate weighted average tier
            if total > 0:
                weighted_avg = sum(tier * count for tier, count in tier_counts.items()) / total
                weighted_avgs[difficulty] = weighted_avg
        
        # Check that higher difficulties favor higher tiers
        if level >= 11 and len(eligible_tiers) > 1:  # Only check if we have at least tier 2 unlocked
            for i in range(1, len(difficulties_to_test)):
                # Higher difficulties should have higher weighted average tier
                if difficulties_to_test[i] in weighted_avgs and difficulties_to_test[0] in weighted_avgs:
                    assert weighted_avgs[difficulties_to_test[i]] >= weighted_avgs[difficulties_to_test[0]]


def test_xp_rewards():
    """Test XP rewards for catching Pokémon and completing adventures."""
    # Create a mock game config with Pokémon of different tiers
    pokemons = {
        f"pokemon_{tier}": Pokemon(name=f"Pokemon {tier}", image_path=f"pokemon_{tier}.png", tier=tier)
        for tier in range(1, 6)  # Create 5 Pokémon with tiers 1-5
    }
    
    mock_game_config = MagicMock(spec=GameConfig)
    mock_game_config.pokemons = pokemons
    
    # Test XP rewards for different combinations of caught Pokémon and difficulties
    test_cases = [
        # (caught_pokemon, difficulty, expected_xp)
        (["pokemon_1"], 1, TIER_XP_REWARDS[1] + 50),  # Tier 1, Difficulty 1
        (["pokemon_5"], 1, TIER_XP_REWARDS[5] + 50),  # Tier 5, Difficulty 1
        (["pokemon_1", "pokemon_2", "pokemon_3"], 3, TIER_XP_REWARDS[1] + TIER_XP_REWARDS[2] + TIER_XP_REWARDS[3] + 150),  # Mixed tiers, Difficulty 3
        ([], 7, 350),  # No Pokémon, Difficulty 7 (only bonus XP)
    ]
    
    for caught_pokemon, difficulty, expected_xp in test_cases:
        # Calculate XP reward using ProgressionManager
        xp_reward = ProgressionManager.calculate_xp_reward(caught_pokemon, difficulty, mock_game_config)
        
        # Check that the XP reward is correct
        assert xp_reward == expected_xp 
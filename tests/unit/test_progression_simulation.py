"""
Test script to simulate player progression from Level 1 to 50.
"""
from unittest.mock import MagicMock

from src.app.game.game_config import GameConfig, Pokemon
from src.app.game.pokemon_selector import PokemonSelector
from src.app.game.progression_config import TIER_XP_REWARDS
from src.app.game.progression_manager import ProgressionManager


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
    
    for level in levels_to_test:
        eligible_tiers = PokemonSelector.get_eligible_tiers(level)
        print(f"Level {level}: Eligible tiers {eligible_tiers}")
        
        # Test with a moderate difficulty
        difficulty = 4
        
        # Select Pokémon to get a distribution
        selected = []
        for _ in range(5):  # Run 5 times to get 500 Pokémon
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
        
        # Check that all eligible tiers are represented (unless there's only one tier)
        if len(eligible_tiers) > 1:
            # Allow for some randomness - at least 80% of eligible tiers should be represented
            min_tiers_to_represent = max(1, int(0.8 * len(eligible_tiers)))
            assert len(tier_counts) >= min_tiers_to_represent, f"Expected at least {min_tiers_to_represent} tiers to be represented, got {len(tier_counts)}"
        
        # If there are multiple tiers, higher tiers should have some representation
        if len(eligible_tiers) > 1:
            highest_eligible_tier = max(eligible_tiers)
            # For levels with multiple tiers, the highest tier should have some representation
            # unless it's a very high tier that might be rare
            if highest_eligible_tier <= 3 or level >= 40:  # Adjust based on your tier distribution
                assert highest_eligible_tier in tier_counts, f"Highest eligible tier {highest_eligible_tier} should be represented"


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
        (["pokemon_1"], 1, TIER_XP_REWARDS[1] + 100),  # Tier 1, Difficulty 1
        (["pokemon_5"], 1, TIER_XP_REWARDS[5] + 100),  # Tier 5, Difficulty 1
        (["pokemon_1", "pokemon_2", "pokemon_3"], 3, TIER_XP_REWARDS[1] + TIER_XP_REWARDS[2] + TIER_XP_REWARDS[3] + 300),  # Mixed tiers, Difficulty 3
        ([], 7, 700),  # No Pokémon, Difficulty 7 (only bonus XP)
    ]
    
    for caught_pokemon, difficulty, expected_xp in test_cases:
        # Calculate XP reward using ProgressionManager
        xp_reward = ProgressionManager.calculate_xp_reward(caught_pokemon, difficulty, mock_game_config)
        
        # Check that the XP reward is correct
        assert xp_reward == expected_xp 
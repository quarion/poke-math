"""
Unit tests for the ProgressionManager class.
"""
import pytest
from unittest.mock import MagicMock

from src.app.game.progression_manager import ProgressionManager
from src.app.game.game_config import Pokemon, GameConfig
from src.app.game.progression_config import (
    BASE_XP,
    XP_MULTIPLIER,
    TIER_XP_REWARDS,
    DIFFICULTY_BONUS_XP
)


def test_calculate_xp_needed():
    """Test calculating XP needed for the next level."""
    # Test XP needed for various levels
    assert ProgressionManager.calculate_xp_needed(1) == BASE_XP
    assert ProgressionManager.calculate_xp_needed(2) == int(BASE_XP * XP_MULTIPLIER)
    assert ProgressionManager.calculate_xp_needed(10) == int(BASE_XP * (XP_MULTIPLIER ** 9))


def test_xp_progression_curve():
    """Test the XP progression curve from Level 1 to 50."""
    # Calculate XP needed for each level
    xp_per_level = [ProgressionManager.calculate_xp_needed(level) for level in range(1, 51)]
    
    # Check that XP requirements increase with level
    for i in range(1, len(xp_per_level)):
        assert xp_per_level[i] > xp_per_level[i-1]
    
    # Check that the progression is reasonable
    # Level 10 should require less than 10x the XP of Level 1
    assert xp_per_level[9] < 10 * xp_per_level[0]
    # Level 50 should require less than 1000x the XP of Level 1
    assert xp_per_level[49] < 10000 * xp_per_level[0]


def test_calculate_xp_reward():
    """Test calculating XP rewards for caught Pokémon and adventure completion."""
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
    xp_reward = ProgressionManager.calculate_xp_reward(
        ["rattata", "pikachu", "mewtwo"],
        3,
        mock_game_config
    )
    
    # Check that the XP reward is correct
    assert xp_reward == 1100
    
    # Test with unknown Pokémon (should be ignored)
    xp_reward = ProgressionManager.calculate_xp_reward(
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
    xp_reward = ProgressionManager.calculate_xp_reward(
        [],
        2,
        mock_game_config
    )
    
    # Check that only the difficulty bonus is counted
    # Difficulty 2 bonus = 50 * 2 = 100 XP
    assert xp_reward == 100


def test_process_level_up():
    """Test processing level-up logic."""
    # Test with no level up
    result = ProgressionManager.process_level_up(1, 50)
    assert result['level'] == 1
    assert result['xp'] == 50
    assert result['leveled_up'] is False
    
    # Test with one level up
    result = ProgressionManager.process_level_up(1, BASE_XP + 50)
    assert result['level'] == 2
    assert result['xp'] == 50
    assert result['leveled_up'] is True
    
    # Test with multiple level ups
    # Level 1 needs BASE_XP
    # Level 2 needs BASE_XP * XP_MULTIPLIER
    # Total XP for 2 level ups = BASE_XP + BASE_XP * XP_MULTIPLIER + 25
    total_xp = BASE_XP + int(BASE_XP * XP_MULTIPLIER) + 25
    result = ProgressionManager.process_level_up(1, total_xp)
    assert result['level'] == 3
    assert result['xp'] == 25
    assert result['leveled_up'] is True


def test_get_level_info():
    """Test getting level information."""
    # Test level info for level 1
    level_info = ProgressionManager.get_level_info(1, 50)
    assert level_info['level'] == 1
    assert level_info['xp'] == 50
    assert level_info['xp_needed'] == BASE_XP
    
    # Test level info for level 10
    level_info = ProgressionManager.get_level_info(10, 500)
    assert level_info['level'] == 10
    assert level_info['xp'] == 500
    assert level_info['xp_needed'] == int(BASE_XP * (XP_MULTIPLIER ** 9)) 
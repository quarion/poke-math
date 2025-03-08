"""
Unit tests for player progression system.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.app.game.session_manager import SessionManager
from src.app.game.models import SessionState


def test_calculate_xp_needed(mock_session_manager):
    """Test XP calculation for different levels."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Test XP needed for different levels
    assert session_manager.calculate_xp_needed(1) == 100
    assert session_manager.calculate_xp_needed(2) == 120
    assert session_manager.calculate_xp_needed(5) == int(100 * (1.2 ** 4))
    assert session_manager.calculate_xp_needed(10) == int(100 * (1.2 ** 9))


def test_add_xp_no_level_up(mock_session_manager):
    """Test adding XP without leveling up."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Reset state to ensure clean test
    session_manager.state.level = 1
    session_manager.state.xp = 0
    
    # Add XP but not enough to level up
    leveled_up = session_manager.add_xp(50)
    
    # Check that XP was added but level didn't change
    assert session_manager.state.xp == 50
    assert session_manager.state.level == 1
    assert not leveled_up


def test_add_xp_with_level_up(mock_session_manager):
    """Test adding XP with level up."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Reset state to ensure clean test
    session_manager.state.level = 1
    session_manager.state.xp = 0
    
    # Add XP enough to level up
    leveled_up = session_manager.add_xp(150)
    
    # Check that level increased and XP is the remainder
    assert session_manager.state.level == 2
    assert session_manager.state.xp == 50  # 150 - 100 = 50
    assert leveled_up


def test_add_xp_multiple_level_ups(mock_session_manager):
    """Test adding XP with multiple level ups."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Reset state to ensure clean test
    session_manager.state.level = 1
    session_manager.state.xp = 0
    
    # Add XP enough for multiple level ups
    # Level 1 needs 100 XP
    # Level 2 needs 120 XP
    # Level 3 needs 144 XP
    # Total: 364 XP for 3 levels
    leveled_up = session_manager.add_xp(400)
    
    # Check that level increased multiple times
    assert session_manager.state.level == 4
    # 400 - 100 - 120 - 144 = 36
    assert session_manager.state.xp == 36
    assert leveled_up


def test_get_level_info(mock_session_manager):
    """Test getting level information."""
    # Use the mock session manager from fixtures
    session_manager = mock_session_manager
    
    # Set initial state
    session_manager.state.level = 3
    session_manager.state.xp = 50
    
    # Get level info
    level_info = session_manager.get_level_info()
    
    # Check level info
    assert level_info['level'] == 3
    assert level_info['xp'] == 50
    assert level_info['xp_needed'] == int(100 * (1.2 ** 2))  # XP needed for level 3 
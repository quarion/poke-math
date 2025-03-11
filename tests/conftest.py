"""
Shared pytest fixtures for poke-math tests.

This module contains fixtures that can be used across multiple test files.
Pytest automatically discovers and makes these fixtures available to all test files.
"""

import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from pathlib import Path
from src.app.game.game_config import load_game_config
from src.app.game.game_manager import GameManager


@pytest.fixture(scope="session")
def test_data_path() -> Path:
    """
    Fixture providing the path to test data file.
    Uses session scope as the path never changes during test run.
    """
    return Path('tests/data/quizzes.json')


@pytest.fixture(scope="session")
def test_pokemon_data_path() -> Path:
    """
    Fixture providing the path to test Pokemon data file.
    Uses session scope as the path never changes during test run.
    """
    return Path('tests/data/pokemons.json')


@pytest.fixture
def quiz_data(test_data_path, test_pokemon_data_path):
    """
    Fixture providing loaded quiz data.
    Creates fresh data for each test to avoid state contamination.
    """
    return load_game_config(test_data_path, test_pokemon_data_path)


@pytest.fixture
def mock_session_manager():
    """Create a SessionManager that doesn't depend on Flask session."""
    from src.app.game.session_manager import SessionManager, SessionState
    from unittest.mock import MagicMock, patch
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.load_user_data.return_value = {'session_state': {}}
    
    # Patch _get_or_create_user_id to avoid Flask session dependency
    with patch('src.app.game.session_manager.SessionManager._get_or_create_user_id', return_value='test_user'):
        
        # Create session manager with mock storage and test user ID
        session_manager = SessionManager(storage=mock_storage, user_id='test_user')
        
        # Initialize with empty state
        session_manager.state = SessionState(
            solved_quizzes=set(),
            quiz_attempts=[],
            user_name=None,
            level=1,
            xp=0,
            caught_pokemon={}
        )
        
        # Mock _save_state to avoid storage calls
        session_manager._save_state = MagicMock()
        
        return session_manager


@pytest.fixture
def game_manager(quiz_data, mock_session_manager):
    """
    Fixture providing a fresh GameManager instance for each test.
    Creates new instance to ensure tests start with clean state.
    """
    return GameManager.initialize_from_session(quiz_data, session_manager=mock_session_manager)


@pytest.fixture
def solved_game_manager(game_manager):
    """
    Fixture providing a GameManager with some quizzes already solved.
    Useful for testing state-dependent behavior.
    """
    # Solve the basic quiz
    game_manager.check_answers('test_basic', {'pikachu': 3})
    return game_manager 
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


@pytest.fixture
def quiz_data(test_data_path):
    """
    Fixture providing loaded quiz data.
    Creates fresh data for each test to avoid state contamination.
    """
    return load_game_config(test_data_path)


@pytest.fixture
def mock_session_manager():
    """Create a SessionManager that doesn't depend on Flask session."""
    from src.app.game.session_manager import SessionManager, SessionState
    session_manager = SessionManager()
    # Initialize with empty state
    session_manager.state = SessionState()
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
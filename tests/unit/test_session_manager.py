"""
Unit tests for session manager functionality.

Tests the SessionManager class that handles session persistence and state management.
"""

import pytest
from src.app.game.session_manager import SessionManager, SessionState

@pytest.fixture
def session_state():
    """Fixture providing a fresh session state."""
    return SessionState()

@pytest.fixture
def session_manager():
    """Fixture providing a fresh session manager."""
    return SessionManager()

def test_session_state_creation(session_state):
    """Test if session state is created with correct initial state."""
    assert len(session_state.solved_quizzes) == 0
    assert len(session_state.variable_mappings) == 0

def test_session_state_reset(session_state):
    """Test resetting session state."""
    # Add some data
    session_state.solved_quizzes.add('test_quiz')
    session_state.variable_mappings['test_quiz'] = {'x': 'pikachu'}
    
    # Reset
    session_state.reset()
    
    # Check if reset worked
    assert len(session_state.solved_quizzes) == 0
    assert len(session_state.variable_mappings) == 0

def test_session_manager_creation(session_manager):
    """Test if session manager is created with correct initial state."""
    assert len(session_manager.solved_quizzes) == 0
    assert len(session_manager.state.variable_mappings) == 0

def test_mark_quiz_solved(session_manager):
    """Test marking a quiz as solved."""
    # Mark quiz as solved
    session_manager.mark_quiz_solved('test_basic')
    
    # Check if it's marked as solved
    assert session_manager.is_quiz_solved('test_basic')
    assert 'test_basic' in session_manager.solved_quizzes
    
    # Check if another quiz is not marked as solved
    assert not session_manager.is_quiz_solved('test_variables')

def test_variable_mappings(session_manager):
    """Test variable mappings functionality."""
    # Test with no mappings initially
    assert session_manager.get_variable_mappings('test_quiz') == {}
    assert not session_manager.has_variable_mappings('test_quiz')
    
    # Set mappings
    test_mappings = {'x': 'pikachu', 'y': 'bulbasaur', 'z': 'charmander'}
    session_manager.set_variable_mappings('test_quiz', test_mappings)
    
    # Check if mappings are stored
    assert session_manager.has_variable_mappings('test_quiz')
    assert session_manager.get_variable_mappings('test_quiz') == test_mappings
    
    # Check if mappings for other quizzes are still empty
    assert not session_manager.has_variable_mappings('other_quiz')
    assert session_manager.get_variable_mappings('other_quiz') == {}

def test_session_manager_reset(session_manager):
    """Test resetting session manager."""
    # Solve some quizzes
    session_manager.mark_quiz_solved('test_basic')
    session_manager.mark_quiz_solved('test_variables')
    
    # Create mappings
    test_mappings = {'x': 'pikachu', 'y': 'bulbasaur', 'z': 'charmander'}
    session_manager.set_variable_mappings('test_quiz', test_mappings)
    
    # Check state before reset
    assert len(session_manager.solved_quizzes) == 2
    assert len(session_manager.state.variable_mappings) > 0
    
    # Reset
    session_manager.reset()
    
    # Check state after reset
    assert len(session_manager.solved_quizzes) == 0
    assert len(session_manager.state.variable_mappings) == 0 
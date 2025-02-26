"""
Unit tests for session manager functionality.

Tests the SessionManager class that handles session persistence and state management.
"""

import pytest
from src.app.session_manager import SessionManager, SessionState
from src.app.game_config import load_game_config

@pytest.fixture
def session_state():
    """Fixture providing a fresh session state."""
    return SessionState()

@pytest.fixture
def session_manager(quiz_data):
    """Fixture providing a fresh session manager."""
    return SessionManager(quiz_data)

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

def test_session_manager_creation(session_manager, quiz_data):
    """Test if session manager is created with correct initial state."""
    assert session_manager.game_config == quiz_data
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

def test_get_or_create_variable_mappings(session_manager):
    """Test getting or creating variable mappings."""
    # Get mappings for a quiz with variables
    mappings = session_manager.get_or_create_variable_mappings('test_variables')
    
    # Check if mappings were created
    assert len(mappings) == 3  # x, y, z
    
    # Check if mappings are stored in state
    assert 'test_variables' in session_manager.state.variable_mappings
    assert session_manager.state.variable_mappings['test_variables'] == mappings
    
    # Get mappings again - should be the same
    mappings2 = session_manager.get_or_create_variable_mappings('test_variables')
    assert mappings2 == mappings
    
    # Get mappings for a non-existent quiz
    empty_mappings = session_manager.get_or_create_variable_mappings('non_existent')
    assert empty_mappings == {}

def test_get_quiz_state(session_manager):
    """Test getting quiz state."""
    # Get state for a basic quiz
    basic_state = session_manager.get_quiz_state('test_basic')
    
    # Check state properties
    assert basic_state['quiz'].id == 'test_basic'
    assert 'pikachu' in basic_state['pokemon_vars']
    assert not basic_state['is_solved']
    
    # Get state for a quiz with variables
    var_state = session_manager.get_quiz_state('test_variables')
    
    # Check state properties
    assert var_state['quiz'].id == 'test_variables'
    assert len(var_state['variable_mappings']) == 3  # x, y, z
    
    # Get state for a non-existent quiz
    assert session_manager.get_quiz_state('non_existent') is None

def test_session_manager_reset(session_manager):
    """Test resetting session manager."""
    # Solve some quizzes
    session_manager.mark_quiz_solved('test_basic')
    session_manager.mark_quiz_solved('test_variables')
    
    # Create mappings
    session_manager.get_quiz_state('test_variables')
    
    # Check state before reset
    assert len(session_manager.solved_quizzes) == 2
    assert len(session_manager.state.variable_mappings) > 0
    
    # Reset
    session_manager.reset()
    
    # Check state after reset
    assert len(session_manager.solved_quizzes) == 0
    assert len(session_manager.state.variable_mappings) == 0 
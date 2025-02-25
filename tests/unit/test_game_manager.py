"""
Unit tests for game manager functionality.

Tests the GameManager class that orchestrates the game and holds the game configuration.
"""

import pytest
from pathlib import Path
from src.app.game.game_config import load_game_config
from src.app.game.game_manager import GameManager
from src.app.game.session_manager import SessionManager, SessionState

@pytest.fixture
def test_data_path():
    return Path('tests/data/quizzes.json')

@pytest.fixture
def quiz_data(test_data_path):
    return load_game_config(test_data_path)

@pytest.fixture
def mock_session_manager():
    """Create a SessionManager that doesn't depend on Flask session."""
    session_manager = SessionManager()
    # Initialize with empty state
    session_manager.state = SessionState()
    return session_manager

@pytest.fixture
def quiz_session(quiz_data, mock_session_manager):
    """Fixture providing a fresh GameManager instance with injected SessionManager."""
    return GameManager.start_session(quiz_data, session_manager=mock_session_manager)

def test_game_manager_creation(quiz_session, quiz_data):
    """Test if GameManager is created with correct initial state."""
    assert isinstance(quiz_session, GameManager)
    assert quiz_session.game_config == quiz_data
    assert isinstance(quiz_session.session_manager, SessionManager)
    assert len(quiz_session.solved_quizzes) == 0

def test_quiz_state_retrieval(quiz_session):
    """Test getting quiz state from GameManager."""
    # Test basic quiz state
    basic_state = quiz_session.get_quiz_state('test_basic')
    assert basic_state is not None
    assert basic_state['quiz'].id == 'test_basic'
    assert 'pikachu' in basic_state['pokemon_vars']
    assert not basic_state['is_solved']
    assert not basic_state['variable_mappings']  # No special variables
    
    # Test variable quiz state
    var_state = quiz_session.get_quiz_state('test_variables')
    assert var_state is not None
    assert var_state['quiz'].id == 'test_variables'
    assert len(var_state['variable_mappings']) == 3  # x, y, z
    
    # Test non-existent quiz
    assert quiz_session.get_quiz_state("non_existent_quiz") is None

def test_variable_mappings_persistence(quiz_session):
    """Test if variable mappings persist between state retrievals."""
    # Get state twice
    state1 = quiz_session.get_quiz_state('test_variables')
    state2 = quiz_session.get_quiz_state('test_variables')
    
    # Mappings should be the same
    assert state1['variable_mappings'] == state2['variable_mappings']
    
    # All variables should be mapped to valid Pokémon
    mappings = state1['variable_mappings']
    assert len(mappings) == 3  # x, y, z
    valid_pokemon = {'pikachu', 'bulbasaur', 'charmander', 'squirtle'}
    for var, pokemon in mappings.items():
        assert pokemon in valid_pokemon

def test_get_or_create_variable_mappings(quiz_session):
    """Test the get_or_create_variable_mappings method in GameManager."""
    # Get mappings for a quiz with variables
    mappings = quiz_session.get_or_create_variable_mappings('test_variables')
    
    # Check if mappings were created
    assert len(mappings) == 3  # x, y, z
    
    # Check if mappings are stored in session manager
    assert quiz_session.session_manager.has_variable_mappings('test_variables')
    assert quiz_session.session_manager.get_variable_mappings('test_variables') == mappings
    
    # Get mappings again - should be the same
    mappings2 = quiz_session.get_or_create_variable_mappings('test_variables')
    assert mappings2 == mappings
    
    # Get mappings for a non-existent quiz
    empty_mappings = quiz_session.get_or_create_variable_mappings('non_existent')
    assert empty_mappings == {}

def test_answer_checking_basic(quiz_session):
    """Test answer checking for basic quizzes."""
    # Test correct answer
    result = quiz_session.check_answers('test_basic', {'pikachu': 3})
    assert result['correct'] is True
    assert 'test_basic' in quiz_session.solved_quizzes
    
    # Test wrong answer
    result = quiz_session.check_answers('test_basic', {'pikachu': 4})
    assert result['correct'] is False

def test_answer_checking_with_variables(quiz_session):
    """Test answer checking for quizzes with special variables."""
    # Get the state to establish variable mappings
    state = quiz_session.get_quiz_state('test_variables')
    
    # Submit correct answers
    answers = {'x': 5, 'y': 5, 'z': 2}
    result = quiz_session.check_answers('test_variables', answers)
    assert result['correct'] is True
    assert 'test_variables' in quiz_session.solved_quizzes
    
    # Test wrong answers
    wrong_answers = {'x': 5, 'y': 5, 'z': 3}
    result = quiz_session.check_answers('test_variables', wrong_answers)
    assert result['correct'] is False

def test_game_manager_reset(quiz_session):
    """Test GameManager reset functionality."""
    # Solve some quizzes
    quiz_session.check_answers('test_basic', {'pikachu': 3})
    quiz_session.check_answers('test_variables', {'x': 5, 'y': 5, 'z': 2})
    assert len(quiz_session.solved_quizzes) == 2
    
    # Get state for variable quiz to create mappings
    quiz_session.get_quiz_state('test_variables')
    # Access variable_mappings through session_manager.state
    assert len(quiz_session.session_manager.state.variable_mappings) > 0
    
    # Reset session
    quiz_session.reset()
    assert len(quiz_session.solved_quizzes) == 0
    # Access variable_mappings through session_manager.state
    assert len(quiz_session.session_manager.state.variable_mappings) == 0

def test_pokemon_image_paths(quiz_session):
    """Test if Pokemon image paths are correctly included in quiz state."""
    # Test basic quiz
    basic_state = quiz_session.get_quiz_state('test_basic')
    assert basic_state['pokemon_vars']['pikachu'] == 'pikachu.png'
    
    # Test variable quiz
    var_state = quiz_session.get_quiz_state('test_variables')
    for var in ['x', 'y', 'z']:
        assert var in var_state['pokemon_vars']
        # The image path should match one of the valid Pokémon image paths
        assert var_state['pokemon_vars'][var] in {'pikachu.png', 'bulbasaur.png', 'charmander.png', 'squirtle.png'} 
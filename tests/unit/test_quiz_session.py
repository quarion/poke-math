"""
Unit tests for quiz session management and state.

Tests the session handling, state management, and answer checking functionality.
"""

import pytest
from pathlib import Path
from src.app.quiz_data import load_quiz_data
from src.app.quiz_session import QuizSession

@pytest.fixture
def test_data_path():
    return Path('tests/data/quizzes.json')

@pytest.fixture
def quiz_data(test_data_path):
    return load_quiz_data(test_data_path)

@pytest.fixture
def quiz_session(quiz_data):
    """Fixture to provide a fresh quiz session for each test"""
    return QuizSession.create_new(quiz_data)

def test_session_creation(quiz_session):
    """Test if session is created with correct initial state."""
    assert isinstance(quiz_session, QuizSession)
    assert len(quiz_session.solved_quizzes) == 0
    # Access variable_mappings through session_manager.state
    assert len(quiz_session.session_manager.state.variable_mappings) == 0

def test_quiz_state_retrieval(quiz_session):
    """Test getting quiz state."""
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

def test_session_reset(quiz_session):
    """Test session reset functionality."""
    # Solve both quizzes
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
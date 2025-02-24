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
from src.app.quiz_data import load_quiz_data
from src.app.quiz_session import QuizSession


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
    return load_quiz_data(test_data_path)


@pytest.fixture
def quiz_session(quiz_data):
    """
    Fixture providing a fresh quiz session for each test.
    Creates new session to ensure tests start with clean state.
    """
    return QuizSession.create_new(quiz_data)


@pytest.fixture
def solved_quiz_session(quiz_session):
    """
    Fixture providing a quiz session with some quizzes already solved.
    Useful for testing state-dependent behavior.
    """
    # Solve the basic quiz
    quiz_session.check_answers('test_basic', {'pikachu': 3})
    return quiz_session 
import pytest
from fractions import Fraction

# Import the module to test
from src.app.equations.equations import MathEquationGenerator


@pytest.fixture
def generator():
    """Create a MathEquationGenerator instance for tests."""
    return MathEquationGenerator()


def test_basic_generation(generator):
    """Test that basic equation generation works."""
    quiz = generator.generate_quiz(num_unknowns=1, num_equations=1)
    
    # Basic assertions
    assert len(quiz.equations) == 1
    assert len(quiz.solution.human_readable) == 1
    assert quiz.equations[0].formatted is not None
    assert quiz.equations[0].symbolic is not None


def test_very_simple_config(generator):
    """Test the very simple configuration works properly."""
    quiz = generator.generate_quiz(
        num_unknowns=1,
        complexity=1,
        num_equations=1,
        max_elements=3,
        allow_fractions=False,
        allow_division=False,
        very_simple=True,
        ensure_operation=False
    )
    
    # Assertions for very simple mode
    assert len(quiz.equations) == 1
    equation_text = quiz.equations[0].formatted
    assert 'x' in equation_text  # Should use 'x' variable
    
    # Solution should be a positive integer for very_simple mode
    x_value = quiz.solution.human_readable['x']
    assert isinstance(x_value, int)
    assert x_value > 0


def test_very_simple_with_small_max_elements(generator):
    """Test very simple mode with small max_elements (bug reproduction)."""
    # Test with max_elements=2 (should still work)
    quiz = generator.generate_quiz(
        num_unknowns=1,
        complexity=1,
        num_equations=1,
        max_elements=2,
        allow_fractions=False,
        allow_division=False,
        very_simple=True,
        ensure_operation=False
    )
    assert len(quiz.equations) == 1
    
    # Test with max_elements=1 (should still work)
    quiz = generator.generate_quiz(
        num_unknowns=1,
        complexity=1,
        num_equations=1,
        max_elements=1,
        allow_fractions=False,
        allow_division=False,
        very_simple=True,
        ensure_operation=False
    )
    assert len(quiz.equations) == 1
    
    # Test with max_elements=0 (edge case)
    quiz = generator.generate_quiz(
        num_unknowns=1,
        complexity=1,
        num_equations=1,
        max_elements=0,
        allow_fractions=False,
        allow_division=False,
        very_simple=True,
        ensure_operation=False
    )
    assert len(quiz.equations) == 1


def test_multiple_unknowns(generator):
    """Test generation with multiple unknown variables."""
    quiz = generator.generate_quiz(
        num_unknowns=2,
        num_equations=2,
        complexity=1
    )
    assert len(quiz.equations) == 2
    assert len(quiz.solution.human_readable) == 2


def test_allow_fractions(generator):
    """Test that fractions are allowed in solutions when specified."""
    quiz = generator.generate_quiz(
        num_unknowns=1,
        allow_fractions=True,
        complexity=2
    )
    # At least one value should be a fraction (but this is random so not guaranteed)
    # We'll check the type is correct even if the random generation sometimes gives integers
    for val in quiz.solution.human_readable.values():
        assert isinstance(val, (int, Fraction))


@pytest.mark.parametrize("max_elements", [0, 1, 2, 3])
def test_very_simple_with_parameterized_max_elements(generator, max_elements):
    """Test very simple mode with different max_elements values using pytest parametrization."""
    quiz = generator.generate_quiz(
        num_unknowns=1,
        complexity=1,
        num_equations=1,
        max_elements=max_elements,
        allow_fractions=False,
        allow_division=False,
        very_simple=True,
        ensure_operation=False
    )
    assert len(quiz.equations) == 1
    # Verify that the solution is valid
    assert len(quiz.solution.human_readable) == 1
    assert 'x' in quiz.solution.human_readable


def test_worksheet_generation(generator):
    """Test generation of a worksheet with multiple problems."""
    num_problems = 5
    worksheet = generator.generate_quiz_worksheet(
        num_problems=num_problems,
        num_unknowns=1,
        complexity=1
    )
    assert len(worksheet) == num_problems
    
    # Check each quiz in the worksheet
    for quiz in worksheet:
        assert len(quiz.equations) == 1
        assert len(quiz.solution.human_readable) == 1 
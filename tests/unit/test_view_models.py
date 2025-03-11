"""
Unit tests for view models functionality.

Tests the replace_variables_with_images method in the view_models module,
focusing on the bug where variables like 'x' in equations can cause issues
with Pokémon names like 'quaxly' that contain those letters.
"""

import pytest
from src.app.view_models import QuizViewModel


@pytest.fixture
def basic_quiz_view_model():
    """Fixture providing a basic quiz view model with simple variables."""
    return QuizViewModel(
        id="test_quiz",
        title="Test Quiz",
        equations=["x + 10 = y", "x * z = 10"],
        variables=["x", "y", "z"],
        image_mapping={
            "x": "pikachu.png",
            "y": "bulbasaur.png",
            "z": "charmander.png"
        },
        description="A test quiz with simple variables",
        is_random=False,
        difficulty=None,
        next_quiz_id=None,
        has_next=False
    )


@pytest.fixture
def problematic_quiz_view_model():
    """Fixture providing a quiz view model with problematic variable and Pokémon names."""
    return QuizViewModel(
        id="problematic_quiz",
        title="Problematic Variable Quiz",
        equations=["x + y = 20", "z * 2 = 10"],
        variables=["x", "y", "z"],
        image_mapping={
            "x": "pikachu.png",
            "y": "bulbasaur.png",
            "z": "quaxly.png"  # Pokémon name contains 'x' which is also a variable
        },
        description="A quiz with problematic variable and Pokémon names",
        is_random=False,
        difficulty=None,
        next_quiz_id=None,
        has_next=False
    )


def test_replace_variables_with_images_basic(basic_quiz_view_model):
    """Test basic variable replacement in simple equations."""
    equation = "x + 10 = y"
    result = basic_quiz_view_model.replace_variables_with_images(equation)
    
    # Check that variables were replaced with image tags
    assert 'src="/static/images/pikachu.png"' in result  # x
    assert 'src="/static/images/bulbasaur.png"' in result  # y
    assert 'class="pokemon-var"' in result
    
    # The equation should no longer contain the original variable names as standalone variables
    assert " x " not in result
    assert " y " not in result


def test_replace_variables_with_images_bug(problematic_quiz_view_model):
    """Test the bug where a variable like 'x' can cause issues with Pokémon names like 'quaxly'."""
    # This test simulates what happens when we try to display the image path itself
    # For example, when debugging or showing the image mapping
    image_path = "quaxly.png"  # This contains 'x' which is also a variable
    result = problematic_quiz_view_model.replace_variables_with_images(image_path)
    
    # The bug: 'x' in 'quaxly.png' should not be replaced with an image tag
    # The current implementation will replace 'x' with its image tag, resulting in a mangled path
    
    # The image path should remain unchanged
    assert result == "quaxly.png", "The image path should not be modified"
    
    # It should not contain any image tags
    assert '<img' not in result, "No HTML tags should be inserted into the image path" 
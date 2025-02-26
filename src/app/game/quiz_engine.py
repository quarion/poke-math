import random
from typing import Dict, Tuple
from src.app.game.game_config import Quiz, GameConfig


def create_variable_mappings(quiz: Quiz, available_pokemons: Dict[str, object]) -> Dict[str, str]:
    """
    Create mappings for special variables (x, y, z) to Pokemon names.
    This is a pure function that can be tested in isolation.
    
    Args:
        quiz: The quiz containing equations with variables
        available_pokemons: Dictionary of available Pokemon names to Pokemon objects
        
    Returns:
        Dictionary mapping variable names to Pokemon names
    """
    # Find all special variables used in the equations
    special_vars = {'x', 'y', 'z'}
    used_vars = set()

    for eq in quiz.equations:
        for var in special_vars:
            if f'{{{var}}}' in eq:
                used_vars.add(var)

    # Create new mappings if needed
    if not used_vars:
        return {}

    # Create mappings using a shuffled list of Pokemon names
    pokemon_names = list(available_pokemons.keys())
    random.shuffle(pokemon_names)

    return {
        var: pokemon_names[i]
        for i, var in enumerate(used_vars)
    }


def check_quiz_answers(quiz: Quiz, user_answers: Dict[str, int]) -> Tuple[bool, Dict[str, bool], bool]:
    """
    Check the user's answers for a quiz.
    This is a pure function that can be tested in isolation.
    
    Args:
        quiz: The quiz to check answers for
        user_answers: Dictionary of variable names to user-provided values
        
    Returns:
        Tuple of (all_correct, correct_answers_dict, all_answered)
    """
    # Map variable names to their actual values
    mapped_answers = {}
    
    # Get all expected answer variables
    expected_vars = set(quiz.answer.values.keys())
    
    # Track which variables were answered
    answered_vars = set()

    for var, value in user_answers.items():
        if var in expected_vars:
            # For all variables (special or Pokemon), use the integer value directly
            mapped_answers[var] = int(value)
            answered_vars.add(var)

    # Check each answer that was provided
    correct_answers = {}
    for var, answer in quiz.answer.values.items():
        if var in mapped_answers:
            correct_answers[var] = mapped_answers[var] == answer
        else:
            # If the variable wasn't provided, mark it as not correct
            correct_answers[var] = False

    all_correct = all(correct_answers.values())
    all_answered = answered_vars == expected_vars

    return all_correct, correct_answers, all_answered


def get_display_variables(game_config: GameConfig,
                          variable_mappings: Dict[str, str]) -> Dict[str, str]:
    """
    Get display variables for a quiz, including Pokemon image paths.
    
    Args:
        quiz: The quiz to get variables for
        game_config: The quiz data containing Pokemon information
        variable_mappings: Dictionary mapping variables to Pokemon names
        
    Returns:
        Dictionary mapping variable names to image paths
    """
    # Create display variables dictionary with all Pokemon
    display_vars = {
        name: pokemon.image_path
        for name, pokemon in game_config.pokemons.items()
    }

    # Add any special variable mappings
    for var, pokemon_name in variable_mappings.items():
        display_vars[var] = game_config.pokemons[pokemon_name].image_path

    return display_vars

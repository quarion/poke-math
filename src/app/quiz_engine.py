import random
from typing import Dict, Set, Tuple
from src.app.game_config import Quiz, GameConfig


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


def check_quiz_answers(quiz: Quiz, user_answers: Dict[str, int]) -> Tuple[bool, Dict[str, bool]]:
    """
    Check the user's answers for a quiz.
    This is a pure function that can be tested in isolation.
    
    Args:
        quiz: The quiz to check answers for
        user_answers: Dictionary of variable names to user-provided values
        
    Returns:
        Tuple of (all_correct, correct_answers_dict)
    """
    # Map variable names to their actual values
    mapped_answers = {}

    for var, value in user_answers.items():
        # For all variables (special or Pokemon), use the integer value directly
        mapped_answers[var] = int(value)

    # Check each answer
    correct_answers = {
        var: mapped_answers.get(var, 0) == answer
        for var, answer in quiz.answer.values.items()
    }

    all_correct = all(correct_answers.values())

    return all_correct, correct_answers


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

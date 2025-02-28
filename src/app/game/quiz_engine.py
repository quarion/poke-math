import random
import uuid
from typing import Dict, Tuple, Any
from src.app.game.game_config import Quiz, GameConfig


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
                          image_mapping: Dict[str, str] = None) -> Dict[str, str]:
    """
    Get display variables for a quiz, including Pokemon image paths.
    
    Args:
        game_config: The game configuration containing Pokemon information
        image_mapping: Optional dictionary mapping variables to image paths
        
    Returns:
        Dictionary mapping variable names to image paths
    """
    # Create display variables dictionary with all Pokemon
    display_vars = {
        name: pokemon.image_path
        for name, pokemon in game_config.pokemons.items()
    }

    # Add any image mappings if provided
    if image_mapping:
        display_vars.update(image_mapping)

    return display_vars


def generate_random_quiz_data(game_config, difficulty: Dict[str, Any], equation_generator) -> Tuple[str, Dict[str, Any]]:
    """
    Generate random quiz data for the given difficulty.

    Args:
        game_config: The game configuration containing Pokemon information
        difficulty: Difficulty configuration
        equation_generator: The equation generator to use

    Returns:
        Tuple of (quiz_id, quiz_data)
    """
    # Generate a random equation using the MathEquationGenerator
    quiz = equation_generator.generate_quiz(**difficulty['params'])

    # Create a unique ID for the random quiz
    random_quiz_id = f"random_{uuid.uuid4().hex[:8]}"

    # Create Pokemon variable mappings for the random variables
    image_mapping = {}
    available_pokemon_images = {name: pokemon.image_path for name, pokemon in game_config.pokemons.items()}

    # Get a list of Pokemon names and shuffle it to ensure random selection
    pokemon_names = list(available_pokemon_images.keys())
    random.shuffle(pokemon_names)

    # Assign a unique Pokemon to each variable
    for i, var in enumerate(quiz.solution.human_readable.keys()):
        # Use modulo to avoid index errors if there are more variables than Pokemon
        pokemon_name = pokemon_names[i % len(pokemon_names)]
        image_mapping[var] = available_pokemon_images[pokemon_name]
        # Remove the used Pokemon to ensure it's not reused
        pokemon_names.remove(pokemon_name)
        available_pokemon_images.pop(pokemon_name)

    # Format equations to ensure consistent variable format
    formatted_equations = []
    for eq in quiz.equations:
        formatted_eq = eq.formatted
        formatted_equations.append(formatted_eq)

    # Create quiz data structure
    quiz_data = {
        'quiz_id': random_quiz_id,
        'title': f"Random {difficulty['name']} Quiz",
        'equations': formatted_equations,
        'solution': {var: str(val) for var, val in quiz.solution.human_readable.items()},
        'difficulty': difficulty,
        'image_mapping': image_mapping,
        'description': f"A randomly generated {difficulty['name'].lower()} difficulty quiz."
    }

    return random_quiz_id, quiz_data
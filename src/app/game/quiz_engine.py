import uuid
from typing import Any, Dict, Tuple

from src.app.game.game_config import GameConfig, Quiz
from src.app.game.pokemon_selector import PokemonSelector


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


def generate_random_quiz_data(game_config, difficulty: Dict[str, Any], equation_generator, player_level: int = 1) -> Tuple[str, Dict[str, Any]]:
    """
    Generate random quiz data for the given difficulty and player level.
    
    The function uses PokemonSelector to select appropriate Pokémon based on the player's level
    and the difficulty of the quiz. Higher player levels unlock higher tier Pokémon, and
    higher difficulties increase the probability of selecting higher tier Pokémon.
    
    Args:
        game_config: The game configuration containing Pokemon information
        difficulty: Difficulty configuration with 'name' and 'level' keys
        equation_generator: The equation generator to use
        player_level: Current player level, determines which Pokémon tiers are available
    
    Returns:
        Tuple of (quiz_id, quiz_data)
    """
    # Generate a random equation using the EquationsGeneratorV2
    quiz = equation_generator.generate_equations(difficulty['params'])

    # Create a unique ID for the random quiz
    random_quiz_id = f"random_{uuid.uuid4().hex[:8]}"

    # Create Pokemon variable mappings for the random variables
    image_mapping = {}
    
    # Get the number of variables needed for this quiz
    num_variables = len(quiz.solution.human_readable.keys())
    
    # Use PokemonSelector to select appropriate Pokemon based on player level and difficulty
    difficulty_level = difficulty.get('level', 1)  # Default to 1 if not specified
    selected_pokemon = PokemonSelector.select_pokemon(
        game_config.pokemons, 
        player_level, 
        difficulty_level, 
        count=num_variables
    )
    
    # Map variables to selected Pokemon
    variables = list(quiz.solution.human_readable.keys())
    for i, pokemon_name in enumerate(selected_pokemon):
        if i < len(variables):  # Ensure we don't go out of bounds
            var = variables[i]
            image_mapping[var] = game_config.pokemons[pokemon_name].image_path

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
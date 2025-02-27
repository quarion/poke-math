"""
PokeMath Web Application
------------------------
This module contains the Flask web application for PokeMath, including:
- Main application setup and configuration
- Route definitions and handlers
- View models and helper functions
"""

import os
import uuid
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from flask import Flask, render_template, request, redirect, url_for, jsonify, session

from src.app.game.game_config import load_game_config, load_equation_difficulties
from src.app.game.game_manager import GameManager
from src.app.equations.equations_generator import MathEquationGenerator
from src.app.storage.session_factory import create_session_manager


# -----------------------------------------------------------------------------
# Application Setup and Configuration
# -----------------------------------------------------------------------------

def create_flask_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    flask_app = Flask(__name__,
                      template_folder=str(Path(__file__).parent.parent / 'templates'),
                      static_folder=str(Path(__file__).parent.parent / 'static'))
    flask_app.secret_key = 'your-secret-key-here'  # Required for session management

    # Add version info to all templates
    @flask_app.context_processor
    def inject_version_info():
        return {'version_info': get_version_info()}

    return flask_app


def get_version_info():
    """
    Get application version information from environment.
    
    Returns:
        dict: Version information
    """
    return {
        'version': os.environ.get('COMMIT_SHA', 'development')
    }


# -----------------------------------------------------------------------------
# Application Initialization
# -----------------------------------------------------------------------------

# Create Flask app
app = create_flask_app()

# Load game configuration
GAME_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'quizzes.json'
GAME_CONFIG = load_game_config(GAME_CONFIG_PATH)

# Load equation difficulties
DIFFICULTY_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'equation_difficulties.json'
EQUATION_DIFFICULTIES = load_equation_difficulties(DIFFICULTY_CONFIG_PATH)

# Create equation generator
EQUATION_GENERATOR = MathEquationGenerator()

# Get Pokemon images from the game configuration
POKEMON_IMAGES = [pokemon.image_path for pokemon in GAME_CONFIG.pokemons.values()]


# -----------------------------------------------------------------------------
# View Models
# -----------------------------------------------------------------------------

@dataclass
class QuizViewModel:
    """Strongly typed view model for quiz templates."""
    # Basic quiz information
    id: str
    title: str
    equations: List[str]
    variables: List[str]
    pokemon_vars: Dict[str, str]  # Variable name -> Pokemon image path

    # Optional fields with default values must come after required fields
    description: str = ""
    is_random: bool = False
    difficulty: Optional[Dict[str, Any]] = None
    next_quiz_id: Optional[str] = None
    has_next: bool = False

    def get_pokemon_image(self, variable: str) -> str:
        """Get the Pokemon image filename for a variable."""
        return self.pokemon_vars.get(variable, "default.png")

    def has_difficulty(self) -> bool:
        """Check if this quiz has difficulty information."""
        return self.difficulty is not None

    def replace_variables_with_images(self, equation: str) -> str:
        """Replace variable placeholders with Pokemon images in an equation."""
        result = equation
        for var, img_path in self.pokemon_vars.items():
            img_tag = f'<img src="/static/images/{img_path}" class="pokemon-var" alt="{var}">'

            # Replace direct variable name
            result = result.replace(var, img_tag)

            # Also replace {var} placeholders
            placeholder = "{" + var + "}"
            result = result.replace(placeholder, img_tag)

        return result

    @classmethod
    def from_random_quiz(cls, quiz_data: Dict[str, Any], pokemon_vars: Dict[str, str]) -> 'QuizViewModel':
        """Create a QuizViewModel from a random quiz dictionary."""
        return cls(
            id=quiz_data['quiz_id'],
            title='Random Mission',
            equations=quiz_data['equations'],
            variables=list(quiz_data['solution'].keys()),
            pokemon_vars=pokemon_vars,
            description='',
            is_random=True,
            difficulty=quiz_data['difficulty'],
            next_quiz_id=None,
            has_next=False
        )

    @classmethod
    def from_regular_quiz(cls, quiz_data: Any, pokemon_vars: Dict[str, str]) -> 'QuizViewModel':
        """Create a QuizViewModel from a regular quiz object."""
        return cls(
            id=quiz_data.id,
            title=quiz_data.title,
            equations=quiz_data.equations,
            variables=list(quiz_data.answer.values.keys()),
            pokemon_vars=pokemon_vars,
            description=quiz_data.description,
            is_random=False,
            next_quiz_id=quiz_data.next_quiz_id,
            has_next=quiz_data.next_quiz_id is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the view model to a dictionary for debugging."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'equations': self.equations,
            'variables': self.variables,
            'pokemon_vars': self.pokemon_vars,
            'is_random': self.is_random,
            'difficulty': self.difficulty,
            'next_quiz_id': self.next_quiz_id,
            'has_next': self.has_next
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"QuizViewModel(id={self.id}, title='{self.title}', variables={self.variables})"


@dataclass
class QuizResultViewModel:
    """Strongly typed view model for quiz results."""
    correct: bool
    correct_answers: Dict[str, bool]  # Variable name -> bool indicating if correct
    all_answered: bool
    correct_count: int
    total_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert the view model to a dictionary for debugging and API responses."""
        return {
            'correct': self.correct,
            'correct_answers': self.correct_answers,
            'all_answered': self.all_answered,
            'correct_count': self.correct_count,
            'total_count': self.total_count
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"QuizResultViewModel(correct={self.correct}, score={self.correct_count}/{self.total_count})"


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def create_game_manager() -> GameManager:
    """
    Create a GameManager instance with session data loaded from persistent storage.
    
    Returns:
        GameManager: Instance with loaded session data
        
    Raises:
        Exception: If Firestore storage is enabled but not available
    """
    try:
        # Create a session manager with Firestore persistence
        # Set use_firestore=False to use Flask session storage instead
        session_manager = create_session_manager(use_firestore=True)

        # Create a GameManager with the session manager
        return GameManager.initialize_from_session(GAME_CONFIG, session_manager)
    except Exception as e:
        # Log the error
        app.logger.error(f"Error connecting to Firestore: {e}")
        # Re-raise the exception to be handled by route handlers
        raise


def process_quiz_answers(user_answers: Dict[str, int],
                         expected_answers: Dict[str, Union[int, str]]) -> QuizResultViewModel:
    """
    Process quiz answers for both random and regular quizzes.
    
    Args:
        user_answers: Dictionary of user-provided answers {var: value}
        expected_answers: Dictionary of expected answers {var: value}
        
    Returns:
        QuizResultViewModel: Standardized result object containing quiz results data
    """
    # Check each answer
    correct_answers = {}
    all_correct = True
    all_answered = len(user_answers) == len(expected_answers)

    for var, expected in expected_answers.items():
        if var in user_answers:
            # For random quizzes, expected might be a string
            expected_value = int(float(expected)) if isinstance(expected, str) else expected
            is_correct = user_answers[var] == expected_value

            correct_answers[var] = is_correct
            if not is_correct:
                all_correct = False
        else:
            all_answered = False

    # Count correct answers
    correct_count = sum(1 for is_correct in correct_answers.values() if is_correct)
    total_count = len(expected_answers)

    # Return a strongly typed result view model
    return QuizResultViewModel(
        correct=all_correct and all_answered,
        correct_answers=correct_answers,
        all_answered=all_answered,
        correct_count=correct_count,
        total_count=total_count
    )


def parse_user_answers(form_data: Dict[str, str], solution_keys: List[str]) -> Dict[str, int]:
    """
    Parse and filter user answers from form data.
    
    Args:
        form_data: Form data from request
        solution_keys: Keys expected in the solution
        
    Returns:
        Dict[str, int]: Filtered and parsed user answers
    """
    return {
        key: int(value)
        for key, value in form_data.items()
        if value.strip() and key in solution_keys  # Only include non-empty values for solution variables
    }


def render_quiz_template(
        is_random: bool,
        quiz_data: Union[Dict[str, Any], object],
        pokemon_vars: Dict[str, str],
        result: Optional[QuizResultViewModel] = None,
        user_answers: Optional[Dict[str, int]] = None,
        already_solved: bool = False
) -> Any:
    """
    Render the quiz template for both random and regular quizzes.
    
    Args:
        is_random: Whether this is a random quiz
        quiz_data: Quiz data (dictionary for random quizzes, object for regular)
        pokemon_vars: Dictionary mapping variable names to Pokemon image paths
        result: Optional result object from checking answers
        user_answers: Optional dictionary of user submitted answers
        already_solved: Flag indicating if the quiz is already solved
        
    Returns:
        Response: Flask response with rendered template
    """
    if user_answers is None:
        user_answers = {}

    # Create a strongly-typed view model based on the quiz type
    quiz = (QuizViewModel.from_random_quiz(quiz_data, pokemon_vars) if is_random
            else QuizViewModel.from_regular_quiz(quiz_data, pokemon_vars))

    template_args = {
        'quiz': quiz,  # Strongly typed view model
        'result': result,
        'user_answers': user_answers,
        'already_solved': already_solved
    }

    return render_template('quiz.html', **template_args)


def generate_random_quiz_data(difficulty: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate random quiz data for the given difficulty.
    
    Args:
        difficulty: Difficulty configuration
        
    Returns:
        Dict: Generated quiz data
    """
    # Generate a random equation using the MathEquationGenerator
    quiz = EQUATION_GENERATOR.generate_quiz(**difficulty['params'])

    # Create a unique ID for the random quiz
    random_quiz_id = f"random_{uuid.uuid4().hex[:8]}"

    # Create Pokemon variable mappings for the random variables
    pokemon_vars = {}
    available_pokemon_images = {name: pokemon.image_path for name, pokemon in GAME_CONFIG.pokemons.items()}

    for var in quiz.solution.human_readable.keys():
        # Select a random Pokemon image from the game configuration
        random_pokemon_name = random.choice(list(available_pokemon_images.keys()))
        pokemon_vars[var] = available_pokemon_images[random_pokemon_name]

    # Format equations to ensure consistent variable format
    formatted_equations = []
    for eq in quiz.equations:
        formatted_eq = eq.formatted
        formatted_equations.append(formatted_eq)

    # Create quiz data structure
    quiz_data = {
        'quiz_id': random_quiz_id,
        'equations': formatted_equations,
        'solution': {var: str(val) for var, val in quiz.solution.human_readable.items()},
        'difficulty': difficulty,
        'pokemon_vars': pokemon_vars
    }

    return random_quiz_id, quiz_data


# -----------------------------------------------------------------------------
# Route Handlers
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    """Display the home page with welcome message."""
    return render_template('index.html')


@app.route('/exercises')
def all_exercises():
    """Display all available community exercises."""
    game_manager = create_game_manager()
    return render_template('all_exercises.html',
                           title="Community Exercises",
                           sections=GAME_CONFIG.sections,
                           solved_quizzes=game_manager.session_manager.solved_quizzes)


@app.route('/profile')
def profile():
    """Display the user's profile with points and progress."""
    game_manager = create_game_manager()
    solved_count = len(game_manager.solved_quizzes)
    # Each solved quiz is worth 1 point
    points = solved_count

    return render_template('profile.html',
                           points=points,
                           solved_count=solved_count)


@app.route('/new-exercise')
def new_exercise():
    """Display difficulty selection screen for random exercise generation."""
    return render_template('new_exercise.html',
                           difficulties=EQUATION_DIFFICULTIES)


@app.route('/generate-random-exercise/<difficulty_id>')
def generate_random_exercise(difficulty_id):
    """Generate a random exercise based on the selected difficulty."""
    # Find the selected difficulty
    selected_difficulty = next((d for d in EQUATION_DIFFICULTIES if d['id'] == difficulty_id), None)

    if not selected_difficulty:
        return "Difficulty not found", 404

    # Generate random quiz data
    random_quiz_id, quiz_data = generate_random_quiz_data(selected_difficulty)

    # Initialize random_quizzes in session if needed
    if 'random_quizzes' not in session:
        session['random_quizzes'] = {}

    # Store the quiz data in the session
    session['random_quizzes'][random_quiz_id] = quiz_data
    session.modified = True

    # Redirect to the quiz page
    return redirect(url_for('random_quiz', quiz_id=random_quiz_id))


@app.route('/random-quiz/<quiz_id>', methods=['GET', 'POST'])
def random_quiz(quiz_id):
    """Display a randomly generated quiz and process answers."""
    game_manager = create_game_manager()

    # Get the stored quiz from the session
    if 'random_quizzes' not in session or quiz_id not in session['random_quizzes']:
        return render_template('quiz_not_found.html', quiz_id=quiz_id)

    stored_quiz = session['random_quizzes'][quiz_id]
    # Add quiz_id to the stored_quiz for the template
    stored_quiz['quiz_id'] = quiz_id

    # Check if this quiz is already solved
    already_solved = game_manager.session_manager.is_quiz_solved(quiz_id)

    # Pre-populate answers if the quiz is already solved
    user_answers = {}
    if already_solved:
        # Show the correct answers for an already solved quiz
        user_answers = {var: int(float(val)) for var, val in stored_quiz['solution'].items()}

    if request.method == 'POST':
        # If the quiz is already solved, don't process the answers again
        if already_solved:
            return render_template('already_solved.html', quiz_id=quiz_id)

        # Parse and filter user answers
        user_answers = parse_user_answers(request.form, stored_quiz['solution'].keys())

        # Process answers
        result = process_quiz_answers(user_answers, stored_quiz['solution'])

        # Update session data if all answers are correct
        if result.correct:
            game_manager.session_manager.mark_quiz_solved(quiz_id)

        # Record the quiz attempt - this will update an existing attempt or create a new one
        game_manager.session_manager.add_quiz_attempt(
            quiz_id=quiz_id,
            quiz_data=stored_quiz,
            score=result.correct_count,
            total=result.total_count,
            completed=result.all_answered
        )

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result.to_dict())

        # For regular form submissions (fallback)
        return render_quiz_template(
            is_random=True,
            quiz_data=stored_quiz,
            pokemon_vars=stored_quiz['pokemon_vars'],
            result=result,
            user_answers=user_answers,
            already_solved=already_solved
        )

    # GET request - track that the user viewed this quiz (for incomplete tracking)
    if not already_solved:
        # Add or update quiz attempt with initial data
        game_manager.session_manager.add_quiz_attempt(
            quiz_id=quiz_id,
            quiz_data=stored_quiz,
            score=0,
            total=len(stored_quiz['solution']),
            completed=False
        )

    # Display the quiz with a flag indicating if it's already solved
    return render_quiz_template(
        is_random=True,
        quiz_data=stored_quiz,
        pokemon_vars=stored_quiz['pokemon_vars'],
        user_answers=user_answers,
        already_solved=already_solved
    )


@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    """Display a predefined quiz and process answers."""
    game_manager = create_game_manager()

    # Check if quiz exists in current GAME_CONFIG
    quiz_exists = False
    is_random = quiz_id.startswith('random_')

    if is_random:
        # For random quizzes, we need to check the session data
        for attempt in game_manager.session_manager.get_quiz_attempts():
            if attempt['quiz_id'] == quiz_id and 'quiz_data' in attempt:
                quiz_exists = True
                break
    else:
        # For regular quizzes, check the game config
        quiz_state = game_manager.get_quiz_state(quiz_id)
        if quiz_state:
            quiz_exists = True

    if not quiz_exists:
        # Quiz no longer exists, show an error page
        return render_template('quiz_not_found.html', quiz_id=quiz_id)

    # Check if this quiz is already solved
    already_solved = game_manager.session_manager.is_quiz_solved(quiz_id)

    # Handle random quiz through the dedicated route
    if is_random:
        return redirect(url_for('random_quiz', quiz_id=quiz_id))

    # Process regular quiz
    quiz_state = game_manager.get_quiz_state(quiz_id)
    quiz = quiz_state['quiz']
    pokemon_vars = quiz_state['pokemon_vars']

    # Pre-populate answers if the quiz is already solved
    user_answers = {}
    if already_solved:
        # Show the correct answers for an already solved quiz
        user_answers = quiz.answer.values

    # Handle form submission
    if request.method == 'POST':
        # If the quiz is already solved, don't process the answers again
        if already_solved:
            return render_template('already_solved.html', quiz_id=quiz_id)

        # Parse user answers
        user_answers = parse_user_answers(request.form, quiz.answer.values.keys())

        # Check answers
        result_data = game_manager.check_answers(quiz_id, user_answers)

        # Create result view model
        result = QuizResultViewModel(
            correct=result_data['correct'],
            correct_answers=result_data['correct_answers'],
            all_answered=result_data['all_answered'],
            correct_count=result_data['correct_count'],
            total_count=result_data['total_count']
        )

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result.to_dict())

        # For regular form submissions
        return render_quiz_template(
            is_random=False,
            quiz_data=quiz,
            pokemon_vars=pokemon_vars,
            result=result,
            user_answers=user_answers,
            already_solved=already_solved
        )

    # GET request - display the quiz
    return render_quiz_template(
        is_random=False,
        quiz_data=quiz,
        pokemon_vars=pokemon_vars,
        user_answers=user_answers,
        already_solved=already_solved
    )


@app.route('/api/quiz/<quiz_id>/reset', methods=['POST'])
def reset_quiz(quiz_id):
    """Reset a solved quiz to allow it to be solved again."""
    game_manager = create_game_manager()

    # Check if this quiz is already solved
    if game_manager.session_manager.is_quiz_solved(quiz_id):
        # Find and remove the quiz from the solved list
        game_manager.session_manager.solved_quizzes.remove(quiz_id)
        game_manager.session_manager.save_session()

        # For random quizzes, also remove any stored quiz attempts
        for i, attempt in enumerate(game_manager.session_manager.get_quiz_attempts()):
            if attempt['quiz_id'] == quiz_id:
                # Remove the specified quiz attempt
                if 'timestamp' in attempt:
                    game_manager.session_manager.remove_quiz_attempt(attempt['timestamp'])
                break

    # Redirect to the quiz page
    return redirect(url_for('quiz', quiz_id=quiz_id))


@app.route('/section/<section_id>')
def section(section_id):
    """Display quizzes for a specific section."""
    game_manager = create_game_manager()

    # Find the requested section
    selected_section = next((s for s in GAME_CONFIG.sections if s.id == section_id), None)

    if not selected_section:
        return "Section not found", 404

    return render_template('section.html',
                           section=selected_section,
                           solved_quizzes=game_manager.session_manager.solved_quizzes)


@app.route('/my-quizzes')
def my_quizzes():
    """Display the user's missions/quizzes."""
    game_manager = create_game_manager()

    # Get all quiz attempts
    attempts = game_manager.session_manager.get_quiz_attempts()

    # Prepare data for the template
    formatted_attempts = []
    for attempt in attempts:
        quiz_id = attempt.get('quiz_id', '')
        is_random = quiz_id.startswith('random_')

        # Check if the quiz still exists
        exists = False
        title = "Unknown Mission"

        if is_random:
            # For random quizzes, check if we have the quiz data
            exists = 'quiz_data' in attempt
            if exists:
                title = "Random Mission"
        else:
            # For regular quizzes, check if it exists in the game config
            quiz_state = game_manager.get_quiz_state(quiz_id)
            exists = quiz_state is not None
            if exists:
                title = quiz_state['quiz'].title

        # Add to formatted attempts
        formatted_attempts.append({
            'id': quiz_id,
            'title': title,
            'timestamp': attempt.get('timestamp', ''),
            'score': attempt.get('score', 0),
            'total': attempt.get('total', 0),
            'completed': attempt.get('completed', False),
            'solved': game_manager.session_manager.is_quiz_solved(quiz_id),
            'exists': exists,
            'quiz_data': attempt.get('quiz_data', {})
        })

    # Sort attempts by timestamp (newest first)
    formatted_attempts.sort(key=lambda x: x['timestamp'], reverse=True)

    # Calculate statistics
    stats = {
        'total_attempts': len(formatted_attempts),
        'total_solved': len(game_manager.session_manager.solved_quizzes)
    }

    return render_template('my_quizzes.html',
                           attempts=formatted_attempts,
                           stats=stats)


@app.route('/forget-quiz', methods=['POST'])
def forget_quiz():
    """Remove a quiz attempt from the user's history."""
    game_manager = create_game_manager()

    # Get the timestamp from the form
    timestamp = request.form.get('timestamp')
    if timestamp:
        # Remove the quiz attempt
        game_manager.session_manager.remove_quiz_attempt(timestamp)

    # Redirect back to my quizzes page
    return redirect(url_for('my_quizzes'))


@app.route('/reset-progress', methods=['POST'])
def reset_progress():
    """Reset all user progress, including solved quizzes and attempts."""
    game_manager = create_game_manager()
    game_manager.reset()
    game_manager.save_session()

    return redirect(url_for('profile'))


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('error.html',
                           error_code=404,
                           error_message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('error.html',
                           error_code=500,
                           error_message="Server error"), 500

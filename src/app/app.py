from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pathlib import Path
from src.app.game.game_config import load_game_config, load_equation_difficulties
from src.app.game.game_manager import GameManager
from src.app.equations.equations_generator import MathEquationGenerator
import os
import uuid
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from src.app.storage import create_session_manager

# Create Flask app with correct template and static folders
app = Flask(__name__,
            template_folder=str(Path(__file__).parent.parent / 'templates'),
            static_folder=str(Path(__file__).parent.parent / 'static'))
app.secret_key = 'your-secret-key-here'  # Required for session management

# Load quiz data at startup - this is shared across all sessions
# and doesn't need to be stored in each user's session
GAME_CONFIG = load_game_config(Path(__file__).parent.parent / 'data' / 'quizzes.json')

EQUATION_DIFFICULTIES = load_equation_difficulties(Path(__file__).parent.parent / 'data' / 'equation_difficulties.json')

# Create equation generator
EQUATION_GENERATOR = MathEquationGenerator()

# Get Pokemon images from the game configuration
POKEMON_IMAGES = [pokemon.image_path for pokemon in GAME_CONFIG.pokemons.values()]


def get_version_info():
    return {
        'version': os.environ.get('COMMIT_SHA', 'development')
    }


# Add context processor to make version_info available to all templates
@app.context_processor
def inject_version_info():
    return {'version_info': get_version_info()}


def get_quiz_session() -> GameManager:
    """
    Get a GameManager instance with session data loaded from the persistent storage.
    
    Raises:
        Exception: If Firestore storage is enabled but not available
    """
    try:
        # Create a session manager with Firestore persistence
        # Set use_firestore=False to use Flask session storage instead
        session_manager = create_session_manager(use_firestore=True)
        
        # Create a GameManager with the session manager
        return GameManager.start_session(GAME_CONFIG, session_manager)
    except Exception as e:
        # Log the error
        app.logger.error(f"Error connecting to Firestore: {e}")
        # Re-raise the exception to be handled by route handlers
        raise


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


def process_quiz_answers(user_answers: Dict[str, int], expected_answers: Dict[str, Union[int, str]]) -> QuizResultViewModel:
    """
    Generic helper function to process quiz answers for both random and regular quizzes.
    
    Args:
        user_answers: Dictionary of user-provided answers {var: value}
        expected_answers: Dictionary of expected answers {var: value}
        
    Returns:
        QuizResultViewModel: A standardized result object containing quiz results data
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


def render_quiz_template(
    is_random: bool, 
    quiz_data: Union[Dict[str, Any], object], 
    pokemon_vars: Dict[str, str], 
    result: Optional[QuizResultViewModel] = None, 
    user_answers: Optional[Dict[str, int]] = None,
    already_solved: bool = False
) -> Any:
    """
    Standardized function to render the quiz template for both random and regular quizzes.
    
    Args:
        is_random: Whether this is a random quiz (included in the unified data)
        quiz_data: For random quizzes, a dictionary with equations, solution, etc. 
                  For regular quizzes, the quiz object from GameManager
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


@app.route('/')
def index():
    """
    Display the home page with welcome message.
    """
    return render_template('index.html')


@app.route('/exercises')
def all_exercises():
    """
    Display all available community exercises.
    """
    quiz_session = get_quiz_session()
    return render_template('all_exercises.html',
                           title="Community Exercises",
                           sections=GAME_CONFIG.sections,
                           solved_quizzes=quiz_session.session_manager.solved_quizzes)


@app.route('/profile')
def profile():
    """
    Display the user's profile with points and progress.
    """
    quiz_session = get_quiz_session()
    solved_count = len(quiz_session.solved_quizzes)
    # Each solved quiz is worth 1 point
    points = solved_count

    return render_template('profile.html',
                           points=points,
                           solved_count=solved_count)


@app.route('/new-exercise')
def new_exercise():
    """
    Display difficulty selection screen for random exercise generation.
    """
    return render_template('new_exercise.html',
                           difficulties=EQUATION_DIFFICULTIES)


@app.route('/generate-random-exercise/<difficulty_id>')
def generate_random_exercise(difficulty_id):
    """
    Generate a random equation based on the selected difficulty.
    """
    # Find the selected difficulty
    selected_difficulty = next((d for d in EQUATION_DIFFICULTIES if d['id'] == difficulty_id), None)

    if not selected_difficulty:
        return "Difficulty not found", 404

    # Generate a random equation using the MathEquationGenerator
    quiz = EQUATION_GENERATOR.generate_quiz(**selected_difficulty['params'])

    # Store the generated quiz in the session
    random_quiz_id = f"random_{uuid.uuid4().hex[:8]}"

    if 'random_quizzes' not in session:
        session['random_quizzes'] = {}

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

    # Store the equations and solution in the session
    session['random_quizzes'][random_quiz_id] = {
        'equations': formatted_equations,
        'solution': {var: str(val) for var, val in quiz.solution.human_readable.items()},
        'difficulty': selected_difficulty,
        'pokemon_vars': pokemon_vars
    }
    session.modified = True

    # Redirect to the quiz page
    return redirect(url_for('random_quiz', quiz_id=random_quiz_id))


@app.route('/random-quiz/<quiz_id>', methods=['GET', 'POST'])
def random_quiz(quiz_id):
    """
    Display a randomly generated quiz.
    """
    quiz_session = get_quiz_session()
    
    # Get the stored quiz from the session
    if 'random_quizzes' not in session or quiz_id not in session['random_quizzes']:
        return render_template('quiz_not_found.html', quiz_id=quiz_id)

    stored_quiz = session['random_quizzes'][quiz_id]
    # Add quiz_id to the stored_quiz for the template
    stored_quiz['quiz_id'] = quiz_id

    # Check if this quiz is already solved
    already_solved = quiz_session.session_manager.is_quiz_solved(quiz_id)

    # Pre-populate answers if the quiz is already solved
    user_answers = {}
    if already_solved:
        # Show the correct answers for an already solved quiz
        user_answers = {var: int(float(val)) for var, val in stored_quiz['solution'].items()}

    if request.method == 'POST':
        # If the quiz is already solved, don't process the answers again
        if already_solved:
            return render_template('already_solved.html', quiz_id=quiz_id)
            
        # Filter out empty inputs
        user_answers = {
            key: int(value)
            for key, value in request.form.items()
            if value.strip() and key in stored_quiz['solution']  # Only include non-empty values for solution variables
        }

        result = process_quiz_answers(user_answers, stored_quiz['solution'])
        
        # Update session data if all answers are correct
        if result.correct:
            quiz_session.session_manager.mark_quiz_solved(quiz_id)
        
        # Record the quiz attempt - this will update an existing attempt or create a new one
        quiz_session.session_manager.add_quiz_attempt(
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
        quiz_session.session_manager.add_quiz_attempt(
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
    quiz_session = get_quiz_session()
    
    # Check if quiz exists in current GAME_CONFIG
    quiz_exists = False
    is_random = quiz_id.startswith('random_')
    stored_quiz_data = None
    
    if is_random:
        # For random quizzes, we need to check the session data
        for attempt in quiz_session.session_manager.get_quiz_attempts():
            if attempt['quiz_id'] == quiz_id and 'quiz_data' in attempt:
                quiz_exists = True
                stored_quiz_data = attempt['quiz_data']
                break
    else:
        # For regular quizzes, check the game config
        quiz_state = quiz_session.get_quiz_state(quiz_id)
        if quiz_state:
            quiz_exists = True

    if not quiz_exists:
        # Quiz no longer exists, show an error page
        return render_template('quiz_not_found.html', quiz_id=quiz_id)
    
    # Check if this quiz is already solved
    already_solved = quiz_session.session_manager.is_quiz_solved(quiz_id)
    
    # Pre-populate answers if the quiz is already solved
    user_answers = {}
    
    # For random quizzes, use the stored data
    if is_random and stored_quiz_data:
        # If quiz is already solved, show the solution
        if already_solved:
            user_answers = {var: int(float(val)) for var, val in stored_quiz_data['solution'].items()}
            
        # Process the random quiz
        if request.method == 'POST':
            # If the quiz is already solved, don't process the answers again
            if already_solved:
                return render_template('already_solved.html', quiz_id=quiz_id)
                
            # Filter out empty inputs
            user_answers = {
                key: int(value)
                for key, value in request.form.items()
                if value.strip() and key in stored_quiz_data['solution']  # Only include non-empty values for solution variables
            }

            result = process_quiz_answers(user_answers, stored_quiz_data['solution'])
            
            # Update session data if all answers are correct
            if result.correct:
                quiz_session.session_manager.mark_quiz_solved(quiz_id)
            
            # Record the quiz attempt - will update existing if present
            quiz_session.session_manager.add_quiz_attempt(
                quiz_id=quiz_id,
                quiz_data=stored_quiz_data,
                score=result.correct_count,
                total=result.total_count,
                completed=result.all_answered
            )

            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result.to_dict())

            # For regular form submissions
            return render_quiz_template(
                is_random=True,
                quiz_data=stored_quiz_data,
                pokemon_vars=stored_quiz_data.get('pokemon_vars', {}),
                result=result,
                user_answers=user_answers,
                already_solved=already_solved
            )

        # GET request - track that the user viewed this quiz (for incomplete tracking)
        if not already_solved:
            # Add or update quiz attempt with initial data
            quiz_session.session_manager.add_quiz_attempt(
                quiz_id=quiz_id,
                quiz_data=stored_quiz_data,
                score=0,
                total=len(stored_quiz_data.get('solution', {})),
                completed=False
            )
        
        # Display the quiz
        return render_quiz_template(
            is_random=True,
            quiz_data=stored_quiz_data,
            pokemon_vars=stored_quiz_data.get('pokemon_vars', {}),
            user_answers=user_answers,
            already_solved=already_solved
        )
    else:
        # Normal quiz handling for non-random quizzes
        quiz_state = quiz_session.get_quiz_state(quiz_id)
        
        # If quiz is already solved, show the solution
        if already_solved:
            user_answers = {var: int(float(val)) for var, val in quiz_state['quiz'].answer.values.items()}
        
        if request.method == 'POST':
            # If the quiz is already solved, don't process the answers again
            if already_solved:
                return render_template('already_solved.html', quiz_id=quiz_id)
                
            # Filter out empty inputs
            user_answers = {
                key: int(value)
                for key, value in request.form.items()
                if value.strip()  # Only include non-empty values
            }

            # Process answers with our helper function
            expected_answers = quiz_state['quiz'].answer.values
            result = process_quiz_answers(user_answers, expected_answers)
            
            # Update session data if all answers are correct
            if result.correct:
                quiz_session.session_manager.mark_quiz_solved(quiz_id)
            
            # Create quiz data for storing attempts
            quiz_data = {
                'quiz_id': quiz_id,
                'title': quiz_state['quiz'].title,
                'equations': quiz_state['quiz'].equations,
                'solution': quiz_state['quiz'].answer.values,
                'is_random': False
            }
            
            # Record the quiz attempt - will update existing if present
            quiz_session.session_manager.add_quiz_attempt(
                quiz_id=quiz_id,
                quiz_data=quiz_data,
                score=result.correct_count,
                total=result.total_count,
                completed=result.all_answered
            )

            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result.to_dict())

            # For regular form submissions (fallback)
            return render_quiz_template(
                is_random=False,
                quiz_data=quiz_state['quiz'],
                pokemon_vars=quiz_state['pokemon_vars'],
                result=result,
                user_answers=user_answers,
                already_solved=already_solved
            )

        # GET request - track that the user viewed this quiz (for incomplete tracking)
        if not already_solved:
            # Create quiz data for storing attempts
            quiz_data = {
                'quiz_id': quiz_id,
                'title': quiz_state['quiz'].title,
                'equations': quiz_state['quiz'].equations,
                'solution': quiz_state['quiz'].answer.values,
                'is_random': False
            }
            
            # Add or update quiz attempt with initial data
            quiz_session.session_manager.add_quiz_attempt(
                quiz_id=quiz_id,
                quiz_data=quiz_data,
                score=0,
                total=len(quiz_state['quiz'].answer.values),
                completed=False
            )

        return render_quiz_template(
            is_random=False,
            quiz_data=quiz_state['quiz'],
            pokemon_vars=quiz_state['pokemon_vars'],
            user_answers=user_answers,
            already_solved=already_solved
        )


@app.route('/reset_progress', methods=['POST'])
def reset_progress():
    quiz_session = get_quiz_session()
    quiz_session.reset()
    # Save the reset session state
    quiz_session.save_session()
    return redirect(url_for('index'))


@app.route('/my-quizzes')
def my_quizzes():
    """Display the user's quiz attempts."""
    quiz_session = get_quiz_session()
    attempts = quiz_session.session_manager.get_quiz_attempts()
    
    # Format attempts for display
    formatted_attempts = []
    for attempt in attempts:
        quiz_id = attempt.get('quiz_id')
        quiz_exists = False
        quiz_title = 'Unknown Mission'
        
        # Check if it's a random quiz with stored data
        if quiz_id.startswith('random_') and 'quiz_data' in attempt:
            quiz_exists = True
            quiz_title = 'Random Mission'
            quiz_data = attempt.get('quiz_data', {})
            if 'title' in quiz_data:
                quiz_title = quiz_data['title']
        else:
            # Check if regular quiz still exists
            quiz = GAME_CONFIG.quizzes_by_id.get(quiz_id)
            if quiz:
                quiz_exists = True
                quiz_title = quiz.title
                
                # For regular quizzes, we need to get the pokemon_vars from the quiz_state
                quiz_state = quiz_session.get_quiz_state(quiz_id)
                if quiz_state and 'pokemon_vars' in quiz_state:
                    # If quiz_data doesn't exist, create it
                    if 'quiz_data' not in attempt:
                        attempt['quiz_data'] = {
                            'quiz_id': quiz_id,
                            'title': quiz_title,
                            'equations': quiz.equations,
                            'solution': quiz.answer.values,
                            'is_random': False,
                            'pokemon_vars': quiz_state['pokemon_vars']
                        }
                    # If quiz_data exists but doesn't have pokemon_vars, add them
                    elif 'pokemon_vars' not in attempt['quiz_data']:
                        attempt['quiz_data']['pokemon_vars'] = quiz_state['pokemon_vars']
        
        formatted_attempt = {
            'id': quiz_id,
            'title': quiz_title,
            'timestamp': attempt.get('timestamp'),
            'score': f"{attempt.get('score')}/{attempt.get('total')}",
            'completed': attempt.get('completed'),
            'solved': quiz_session.session_manager.is_quiz_solved(quiz_id),
            'exists': quiz_exists  # Flag to indicate if quiz still exists
        }
        
        # Include quiz_data if it exists
        if 'quiz_data' in attempt:
            formatted_attempt['quiz_data'] = attempt['quiz_data']
        
        formatted_attempts.append(formatted_attempt)
    
    # Sort by timestamp, most recent first
    formatted_attempts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate total stats
    total_attempts = len(formatted_attempts)
    total_solved = sum(1 for attempt in formatted_attempts if attempt['solved'])
    
    return render_template(
        'my_quizzes.html',
        attempts=formatted_attempts,
        stats={
            'total_attempts': total_attempts,
            'total_solved': total_solved
        }
    )


@app.route('/forget-quiz', methods=['POST'])
def forget_quiz():
    """Remove a quiz attempt from the user's history."""
    quiz_session = get_quiz_session()
    timestamp = request.form.get('timestamp')
    
    if timestamp:
        quiz_session.session_manager.remove_quiz_attempt(timestamp)
    
    return redirect(url_for('my_quizzes'))


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0')


# Add error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle exceptions from Firestore and other services."""
    # Log the error
    app.logger.error(f"Unhandled exception: {e}")
    
    # Customize error message based on error type
    error_message = "An unexpected error occurred."
    
    if "Firebase" in str(e) or "Firestore" in str(e):
        error_message = "Could not connect to the database. Please try again later."
    
    # Render error template
    return render_template('error.html', 
                           error_message=error_message,
                           error_details=str(e)), 500

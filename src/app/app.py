from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pathlib import Path
from src.app.game.game_config import load_game_config, load_equation_difficulties
from src.app.game.game_manager import GameManager
from src.app.equations.equations_generator import MathEquationGenerator
import os
import uuid
import random

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


def get_quiz_session() -> GameManager:
    """
    Get a GameManager instance with session data loaded from Flask session.
    """
    # We don't provide a session_manager here, so it will be loaded from Flask session
    return GameManager.start_session(GAME_CONFIG)


@app.route('/')
def index():
    """
    Display the home page with welcome message.
    """
    return render_template('index.html',
                           version_info=get_version_info())


@app.route('/exercises')
def all_exercises():
    """
    Display all available exercises.
    """
    quiz_session = get_quiz_session()
    return render_template('all_exercises.html',
                           sections=GAME_CONFIG.sections,
                           solved_quizzes=quiz_session.solved_quizzes,
                           version_info=get_version_info())


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
                           solved_count=solved_count,
                           version_info=get_version_info())


@app.route('/new-exercise')
def new_exercise():
    """
    Display difficulty selection screen for random exercise generation.
    """
    return render_template('new_exercise.html',
                           difficulties=EQUATION_DIFFICULTIES,
                           version_info=get_version_info())


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
    # Get the stored quiz from the session
    if 'random_quizzes' not in session or quiz_id not in session['random_quizzes']:
        return "Quiz not found", 404

    stored_quiz = session['random_quizzes'][quiz_id]

    if request.method == 'POST':
        # Filter out empty inputs
        user_answers = {
            key: int(value)
            for key, value in request.form.items()
            if value.strip() and key in stored_quiz['solution']  # Only include non-empty values for solution variables
        }

        # Check the answers
        correct_answers = {}
        all_correct = True
        all_answered = len(user_answers) == len(stored_quiz['solution'])

        for var, expected in stored_quiz['solution'].items():
            if var in user_answers:
                is_correct = user_answers[var] == int(float(expected))
                correct_answers[var] = is_correct
                if not is_correct:
                    all_correct = False
            else:
                all_answered = False

        # Count correct answers
        correct_count = sum(1 for is_correct in correct_answers.values() if is_correct)
        total_count = len(stored_quiz['solution'])

        result = {
            'correct': all_correct and all_answered,
            'correct_answers': correct_answers,
            'all_answered': all_answered,
            'correct_count': correct_count,
            'total_count': total_count
        }

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)

        # For regular form submissions (fallback)
        return render_template('quiz.html',
                               is_random=True,
                               quiz_id=quiz_id,
                               equations=stored_quiz['equations'],
                               solution=stored_quiz['solution'],
                               difficulty=stored_quiz['difficulty'],
                               pokemon_vars=stored_quiz['pokemon_vars'],
                               result=result,
                               user_answers=user_answers,
                               version_info=get_version_info())

    # GET request - just display the quiz
    return render_template('quiz.html',
                           is_random=True,
                           quiz_id=quiz_id,
                           equations=stored_quiz['equations'],
                           solution=stored_quiz['solution'],
                           difficulty=stored_quiz['difficulty'],
                           pokemon_vars=stored_quiz['pokemon_vars'],
                           result=None,
                           user_answers={},
                           version_info=get_version_info())


@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz_session = get_quiz_session()
    quiz_state = quiz_session.get_quiz_state(quiz_id)

    if not quiz_state:
        return "Quiz not found", 404

    if request.method == 'POST':
        # Filter out empty inputs
        user_answers = {
            key: int(value)
            for key, value in request.form.items()
            if value.strip()  # Only include non-empty values
        }

        result = quiz_session.check_answers(quiz_id, user_answers)
        # Save the updated session state
        quiz_session.save_session()

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)

        # For regular form submissions (fallback)
        return render_template('quiz.html',
                               is_random=False,
                               quiz=quiz_state['quiz'],
                               pokemon_vars=quiz_state['pokemon_vars'],
                               result=result,
                               user_answers=user_answers,
                               version_info=get_version_info())

    return render_template('quiz.html',
                           is_random=False,
                           quiz=quiz_state['quiz'],
                           pokemon_vars=quiz_state['pokemon_vars'],
                           result=None,
                           user_answers={},
                           version_info=get_version_info())


@app.route('/reset_progress', methods=['POST'])
def reset_progress():
    quiz_session = get_quiz_session()
    quiz_session.reset()
    # Save the reset session state
    quiz_session.save_session()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0')

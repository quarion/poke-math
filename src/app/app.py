"""
PokeMath Web Application
------------------------
This module contains the Flask web application for PokeMath, including:
- Main application setup and configuration
- Route definitions and handlers
- Helper functions for request processing

Authentication:
- Users can log in with Google or as a guest
- Guest accounts are persisted using cookies for 30 days
- Progress is saved for both Google and guest accounts
"""

import os
import uuid
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response
from flask_wtf.csrf import CSRFProtect

from src.app.game.game_config import load_game_config, load_equation_difficulties
from src.app.game.game_manager import GameManager
from src.app.equations.equations_generator_v2 import EquationsGeneratorV2
from src.app.game.quiz_engine import generate_random_quiz_data
from src.app.storage.session_factory import create_session_manager
from src.app.auth.auth import AuthManager
from src.app.firebase.firebase_init import get_auth_client
from src.app.view_models import QuizViewModel, QuizResultViewModel
import json


# -----------------------------------------------------------------------------
# Authentication Helper
# -----------------------------------------------------------------------------

def login_required(f):
    """
    Decorator to require authentication for routes.
    When applied to a route function, it will check if the user is authenticated
    before allowing access to the route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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
    
    # Initialize CSRF protection
    csrf = CSRFProtect(flask_app)

    # Configure CSRF protection
    flask_app.config['WTF_CSRF_ENABLED'] = True
    flask_app.config['WTF_CSRF_SECRET_KEY'] = 'a-very-secret-key'  # Should be a strong random key in production
    flask_app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour in seconds
    flask_app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Don't check CSRF by default, only where explicitly required
    flask_app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']  # Only check these methods

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

# Initialize CSRF protection separately to make it available globally
csrf = CSRFProtect(app)

# Configure CSRF protection
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = 'a-very-secret-key'  # Should be a strong random key in production
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour in seconds
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Don't check CSRF by default, only where explicitly required
app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']  # Only check these methods

# Add after_request handler to set guest cookie
@app.after_request
def after_request(response):
    """
    Process response after each request.
    
    This function:
    1. Sets the guest cookie for guest users
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response
    """
    # Set guest cookie if user is a guest
    AuthManager.set_guest_cookie(response)
    
    return response

# Load game configuration
GAME_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'quizzes.json'
POKEMON_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'pokemons.json'
GAME_CONFIG = load_game_config(GAME_CONFIG_PATH, POKEMON_CONFIG_PATH)

# Load equation difficulties
DIFFICULTY_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'equation_difficulties_v2.json'
EQUATION_DIFFICULTIES = load_equation_difficulties(DIFFICULTY_CONFIG_PATH)

# Create equation generator
EQUATION_GENERATOR = EquationsGeneratorV2()

# Get Pokemon images from the game configuration
POKEMON_IMAGES = [pokemon.image_path for pokemon in GAME_CONFIG.pokemons.values()]


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
            # Convert expected value to int if it's a string
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
        quiz_data: Dict[str, Any],
        image_mapping: Dict[str, str],
        result: Optional[QuizResultViewModel] = None,
        user_answers: Optional[Dict[str, int]] = None,
        already_solved: bool = False,
        adventure_results: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Render the quiz template for both random and regular quizzes.
    
    Args:
        is_random: Whether this is a random quiz
        quiz_data: Quiz data in unified dictionary format
        image_mapping: Dictionary mapping variable names to Pokemon image paths
        result: Optional result object from checking answers
        user_answers: Optional dictionary of user submitted answers
        already_solved: Flag indicating if the quiz is already solved
        adventure_results: Optional dictionary with adventure completion results
        
    Returns:
        Response: Flask response with rendered template
    """
    if user_answers is None:
        user_answers = {}

    # Create a strongly-typed view model
    quiz = QuizViewModel(
        id=quiz_data.get('quiz_id', ''),
        title=quiz_data.get('title', 'Random Mission' if is_random else 'Quiz'),
        equations=quiz_data.get('equations', []),
        variables=list(quiz_data.get('solution', {}).keys()),
        image_mapping=image_mapping,
        description=quiz_data.get('description', ''),
        is_random=is_random,
        difficulty=quiz_data.get('difficulty'),
        next_quiz_id=quiz_data.get('next_quiz_id'),
        has_next=quiz_data.get('next_quiz_id') is not None
    )

    template_args = {
        'quiz': quiz,  # Strongly typed view model
        'result': result,
        'user_answers': user_answers,
        'already_solved': already_solved,
        'adventure_results': adventure_results
    }

    return render_template('quiz.html', **template_args)


# -----------------------------------------------------------------------------
# Route Handlers
# -----------------------------------------------------------------------------

@app.route('/')
@login_required
def index():
    """
    Display the home page.
    
    Returns:
        Rendered index page template
    """
    # Get the user name from the session manager
    session_manager = create_session_manager()
    user_name = session_manager.get_user_name()
    
    return render_template('index.html', user_name=user_name)


@app.route('/exercises')
@login_required
def all_exercises():
    """Display all available community exercises."""
    game_manager = create_game_manager()
    return render_template('all_exercises.html',
                           title="Community Exercises",
                           sections=GAME_CONFIG.sections,
                           solved_quizzes=game_manager.session_manager.solved_quizzes)


@app.route('/profile')
@login_required
def profile():
    """
    Display user profile with solved quizzes and level information.
    """
    game_manager = create_game_manager()
    
    # Count solved quizzes
    solved_count = len(game_manager.solved_quizzes)
    # Each solved quiz is worth 1 point
    points = solved_count
    
    # Get user name and guest status
    user_name = game_manager.session_manager.get_user_name()
    is_guest = AuthManager.is_guest()
    
    # Get level information
    level_info = game_manager.get_player_level_info()
    
    # Get caught Pokémon
    caught_pokemon = game_manager.session_manager.get_caught_pokemon()
    
    # Prepare collection data for the template
    collection = []
    for pokemon_id, count in caught_pokemon.items():
        if pokemon_id in game_manager.game_config.pokemons:
            pokemon = game_manager.game_config.pokemons[pokemon_id]
            collection.append({
                'id': pokemon_id,
                'name': pokemon.name,
                'image_path': pokemon.image_path,
                'count': count
            })
    
    # Sort by name
    collection.sort(key=lambda p: p['name'])
    
    # Calculate totals
    total_unique_pokemon = len(caught_pokemon)
    total_available_pokemon = len(game_manager.game_config.pokemons)

    return render_template('profile.html',
                           points=points,
                           solved_count=solved_count,
                           user_name=user_name,
                           is_guest=is_guest,
                           level_info=level_info,
                           collection=collection,
                           total_unique_pokemon=total_unique_pokemon,
                           total_available_pokemon=total_available_pokemon)


@app.route('/new-exercise')
@login_required
def new_exercise():
    """Display difficulty selection screen for random exercise generation."""
    return render_template('new_exercise.html',
                           difficulties=EQUATION_DIFFICULTIES)


@app.route('/generate-random-exercise/<difficulty_id>')
@login_required
def generate_random_exercise(difficulty_id):
    """Generate a random exercise based on the selected difficulty."""
    # Find the selected difficulty
    selected_difficulty = next((d for d in EQUATION_DIFFICULTIES if d['id'] == difficulty_id), None)

    if not selected_difficulty:
        return "Difficulty not found", 404

    game_manager = create_game_manager()
    
    # Get the player's current level
    level_info = game_manager.get_player_level_info()
    player_level = level_info['level']
    
    random_quiz_id, quiz_data = generate_random_quiz_data(
        GAME_CONFIG, 
        selected_difficulty, 
        EQUATION_GENERATOR,
        player_level=player_level
    )

    # Store the quiz in the session manager
    game_manager.session_manager.save_quiz_data(random_quiz_id, quiz_data, is_random=True)

    return redirect(url_for('quiz', quiz_id=random_quiz_id))


@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
@login_required
def quiz(quiz_id):
    """
    Display and process a quiz.
    """
    game_manager = create_game_manager()
    
    # Check if this is a random quiz ID format
    is_random = quiz_id.startswith('random_')
    
    # Get quiz data from session manager
    session_manager = game_manager.session_manager
    quiz_data = session_manager.get_quiz_data(quiz_id)
    
    # If not found in session, try to get from game config (for regular quizzes)
    if not quiz_data:
        if not is_random:
            # Regular quiz - get from game config
            quiz_state = game_manager.get_quiz_state(quiz_id)
            if quiz_state:
                # Convert to unified format
                quiz = quiz_state['quiz']
                regular_quiz_data = {
                    'quiz_id': quiz_id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'equations': quiz.equations,
                    'solution': quiz.answer.values,
                    'image_mapping': quiz_state['image_mapping'],
                    'next_quiz_id': quiz.next_quiz_id,
                    'is_random': False
                }
                quiz_data = regular_quiz_data
                session_manager.save_quiz_data(quiz_id, quiz_data, is_random=False)
            else:
                return render_template('quiz_not_found.html', quiz_id=quiz_id)
        else:
            # Random quiz not found - simply return not found page
            return render_template('quiz_not_found.html', quiz_id=quiz_id)
    
    # Check if this quiz is already solved
    already_solved = game_manager.session_manager.is_quiz_solved(quiz_id)
    
    # Get user answers if any
    user_answers = session_manager.get_quiz_answers(quiz_id)
    
    # Pre-populate answers if the quiz is already solved and user hasn't entered anything
    if already_solved and not user_answers:
        # Show the correct answers for an already solved quiz
        user_answers = {var: int(float(val)) for var, val in quiz_data['solution'].items()}
        session_manager.save_quiz_answers(quiz_id, user_answers)
    
    # Initialize adventure results data
    adventure_results = None
    
    # Handle form submission
    if request.method == 'POST':
        # If the quiz is already solved, don't process the answers again
        if already_solved:
            return render_template('already_solved.html', quiz_id=quiz_id)
        
        # Parse user answers
        user_answers = parse_user_answers(request.form, quiz_data['solution'].keys())
        
        # Save the answers
        session_manager.save_quiz_answers(quiz_id, user_answers)
        
        # Check answers
        result = process_quiz_answers(user_answers, quiz_data['solution'])

        # Update session data if all answers are correct
        if result.correct:
            game_manager.session_manager.mark_quiz_solved(quiz_id)
            
            # Process adventure completion if the quiz was solved correctly
            # Determine difficulty level
            difficulty = quiz_data.get('difficulty').get('difficulty')
            
            # Determine which Pokémon to catch based on the quiz
            # For now, we'll use the Pokémon from the image mapping as the caught Pokémon
            caught_pokemon = []
            for var, img_path in quiz_data['image_mapping'].items():
                # Extract Pokémon ID from image path (remove file extension)
                pokemon_id = img_path.split('.')[0]
                if pokemon_id not in caught_pokemon:
                    caught_pokemon.append(pokemon_id)
            
            # Record caught Pokémon and their new counts
            pokemon_counts = {}
            for pokemon_id in caught_pokemon:
                pokemon_counts[pokemon_id] = game_manager.session_manager.catch_pokemon(pokemon_id)
            
            # Calculate and award XP using the new progression system
            rewards = game_manager.calculate_adventure_rewards(caught_pokemon, difficulty)
            
            # Get updated level info
            level_info = game_manager.get_player_level_info()
            
            # Get caught Pokémon details for display
            caught_pokemon_details = []
            for pokemon_id in caught_pokemon:
                if pokemon_id in game_manager.game_config.pokemons:
                    pokemon = game_manager.game_config.pokemons[pokemon_id]
                    caught_pokemon_details.append({
                        'id': pokemon_id,
                        'name': pokemon.name,
                        'image_path': pokemon.image_path
                    })
            
            # Create adventure results data
            adventure_results = {
                'caught_pokemon': caught_pokemon_details,
                'pokemon_counts': pokemon_counts,
                'xp_gained': rewards['xp_reward'],
                'leveled_up': rewards['leveled_up'],
                'level_info': level_info
            }
            
            # Add adventure results to the result dictionary for AJAX requests
            result_dict = result.to_dict()
            result_dict['adventure_results'] = adventure_results
            
            # If it's an AJAX request, return JSON with adventure results
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result_dict)
        else:
            # If it's an AJAX request, return JSON without adventure results
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result.to_dict())
        
        # For regular form submissions
        return render_quiz_template(
            is_random=is_random,
            quiz_data=quiz_data,
            image_mapping=quiz_data['image_mapping'],
            result=result,
            user_answers=user_answers,
            already_solved=already_solved,
            adventure_results=adventure_results
        )
    
    # GET request - just display the quiz
    return render_quiz_template(
        is_random=is_random,
        quiz_data=quiz_data,
        image_mapping=quiz_data['image_mapping'],
        user_answers=user_answers,
        already_solved=already_solved
    )


@app.route('/api/quiz/<quiz_id>/reset', methods=['POST'])
@login_required
def reset_quiz(quiz_id):
    """Reset a solved quiz to allow it to be solved again."""
    # This route is protected by CSRF token via the form submission
    game_manager = create_game_manager()

    # Check if this quiz is already solved
    if game_manager.session_manager.is_quiz_solved(quiz_id):
        # Find and remove the quiz from the solved list
        game_manager.session_manager.solved_quizzes.remove(quiz_id)
        game_manager.session_manager.save_session()

    # Also clear any stored user answers
    session_manager = game_manager.session_manager
    attempt = session_manager.find_quiz_attempt(quiz_id)
    
    if attempt:
        # Clear user answers but keep the quiz data
        attempt.user_answers = {}
        session_manager.save_session()

    # Redirect to the quiz page
    return redirect(url_for('quiz', quiz_id=quiz_id))

@app.route('/my-quizzes')
@login_required
def my_quizzes():
    """Display the user's missions/quizzes."""
    game_manager = create_game_manager()

    # Get all quiz attempts
    attempts = game_manager.session_manager.get_quiz_attempts()

    # Get user name for personalization
    user_name = game_manager.session_manager.get_user_name()
    
    # Prepare data for the template
    formatted_attempts = []
    for attempt in attempts:
        quiz_id = attempt.quiz_id
        quiz_data = attempt.quiz_data
        is_random = quiz_data.is_random

        # Format the attempt for display
        formatted_attempts.append({
            'id': quiz_id,
            'title': quiz_data.title,
            'timestamp': attempt.timestamp,
            'completed': game_manager.session_manager.is_quiz_solved(quiz_id),
            'solved': game_manager.session_manager.is_quiz_solved(quiz_id),
            'exists': True,  # We now store all quiz data, so it always exists
            'is_random': is_random,
            'user_answers': attempt.user_answers,
            'quiz_data': quiz_data.to_dict(),  # Include the full quiz data
            'image_mapping': quiz_data.image_mapping  # Include the image mapping directly
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
                           stats=stats,
                           user_name=user_name)


@app.route('/forget-quiz', methods=['POST'])
@login_required
def forget_quiz():
    """Remove a quiz attempt from the user's history."""
    # This route is protected by CSRF token via the form submission
    game_manager = create_game_manager()

    # Get the timestamp from the form
    timestamp = request.form.get('timestamp')
    quiz_id = request.form.get('quiz_id')
    
    if timestamp:
        # Remove the quiz attempt by timestamp
        game_manager.session_manager.remove_quiz_attempt(timestamp)
    elif quiz_id:
        # Remove by quiz_id if timestamp not provided
        attempt = game_manager.session_manager.find_quiz_attempt(quiz_id)
        if attempt:
            game_manager.session_manager.remove_quiz_attempt(attempt.timestamp)
    
    # Also remove from solved quizzes if it was solved
    if quiz_id and quiz_id in game_manager.session_manager.solved_quizzes:
        game_manager.session_manager.solved_quizzes.remove(quiz_id)
        game_manager.session_manager.save_session()

    # Redirect back to my quizzes page
    return redirect(url_for('my_quizzes'))


@app.route('/reset-progress', methods=['POST'])
@login_required
def reset_progress():
    """Reset all user progress, including solved quizzes and attempts."""
    # This route is protected by CSRF token via the form submission
    game_manager = create_game_manager()
    game_manager.reset()
    game_manager.save_session()

    return redirect(url_for('profile'))


@app.route('/adventure/complete', methods=['POST'])
@login_required
def complete_adventure():
    """
    Complete an adventure and award XP.
    """
    data = request.json
    difficulty = data.get('difficulty', 1)
    caught_pokemon = data.get('caught_pokemon', [])
    
    # Get game manager
    game_manager = create_game_manager()
    
    # Record caught Pokémon and their new counts
    pokemon_counts = {}
    for pokemon_id in caught_pokemon:
        pokemon_counts[pokemon_id] = game_manager.session_manager.catch_pokemon(pokemon_id)
    
    # Calculate and award XP using the new progression system
    rewards = game_manager.calculate_adventure_rewards(caught_pokemon, difficulty)
    
    # Get updated level info
    level_info = game_manager.get_player_level_info()
    
    return jsonify({
        'success': True,
        'xp_gained': rewards['xp_reward'],
        'pokemon_counts': pokemon_counts,
        'leveled_up': rewards['leveled_up'],
        'level_info': level_info
    })

# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@app.route('/login')
def login():
    """
    Display the login page.
    
    If the user is already authenticated, redirect to the home page.
    
    Returns:
        Rendered login template or redirect to home page
    """
    # If user is already authenticated in session, redirect to home page
    if AuthManager.is_authenticated():
        app.logger.info("User already authenticated in session, redirecting to index")
        return redirect(url_for('index'))
    
    # Add Firebase check and debug info to help identify issues
    try:
        # Check if request has Firebase ID token in header (sometimes Firebase Auth redirects with this)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            app.logger.info("Found Firebase ID token in Authorization header")
            token = auth_header.split('Bearer ')[1]
            
            # Try to verify the token
            try:
                decoded_token = get_auth_client().verify_id_token(token)
                uid = decoded_token['uid']
                app.logger.info(f"Auto-login via token - UID: {uid}")
                
                # Set up session
                session['user_id'] = uid
                session['auth_type'] = 'google'
                session['authenticated'] = True
                session['is_guest'] = False
                
                # Check if user exists
                session_manager = create_session_manager()
                if session_manager.get_user_name():
                    return redirect(url_for('index'))
                else:
                    return redirect(url_for('name_input'))
            except Exception as e:
                app.logger.error(f"Error verifying token from header: {str(e)}")
    except Exception as e:
        app.logger.error(f"Error in login route: {str(e)}")
    
    # Otherwise, show the login page
    app.logger.info("Showing login page")
    return render_template('login.html')

@app.route('/auth_callback', methods=['POST'])
@csrf.exempt  # Exempt this route from CSRF protection
def auth_callback():
    """
    Handle Firebase authentication callback.
    
    Processes both regular Firebase authentication and anonymous (guest) logins.
    
    Returns:
        JSON response with success status and redirect URL
    """
    try:
        # Log the request for debugging
        app.logger.info("Auth callback received")
        app.logger.info(f"Request content type: {request.content_type}")
        app.logger.info(f"Request headers: {request.headers}")
        
        # Get the ID token from the request
        data = request.json
        if not data:
            app.logger.error("No JSON data received in auth_callback")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        app.logger.info(f"Request data keys: {data.keys()}")
        id_token = data.get('id_token')
        is_guest = data.get('is_guest', False)
        
        app.logger.info(f"Is guest login: {is_guest}")
        
        if not id_token:
            app.logger.error("No ID token provided in auth_callback")
            return jsonify({'success': False, 'error': 'No ID token provided'}), 400
        
        try:
            # Verify the ID token with Firebase Admin SDK
            app.logger.info("Verifying ID token...")
            decoded_token = get_auth_client().verify_id_token(id_token)
            uid = decoded_token['uid']
            app.logger.info(f"Token verified successfully for UID: {uid}")
            
            # Create a session for the user
            session['user_id'] = uid
            app.logger.info(f"Session user_id set to: {uid}")
            
            if is_guest:
                # Handle guest login
                app.logger.info("Processing guest login")
                session['auth_type'] = 'guest'
                session['authenticated'] = True
                session['is_guest'] = True
                # Redirect to name input page for guests
                redirect_url = url_for('name_input')
                app.logger.info(f"Guest redirect URL: {redirect_url}")
                return jsonify({'success': True, 'redirect': redirect_url})
            else:
                # Regular user login
                app.logger.info("Processing regular user login")
                session['auth_type'] = 'google'
                session['authenticated'] = True
                session['is_guest'] = False
                
                # Check if user exists in the database
                app.logger.info("Checking for existing user name...")
                session_manager = create_session_manager()
                user_name = session_manager.get_user_name()
                app.logger.info(f"User name from session: {user_name}")
                
                if user_name:
                    # Existing user, redirect to home page
                    redirect_url = url_for('index')
                    app.logger.info(f"Existing user redirect URL: {redirect_url}")
                    return jsonify({'success': True, 'redirect': redirect_url})
                else:
                    # New user, redirect to profile setup
                    redirect_url = url_for('name_input')
                    app.logger.info(f"New user redirect URL: {redirect_url}")
                    return jsonify({'success': True, 'redirect': redirect_url})
        
        except Exception as e:
            app.logger.error(f"Token verification error: {str(e)}")
            return jsonify({'success': False, 'error': f'Token verification failed: {str(e)}'}), 401
            
    except Exception as e:
        app.logger.error(f"Error in auth_callback: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/name')
@login_required
def name_input():
    """
    Display the name input page.
    
    Returns:
        Rendered name input page template
    """
    # Get the current name if it exists
    current_name = create_session_manager().get_user_name()
    
    return render_template('name_input.html', current_name=current_name)

@app.route('/save-name', methods=['POST'])
@login_required
def save_name():
    """
    Save the user's Pokemon-style name.
    
    Returns:
        Redirect to home page or name input page with error
    """
    try:
        # Get the trainer name from the form
        trainer_name = request.form.get('trainer_name', '').strip()
        
        # Validate the trainer name
        if not trainer_name:
            return render_template('name_input.html', error='Please enter a name')
        
        if len(trainer_name) > 20:
            return render_template('name_input.html', error='Name must be 20 characters or less')
        
        # Save the trainer name
        session_manager = create_session_manager()
        session_manager.set_user_name(trainer_name)
        
        # Redirect to home page
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error in save_name: {e}")
        return render_template('name_input.html', error=f'An error occurred: {str(e)}')

@app.route('/logout')
def logout():
    """
    Log out the current user.
    
    Returns:
        Redirect to login page with a script to sign out from Firebase
    """
    AuthManager.logout()
    
    # Create a response that includes a script to sign out from Firebase
    response = make_response(render_template('logout.html'))
    
    return response

# Update context processor to add is_authenticated and csrf_token to templates
@app.context_processor
def inject_auth_status():
    """
    Add authentication status and CSRF token to all templates.
    
    Returns:
        Dictionary with is_authenticated value and csrf_token function
    """
    from flask_wtf.csrf import generate_csrf
    return {
        'is_authenticated': AuthManager.is_authenticated(),
        'csrf_token': generate_csrf
    }

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

@app.route('/api/dev/quiz/<quiz_id>/answers', methods=['GET'])
@login_required
def dev_get_quiz_answers(quiz_id):
    """
    Development-only endpoint to get the correct answers for a quiz.
    This endpoint is only available in development mode.
    
    Args:
        quiz_id: The ID of the quiz to get answers for
        
    Returns:
        JSON with the correct answers
    """
    # Only allow this endpoint in development mode
    if not app.debug:
        return jsonify({"error": "This endpoint is only available in development mode"}), 403
    
    # Get quiz data
    game_manager = create_game_manager()
    session_manager = game_manager.session_manager
    quiz_data = session_manager.get_quiz_data(quiz_id)
    
    # If not found in session, try to get from game config (for regular quizzes)
    if not quiz_data:
        if not quiz_id.startswith('random_'):
            # Regular quiz - get from game config
            quiz_state = game_manager.get_quiz_state(quiz_id)
            if quiz_state:
                # Convert to unified format
                quiz = quiz_state['quiz']
                quiz_data = {
                    'quiz_id': quiz_id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'equations': quiz.equations,
                    'solution': quiz.answer.values,
                    'image_mapping': quiz_state['image_mapping'],
                    'next_quiz_id': quiz.next_quiz_id,
                    'is_random': False
                }
            else:
                return jsonify({"error": "Quiz not found"}), 404
        else:
            # Random quiz not found
            return jsonify({"error": "Quiz not found"}), 404
    
    # Return the correct answers
    return jsonify({
        "quiz_id": quiz_id,
        "answers": quiz_data['solution']
    })

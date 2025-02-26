from flask import Flask, render_template, request, redirect, url_for, jsonify
from pathlib import Path
from src.app.game.game_config import load_game_config
from src.app.game.game_manager import GameManager
import os

# Create Flask app with correct template and static folders
app = Flask(__name__, 
            template_folder=str(Path(__file__).parent.parent / 'templates'),
            static_folder=str(Path(__file__).parent.parent / 'static'))
app.secret_key = 'your-secret-key-here'  # Required for session management

# Load quiz data at startup - this is shared across all sessions
# and doesn't need to be stored in each user's session
QUIZ_DATA = load_game_config(Path(__file__).parent.parent / 'data' / 'quizzes.json')

def get_version_info():
    return {
        'version': os.environ.get('COMMIT_SHA', 'development')
    }

def get_quiz_session() -> GameManager:
    """
    Get a GameManager instance with session data loaded from Flask session.
    """
    return GameManager.start_session(QUIZ_DATA)

@app.route('/')
def index():
    quiz_session = get_quiz_session()
    return render_template('index.html', 
                         sections=QUIZ_DATA.sections,
                         solved_quizzes=quiz_session.solved_quizzes,
                         version_info=get_version_info())

@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz_session = get_quiz_session()
    quiz_state = quiz_session.get_quiz_state(quiz_id)
    
    if not quiz_state:
        return "Quiz not found", 404

    if request.method == 'POST':
        user_answers = {
            key: int(value) 
            for key, value in request.form.items()
        }
        
        result = quiz_session.check_answers(quiz_id, user_answers)
        # Save the updated session state
        quiz_session.save_session()
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(result)
            
        # For regular form submissions (fallback)
        return render_template('quiz.html',
                             quiz=quiz_state['quiz'],
                             pokemon_vars=quiz_state['pokemon_vars'],
                             result=result['correct'],
                             user_answers=user_answers,
                             version_info=get_version_info())

    return render_template('quiz.html',
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

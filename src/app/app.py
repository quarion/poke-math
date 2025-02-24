from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pathlib import Path
from src.app.quiz_data import load_quiz_data
from src.app.quiz_session import QuizSession
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Load quiz data at startup - this is shared across all sessions
# and doesn't need to be stored in each user's session
QUIZ_DATA = load_quiz_data(Path('data/quizzes.json'))

def get_version_info():
    """Get version information for the application."""
    return {
        'version': os.environ.get('COMMIT_SHA', 'development')
    }

def get_or_create_quiz_session() -> QuizSession:
    """
    Get the current quiz session or create a new one.
    
    This function manages the Flask session and ensures we have a QuizSession
    object for the current user. Only the session state (solved quizzes and
    variable mappings) is stored in the session, not the entire quiz data.
    """
    if 'quiz_session' not in session:
        session['quiz_session'] = QuizSession.create_new(QUIZ_DATA)
    return session['quiz_session']

@app.route('/')
def index():
    quiz_session = get_or_create_quiz_session()
    return render_template('index.html', 
                         sections=QUIZ_DATA.sections,
                         solved_quizzes=quiz_session.solved_quizzes,
                         version_info=get_version_info())

@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz_session = get_or_create_quiz_session()
    quiz_state = quiz_session.get_quiz_state(quiz_id)
    
    if not quiz_state:
        return "Quiz not found", 404

    if request.method == 'POST':
        user_answers = {
            key: int(value) 
            for key, value in request.form.items()
        }
        
        result = quiz_session.check_answers(quiz_id, user_answers)
        
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
    quiz_session = get_or_create_quiz_session()
    quiz_session.reset()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

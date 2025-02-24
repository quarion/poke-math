from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

def get_version_info():
    # Check if we're running locally (development mode)
    return {
        'version': os.environ.get('COMMIT_SHA', 'development')
    }

def load_quizzes():
    with open(os.path.join('data', 'quizzes.json')) as f:
        data = json.load(f)
        # Create a dictionary of all quizzes from all sections
        quizzes_dict = {}
        sections = data['sections']
        
        # Add display numbers to quizzes within each section
        for section in sections:
            for index, quiz in enumerate(section['quizzes'], 1):
                quiz['display_number'] = index
                quizzes_dict[quiz['id']] = quiz
                # Add section information to the quiz
                quiz['section_id'] = section['id']
                quiz['section_title'] = section['title']
        return data['pokemons'], quizzes_dict, sections

@app.route('/')
def index():
    # Load quizzes for each request
    pokemon_variables, quizzes, sections = load_quizzes()
    # Initialize solved_quizzes in session if it doesn't exist
    if 'solved_quizzes' not in session:
        session['solved_quizzes'] = {}
    return render_template('index.html', 
                         sections=sections,
                         solved_quizzes=session['solved_quizzes'],
                         version_info=get_version_info())

@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    # Load quizzes for each request
    pokemon_variables, quizzes, sections = load_quizzes()
    
    quiz_data = quizzes.get(quiz_id)
    if not quiz_data:
        return "Quiz not found", 404

    # Debug print
    print("Pokemon vars:", pokemon_variables)
    print("Quiz data:", quiz_data)

    if request.method == 'POST':
        user_answers = request.form.to_dict()
        correct = all(
            int(user_answers.get(pokemon, 0)) == answer 
            for pokemon, answer in quiz_data['answer'].items()
        )
        if correct:
            if 'solved_quizzes' not in session:
                session['solved_quizzes'] = {}
            session['solved_quizzes'][quiz_id] = True
            session.modified = True
        return render_template('quiz.html', 
                             quiz=quiz_data,
                             pokemon_vars=pokemon_variables,
                             result=correct,
                             request=request,
                             user_answers=user_answers,
                             version_info=get_version_info())

    return render_template('quiz.html', 
                         quiz=quiz_data,
                         pokemon_vars=pokemon_variables,
                         result=None,
                         request=request,
                         user_answers={},
                         version_info=get_version_info())

@app.route('/reset_progress', methods=['POST'])
def reset_progress():
    session['solved_quizzes'] = {}
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

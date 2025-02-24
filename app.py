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

# Move this outside the function to keep it as a global variable
def load_quizzes():
    with open(os.path.join('data', 'quizzes.json')) as f:
        data = json.load(f)
        return data['pokemons'], data['quizzes']

@app.route('/')
def index():
    # Load quizzes for each request
    pokemon_variables, quizzes = load_quizzes()
    # Initialize solved_quizzes in session if it doesn't exist
    if 'solved_quizzes' not in session:
        session['solved_quizzes'] = {}
    return render_template('index.html', 
                         quizzes=quizzes, 
                         solved_quizzes=session['solved_quizzes'],
                         version_info=get_version_info())

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    # Load quizzes for each request
    pokemon_variables, quizzes = load_quizzes()
    
    quiz_data = quizzes.get(str(quiz_id))
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
            session['solved_quizzes'][str(quiz_id)] = True
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

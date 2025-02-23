from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

app = Flask(__name__)

# Move this outside the function to keep it as a global variable
def load_quizzes():
    with open(os.path.join('data', 'quizzes.json')) as f:
        data = json.load(f)
        return data['pokemons'], data['quizzes']

@app.route('/')
def index():
    # Load quizzes for each request
    pokemon_variables, quizzes = load_quizzes()
    return render_template('index.html', quizzes=quizzes)

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
        return render_template('quiz.html', 
                             quiz=quiz_data,
                             pokemon_vars=pokemon_variables,
                             result=correct,
                             request=request,
                             user_answers=user_answers)

    return render_template('quiz.html', 
                         quiz=quiz_data,
                         pokemon_vars=pokemon_variables,
                         result=None,
                         request=request,
                         user_answers={})

if __name__ == '__main__':
    app.run(debug=True)

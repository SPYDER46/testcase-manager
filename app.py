# app.py
import sqlite3 
from flask import Flask, render_template, request, redirect, url_for
from models import init_db, add_test_case, get_all_test_cases, get_test_case_by_id, update_test_case
from collections import defaultdict

app = Flask(__name__)
init_db()

GAMES = ['Aviator', 'CricketX', 'Piggy Dash', 'Roller Blitz','Marble Gp', 'Hilo', 'Mines','Roulette', 'Keno','Tower', 'Rummy', 'TeenPatti', 'Ludo', 'Snake&Ladder', 'Andar Bahar'
         , 'Poker', 'Carrom' ]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        new_game = request.form.get('new_game', '').strip()
        if new_game and new_game not in GAMES:
            GAMES.append(new_game)
    return render_template('games.html', games=GAMES)

@app.route('/games/<game_name>')
def index(game_name):
    test_cases = get_all_test_cases(game_name)
    grouped_cases = defaultdict(list)
    for case in test_cases:
        grouped_cases['All Test Cases'].append(case)
    return render_template('index.html', game_name=game_name, grouped_cases=dict(grouped_cases))

@app.route('/games/<game_name>/add', methods=['GET', 'POST'])
def add(game_name):
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'steps': request.form['steps'],
            'expected_result': request.form['expected_result'],
            'actual_result': request.form['actual_result'],
            'status': request.form['status'],
            'priority': request.form['priority'],
            'iteration': request.form['iteration'],
        }
        created_by = request.form.get('created_by', 'Unknown')  # safer fallback
        add_test_case(game_name, data, created_by)
        return redirect(url_for('index', game_name=game_name))
    return render_template('add_testcase.html', game_name=game_name)


@app.route('/games/<game_name>/testcase/<int:testcase_id>', methods=['GET', 'POST'])
def view_testcase(game_name, testcase_id):
    test_case = get_test_case_by_id(testcase_id)
    if not test_case:
        return f"Test Case with ID {testcase_id} not found.", 404

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_case_history WHERE test_case_id = ? ORDER BY iteration ASC', (testcase_id,))
        history = c.fetchall()

    if request.method == 'POST':
        iteration = int(request.form['iteration'])
        actual_result = request.form['actual_result']
        status = request.form['status']
        description = request.form['description']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        priority = request.form['priority']
        created_by = request.form['created_by']

        update_test_case(
            testcase_id, actual_result, status, iteration, 
            description, steps, expected_result, priority, created_by
        )
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    return render_template(
        'view_testcase.html',
        game_name=game_name,
        test_case=test_case,
        history=history,
        user_name=''  # Pre-fill if you have a login system
    )

@app.route('/games/<game_name>/delete/<int:testcase_id>', methods=['POST'])
def delete_testcase(game_name, testcase_id):
    from models import delete_test_case
    delete_test_case(testcase_id)
    return redirect(url_for('index', game_name=game_name))

@app.route('/games/<game_name>/testcase/<int:testcase_id>/update', methods=['POST'])
def update_testcase(game_name, testcase_id):
    iteration = int(request.form['iteration'])
    actual_result = request.form['actual_result']
    status = request.form['status']
    description = request.form['description']
    steps = request.form['steps']
    expected_result = request.form['expected_result']
    priority = request.form['priority']
    created_by = request.form['created_by']

    update_test_case(
        testcase_id, actual_result, status, iteration,
        description, steps, expected_result, priority, created_by
    )

    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

if __name__ == '__main__':
    app.run(debug=True)

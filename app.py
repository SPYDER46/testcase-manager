# app.py
import sqlite3 
from flask import Flask, render_template, request, redirect, url_for
from models import init_db, add_test_case, get_all_test_cases, get_test_case_by_id,backfill_testcase_numbers, update_test_case
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
init_db()
backfill_testcase_numbers()

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
            # 'actual_result': request.form['actual_result'],
            'status': request.form['status'],
            'priority': request.form['priority'],
            'iteration': 0,
        }
        created_by = request.form.get('created_by', 'Unknown')  # safer fallback
        add_test_case(game_name, data, created_by)
        return redirect(url_for('index', game_name=game_name))
    return render_template('add_testcase.html', game_name=game_name)

@app.route('/games/<game_name>/testcase/<int:testcase_id>', methods=['GET', 'POST'])
def view_testcase(game_name, testcase_id):
    if request.method == 'POST':
        iteration = int(request.form['iteration'])
        actual_result = request.form['actual_result']
        status = request.form['status']
        description = request.form['description']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        priority = request.form['priority']
        created_by = request.form['created_by']

        # requirement_references = request.form.get('requirement_references')
        # doc_versions = request.form.get('doc_versions')
        # approval_for_release = request.form.get('approval_for_release')
        # phase_no = int(request.form.get('phase_no'))
        # date_time_received = request.form.get('date_time_received')

        update_test_case(
            testcase_id, actual_result, status, iteration, 
            description, steps, expected_result, priority, created_by,
            # requirement_references, doc_versions, approval_for_release, phase_no, date_time_received
        )

        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    # GET logic
    test_case = get_test_case_by_id(testcase_id)
    if not test_case:
        return f"Test Case with ID {testcase_id} not found.", 404

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_case_history WHERE test_case_id = ? ORDER BY iteration ASC', (testcase_id,))
        history = c.fetchall()

    return render_template(
        'view_testcase.html',
        game_name=game_name,
        test_case=test_case,
        history=history,
        user_name=''
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

@app.route('/games/<game_name>/testcase/<int:testcase_id>/iteration/<int:iteration_id>/edit', methods=['GET', 'POST'])
def edit_iteration(game_name, testcase_id, iteration_id):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_case_history WHERE id = ?', (iteration_id,))
        iteration = c.fetchone()

    if not iteration:
        return "Iteration not found", 404

    if request.method == 'POST':
        description = request.form['description']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        actual_result = request.form['actual_result']
        status = request.form['status']
        priority = request.form['priority']

        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('''UPDATE test_case_history SET 
                            description = ?, 
                            steps = ?, 
                            expected_result = ?, 
                            actual_result = ?, 
                            status = ?, 
                            priority = ?, 
                            updated_at = ?
                         WHERE id = ?''',
                      (description, steps, expected_result, actual_result, status, priority, updated_at, iteration_id))
            conn.commit()

        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    return render_template('edit_iteration.html', iteration=iteration, game_name=game_name, testcase_id=testcase_id)


@app.route('/games/<game_name>/testcase/<int:testcase_id>/iteration/<int:iteration_id>/delete', methods=['POST'])
def delete_iteration(game_name, testcase_id, iteration_id):
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM test_case_history WHERE id = ?', (iteration_id,))
        conn.commit()
    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))


from flask import request  # Make sure this is imported

@app.route('/games/<game_name>/summary')
def summary_report(game_name):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('SELECT * FROM test_cases WHERE game = ?', (game_name,))
        test_cases = c.fetchall()

        total_cases = len(test_cases)
        # total_scenarios = sum(tc['iteration'] for tc in test_cases)

        status_counts = {'Pass': 0, 'Fail': 0, 'Pending': 0, 'Hold': 0, 'Discussion': 0}
        priorities = {'Major': 0, 'Medium': 0, 'Minor': 0}

        for tc in test_cases:
            status = tc['status']
            priority = tc['priority']
            if status in status_counts:
                status_counts[status] += 1
            if priority in priorities:
                priorities[priority] += 1

        # Calculate status percentages
        def calc_percent(count):
            return round((count / total_cases) * 100, 2) if total_cases > 0 else 0.0

        pass_percentage = calc_percent(status_counts['Pass'])
        fail_percentage = calc_percent(status_counts['Fail'])

        # Get latest tester and updated_at from test_case_history
        c.execute('''
            SELECT created_by, updated_at 
            FROM test_case_history 
            WHERE test_case_id IN (SELECT id FROM test_cases WHERE game = ?)
              AND created_by IS NOT NULL AND TRIM(created_by) != ''
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (game_name,))
        row = c.fetchone()
        tester = row['created_by'] if row else "Unknown"
        last_updated = row['updated_at'] if row else "N/A"

        # Get manually entered values from query string
        art_version = request.args.get('Art_version', 'N/A')
        uiux_version = request.args.get('UI/UX_version', 'N/A')
        developer = request.args.get('Developer Name', 'N/A')
        phase_no = request.args.get('phase_no', 1)
        date_received = request.args.get('date_time_received', 'N/A')
        date_delivered = datetime.now().strftime('%Y-%m-%d %I:%M %p')  # 💡 Now dynamic
        iteration_no = request.args.get('iteration_no', 'N/A')

        return render_template(
            'summary.html',
            game_name=game_name,
            total_cases=total_cases,
            # total_scenarios=total_scenarios,
            status_counts=status_counts,
            priorities=priorities,
            pass_percentage=pass_percentage,
            fail_percentage=fail_percentage,
            tester=tester,
            developer=developer,
            date_received=date_received,
            date_delivered=date_delivered,
            phase_no=phase_no,
            iteration=iteration_no,
            art_version=art_version,
            uiux_version=uiux_version
        )

if __name__ == '__main__':
    app.run(debug=True)

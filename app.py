from flask import Flask, render_template, request, redirect, url_for
import models
from collections import defaultdict
from datetime import datetime

from models import (
    init_db,
    add_test_case,
    get_all_test_cases,
    get_test_case_by_id,
    backfill_testcase_numbers,
    update_test_case,
    delete_test_case,
    get_test_case_history_by_test_case_id,
    get_iteration_by_id,
    update_iteration,
    delete_iteration_by_id,
    get_latest_tester_and_update
)

app = Flask(__name__)
init_db()
backfill_testcase_numbers()

GAMES = ['Aviator', 'CricketX', 'Piggy Dash', 'Roller Blitz', 'Marble Gp', 'Hilo', 'Mines', 'Roulette', 'Keno',
         'Tower', 'Rummy', 'TeenPatti', 'Ludo', 'Snake&Ladder', 'Andar Bahar', 'Poker', 'Carrom']


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
            'status': request.form['status'],
            'priority': request.form['priority'],
            'iteration': 0,
        }
        created_by = request.form.get('created_by', 'Unknown')
        add_test_case(game_name, data, created_by)
        return redirect(url_for('index', game_name=game_name))
    return render_template('add_testcase.html', game_name=game_name)


@app.route('/games/<game_name>/testcase/<int:testcase_id>', methods=['GET', 'POST'])
def view_testcase(game_name, testcase_id):
    if request.method == 'POST':
        try:
            iteration = int(request.form['iteration'])
        except (ValueError, TypeError):
            iteration = 0  # Default iteration if invalid input

        actual_result = request.form.get('actual_result', '')
        status = request.form.get('status', '')
        description = request.form.get('description', '')
        steps = request.form.get('steps', '')
        expected_result = request.form.get('expected_result', '')
        priority = request.form.get('priority', '')
        created_by = request.form.get('created_by', 'Unknown')

        update_test_case(
            testcase_id, actual_result, status, iteration,
            description, steps, expected_result, priority, created_by
        )
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    # GET request
    test_case = get_test_case_by_id(testcase_id)
    if not test_case:
        return f"Test Case with ID {testcase_id} not found.", 404

    def parse_datetime(dt_str):
        """Helper to parse datetime strings robustly."""
        if not dt_str:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    # Format test_case date_created
    dt_created = parse_datetime(test_case.get('date_created'))
    test_case['date_created'] = dt_created.strftime("%b %d, %Y %I:%M %p") if dt_created else ''

    # Format history dates
    history = get_test_case_history_by_test_case_id(testcase_id)
    for entry in history:
        dt_created_at = parse_datetime(entry.get('created_at'))
        dt_updated_at = parse_datetime(entry.get('updated_at'))

        entry['created_at'] = dt_created_at.strftime("%b %d, %Y %I:%M %p") if dt_created_at else ''
        entry['updated_at'] = dt_updated_at.strftime("%b %d, %Y %I:%M %p") if dt_updated_at else ''

    return render_template(
        'view_testcase.html',
        game_name=game_name,
        test_case=test_case,
        history=history,
        user_name=''
    )


@app.route('/game/<game_name>/delete/<int:testcase_id>', methods=['POST'])
def delete_testcase(game_name, testcase_id):
    delete_test_case(testcase_id)
    return redirect(url_for('index', game_name=game_name))


@app.route('/games/<game_name>/testcase/<int:testcase_id>/update', methods=['POST'])
def update_testcase_route(game_name, testcase_id):
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
    iteration = get_iteration_by_id(iteration_id) 
    
    if not iteration:
        return "Iteration not found", 404

    if request.method == 'POST':
        description = request.form['description']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        actual_result = request.form['actual_result']
        status = request.form['status']
        priority = request.form['priority']

        updated_at = datetime.now().strftime('%Y-%m-%d %I:%M %p')

        update_iteration(iteration_id, description, steps, expected_result, actual_result, status, priority, updated_at)

        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    return render_template('edit_iteration.html', iteration=iteration, game_name=game_name, testcase_id=testcase_id)


@app.route('/games/<game_name>/testcase/<int:testcase_id>/iteration/<int:iteration_id>/delete', methods=['POST'])
def delete_iteration_route(game_name, testcase_id, iteration_id):
    print(f"Deleting iteration: {iteration_id}")
    delete_iteration_by_id(iteration_id)
    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))


@app.route('/games/<game_name>/summary')
def summary_report(game_name):
    from flask import request  

    test_cases = get_all_test_cases(game_name)
    total_cases = len(test_cases)

    status_counts = {'Pass': 0, 'Fail': 0, 'Pending': 0, 'Hold': 0, 'Discussion': 0}
    priorities = {'Major': 0, 'Medium': 0, 'Minor': 0}

    for tc in test_cases:
        status = tc['status']
        priority = tc['priority']
        if status in status_counts:
            status_counts[status] += 1
        if priority in priorities:
            priorities[priority] += 1

    def calc_percent(count):
        return round((count / total_cases) * 100, 2) if total_cases > 0 else 0.0

    pass_percentage = calc_percent(status_counts['Pass'])
    fail_percentage = calc_percent(status_counts['Fail'])

    # Get latest tester and updated_at from test_case_history
    tester, last_updated = get_latest_tester_and_update(game_name)

    # Get manually entered values from query string
    art_version = request.args.get('Art_version', 'N/A')
    uiux_version = request.args.get('UI/UX_version', 'N/A')
    developer = request.args.get('Developer Name', 'N/A')
    phase_no = request.args.get('phase_no', 'N/A')
    date_received = request.args.get('date_time_received', 'N/A')
    date_delivered = datetime.now().strftime('%Y-%m-%d %I:%M %p')
    iteration_no = request.args.get('iteration_no', 'N/A')

    return render_template(
        'summary.html',
        game_name=game_name,
        total_cases=total_cases,
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


@app.route('/games/<game_name>/testcase/<int:testcase_id>/update_iteration', methods=['POST'])
def update_iteration_route(game_name, testcase_id):
    iteration = request.form.get('iteration', type=int)
    if iteration is None or iteration < 1:
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))
    success = update_iteration(testcase_id, iteration)
    if not success:
        pass

    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))


if __name__ == '__main__':
    app.run(debug=True)

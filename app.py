from flask import Flask, render_template, request, redirect, url_for
import models
from collections import defaultdict
from datetime import datetime
from collections import defaultdict

from models import (
    init_db,
    add_test_case,
    get_all_test_cases,
    get_test_case_by_id,
    backfill_testcase_numbers,
    update_test_case,
    delete_test_case,
    get_iterations_by_test_case_id,
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
    test_cases, all_same_iteration = get_all_test_cases(game_name)
    print(f"test_cases sample: {test_cases[:2]}")  # Inspect first two test cases
    
    # Ensure test_cases is not empty before accessing
    if test_cases and isinstance(test_cases[0], dict):
        first_iteration = test_cases[0].get('iteration', None)
    else:
        first_iteration = None

    grouped_cases = defaultdict(list)
    for case in test_cases:
        grouped_cases['All Test Cases'].append(case)
    return render_template('index.html', game_name=game_name, grouped_cases=grouped_cases, all_same_iteration=all_same_iteration)





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


from models import add_iteration, update_test_case_iteration
@app.route('/games/<game_name>/testcase/<int:testcase_id>', methods=['GET', 'POST'])
def view_testcase(game_name, testcase_id):
    if request.method == 'POST':
        try:
            iteration = int(request.form['iteration'])
            if iteration < 1:
                iteration = 1
        except (ValueError, TypeError):
            iteration = 1  

        actual_result = request.form.get('actual_result', '')
        status = request.form.get('status', '')
        description = request.form.get('description', '')
        steps = request.form.get('steps', '')
        expected_result = request.form.get('expected_result', '')
        priority = request.form.get('priority', '')
        created_by = request.form.get('created_by', '')

        add_iteration(
            testcase_id,
            actual_result,
            status,
            iteration,
            description,
            steps,
            expected_result,
            priority,
            created_by
)

        # Optionally update the main test case iteration count
        update_test_case_iteration(testcase_id, iteration)

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

    # Get iterations properly from models
    iterations = get_iterations_by_test_case_id(testcase_id)

    # Render template with iterations instead of undefined history
    return render_template(
        'view_testcase.html',
        game_name=game_name,
        test_case=test_case,
        iterations=iterations,
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
    # Your edit logic here, e.g. render edit form or process edits
    iteration = get_iteration_by_id(iteration_id)
    if not iteration:
        return "Iteration not found", 404

    if request.method == 'POST':
        # process update form
        description = request.form['description']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        actual_result = request.form['actual_result']
        status = request.form['status']
        priority = request.form['priority']
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        update_iteration(iteration_id, description, steps, expected_result, actual_result, status, priority, updated_at)
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    # GET request - render form with current iteration data
    return render_template(
            'edit_iteration.html',
            game_name=game_name,
            testcase_id=testcase_id,
            iteration_id=iteration_id,
            iteration=iteration,  # 👈 THIS is the key fix
            description=iteration['description'],
            steps=iteration['steps'],
            expected_result=iteration['expected_result'],
            actual_result=iteration['actual_result'],
            status=iteration['status'],
            priority=iteration['priority'],
)


from models import delete_iteration_by_id, reorder_iterations
@app.route('/game/<game_name>/testcase/<int:testcase_id>/iteration/<int:iteration_id>/delete', methods=['POST'])
def delete_iteration_route(game_name, testcase_id, iteration_id):
    delete_iteration_by_id(iteration_id)
    reorder_iterations(testcase_id)
    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))
pass

def calculate_priorities(test_cases):
    priorities = {'Major': 0, 'Medium': 0, 'Minor': 0}
    for tc in test_cases:
        p = tc.get('priority', 'Minor')
        if p in priorities:
            priorities[p] += 1
    return priorities

def get_test_cases(game_name):
    return [
        {'status': 'Pass', 'priority': 'Major', 'game_name': game_name},
        {'status': 'Fail', 'priority': 'Minor', 'game_name': game_name},
        {'status': 'Hold', 'priority': 'Minor', 'game_name': game_name},
    ]
@app.route('/games/<game_name>/summary')
def summary_report(game_name):
    iteration_no = request.args.get('iteration_no', 'N/A')
    art_version = request.args.get('art_version', 'N/A')
    uiux_version = request.args.get('uiux_version', 'N/A')
    developer = request.args.get('developer_name', 'N/A')
    tester = request.args.get('tester', 'N/A')
    phase_no = request.args.get('phase_no', 'N/A')
    date_received_raw = request.args.get('date_time_received', 'N/A')
    date_delivered_raw = request.args.get('date_time_delivered', 'N/A')
    new_bugs = request.args.get('New_bug', 'N/A')
    repeated_bugs = request.args.get('Repeated_bugs', 'N/A')

    def format_date(dt_str):
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return dt_str

    date_received = format_date(date_received_raw) if date_received_raw != 'N/A' else 'N/A'
    date_delivered = format_date(date_delivered_raw) if date_delivered_raw != 'N/A' else 'N/A'

    test_cases, _ = get_all_test_cases(game_name)

    def extract_tc_id(tc):
        return tc.get('id') if 'id' in tc else tc.get('testcase_id')

    total_cases = len(set(extract_tc_id(tc) for tc in test_cases if extract_tc_id(tc) is not None))

    def count_status(status_name):
        try:
            current_iteration = int(iteration_no)
        except:
            current_iteration = None

        if current_iteration is None:
            return sum(tc.get('status', '').strip().lower() == status_name.lower() for tc in test_cases)

        return sum(
            tc.get('status', '').strip().lower() == status_name.lower()
            and tc.get('iteration') == current_iteration
            for tc in test_cases
        )

    status_counts = {
        'Pass': count_status('Pass'),
        'Fail': count_status('Fail'),
        'Pending': count_status('Pending'),
        'Hold': count_status('Hold'),
        'Discussion': count_status('Discussion'),
    }

    pass_percentage = round((status_counts['Pass'] / total_cases) * 100, 2) if total_cases else 0
    fail_percentage = round((status_counts['Fail'] / total_cases) * 100, 2) if total_cases else 0

    priorities = calculate_priorities(test_cases)

    return render_template('summary.html',
                           game_name=game_name,
                           iteration_no=iteration_no,
                           art_version=art_version,
                           uiux_version=uiux_version,
                           developer=developer,
                           tester=tester,
                           phase_no=phase_no,
                           date_received=date_received,
                           date_delivered=date_delivered,
                           total_cases=total_cases,
                           status_counts=status_counts,
                           pass_percentage=pass_percentage,
                           fail_percentage=fail_percentage,
                           priorities=priorities,
                           repeated_bugs=repeated_bugs,
                           new_bugs=new_bugs)

@app.route('/games/<game_name>/testcase/<int:testcase_id>/update_iteration', methods=['POST'])
def update_iteration_route(game_name, testcase_id):
    iteration_id = request.form.get('iteration_id', type=int)
    if not iteration_id:
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    description = request.form.get('description', '')
    steps = request.form.get('steps', '')
    expected_result = request.form.get('expected_result', '')
    actual_result = request.form.get('actual_result', '')
    status = request.form.get('status', '')
    priority = request.form.get('priority', '')
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    success = update_iteration(iteration_id, description, steps, expected_result, actual_result, status, priority, updated_at)
    if not success:
        pass

    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

@app.template_filter('datetimeformat')
def datetimeformat(value):
    from datetime import datetime
    if not value:
        return ''
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%b %d, %Y %I:%M %p")
        except ValueError:
            continue
    return value 

@app.route('/games/<game_name>/complete_testing', methods=['POST'])
def complete_testing(game_name):
    return redirect(url_for('summary_report', game_name=game_name))

def format_date(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%b %d, %Y %I:%M %p")  
    except Exception:
        return dt_str
    



if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
import models
from collections import defaultdict
from datetime import datetime
import csv
from io import StringIO
import psycopg2 
from flask import jsonify
from models import get_connection
from flask import flash, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
import uuid 
from flask_mail import Mail, Message
import os



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
    get_latest_tester_and_update,
    get_test_suites,
    get_all_games,        
    add_game_db,           
    delete_game_db,


)

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY')

init_db()
backfill_testcase_numbers()

# GAMES =['Aviator', 'CricketX', 'Piggy Dash', 'Roller Blitz', 'Marble Gp', 'Hilo', 'Mines', 'Roulette', 'Keno',
#          'Tower', 'Rummy', 'TeenPatti', 'Ludo', 'Snake&Ladder', 'Andar Bahar', 'Poker', 'Carrom']

games_list = []

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,

    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
)

mail = Mail(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        organization = request.form['organization']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, email, password, organization, role) 
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, hashed_password, organization, role))
            conn.commit()

            # Send welcome email
            send_welcome_email(email, username)

            return redirect(url_for('login'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            message = "Email or Username already exists!"
        finally:
            cur.close()
            conn.close()

    return render_template('register.html', message=message)


def send_welcome_email(user_email, username):
    """Send a welcome email to the newly registered user."""
    msg = Message(
        subject="Welcome to TEST SLOW!",
        sender=app.config['MAIL_USERNAME'],
        recipients=[user_email],
        body=f"""
Hi {username},

Welcome to TEST SLOW! 

We're thrilled to have you join our platform. Dive in, and enjoy the experience!

Best regards,  
TEST SLOW
"""
    )
    try:
        mail.send(msg)
        print(f"Welcome email sent to {user_email}")
    except Exception as e:
        print(f"Error sending welcome email: {e}")


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        print(f"Trying to login with email: {email}")
        print(f"User found: {user}")

        if user:
            print("User exists, checking password...")
            if check_password_hash(user[3], password):
                print("Password matched!")
            else:
                print("Password mismatch.")
        else:
            print("No user found.")
      
        cur.close()
        conn.close()     


        # if user and check_password_hash(user[3], password):
            # ----- For Railway and Laptop ------#
        if user and check_password_hash(user[2], password):
            # Set session data
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[2]
            session['organization'] = user[4]  
            session['role'] = user[5]       

            return redirect(url_for('home'))
        else:
            message = "Invalid email or password."

    return render_template('login.html', message=message)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = ""
    if request.method == 'POST':
        email = request.form.get('email')

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            reset_token = str(uuid.uuid4())
            reset_link = url_for('reset_password', token=reset_token, _external=True)

            # Send email
            msg = Message(
                subject="Password Reset Request",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=f"Click the following link to reset your password: {reset_link}"
            )
            mail.send(msg)

            message = "If this email exists in our system, a password reset link has been sent."
        else:
            message = "If this email exists in our system, a password reset link has been sent."

    return render_template('forgot_password.html', message=message)

@app.route('/<game_name>/invite', methods=['POST'])
def invite_user(game_name):
    email = request.form['email']
    role = request.form['role']

    try:
        # Correctly generate the full URL to the project's test plan page
        project_url = url_for('index', game_name=game_name, _external=True)

        msg = Message(
            subject=f"You're invited to join project: {game_name}",
            recipients=[email],
            body=f"""
You've been invited to join the project '{game_name}' as a {role.capitalize()}.

Click the link below to access the project:
{project_url}

If you don’t have an account yet, please register first.

Thanks,  
TestSlow Team
"""
        )
        mail.send(msg)
        flash(f"Invitation sent to {email}.", "success")
    except Exception as e:
        print(f"Email send failed: {e}")
        flash("Failed to send email. Please check your configuration.", "danger")

    return redirect(url_for('index', game_name=game_name))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    message = ""
    # TODO: Validate token (check DB and expiry)
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        hashed_password = generate_password_hash(new_password)

        # TODO: Find user by token, update password in DB, invalidate token
        
        message = "Password has been reset successfully."
        return redirect(url_for('login'))

    return render_template('reset_password.html', message=message)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  
    return redirect(url_for('login'))


def smart_csv_reader(file_contents):
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(file_contents.splitlines()[0])
    return csv.DictReader(StringIO(file_contents), dialect=dialect)

from flask import flash

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'organization' not in session:
        return redirect(url_for('login'))

    org_name = session['organization']
    user_role = session.get('role')       
    username = session.get('username')    

    if request.method == 'POST':
        name = request.form['game_name']
        phase = request.form.get('game_phase')  
        category = request.form.get('category')

        success, error_message = add_game_db(name, phase, category, org_name, user_role)

        if not success:
            flash(error_message, 'danger')  
        else:
            flash("Game added successfully!", 'success')

        return redirect(url_for('home'))

    games_from_db = get_all_games_by_organization(org_name)
    return render_template(
        'games.html',
        games=games_from_db,
        user_role=user_role,    
        username=username,
        user_organization=org_name
    )

def add_game_db(name, phase, category, org_name, user_role):
    if user_role.lower() not in ('pm', 'tester', 'admin'):
        return False, "Only PMs or Testers can add new games."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO games (name, phase, category, organization) VALUES (%s, %s, %s, %s)",
            (name, phase, category, org_name)
        )
        conn.commit()
        return True, None
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Game with this name already exists."
    finally:
        cur.close()
        conn.close()


def get_all_games_by_organization(organization):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, phase, category FROM games WHERE organization = %s", (organization,))
    games = cur.fetchall()
    cur.close()
    conn.close()
    return [{'name': g[0], 'phase': g[1], 'category': g[2]} for g in games]

@app.route('/add_game', methods=['POST'])
def add_game():
    if 'organization' not in session:
        return redirect(url_for('login'))

    game_name = request.form.get('game_name', '').strip()
    game_phase = request.form.get('game_phase', '').strip()
    categories = request.form.get('categories', '').strip()
    organization = session['organization'] 

    if game_name:
        add_game_db(game_name, game_phase, categories, organization)

    return redirect(url_for('home'))


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


@app.route('/delete/<game_name>', methods=['POST'])
def delete_game(game_name):
    delete_game_db(game_name)  # Delete game from DB
    return redirect(url_for('home'))

from models import add_iteration, update_test_case_iteration
@app.route('/games/<game_name>/testcase/<int:testcase_id>', methods=['GET', 'POST'])
def view_testcase(game_name, testcase_id):
    if request.method == 'POST':
        try:
            iteration = int(request.form.get('iteration', 0))
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

        update_test_case_iteration(testcase_id, iteration)

        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    # GET request
    test_case = get_test_case_by_id(testcase_id)
    if not test_case:
        return f"Test Case with ID {testcase_id} not found.", 404

    def parse_datetime(dt_str):
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

    dt_created = parse_datetime(test_case.get('date_created'))
    test_case['date_created'] = dt_created.strftime("%b %d, %Y %I:%M %p") if dt_created else ''

    # Fetch associated test suites for this testcase
    iterations = get_iterations_by_test_case_id(testcase_id)

    return render_template(
        'view_testcase.html',
        game_name=game_name,
        testcase_id=testcase_id,
        test_case=test_case,
        iterations=iterations,
        suites = get_test_suites(testcase_id), 
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
            iteration=iteration,  
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

    # Try to parse new/repeated bugs from form
    try:
        new_bugs = int(request.args.get('New_bug'))
    except (TypeError, ValueError):
        new_bugs = None

    try:
        repeated_bugs = int(request.args.get('Repeated_bugs'))
    except (TypeError, ValueError):
        repeated_bugs = None

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

    # Get unique iteration numbers from test cases
    iterations_in_cases = {int(tc.get('iteration', 0)) for tc in test_cases if tc.get('iteration') is not None}

    # Check if all iterations are the same (only one unique iteration)
    all_same_iteration = len(iterations_in_cases) == 1

    # Parse iteration_no safely
    try:
        requested_iteration = int(iteration_no)
    except (ValueError, TypeError):
        requested_iteration = None

    # Determine which iteration to use for filtering
    if all_same_iteration:
        iteration_to_use = None  # No filtering — show all
    else:
        # Filter by requested iteration if valid, else fallback to max iteration
        if requested_iteration in iterations_in_cases:
            iteration_to_use = requested_iteration
        else:
            iteration_to_use = max(iterations_in_cases) if iterations_in_cases else None

    def count_status(status_name):
        status_name_lower = status_name.lower()
        if iteration_to_use is None:
            # No iteration filtering - count all test cases with status
            return sum(tc.get('status', '').strip().lower() == status_name_lower for tc in test_cases)
        else:
            # Filter by iteration_to_use
            return sum(
                (tc.get('status', '').strip().lower() == status_name_lower) and
                (int(tc.get('iteration', 0)) == iteration_to_use)
                for tc in test_cases if tc.get('iteration') is not None
            )

    status_counts = {
        'Pass': count_status('Pass'),
        'Fail': count_status('Fail'),
        'Pending': count_status('Pending'),
        'Hold': count_status('Hold'),
        'Discussion': count_status('Discussion'),
    }

    total_cases = len(set(
        extract_tc_id(tc)
        for tc in test_cases
        if iteration_to_use is None or int(tc.get('iteration', 0)) == iteration_to_use
    ))

    pass_percentage = round((status_counts['Pass'] / total_cases) * 100, 2) if total_cases else 0
    fail_percentage = round((status_counts['Fail'] / total_cases) * 100, 2) if total_cases else 0

    priorities = calculate_priorities(test_cases)

    # Calculate new/repeated bugs only if not given and iteration > 1
    if (new_bugs is None or repeated_bugs is None) and iteration_to_use and iteration_to_use > 1:
        new_bugs = 0
        repeated_bugs = 0

        iteration_status_map = defaultdict(dict)
        for tc in test_cases:
            tc_id = extract_tc_id(tc)
            if tc_id is None:
                continue
            iteration = tc.get('iteration')
            status = tc.get('status', '').strip().lower()
            if iteration is not None:
                iteration_status_map[iteration][tc_id] = status

        prev_status_map = iteration_status_map.get(iteration_to_use - 1, {})
        current_status_map = iteration_status_map.get(iteration_to_use, {})

        for tc_id, curr_status in current_status_map.items():
            prev_status = prev_status_map.get(tc_id)
            if curr_status == 'fail':
                if prev_status == 'pass':
                    new_bugs += 1
                elif prev_status == 'fail':
                    repeated_bugs += 1
    else:
        if new_bugs is None:
            new_bugs = 0
        if repeated_bugs is None:
            repeated_bugs = 0

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
    
    if isinstance(value, datetime):
        return value.strftime("%b %d, %Y %I:%M %p")
    
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%b %d, %Y %I:%M %p")
        except ValueError:
            continue
    
    return str(value)


@app.route('/games/<game_name>/complete_testing', methods=['POST'])
def complete_testing(game_name):
    return redirect(url_for('summary_report', game_name=game_name))

def format_date(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%b %d, %Y %I:%M %p")  
    except Exception:
        return dt_str
    
@app.route('/add_suite/<game_name>/<int:testcase_id>', methods=['POST'])
def add_suite(game_name, testcase_id):
    suite_name = request.form['suite_name']
    description = request.form['description']
    
    status = request.form['status']
    iteration = request.form.get('iteration', '')  
    expected = request.form['expected']
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO test_suites (testcase_id, suite_name, description, status, iteration, expected)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (testcase_id, suite_name, description, status, iteration, expected))
            conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to insert suite: {e}")  
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id, error='duplicate'))

    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@app.route('/edit_suite/<game_name>/<int:testcase_id>/<int:suite_id>', methods=['GET', 'POST'])
def edit_suite(game_name, testcase_id, suite_id):
    if request.method == 'POST':
    # Get form data
        suite_name = request.form['suite_name']
        description = request.form['description']
        iteration = request.form.get('iteration')
        status = request.form.get('status')
        actual = request.form.get('actual')

        conn = get_connection()
        with conn.cursor() as cur:
            # Optional: Fetch current suite data for history before updating
            cur.execute("SELECT * FROM test_suites WHERE id = %s", (suite_id,))
            old_row = cur.fetchone()

            # Insert current state into history table
            cur.execute("""
                INSERT INTO suite_history (suite_id, suite_name, description, status, iteration, actual, modified_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
            """, (suite_id, suite_name, description, status, iteration, actual))



            # Update the suite
            cur.execute("""
                UPDATE test_suites
                SET suite_name = %s, description = %s, status = %s, iteration = %s, actual = %s
                WHERE id = %s
            """, (suite_name, description, status, iteration, actual, suite_id))
            conn.commit()
            
        return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))

    # GET request
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM test_suites WHERE id = %s", (suite_id,))
        row = cur.fetchone()

    if not row:
        return "Suite not found", 404

    # suite = {
    #     'id': row[0],
    #     'suite_name': row[2],
    #     'description': row[3],
    #     'created_at': row[6],
    #     'testcase_id': row[4],
    #     'status': row[4],
    #     'iteration': row[5],
    #     'actual': row[7]

    # }

    # For Railway app
    suite = {
        'id': row[0],
        'suite_name': row[2],
        'description': row[3],
        'created_at': row[6],
        'testcase_id': row[1],
        'status': row[4],
        'iteration': row[5],
        'actual': row[7],
        'expected': row[8]

    }
    
    # For moniter DB

    # suite = {
    #     'id': row[0],
    #     'suite_name': row[1],
    #     'description': row[2],
    #     'created_at': row[3],
    #     'testcase_id': row[4],
    #     'status': row[5],
    #     'iteration': row[6],
    #     'actual': row[7],
    #     'expected': row[8]

    # }

    return render_template('edit_suite.html', game_name=game_name, testcase_id=testcase_id, suite_id=suite_id, suite=suite)

@app.route('/suite_history/<game_name>/<int:testcase_id>/<int:suite_id>')
def suite_history(game_name, testcase_id, suite_id):
    conn = get_connection()
    with conn.cursor() as cur:
        # Fetch suite history entries for the given suite_id
        cur.execute("""
            SELECT * FROM suite_history
            WHERE suite_id = %s
            ORDER BY modified_at DESC
        """, (suite_id,))
        history = cur.fetchall()

        # Fetch suite info from test_suites table using suite_id
        cur.execute("""
            SELECT * FROM test_suites
            WHERE id = %s
        """, (suite_id,))
        suite = cur.fetchone()

    return render_template(
        'case_history.html',
        history=history,
        suite=suite,
        suite_id=suite_id,
        game_name=game_name,
        testcase_id=testcase_id
    )

@app.route('/delete_suite_history/<int:history_id>/<int:suite_id>/<game_name>/<int:testcase_id>', methods=['POST'])
def delete_suite_history(history_id, suite_id, game_name, testcase_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM suite_history WHERE id = %s", (history_id,))
        conn.commit()
    return redirect(url_for('suite_history', suite_id=suite_id, game_name=game_name, testcase_id=testcase_id))


@app.route('/delete_suite/<game_name>/<int:testcase_id>/<int:suite_id>', methods=['POST'])
def delete_suite(game_name, testcase_id, suite_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM test_suites WHERE id = %s", (suite_id,))
        conn.commit()

    return redirect(url_for('view_testcase', game_name=game_name, testcase_id=testcase_id))
    

if __name__ == '__main__':
    app.run(debug=True)

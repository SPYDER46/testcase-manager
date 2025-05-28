import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dateutil import parser

DB_CONFIG = {
    'host': 'localhost',
    'database': 'testdb',
    'user': 'postgres',
    'password': 'root',
    'port': 5432
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id SERIAL PRIMARY KEY,
                    game TEXT,
                    testcase_number INTEGER,
                    title TEXT,
                    description TEXT,
                    steps TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    status TEXT,
                    priority TEXT,
                    iteration INTEGER,
                    created_by TEXT,
                    date_created TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS test_case_history (
                id SERIAL PRIMARY KEY,
                test_case_id INTEGER REFERENCES test_cases(id),
                iteration INTEGER,
                title TEXT,
                description TEXT,
                steps TEXT,
                expected_result TEXT,
                actual_result TEXT,
                status TEXT,
                priority TEXT,
                updated_at TEXT,
                created_by TEXT,
                requirement_references TEXT,
                defect_references TEXT,
                defect_status TEXT,
                created_at TEXT
            )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS iteration (
                id SERIAL PRIMARY KEY,
                test_case_id INTEGER NOT NULL,
                iteration INTEGER NOT NULL,
                description TEXT,
                steps TEXT,
                expected_result TEXT,
                actual_result TEXT,
                status VARCHAR(50),
                priority VARCHAR(50),
                created_by VARCHAR(100),
                updated_at TIMESTAMP,
                FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
                );
            ''')


def add_test_case(game, data, created_by):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT COALESCE(MAX(testcase_number), 0) FROM test_cases WHERE game = %s', (game,))
            max_tc_num = c.fetchone()['coalesce'] or 0  # Using RealDictCursor
            new_tc_num = max_tc_num + 1
            now = datetime.now()  
            
            c.execute('''
                INSERT INTO test_cases (
                    game, testcase_number, title, description, steps, expected_result,
                    actual_result, status, priority, iteration, created_by, date_created
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, date_created
            ''', (
                game, new_tc_num, data['title'], data['description'], data['steps'], data['expected_result'],
                '', data['status'], data['priority'], data['iteration'], created_by, now
            ))
            row = c.fetchone()
            new_id = row['id']
            date_created = row['date_created']

            conn.commit()

            formatted_date_created = date_created.strftime("%b %d, %Y %I:%M %p")

            return new_id, formatted_date_created



def get_all_test_cases(game):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT * FROM test_cases WHERE game = %s ORDER BY testcase_number', (game,))
            return c.fetchall()


def get_test_case_by_id(testcase_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT * FROM test_cases WHERE id = %s', (testcase_id,))
            return c.fetchone()


def backfill_testcase_numbers():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('''
                WITH numbered AS (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY game ORDER BY id) AS rn
                    FROM test_cases
                )
                UPDATE test_cases
                SET testcase_number = numbered.rn
                FROM numbered
                WHERE test_cases.id = numbered.id
            ''')
            conn.commit()


def update_test_case(testcase_id, actual_result, status, iteration, description, steps, expected_result, priority, created_by):
    with get_connection() as conn:
        with conn.cursor() as c:
            now = datetime.now().strftime('%Y-%m-%d %I:%M %p')

            # Update test_cases table first
            c.execute('''
                UPDATE test_cases
                SET actual_result = %s, status = %s, iteration = %s,
                    description = %s, steps = %s, expected_result = %s,
                    priority = %s, created_by = %s
                WHERE id = %s
            ''', (actual_result, status, iteration, description, steps, expected_result, priority, created_by, testcase_id))

            # Insert into test_case_history (single correct insert)
            c.execute('''
                INSERT INTO test_case_history (
                    test_case_id, iteration, title, description, steps, expected_result,
                    actual_result, status, priority, updated_at, created_by, created_at
                )
                SELECT id, %s, title, %s, %s, %s, %s, %s, %s, %s, %s, %s
                FROM test_cases WHERE id = %s
            ''', (iteration, description, steps, expected_result, actual_result, status, priority, now, created_by, now, testcase_id))

            conn.commit()

def delete_test_case(testcase_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('DELETE FROM test_case_history WHERE test_case_id = %s', (testcase_id,))
            c.execute('DELETE FROM iteration WHERE test_case_id = %s', (testcase_id,))
            c.execute('DELETE FROM test_cases WHERE id = %s', (testcase_id,))
            conn.commit()

def get_test_case_history_by_test_case_id(testcase_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('''
                SELECT * FROM test_case_history WHERE test_case_id = %s ORDER BY created_at DESC
            ''', (testcase_id,))
            return c.fetchall()
        
def add_iteration(test_case_id, actual_result, status, iteration, description, steps, expected_result, priority, created_by):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(iteration) FROM iteration WHERE test_case_id = %s", (test_case_id,))
    max_iteration = cursor.fetchone()[0] or 0
    new_iteration_number = max_iteration + 1

    now = datetime.now()  # keep it as a datetime object for TIMESTAMP

    cursor.execute("""
        INSERT INTO iteration (
            iteration, test_case_id, description, steps, expected_result,
            actual_result, status, priority, created_by, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        new_iteration_number, test_case_id, description, steps, expected_result,
        actual_result, status, priority, created_by, now
    ))

    conn.commit()
    conn.close()
 

from psycopg2.extras import RealDictCursor  

def get_iterations_by_test_case_id(testcase_id):
    iterations = []
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, iteration, description, actual_result, status, priority, created_by, updated_at
                FROM iteration
                WHERE test_case_id = %s
                ORDER BY iteration ASC
            """, (testcase_id,))


            rows = cursor.fetchall()

            for row in rows:
                updated_at = ''

                if row['updated_at']:
                    try:
                        updated_at = row['updated_at'].strftime("%b %d, %Y %I:%M %p")
                    except Exception as e:
                        print("Date format error:", e)
                        updated_at = str(row['updated_at'])


                iterations.append({
                    'id': row['id'], 
                    'iteration': row['iteration'],
                    'description': row['description'] or '',
                    'actual_result': row['actual_result'] or '',
                    'status': row['status'].capitalize() if row['status'] else '',
                    'priority': row['priority'] or '',
                    'updated_by': row['created_by'] or 'Unknown',
                    'updated_at': updated_at
                })
    finally:
        conn.close()
    return iterations


def get_iteration_by_id(iteration_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT * FROM iteration WHERE id = %s', (iteration_id,))
            return c.fetchone()

def update_iteration(iteration_id, description, steps, expected_result, actual_result, status, priority, updated_at):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE iteration
                SET description = %s,
                    steps = %s,
                    expected_result = %s,
                    actual_result = %s,
                    status = %s,
                    priority = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                description, steps, expected_result, actual_result,
                status, priority, updated_at, iteration_id
            ))
            conn.commit()
    return True



def reorder_iterations(test_case_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM iteration WHERE test_case_id = %s ORDER BY iteration
    """, (test_case_id,))
    rows = cursor.fetchall()
    
    for idx, (iteration_id,) in enumerate(rows, start=1):
        cursor.execute("""
            UPDATE iteration SET iteration = %s WHERE id = %s
        """, (idx, iteration_id))
    
    conn.commit()
    conn.close()


def delete_iteration_by_id(iteration_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('DELETE FROM iteration WHERE id = %s', (iteration_id,))
            conn.commit()

def update_test_case_iteration(testcase_id, iteration):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE test_cases SET iteration = %s WHERE id = %s", (iteration, testcase_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_latest_tester_and_update(game_name):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('''
                SELECT created_by, updated_at FROM test_case_history
                WHERE test_case_id IN (SELECT id FROM test_cases WHERE game = %s)
                ORDER BY updated_at DESC LIMIT 1
            ''', (game_name,))
            row = c.fetchone()
            if row:
                return row[0], row[1]
            return "N/A", "N/A"
        
def get_all_test_cases_with_latest(game):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT * FROM test_cases WHERE game = %s ORDER BY testcase_number', (game,))
            test_cases = c.fetchall()
            
            for case in test_cases:
                testcase_id = case['id']

                # Fetch latest from test_case_history
                c.execute('''
                    SELECT status, priority, iteration, updated_at 
                    FROM test_case_history
                    WHERE test_case_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                ''', (testcase_id,))
                latest_hist = c.fetchone()

                if latest_hist:
                    case['status'] = latest_hist['status'] or case['status']
                    case['priority'] = latest_hist['priority'] or case['priority']
                    case['iteration'] = latest_hist['iteration'] or case['iteration']
                    if latest_hist['updated_at']:
                        case['last_updated'] = latest_hist['updated_at'].strftime("%b %d, %Y %I:%M %p")
                else:
                    # Fallback if no history found
                    case['iteration'] = case['iteration'] or 0
                    if case['date_created']:
                        try:
                            case['last_updated'] = case['date_created'].strftime("%b %d, %Y %I:%M %p")
                        except Exception:
                            case['last_updated'] = str(case['date_created'])
                    else:
                        case['last_updated'] = '-'
            
            return test_cases






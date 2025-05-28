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
                    test_case_id INTEGER REFERENCES test_cases(id),
                    iteration INTEGER,
                    description TEXT,
                    steps TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    status TEXT,
                    priority TEXT,
                    created_by TEXT,
                    updated_at TEXT
                )
            ''')

def add_test_case(game, data, created_by):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute('SELECT COALESCE(MAX(testcase_number), 0) FROM test_cases WHERE game = %s', (game,))
            max_tc_num = c.fetchone()['coalesce'] or 0  # Using RealDictCursor
            new_tc_num = max_tc_num + 1
            now = datetime.now()  # Keep it as datetime object
            
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
        
def add_iteration(test_case_id, actual_result, status, description, steps, expected_result, priority, created_by):
    conn = get_connection()
    cursor = conn.cursor()

    # Get max iteration number for this test case
    cursor.execute("SELECT MAX(iteration) FROM iteration WHERE test_case_id = %s", (test_case_id,))
    max_iteration = cursor.fetchone()[0] or 0
    new_iteration_number = max_iteration + 1

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Proper timestamp for updated_at

    cursor.execute("""
        INSERT INTO iteration
            (test_case_id, actual_result, status, iteration, description, steps,
             expected_result, priority, created_by, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        test_case_id, actual_result, status, new_iteration_number,
        description, steps, expected_result, priority, created_by, now
    ))
    
    conn.commit()
    conn.close()   

def get_iterations_by_test_case_id(testcase_id):
    iterations = []
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, test_case_id, iteration, description, steps, expected_result,
                       actual_result, status, priority, created_at, updated_at, created_by
                FROM iteration
                WHERE test_case_id = %s
                ORDER BY updated_at ASC
            """, (testcase_id,))

            rows = cursor.fetchall()

            for row in rows:
                # Format updated_at
                updated_at = ''
                if row[10]:
                    if isinstance(row[10], str):
                        updated_at = parser.parse(row[10]).strftime("%b %d, %Y %I:%M %p")
                    else:
                        updated_at = row[10].strftime("%b %d, %Y %I:%M %p")

                iterations.append({
                    'id': row[0],
                    'iteration': row[2],
                    'description': row[3],
                    'steps': row[4],
                    'expected_result': row[5],
                    'actual_result': row[6],
                    'status': row[7].capitalize() if row[7] else '',
                    'priority': row[8].capitalize() if row[8] else '',
                    'updated_by': row[11] or 'Unknown',
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
        with conn.cursor() as c:
            c.execute('''
                UPDATE iteration
                SET description = %s, steps = %s, expected_result = %s,
                    actual_result = %s, status = %s, priority = %s, updated_at = %s
                WHERE id = %s
            ''', (description, steps, expected_result, actual_result, status, priority, updated_at, iteration_id))
            conn.commit()

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


def update_iteration(testcase_id, iteration):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute('UPDATE test_cases SET iteration = %s WHERE id = %s', (iteration, testcase_id))
            conn.commit()
            return True
        
        



# models.py
import sqlite3
from datetime import datetime

DB_NAME = 'database.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS test_case_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_case_id INTEGER,
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
            doc_versions TEXT,
            approval_for_release TEXT,
            phase_no INTEGER,
            date_time_received TEXT,
            FOREIGN KEY(test_case_id) REFERENCES test_cases(id)
        )''')
        conn.commit()

def add_test_case(game, data, created_by):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Ensure we ignore NULLs when getting max
        c.execute('SELECT MAX(testcase_number) FROM test_cases WHERE game = ? AND testcase_number IS NOT NULL', (game,))
        max_number = c.fetchone()[0]
        next_number = (max_number or 0) + 1

        c.execute('''INSERT INTO test_cases (
            game, testcase_number, title, description, steps, expected_result, status, priority, iteration, created_by, date_created
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            game, next_number, data['title'], data['description'], data['steps'],
            data['expected_result'], data['status'],
            data['priority'], data['iteration'], created_by,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

def backfill_testcase_numbers():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Get unique games
        c.execute('SELECT DISTINCT game FROM test_cases')
        games = [row['game'] for row in c.fetchall()]

        for game in games:
            c.execute('SELECT id FROM test_cases WHERE game = ? ORDER BY id ASC', (game,))
            all_cases = c.fetchall()

            for idx, row in enumerate(all_cases, start=1):
                c.execute('UPDATE test_cases SET testcase_number = ? WHERE id = ?', (idx, row['id']))

        conn.commit()
        print("Test case numbers backfilled per game.")


def update_test_case(testcase_id, actual_result, status, iteration,
                     description, steps, expected_result, priority, created_by,
                     requirement_references=None, doc_versions=None, approval_for_release=None,
                     phase_no=None, date_time_received=None):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('SELECT title, description, steps, expected_result, priority FROM test_cases WHERE id = ?', (testcase_id,))
        result = c.fetchone()

        if not result:
            print("Test case not found.")
            return

        title = result['title']
        existing_description = result['description']
        existing_steps = result['steps']
        existing_expected_result = result['expected_result']
        existing_priority = result['priority']

        c.execute('''INSERT INTO test_case_history (
            test_case_id, iteration, title, description, steps, 
            expected_result, actual_result, status, priority, updated_at, created_by,
            requirement_references, doc_versions, approval_for_release, phase_no, date_time_received
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            testcase_id, iteration, title,
            description or existing_description,
            steps or existing_steps,
            expected_result or existing_expected_result,
            actual_result, status,
            priority or existing_priority,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            created_by,
            requirement_references,
            doc_versions,
            approval_for_release,
            phase_no,
            date_time_received
        ))

        c.execute('''UPDATE test_cases
            SET actual_result = ?, status = ?, iteration = ?, priority = ?
            WHERE id = ?''', (actual_result, status, iteration, priority, testcase_id))
        conn.commit()

def get_all_test_cases(game):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''
            SELECT 
                tc.*,
                COALESCE((
                    SELECT MAX(updated_at) 
                    FROM test_case_history 
                    WHERE test_case_id = tc.id
                ), tc.date_created) AS last_updated
            FROM test_cases tc
            WHERE tc.game = ?
            ORDER BY tc.testcase_number ASC
        ''', (game,))

        return c.fetchall()

def get_test_case_by_id(testcase_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_cases WHERE id = ?', (testcase_id,))
        return c.fetchone()

def delete_test_case(testcase_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Get game before delete
        c.execute('SELECT game FROM test_cases WHERE id = ?', (testcase_id,))
        row = c.fetchone()
        if not row:
            return
        game = row['game']

        # Delete the test case
        c.execute('DELETE FROM test_cases WHERE id = ?', (testcase_id,))
        c.execute('DELETE FROM test_case_history WHERE test_case_id = ?', (testcase_id,))

        # Reorder the remaining test cases
        c.execute('SELECT id FROM test_cases WHERE game = ? ORDER BY testcase_number ASC', (game,))
        all_cases = c.fetchall()

        for idx, case in enumerate(all_cases, start=1):
            c.execute('UPDATE test_cases SET testcase_number = ? WHERE id = ?', (idx, case['id']))

        conn.commit()


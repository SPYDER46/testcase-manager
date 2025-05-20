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
            FOREIGN KEY(test_case_id) REFERENCES test_cases(id)
        )''')
        conn.commit()

def add_test_case(game, data, created_by):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO test_cases (
            game, title, description, steps, expected_result, 
            actual_result, status, priority, iteration, created_by, date_created
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            game, data['title'], data['description'], data['steps'],
            data['expected_result'], data['actual_result'], data['status'],
            data['priority'], data['iteration'], created_by,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

def update_test_case(testcase_id, actual_result, status, iteration,
                     description, steps, expected_result, priority, created_by):
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
            expected_result, actual_result, status, priority, updated_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            testcase_id, iteration, title,
            description or existing_description,
            steps or existing_steps,
            expected_result or existing_expected_result,
            actual_result, status,
            priority or existing_priority,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            created_by
        ))

        c.execute('''UPDATE test_cases
            SET actual_result = ?, status = ?, iteration = ?, priority = ?
            WHERE id = ?''', (actual_result, status, iteration, priority, testcase_id))
        conn.commit()

def get_all_test_cases(game):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_cases WHERE game = ? ORDER BY id ASC', (game,))
        return c.fetchall()

def get_test_case_by_id(testcase_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_cases WHERE id = ?', (testcase_id,))
        return c.fetchone()

def delete_test_case(testcase_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM test_cases WHERE id = ?', (testcase_id,))
        c.execute('DELETE FROM test_case_history WHERE test_case_id = ?', (testcase_id,))
        conn.commit()

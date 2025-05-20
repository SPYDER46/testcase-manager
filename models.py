# models.py
import sqlite3
from datetime import datetime

DB_NAME = 'database.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT,
                title TEXT,
                description TEXT,
                steps TEXT,
                expected_result TEXT,
                actual_result TEXT,
                status TEXT,
                priority TEXT,
                iteration TEXT,
                created_by TEXT,
                date_created TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS test_case_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id INTEGER,
                iteration TEXT,
                actual_result TEXT,
                status TEXT,
                updated_at TEXT,
                FOREIGN KEY(test_case_id) REFERENCES test_cases(id)
            )
        ''')
        conn.commit()

def add_test_case(game, data):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO test_cases (
                game, title, description, steps,
                expected_result, actual_result, status, priority,
                iteration, date_created
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            game, data['title'], data['description'], data['steps'],
            data['expected_result'], data['actual_result'], data['status'],
            data['priority'], data['iteration'], 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
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

def update_test_case(testcase_id, actual_result, status):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Fetch iteration from test case
        c.execute('SELECT iteration FROM test_cases WHERE id = ?', (testcase_id,))
        iteration = c.fetchone()['iteration']

        # ✅ Insert into history
        c.execute('''
            INSERT INTO test_case_history (test_case_id, iteration, actual_result, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            testcase_id, iteration, actual_result, status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        # ✅ Update current state
        c.execute('''
            UPDATE test_cases
            SET actual_result = ?, status = ?
            WHERE id = ?
        ''', (actual_result, status, testcase_id))
        conn.commit()

def delete_test_case(testcase_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM test_cases WHERE id = ?', (testcase_id,))
        conn.commit()

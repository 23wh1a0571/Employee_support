import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "./data/enterprise.db")

def check_leave_balance(emp_id: str) -> str:
    """Queries leave balance from SQLite database."""
    if not os.path.exists(DB_PATH):
        return f"Database file not found at {DB_PATH}."
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, leave_balance FROM employees WHERE UPPER(emp_id) = ?", (emp_id.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return f"Employee {row['name']} ({emp_id.upper()}) has {row['leave_balance']} days of leave remaining."
    return f"No employee found with ID {emp_id}."
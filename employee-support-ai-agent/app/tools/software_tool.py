import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "./data/enterprise.db")

def check_software_request(emp_id: str) -> str:
    """Queries pending software access requests for an employee."""
    if not os.path.exists(DB_PATH):
        return f"Database file not found at {DB_PATH}."
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT software_name, status FROM software_requests WHERE UPPER(emp_id) = ?", (emp_id.strip().upper(),))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        results = [f"{r['software_name']}: {r['status']}" for r in rows]
        return f"Software requests for {emp_id.upper()}: " + ", ".join(results)
    return f"No pending software requests found for employee {emp_id}."
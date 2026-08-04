import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "./data/enterprise.db")

def query_employee_db(query: str) -> str:
    """Executes a SQL SELECT query against the enterprise SQLite database."""
    if not os.path.exists(DB_PATH):
        return "Error: Enterprise database file not found. Please run seed.py first."

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Security check to prevent unintended mutations
        if not query.strip().upper().startswith("SELECT"):
            return "Error: Only read-only SELECT queries are allowed."

        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()

        if not rows:
            return "No matching records found in the database."

        formatted_results = [dict(zip(columns, row)) for row in rows]
        return str(formatted_results)

    except Exception as e:
        return f"Database Query Error: {str(e)}"

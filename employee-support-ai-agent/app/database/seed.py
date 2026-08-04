import sqlite3
import os
import io
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "enterprise.db")

def get_db_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_quoted_csv(filepath: str) -> pd.DataFrame:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    cleaned_lines = []
    for line in lines:
        s = line.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1].replace('""', '"')
        cleaned_lines.append(s)
    return pd.read_csv(io.StringIO("\n".join(cleaned_lines)), skipinitialspace=True)

def find_csv_file(file_name: str) -> str:
    candidate_paths = [
        os.path.join(BASE_DIR, "data", "policies", file_name),
        os.path.join(BASE_DIR, "data", file_name),
        os.path.join(os.getcwd(), "data", "policies", file_name),
        os.path.join(os.getcwd(), "data", file_name),
        os.path.join(BASE_DIR, file_name),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None

def create_extended_schema(conn):
    cursor = conn.cursor()
    # Leave Submissions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            request_id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days_requested INTEGER NOT NULL,
            status TEXT DEFAULT 'Approved',
            created_at TEXT NOT NULL
        )
    """)
    # Software Assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS software_assignments (
            assignment_id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            software_name TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            assigned_date TEXT NOT NULL
        )
    """)
    # Audit Logging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            action_type TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()

def seed_database():
    conn = get_db_connection()
    print("🚀 Seeding database directly from CSV files...")

    def process_and_seed(file_name: str, table_name: str):
        file_path = find_csv_file(file_name)
        if file_path:
            try:
                df = load_quoted_csv(file_path)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                print(f"  • Successfully loaded {len(df)} records into '{table_name}' from: {file_path}")
            except Exception as e:
                print(f"  ❌ Failed to process {file_name}: {str(e)}")
        else:
            print(f"  ⚠️ Warning: Could not locate {file_name}")

    process_and_seed("employees.csv", "employees")
    process_and_seed("leave.csv", "leave_balances")
    process_and_seed("ticket.csv", "tickets")
    process_and_seed("software.csv", "software_requests")
    process_and_seed("company_policy.csv", "policies")

    create_extended_schema(conn)

    conn.commit()
    conn.close()
    print("✅ Database successfully initialized and seeded at:", DB_PATH)

if __name__ == "__main__":
    seed_database()
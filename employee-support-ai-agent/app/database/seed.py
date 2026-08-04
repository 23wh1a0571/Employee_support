import sqlite3
import os
import io
import pandas as pd

# Path to the database file in project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "enterprise.db")

def get_db_connection():
    """Creates directory if needed and establishes connection to SQLite database."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_quoted_csv(filepath: str) -> pd.DataFrame:
    """Strips outer wrapping quotes and fixes inner escaped quotes from CSV files."""
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
    """Searches for the CSV file in data/policies/ and other standard locations."""
    candidate_paths = [
        os.path.join(BASE_DIR, "data", "policies", file_name),  # app_root/data/policies/file.csv
        os.path.join(BASE_DIR, "data", file_name),             # app_root/data/file.csv
        os.path.join(os.getcwd(), "data", "policies", file_name), # current_dir/data/policies/file.csv
        os.path.join(os.getcwd(), "data", file_name),          # current_dir/data/file.csv
        os.path.join(BASE_DIR, file_name),                    # app_root/file.csv
    ]
    
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None

def seed_database():
    """Reads all enterprise CSV datasets and populates SQLite database tables."""
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
            print(f"  ⚠️ Warning: Could not locate {file_name} in data/policies/ or standard paths.")

    # Seed all tables
    process_and_seed("employees.csv", "employees")
    process_and_seed("leave.csv", "leave_balances")
    process_and_seed("ticket.csv", "tickets")
    process_and_seed("software.csv", "software_requests")
    process_and_seed("company_policy.csv", "policies")

    conn.commit()
    conn.close()
    print("✅ Database successfully initialized and seeded at:", DB_PATH)

if __name__ == "__main__":
    seed_database()
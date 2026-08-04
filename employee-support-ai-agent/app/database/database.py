import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "enterprise.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        emp_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payslips (
        emp_id TEXT PRIMARY KEY,
        basic_salary REAL NOT NULL,
        allowances REAL NOT NULL,
        deductions REAL NOT NULL,
        net_pay REAL NOT NULL,
        payslip_url TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_balances (
        emp_id TEXT PRIMARY KEY,
        annual_leave INTEGER NOT NULL,
        sick_leave INTEGER NOT NULL,
        casual_leave INTEGER NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        emp_id TEXT NOT NULL,
        issue TEXT NOT NULL,
        status TEXT NOT NULL,
        assigned_tech TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS software_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT NOT NULL,
        software_name TEXT NOT NULL,
        status TEXT NOT NULL,
        requested_date TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
    );
    """)

    conn.commit()
    conn.close()

def seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Seed Employees
    employees = [
        ("EMP101", "Kavya Sharma", "kavya@enterprise.com", "Engineering"),
        ("EMP106", "Ananya Roy", "ananya@enterprise.com", "Data Science")
    ]
    cursor.executemany("INSERT OR REPLACE INTO employees VALUES (?, ?, ?, ?)", employees)

    # Seed Payslips
    payslips = [
        ("EMP101", 85000.0, 15000.0, 10000.0, 90000.0, "https://sso.enterprise.com/payslips/EMP101_July2026.pdf"),
        ("EMP106", 95000.0, 20000.0, 12000.0, 103000.0, "https://sso.enterprise.com/payslips/EMP106_July2026.pdf")
    ]
    cursor.executemany("INSERT OR REPLACE INTO payslips VALUES (?, ?, ?, ?, ?, ?)", payslips)

    # Seed Leave Balances
    leaves = [
        ("EMP101", 12, 5, 3),
        ("EMP106", 18, 4, 2)
    ]
    cursor.executemany("INSERT OR REPLACE INTO leave_balances VALUES (?, ?, ?, ?)", leaves)

    # Seed Tickets
    tickets = [
        ("TCK-501", "EMP101", "VPN Access Failure on Corporate Network", "In Progress", "Alex Rivera (IT Tier-2)", "August 04, 2026"),
        ("TCK-502", "EMP106", "MacBook Battery Replacement Request", "Resolved", "Sara Chen (IT Hardware)", "August 01, 2026")
    ]
    cursor.executemany("INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?)", tickets)

    # Seed Software Requests
    sw_reqs = [
        ("EMP101", "Figma Enterprise Pro", "Approved", "2026-07-28"),
        ("EMP106", "Docker Desktop Business", "Pending Manager Approval", "2026-08-02")
    ]
    cursor.executemany("INSERT OR REPLACE INTO software_requests (emp_id, software_name, status, requested_date) VALUES (?, ?, ?, ?)", sw_reqs)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_db()
    print("✅ Database initialized and seeded successfully at enterprise.db")
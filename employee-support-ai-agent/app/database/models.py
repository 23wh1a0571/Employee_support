import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "./data/enterprise.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT,
            department TEXT,
            leave_balance INTEGER
        );
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            emp_id TEXT,
            issue TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS leave_requests (
            request_id TEXT PRIMARY KEY,
            emp_id TEXT,
            days INTEGER,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS software_requests (
            request_id TEXT PRIMARY KEY,
            emp_id TEXT,
            software_name TEXT,
            status TEXT
        );
    """)
    conn.commit()
    conn.close()
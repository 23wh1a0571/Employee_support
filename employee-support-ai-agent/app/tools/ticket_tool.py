import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "./data/enterprise.db")

def check_ticket_status(ticket_id: str) -> str:
    """Queries support ticket status from database."""
    if not os.path.exists(DB_PATH):
        return f"Database file not found at {DB_PATH}."
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT issue, status FROM tickets WHERE UPPER(ticket_id) = ?", (ticket_id.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return f"Ticket {ticket_id.upper()} ({row['issue']}) status: {row['status']}."
    return f"Ticket {ticket_id} not found."
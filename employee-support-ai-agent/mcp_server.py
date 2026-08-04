import sqlite3
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Enterprise HR & IT MCP Server")

# Resolve absolute path to enterprise.db in the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "enterprise.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def get_payslip_details(emp_id: str) -> str:
    """Fetch salary and payslip details for an employee from employees dataset."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, last_name, salary_usd, department, job_title
            FROM employees
            WHERE UPPER(employee_id) = UPPER(?)
        """, (emp_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"No payslip details found for Employee ID: {emp_id}"

        annual_salary = float(row['salary_usd'])
        monthly_gross = annual_salary / 12.0
        deductions = monthly_gross * 0.20
        net_take_home = monthly_gross - deductions

        return (
            f"### 💳 PAYSLIP DETAILS\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Department:** {row['department']} ({row['job_title']})\n"
            f"* **Annual Base Salary:** ${annual_salary:,.2f}\n"
            f"* **Estimated Monthly Gross:** ${monthly_gross:,.2f}\n"
            f"* **Estimated Deductions:** ${deductions:,.2f}\n"
            f"* **Estimated Net Take-Home:** **${net_take_home:,.2f}**\n\n"
            f"🔗 [Download Monthly Payslip Statement PDF](https://sso.enterprise.com/payslips/{emp_id.upper()}_Statement.pdf)"
        )
    except Exception as e:
        return f"Error querying payslip for {emp_id}: {str(e)}"

@mcp.tool()
def check_leave_balance(emp_id: str) -> str:
    """Check remaining annual, sick, and casual leave balances."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.first_name, e.last_name, l.annual_leave_remaining, l.sick_leave_remaining, l.casual_leave_remaining
            FROM employees e
            JOIN leave_balances l ON UPPER(e.employee_id) = UPPER(l.employee_id)
            WHERE UPPER(e.employee_id) = UPPER(?)
        """, (emp_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"No leave record found for Employee ID: {emp_id}"

        annual = int(row['annual_leave_remaining'])
        sick = int(row['sick_leave_remaining'])
        casual = int(row['casual_leave_remaining'])
        total = annual + sick + casual

        return (
            f"### 🏖️ LEAVE BALANCE DETAILS\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Annual Leave Remaining:** {annual} days\n"
            f"* **Sick Leave Remaining:** {sick} days\n"
            f"* **Casual Leave Remaining:** {casual} days\n"
            f"* **Total Available Leave:** **{total} days**"
        )
    except Exception as e:
        return f"Error fetching leave balance for {emp_id}: {str(e)}"

@mcp.tool()
def generate_password_reset_link(emp_id: str) -> str:
    """Generate an official SSO password reset authorization link."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, email FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"Cannot generate password reset link. Employee ID {emp_id} does not exist."

        reset_url = f"https://sso.enterprise.com/reset-password?token=okta_{emp_id.upper()}_temp_reset"
        return (
            f"### 🔐 PASSWORD RESET GENERATED\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Employee Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Work Email:** {row['email']}\n"
            f"* **Reset Link:** [Reset Your SSO Password]({reset_url})\n"
            f"* **Status:** 🟢 Active *(Link expires in 15 minutes)*"
        )
    except Exception as e:
        return f"Error generating password link for {emp_id}: {str(e)}"

@mcp.tool()
def check_ticket_status(ticket_id: str) -> str:
    """Check status of an existing IT support ticket."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticket_id, employee_id, title, category, priority, status, created_date, assigned_to
            FROM tickets
            WHERE UPPER(ticket_id) = UPPER(?)
        """, (ticket_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"No IT support ticket found matching Ticket ID: {ticket_id.upper()}"

        return (
            f"### 🎫 IT SUPPORT TICKET STATUS\n\n"
            f"* **Ticket ID:** `{row['ticket_id']}`\n"
            f"* **Requested By:** `{row['employee_id']}`\n"
            f"* **Title / Summary:** {row['title']}\n"
            f"* **Category:** {row['category']} | **Priority:** `{row['priority']}`\n"
            f"* **Status:** **{row['status']}**\n"
            f"* **Assigned Tech ID:** `{row['assigned_to']}`\n"
            f"* **Created Date:** {row['created_date']}"
        )
    except Exception as e:
        return f"Error fetching ticket {ticket_id}: {str(e)}"

@mcp.tool()
def check_software_request(emp_id: str) -> str:
    """Check software details and license info."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT software_id, name, category, license_type, requires_manager_approval, description
            FROM software_requests
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"No software items found in catalog."

        res = [f"### 💻 SOFTWARE CATALOG INFO\n"]
        for r in rows[:5]:
            res.append(f"* **{r['name']}** (`{r['software_id']}`) | **Category:** {r['category']} | **Approval Required:** `{r['requires_manager_approval']}`")
        return "\n".join(res)
    except Exception as e:
        return f"Error checking software catalog: {str(e)}"

if __name__ == "__main__":
    mcp.run()
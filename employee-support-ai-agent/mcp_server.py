import sqlite3
import os
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Enterprise HR, IT & Support MCP Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "enterprise.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(conn, emp_id: str, action_type: str, details: str):
    try:
        timestamp = datetime.datetime.now().isoformat()
        conn.execute(
            "INSERT INTO audit_logs (employee_id, action_type, details, timestamp) VALUES (?, ?, ?, ?)",
            (emp_id, action_type, details, timestamp)
        )
    except Exception as e:
        print(f"Audit log error: {str(e)}")

# ==========================================
# 1. RAG & POLICY SEARCH
# ==========================================

@mcp.tool()
def query_company_policy(query: str) -> str:
    """Perform search over company policy documents in SQLite/ChromaDB."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        param = f"%{query}%"
        cursor.execute("""
            SELECT policy_id, policy_name, category, content
            FROM policies
            WHERE policy_name LIKE ? OR category LIKE ? OR content LIKE ?
            LIMIT 3
        """, (param, param, param))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"No specific policy documentation found matching: '{query}'. Please consult HR directly."

        res = [f"### 📄 COMPANY POLICY SEARCH RESULTS FOR '{query}'\n"]
        for r in rows:
            res.append(f"#### {r['policy_name']} (`{r['policy_id']}`)\n* **Category:** {r['category']}\n* **Details:** {r['content']}\n")
        return "\n".join(res)
    except Exception as e:
        return f"Error querying policy documents: {str(e)}"

# ==========================================
# 2. HR TOOLS
# ==========================================

@mcp.tool()
def check_leave_balance(emp_id: str) -> str:
    """Check remaining leave balances for a specific employee."""
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

        if not row:
            conn.close()
            return f"Employee ID `{emp_id}` was not found in the records."

        annual = int(row['annual_leave_remaining'])
        sick = int(row['sick_leave_remaining'])
        casual = int(row['casual_leave_remaining'])
        
        log_audit(conn, emp_id, "HR_LEAVE_CHECK", "Checked leave balances")
        conn.commit()
        conn.close()

        return (
            f"### 🏖️ LEAVE BALANCE DETAILS\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Annual Leave Remaining:** {annual} days\n"
            f"* **Sick Leave Remaining:** {sick} days\n"
            f"* **Casual Leave Remaining:** {casual} days\n"
            f"* **Total Available Leave:** **{annual + sick + casual} days**"
        )
    except Exception as e:
        return f"Error fetching leave balance: {str(e)}"

@mcp.tool()
def apply_leave(emp_id: str, days: int, leave_type: str = "Annual") -> str:
    """Submit a leave application for Manager/HR review. Does NOT auto-approve."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        col_map = {"annual": "annual_leave_remaining", "sick": "sick_leave_remaining", "casual": "casual_leave_remaining"}
        col = col_map.get(leave_type.lower(), "annual_leave_remaining")

        cursor.execute(f"SELECT {col} FROM leave_balances WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return f"Employee ID `{emp_id}` was not found in the employee database."

        current_bal = int(row[0])
        if current_bal < days:
            conn.close()
            return f"Cannot submit request. Available {leave_type} balance is {current_bal} days, but {days} days were requested."

        req_id = f"LR-{datetime.datetime.now().strftime('%M%S')}"
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        status = "Pending Manager & HR Review"

        cursor.execute("""
            INSERT INTO leave_requests (request_id, employee_id, leave_type, start_date, end_date, days_requested, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (req_id, emp_id.upper(), leave_type.capitalize(), today_str, today_str, days, status, today_str))

        log_audit(conn, emp_id, "HR_LEAVE_SUBMITTED", f"Submitted {days} day(s) {leave_type} leave request for manager review")
        conn.commit()
        conn.close()

        return (
            f"### 📑 LEAVE REQUEST SUBMITTED FOR MANAGER REVIEW\n\n"
            f"* **Request ID:** `{req_id}`\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Leave Type:** {leave_type.capitalize()}\n"
            f"* **Days Requested:** {days}\n"
            f"* **Current Status:** 🟡 **{status}**\n\n"
            f"ℹ️ *Your request has been routed to your manager's approval portal. Your leave balance will remain unchanged ({current_bal} days) until your manager reviews and approves this request.*"
        )
    except Exception as e:
        return f"Error submitting leave request: {str(e)}"

@mcp.tool()
def get_payslip_details(emp_id: str) -> str:
    """Fetch monthly payslip details and generate a downloadable payslip statement."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, salary_usd, department, job_title FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"No payslip details found for Employee ID: {emp_id}"

        annual_salary = float(row['salary_usd'])
        monthly_gross = annual_salary / 12.0
        tax_deduction = monthly_gross * 0.15
        pf_deduction = monthly_gross * 0.05
        net_take_home = monthly_gross - tax_deduction - pf_deduction
        current_month = datetime.date.today().strftime("%B %Y")

        log_audit(conn, emp_id, "HR_PAYSLIP_DOWNLOAD", f"Generated downloadable payslip for {current_month}")
        conn.commit()
        conn.close()

        return (
            f"### 💳 OFFICIAL PAYSLIP STATEMENT ({current_month.upper()})\n\n"
            f"**EMPLOYEE INFORMATION**\n"
            f"* **Employee Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Department:** {row['department']}\n"
            f"* **Designation:** {row['job_title']}\n\n"
            f"**EARNINGS & DEDUCTIONS BREAKDOWN**\n"
            f"| Item | Amount (USD) |\n"
            f"| :--- | :--- |\n"
            f"| Basic Monthly Gross | ${monthly_gross:,.2f} |\n"
            f"| Income Tax (15%) | -${tax_deduction:,.2f} |\n"
            f"| Provident Fund (5%) | -${pf_deduction:,.2f} |\n"
            f"| **NET PAYABLE** | **${net_take_home:,.2f}** |\n\n"
            f"📥 **Download Status:** *Statement generated successfully. Use the Export button below to download text/PDF statement.*"
        )
    except Exception as e:
        return f"Error fetching payslip: {str(e)}"

# ==========================================
# 3. IT TOOLS
# ==========================================

@mcp.tool()
def request_software_access(emp_id: str, software_name: str = "") -> str:
    """Provision software license access after validating the software name."""
    try:
        if not software_name or len(software_name.strip()) < 2 or software_name.lower() in ["general access", "unspecified", "software"]:
            return (
                f"⚠️ **SPECIFIC SOFTWARE REQUIRED**\n\n"
                f"Please specify the **exact software tool** you require (e.g., *'Request Figma access for {emp_id}'*, *'Request Slack license for {emp_id}'*, or *'Request Salesforce for {emp_id}'*)."
            )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        emp_row = cursor.fetchone()

        if not emp_row:
            conn.close()
            return f"Employee ID `{emp_id}` does not exist."

        assign_id = f"SWA-{datetime.datetime.now().strftime('%M%S')}"
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        high_cost_sw = ["salesforce", "aws", "figma", "tableau", "jira enterprise"]
        requires_approval = any(sw in software_name.lower() for sw in high_cost_sw)
        status = "Pending IT Sign-off" if requires_approval else "Active"

        cursor.execute("""
            INSERT INTO software_assignments (assignment_id, employee_id, software_name, status, assigned_date)
            VALUES (?, ?, ?, ?, ?)
        """, (assign_id, emp_id.upper(), software_name, status, today_str))

        log_audit(conn, emp_id, "IT_SOFTWARE_REQUEST", f"Requested software '{software_name}' (Status: {status})")
        conn.commit()
        conn.close()

        if requires_approval:
            return (
                f"### ⏳ SOFTWARE REQUEST SUBMITTED (APPROVAL REQUIRED)\n\n"
                f"* **Assignment ID:** `{assign_id}`\n"
                f"* **Employee ID:** `{emp_id.upper()}` ({emp_row['first_name']} {emp_row['last_name']})\n"
                f"* **Software Requested:** {software_name}\n"
                f"* **Status:** 🟡 **{status}**\n\n"
                f"⚠️ *`{software_name}` is classified as a paid enterprise tool. A license request has been routed to the IT Support Workspace for approval.*"
            )

        return (
            f"### 💻 SOFTWARE PROVISIONED SUCCESSFULLY\n\n"
            f"* **Assignment ID:** `{assign_id}`\n"
            f"* **Employee ID:** `{emp_id.upper()}` ({emp_row['first_name']} {emp_row['last_name']})\n"
            f"* **Software Requested:** {software_name}\n"
            f"* **Status:** 🟢 **Active / Access Granted**"
        )
    except Exception as e:
        return f"Error requesting software access: {str(e)}"

@mcp.tool()
def generate_password_reset_link(emp_id: str) -> str:
    """Generate SSO password reset authorization link."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, email FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"Employee ID {emp_id} does not exist."

        log_audit(conn, emp_id, "IT_PWD_RESET", "Generated password reset link")
        conn.commit()
        conn.close()

        return (
            f"### 🔐 PASSWORD RESET GENERATED\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Work Email:** {row['email']}\n"
            f"* **Reset Link:** [Reset Password](https://sso.enterprise.com/reset-password?token=okta_{emp_id.upper()}_temp)"
        )
    except Exception as e:
        return f"Error resetting password: {str(e)}"

@mcp.tool()
def unlock_user_account(emp_id: str) -> str:
    """Unlock locked enterprise user account."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, email FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"Employee ID {emp_id} does not exist."

        log_audit(conn, emp_id, "IT_ACCOUNT_UNLOCK", "Unlocked user SSO account")
        conn.commit()
        conn.close()

        return (
            f"### 🔓 ACCOUNT UNLOCKED SUCCESSFULY\n\n"
            f"* **Employee ID:** `{emp_id.upper()}`\n"
            f"* **Account Name:** {row['first_name']} {row['last_name']}\n"
            f"* **Work Email:** {row['email']}\n"
            f"* **Status:** 🟢 **Active / Unlocked**"
        )
    except Exception as e:
        return f"Error unlocking account: {str(e)}"

# ==========================================
# 4. SUPPORT TOOLS
# ==========================================

@mcp.tool()
def create_support_ticket(emp_id: str, title: str, category: str = "Hardware") -> str:
    """Create a new IT/Support ticket."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM employees WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
        emp_row = cursor.fetchone()

        if not emp_row:
            conn.close()
            return f"Employee ID `{emp_id}` does not exist."

        cursor.execute("SELECT ticket_id FROM tickets ORDER BY ROWID DESC LIMIT 1")
        last_ticket = cursor.fetchone()
        next_num = 1001
        if last_ticket and last_ticket['ticket_id']:
            parts = last_ticket['ticket_id'].split('-')
            if len(parts) == 2 and parts[1].isdigit():
                next_num = int(parts[1]) + 1

        new_ticket_id = f"TCK-{next_num}"
        created_date = datetime.date.today().strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO tickets (ticket_id, employee_id, title, category, priority, status, created_date, assigned_to)
            VALUES (?, ?, ?, ?, 'Medium', 'Open', ?, 'EMP-018')
        """, (new_ticket_id, emp_id.upper(), title, category, created_date))

        log_audit(conn, emp_id, "SUPPORT_CREATE_TICKET", f"Created ticket {new_ticket_id}")
        conn.commit()
        conn.close()

        return (
            f"### 🎫 IT SUPPORT TICKET CREATED\n\n"
            f"* **Ticket ID:** `{new_ticket_id}`\n"
            f"* **Requested By:** {emp_row['first_name']} {emp_row['last_name']} (`{emp_id.upper()}`)\n"
            f"* **Title:** {title}\n"
            f"* **Category:** {category}\n"
            f"* **Assigned Desk:** IT Support Specialist (`EMP-018`)\n"
            f"* **Status:** 🟢 **Open**"
        )
    except Exception as e:
        return f"Error creating ticket: {str(e)}"

@mcp.tool()
def check_ticket_status(ticket_id: str) -> str:
    """View details and status of an existing ticket."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE UPPER(ticket_id) = UPPER(?)", (ticket_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"No ticket found matching ID: `{ticket_id.upper()}`"

        return (
            f"### 🎫 SUPPORT TICKET STATUS\n\n"
            f"* **Ticket ID:** `{row['ticket_id']}`\n"
            f"* **Employee ID:** `{row['employee_id']}`\n"
            f"* **Title:** {row['title']}\n"
            f"* **Category:** {row['category']} | **Priority:** `{row['priority']}`\n"
            f"* **Assigned To:** `{row['assigned_to']}`\n"
            f"* **Status:** **{row['status']}**"
        )
    except Exception as e:
        return f"Error checking ticket: {str(e)}"

@mcp.tool()
def close_support_ticket(ticket_id: str) -> str:
    """Close an active support ticket."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_id, employee_id FROM tickets WHERE UPPER(ticket_id) = UPPER(?)", (ticket_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"Cannot close. No ticket found matching ID: `{ticket_id.upper()}`"

        cursor.execute("UPDATE tickets SET status = 'Closed' WHERE UPPER(ticket_id) = UPPER(?)", (ticket_id,))
        log_audit(conn, row['employee_id'], "SUPPORT_CLOSE_TICKET", f"Closed ticket {ticket_id}")
        conn.commit()
        conn.close()

        return (
            f"### 🔴 SUPPORT TICKET CLOSED\n\n"
            f"* **Ticket ID:** `{ticket_id.upper()}`\n"
            f"* **Status:** 🔴 **Closed / Resolved**"
        )
    except Exception as e:
        return f"Error closing ticket: {str(e)}"

if __name__ == "__main__":
    mcp.run()
import streamlit as st
import requests
import sqlite3

st.set_page_config(page_title="Enterprise Portal & Workflows", layout="wide")

API_URL = "http://localhost:8000/api/chat"
DB_PATH = "enterprise.db"

def render_chat_assistant(key_prefix="default"):
    st.markdown("### 💬 Enterprise AI Chat Assistant")
    st.caption("Ask policy questions, check balances, submit leave requests, download payslips, or raise support tickets.")

    session_key = f"messages_{key_prefix}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    for msg in st.session_state[session_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "PAYSLIP STATEMENT" in msg["content"]:
                st.download_button(
                    label="📥 Download Payslip (.txt)",
                    data=msg["content"],
                    file_name="Payslip_Statement.txt",
                    mime="text/plain",
                    key=f"dl_{key_prefix}_{hash(msg['content'])}"
                )

    if user_input := st.chat_input("Ask a question or issue a command...", key=f"input_{key_prefix}"):
        st.session_state[session_key].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                res = requests.post(API_URL, json={"message": user_input})
                if res.status_code == 200:
                    reply = res.json()["response"]
                    st.markdown(reply)
                    if "PAYSLIP STATEMENT" in reply:
                        st.download_button(
                            label="📥 Download Payslip (.txt)",
                            data=reply,
                            file_name="Payslip_Statement.txt",
                            mime="text/plain",
                            key=f"dl_new_{key_prefix}_{hash(reply)}"
                        )
                    st.session_state[session_key].append({"role": "assistant", "content": reply})
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Failed to connect to API server at {API_URL}. Is main.py running?")

# ==========================================
# SIDEBAR: ROLE-BASED ACCESS CONTROL (RBAC)
# ==========================================
st.sidebar.title("🔒 Enterprise SSO Login")

if "user_role" not in st.session_state:
    st.session_state.user_role = "Employee"

role_choice = st.sidebar.radio(
    "Select Portal View:",
    ["Employee Assistant", "HR Manager Portal", "IT Support Workspace"]
)

if role_choice == "HR Manager Portal":
    manager_pass = st.sidebar.text_input("Enter Manager Password:", type="password")
    if manager_pass == "admin123":
        st.session_state.user_role = "HR_Manager"
        st.sidebar.success("🟢 Authenticated as HR Manager")
    else:
        st.session_state.user_role = "Employee"
        if manager_pass:
            st.sidebar.error("🔴 Invalid Password. Restricted to Employee Mode.")

elif role_choice == "IT Support Workspace":
    it_pass = st.sidebar.text_input("Enter IT Support Password (it123):", type="password")
    if it_pass == "it123":
        st.session_state.user_role = "IT_Support"
        st.sidebar.success("🟢 Authenticated as IT Support Specialist")
    else:
        st.session_state.user_role = "Employee"
        if it_pass:
            st.sidebar.error("🔴 Invalid Password. Restricted to Employee Mode.")
else:
    st.session_state.user_role = "Employee"
    st.sidebar.info("👤 Logged in as Regular Employee")

# ==========================================
# DYNAMIC NAVIGATION BASED ON ROLE
# ==========================================

if st.session_state.user_role == "HR_Manager":
    st.title("📊 HR & Manager Approval Portal")
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("⏳ Pending Employee Leave Requests (Requires Verification)")
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM leave_requests WHERE status LIKE '%Pending%' ORDER BY ROWID DESC")
            pending_leaves = cursor.fetchall()

            if pending_leaves:
                for req in pending_leaves:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1:
                            st.markdown(f"**Request ID:** `{req['request_id']}`")
                            st.write(f"**Employee:** `{req['employee_id']}`")
                            st.write(f"**Leave Type:** {req['leave_type']} ({req['days_requested']} days)")
                        with c2:
                            if st.button("🟢 Approve", key=f"app_{req['request_id']}"):
                                days = int(req['days_requested'])
                                emp_id = req['employee_id']
                                leave_type = req['leave_type'].lower()
                                col = "annual_leave_remaining" if "annual" in leave_type else ("sick_leave_remaining" if "sick" in leave_type else "casual_leave_remaining")
                                
                                cursor.execute(f"SELECT {col} FROM leave_balances WHERE UPPER(employee_id) = UPPER(?)", (emp_id,))
                                bal_row = cursor.fetchone()
                                if bal_row:
                                    new_bal = max(0, int(bal_row[0]) - days)
                                    cursor.execute(f"UPDATE leave_balances SET {col} = ? WHERE UPPER(employee_id) = UPPER(?)", (new_bal, emp_id))
                                
                                cursor.execute("UPDATE leave_requests SET status = 'Approved' WHERE request_id = ?", (req['request_id'],))
                                conn.commit()
                                st.success(f"Approved {req['request_id']}! Balance updated.")
                                st.rerun()
                        with c3:
                            if st.button("🔴 Reject", key=f"rej_{req['request_id']}"):
                                cursor.execute("UPDATE leave_requests SET status = 'Rejected' WHERE request_id = ?", (req['request_id'],))
                                conn.commit()
                                st.warning(f"Rejected {req['request_id']}!")
                                st.rerun()
            else:
                st.info("No pending leave requests requiring manager verification.")

            st.divider()

            st.subheader("📋 Recent Employee HR Queries & Audit Trail")
            cursor.execute("SELECT * FROM audit_logs WHERE action_type LIKE 'HR%' ORDER BY log_id DESC LIMIT 10")
            logs = cursor.fetchall()
            if logs:
                for log in logs:
                    st.caption(f"[{log['timestamp']}] Employee `{log['employee_id']}` (`{log['action_type']}`): {log['details']}")
            else:
                st.caption("No recent HR audit records.")

            conn.close()
        except Exception as e:
            st.warning(f"Database connection offline or uninitialized: {str(e)}")

    with col_right:
        render_chat_assistant(key_prefix="manager")

elif st.session_state.user_role == "IT_Support":
    st.title("🛠️ IT Support Service Desk Portal")
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("🎫 Active IT Support Tickets")
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM tickets WHERE status != 'Closed' ORDER BY ROWID DESC")
            open_tickets = cursor.fetchall()

            if open_tickets:
                for tck in open_tickets:
                    with st.expander(f"📌 {tck['ticket_id']} - {tck['title']} (`{tck['employee_id']}`)"):
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            st.write(f"**Category:** {tck['category']}")
                            st.write(f"**Priority:** {tck['priority']}")
                            st.write(f"**Status:** `{tck['status']}`")
                        with c2:
                            if tck['status'] == "Open":
                                if st.button("🟡 Mark In Progress", key=f"prog_{tck['ticket_id']}"):
                                    cursor.execute("UPDATE tickets SET status = 'In Progress' WHERE ticket_id = ?", (tck['ticket_id'],))
                                    conn.commit()
                                    st.success(f"{tck['ticket_id']} set to In Progress!")
                                    st.rerun()
                            
                            if st.button("🔴 Resolve & Close", key=f"cls_{tck['ticket_id']}"):
                                cursor.execute("UPDATE tickets SET status = 'Closed' WHERE ticket_id = ?", (tck['ticket_id'],))
                                conn.commit()
                                st.warning(f"{tck['ticket_id']} closed!")
                                st.rerun()
            else:
                st.info("No active tickets requiring IT intervention.")

            st.divider()

            st.subheader("💻 Software Access Requests")
            cursor.execute("SELECT * FROM software_assignments WHERE status LIKE '%Pending%' ORDER BY ROWID DESC")
            pending_sw = cursor.fetchall()

            if pending_sw:
                for sw in pending_sw:
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**{sw['software_name']}** for `{sw['employee_id']}`")
                    with c2:
                        if st.button("🟢 Grant License", key=f"sw_{sw['assignment_id']}"):
                            cursor.execute("UPDATE software_assignments SET status = 'Active' WHERE assignment_id = ?", (sw['assignment_id'],))
                            conn.commit()
                            st.success(f"License granted for {sw['software_name']}!")
                            st.rerun()
            else:
                st.info("No pending software license requests.")

            st.divider()

            st.subheader("📋 IT Operational Logs")
            cursor.execute("SELECT * FROM audit_logs WHERE action_type LIKE 'IT%' OR action_type LIKE 'SUPPORT%' ORDER BY log_id DESC LIMIT 10")
            it_logs = cursor.fetchall()
            if it_logs:
                for log in it_logs:
                    st.caption(f"[{log['timestamp']}] Employee `{log['employee_id']}` (`{log['action_type']}`): {log['details']}")

            conn.close()
        except Exception as e:
            st.warning(f"Database connection offline or uninitialized: {str(e)}")

    with col_right:
        render_chat_assistant(key_prefix="it_support")

else:
    st.title("🤖 Enterprise HR & IT AI Assistant")
    render_chat_assistant(key_prefix="employee")
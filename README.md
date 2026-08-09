# Enterprise HR, IT & Support AI Assistant

An intelligent multi-role enterprise assistant capable of intent classification, tool invocation via Model Context Protocol (MCP), and role-based action management (Employee, HR Manager, IT Support Desk).

## 🚀 Key Features

* **Multi-Domain Tool Execution:**
  * **HR:** Leave balance lookup, leave application routing, monthly payslip statement generation.
  * **IT Support:** Password reset link generation, account unlocking, software provisioning (with cost-threshold approval routing), and hardware ticket logging.
  * **Finance:** Expense reimbursement claim submission and status tracking.
* **Role-Based Access Control (RBAC):**
  * **Employee Mode:** Self-service chat assistant.
  * **HR Manager Portal:** Pending leave/expense approval queue & audit trail.
  * **IT Support Workspace:** Active hardware ticket management & software license allocation.
* **Architecture:** FastMCP Tool Server + FastAPI REST API + Streamlit Multi-Portal UI.

---

## 🛠️ Project Structure

```text
├── app/
│   ├── agent/
│   │   └── graph.py          # Agent graph integration
│   └── api/
│       └── routes.py         # Intent classification & tool routing API
├── frontend/
│   └── streamlit_app.py      # Streamlit multi-portal UI (Employee, HR, IT)
├── database_setup.py          # SQLite database schema initializer
├── mcp_server.py              # FastMCP tool definitions & audit logging
├── main.py                    # FastAPI entry point
├── test_cases.json            # Benchmark evaluation dataset
├── REPORT.md                  # Technical architecture report
└── requirements.txt           # Python dependencies

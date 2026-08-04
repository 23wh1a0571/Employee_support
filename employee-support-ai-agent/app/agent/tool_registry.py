from langchain_core.tools import tool
from app.tools.leave_tool import check_leave_balance
from app.tools.ticket_tool import check_ticket_status
from app.tools.password_tool import reset_password_guidelines
from app.tools.software_tool import check_software_request
from app.tools.greeting_tool import handle_greeting

@tool
def check_leave_balance_tool(emp_id: str) -> str:
    """Check remaining leave balance for an employee. Pass the employee ID string like EMP101."""
    return check_leave_balance(emp_id)

@tool
def check_ticket_status_tool(ticket_id: str) -> str:
    """Check IT support ticket status. Pass the ticket ID string like TCK-501."""
    return check_ticket_status(ticket_id)

@tool
def reset_password_tool() -> str:
    """Provides instructions and guidelines for corporate password resets."""
    return reset_password_guidelines()

@tool
def check_software_request_tool(emp_id: str) -> str:
    """Check status of software access requests. Pass the employee ID string like EMP101."""
    return check_software_request(emp_id)

@tool
def handle_greeting_tool() -> str:
    """Respond to general greetings like hi, hello, hey."""
    return handle_greeting()

all_tools = [
    check_leave_balance_tool,
    check_ticket_status_tool,
    reset_password_tool,
    check_software_request_tool,
    handle_greeting_tool
]
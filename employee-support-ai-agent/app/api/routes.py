import re
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agent.graph import build_agent

router = APIRouter()

_mcp_tools = None

async def get_tools():
    global _mcp_tools
    if _mcp_tools is None:
        _, _mcp_tools = await build_agent()
        print("\n==================================================")
        print("🔧 REGISTERED MCP TOOLS:")
        for t in _mcp_tools:
            print(f"  • {t.name}")
        print("==================================================\n")
    return _mcp_tools

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def extract_emp_id(text: str) -> Optional[str]:
    """Extracts employee IDs and preserves hyphen formatting like EMP-001 or EMP-023."""
    match = re.search(r'EMP[-_\s]?(\d+)', text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        return f"EMP-{num:03d}"
    return None

def extract_ticket_id(text: str) -> Optional[str]:
    """Extracts ticket IDs like TCK-1001 or TCK-1002."""
    match = re.search(r'TCK[-_\s]?(\d+)', text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        return f"TCK-{num}"
    return None

async def direct_mcp_executor(user_msg: str, tools) -> str:
    msg = user_msg.lower().strip()
    
    # 1. Greetings
    if msg in ["hi", "hii", "hello", "hey", "how are you", "how are you?"]:
        return "Hello! I am your Enterprise HR & IT Assistant running on pure MCP. How can I help you today?"

    tool_dict = {t.name.lower(): t for t in tools} if tools else {}
    
    emp_id = extract_emp_id(user_msg)
    ticket_id = extract_ticket_id(user_msg)

    # 2. Payslips / Payroll / Salary
    if any(w in msg for w in ["payslip", "salary", "take-home", "take home", "pay", "deduction", "allowance"]):
        target_id = emp_id or "EMP-001"
        for name, tool in tool_dict.items():
            if "payslip" in name or "salary" in name or "pay" in name:
                return await tool.ainvoke({"emp_id": target_id})

    # 3. Password Reset / Login Issues
    if any(w in msg for w in ["password", "reset", "logout", "logged out", "sso", "login", "log in", "sign in", "cant log", "cannot log", "locked", "account"]):
        if not emp_id:
            return "Please provide your Employee ID (e.g., EMP-001) so I can generate a password reset link for your account."
        for name, tool in tool_dict.items():
            if "password" in name or "reset" in name or "sso" in name:
                return await tool.ainvoke({"emp_id": emp_id})

    # 4. Leave Balance / PTO / Vacation / Holidays / Days Off
    if any(w in msg for w in ["leave", "pto", "balance", "vacation", "annual", "sick", "holiday", "holidays", "off", "day off"]):
        target_id = emp_id or "EMP-001"
        for name, tool in tool_dict.items():
            if "leave" in name or "pto" in name or "balance" in name:
                return await tool.ainvoke({"emp_id": target_id})

    # 5. IT Support Tickets
    if any(w in msg for w in ["ticket", "tck", "issue", "status", "support"]):
        target_ticket = ticket_id or "TCK-1001"
        for name, tool in tool_dict.items():
            if "ticket" in name or "tck" in name:
                return await tool.ainvoke({"ticket_id": target_ticket})

    # 6. Software Access Requests
    if any(w in msg for w in ["software", "request", "figma", "jira", "access"]):
        target_id = emp_id or "EMP-001"
        for name, tool in tool_dict.items():
            if "software" in name or "access" in name or "request" in name:
                return await tool.ainvoke({"emp_id": target_id})

    # Default fallback help menu
    return (
        "I can help you with HR and IT tasks using direct MCP tools:\n"
        "• Check Payslips: 'Give me payslip for EMP-006'\n"
        "• Password Reset: 'Reset password for EMP-001'\n"
        "• Leave Balance: 'Check leave balance for EMP-001'\n"
        "• IT Support Tickets: 'Check status of ticket TCK-1001'"
    )

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message string cannot be empty.")

    tools = await get_tools()

    try:
        output_message = await direct_mcp_executor(request.message, tools)
        return ChatResponse(response=str(output_message))
    except Exception as e:
        print("\n--- MCP EXECUTION ERROR TRACEBACK ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"MCP Execution Error: {str(e)}")
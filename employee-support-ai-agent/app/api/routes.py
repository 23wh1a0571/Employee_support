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
    return _mcp_tools

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def extract_emp_id(text: str) -> Optional[str]:
    match = re.search(r'EMP[-_\s]?(\d+)', text, re.IGNORECASE)
    if match:
        return f"EMP-{int(match.group(1)):03d}"
    return None

def extract_ticket_id(text: str) -> Optional[str]:
    match = re.search(r'TCK[-_\s]?(\d+)', text, re.IGNORECASE)
    if match:
        return f"TCK-{int(match.group(1))}"
    return None

def extract_days(text: str) -> int:
    match = re.search(r'(\d+)\s*days?', text, re.IGNORECASE)
    return int(match.group(1)) if match else 1

def extract_software_name(text: str) -> str:
    cleaned = re.sub(r'EMP[-_\s]?\d+', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(need|access|to|software|for|request|provision|grant|license|app|i)\b', '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned

async def direct_mcp_executor(user_msg: str, tools) -> str:
    msg = user_msg.lower().strip()
    tool_dict = {t.name.lower(): t for t in tools} if tools else {}
    emp_id = extract_emp_id(user_msg)
    ticket_id = extract_ticket_id(user_msg)

    # 1. SUPPORT DOMAIN
    if "close" in msg and "ticket" in msg:
        if not ticket_id:
            return "Please specify the **Ticket ID** you want to close (e.g., `TCK-1001`)."
        return await tool_dict["close_support_ticket"].ainvoke({"ticket_id": ticket_id})

    if ("check" in msg or "view" in msg or "status" in msg) and ("ticket" in msg or ticket_id):
        if not ticket_id:
            return "Please specify the **Ticket ID** you would like to check (e.g., `TCK-1001`)."
        return await tool_dict["check_ticket_status"].ainvoke({"ticket_id": ticket_id})

    if any(w in msg for w in ["ticket", "charger", "broken", "laptop", "mouse", "keyboard", "screen", "issue", "raise"]):
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) so I can log this support ticket for you."
        title = re.sub(r'EMP[-_\s]?\d+', '', user_msg, flags=re.IGNORECASE).strip()
        title = re.sub(r'\b(can|you|add|create|raise|ticket|for|i|have|my)\b', '', title, flags=re.IGNORECASE).strip()
        title = title.capitalize() if title else "Hardware Issue"
        return await tool_dict["create_support_ticket"].ainvoke({"emp_id": emp_id, "title": title, "category": "Hardware"})

    # 2. POLICY & DOCUMENT SEARCH (RAG)
    if any(w in msg for w in ["policy", "reimbursement", "parental", "byod", "allowance", "handbook", "rule"]):
        return await tool_dict["query_company_policy"].ainvoke({"query": user_msg})

    # 3. HR DOMAIN - LEAVE APPLICATION (Priority)
    if any(w in msg for w in ["apply", "take", "need", "request", "have", "want", "get", "can i"]) and any(w in msg for w in ["leave", "holiday", "pto", "vacation", "time off"]) and extract_days(user_msg) > 0:
        if not emp_id:
            return "To submit a leave request for your manager's review, please specify your **Employee ID** (e.g., `EMP-012`)."
        days = extract_days(user_msg)
        l_type = "Sick" if "sick" in msg else ("Casual" if "casual" in msg else "Annual")
        return await tool_dict["apply_leave"].ainvoke({"emp_id": emp_id, "days": days, "leave_type": l_type})

    # 4. HR DOMAIN - LEAVE BALANCE CHECK (Includes "tell me the leaves", "show leaves", etc.)
    if any(w in msg for w in ["leaves", "leave", "pto", "balance", "how many days", "remaining"]):
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) so I can retrieve your leave balance."
        return await tool_dict["check_leave_balance"].ainvoke({"emp_id": emp_id})

    if "payslip" in msg or "salary" in msg or "download payslip" in msg:
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) to view or download your payslip."
        return await tool_dict["get_payslip_details"].ainvoke({"emp_id": emp_id})

    # 5. IT DOMAIN - SOFTWARE ACCESS REQUEST
    if any(w in msg for w in ["software", "application", "tool", "license", "access to"]):
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) to request software access."
        sw_name = extract_software_name(user_msg)
        return await tool_dict["request_software_access"].ainvoke({"emp_id": emp_id, "software_name": sw_name})

    # 6. IT DOMAIN - UNLOCK & PASSWORD RESET
    if "unlock" in msg and "account" in msg:
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) to request an account unlock."
        return await tool_dict["unlock_user_account"].ainvoke({"emp_id": emp_id})

    if "password" in msg or "reset" in msg:
        if not emp_id:
            return "Please provide your **Employee ID** (e.g., `EMP-012`) to generate an SSO password reset link."
        return await tool_dict["generate_password_reset_link"].ainvoke({"emp_id": emp_id})

    return (
        "Enterprise Assistant ready:\n\n"
        "• **HR:** 'Check leave balance for EMP-012', 'Download payslip for EMP-012'\n"
        "• **IT:** 'Unlock account for EMP-012', 'Request Figma software access for EMP-012'\n"
        "• **Support:** 'Add a ticket that laptop charger is broken for EMP-015'\n"
        "• **Policy Search:** 'What is our parental leave policy?'"
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
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Execution Error: {str(e)}")
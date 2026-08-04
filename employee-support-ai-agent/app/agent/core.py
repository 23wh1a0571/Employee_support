import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

from app.tools.database_tools import query_employee_db
from app.tools.policy_tools import get_company_policy

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Define Schemas for Groq Compatibility
class DBSchema(BaseModel):
    query: str = Field(description="A valid SQL SELECT query to execute on the employee SQLite database.")

class PolicySchema(BaseModel):
    query: str = Field(description="The natural language policy question to search in the policy vector database.")

# 1. Define tools for the agent
tools = [
    StructuredTool.from_function(
        func=query_employee_db,
        name="query_employee_db",
        description="Executes read-only SQL queries against the employee enterprise SQLite database. Tables: 'employees', 'tickets', 'leave_requests', 'software_requests'.",
        args_schema=DBSchema
    ),
    StructuredTool.from_function(
        func=get_company_policy,
        name="get_company_policy",
        description="Retrieves company policy context via semantic search over policy documents. Input should be a clear policy question.",
        args_schema=PolicySchema
    )
]

# 2. System Prompt
system_prompt = """
You are an intelligent internal HR & IT Support Assistant for enterprise employees.
Your job is to answer user queries accurately by using the available tools:

1. Use `query_employee_db` when asked for specific records like employee info, leave balances, software details, or ticket statuses.
2. Use `get_company_policy` when asked general policy or procedural questions (e.g., PTO rollover, remote work guidelines).

Rules:
- Be clear, direct, and professional.
- Do not fabricate database records or policy rules; rely strictly on retrieved context.
"""

class AgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    def invoke(self, input_data):
        user_input = input_data.get("input", "")
        result = self.agent.invoke({"messages": [("user", user_input)]})
        output = result["messages"][-1].content
        return {"output": output}

def get_agent_executor():
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        temperature=0.2
    )
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    return AgentWrapper(agent)
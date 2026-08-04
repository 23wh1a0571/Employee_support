from app.tools.database_tools import query_employee_db
from app.tools.policy_tools import get_company_policy

print("--- Testing Database Tool ---")
db_result = query_employee_db("SELECT employee_id, first_name, email FROM employees LIMIT 2;")
print(db_result)

print("\n--- Testing Policy RAG Tool ---")
rag_result = get_company_policy("What is our leave carryover policy?")
print(rag_result)

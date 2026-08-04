import time
from app.agent.graph import build_agent

test_queries = [
    {"query": "Check leave balance for EMP101", "expected_tool": "check_leave_balance"},
    {"query": "What is status of ticket TCK-501?", "expected_tool": "check_ticket_status"}
]

def run_eval():
    agent = build_agent()
    print("--- Starting Evaluation Suite ---")
    for item in test_queries:
        start = time.time()
        res = agent.invoke({"messages": [("user", item["query"])]})
        duration = round(time.time() - start, 2)
        print(f"\nQuery: {item['query']}\nResponse: {res['messages'][-1].content}\nLatency: {duration}s")

if __name__ == "__main__":
    run_eval()
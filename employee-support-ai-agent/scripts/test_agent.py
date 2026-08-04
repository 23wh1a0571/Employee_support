from app.agent.core import get_agent_executor

def run_test():
    executor = get_agent_executor()
    
    print("\n--- Test 1: Policy Retrieval Query ---")
    response1 = executor.invoke({"input": "What is our policy on carryover leave?"})
    print("\nAgent Answer:\n", response1["output"])

    print("\n--- Test 2: Database Query ---")
    response2 = executor.invoke({"input": "How many active employees are in the Executive department?"})
    print("\nAgent Answer:\n", response2["output"])

if __name__ == "__main__":
    run_test()

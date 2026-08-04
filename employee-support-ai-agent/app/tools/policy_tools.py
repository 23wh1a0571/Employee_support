from app.rag.retriever import search_company_policies

def get_company_policy(query: str) -> str:
    """Retrieves relevant company policy documents based on semantic search."""
    return search_company_policies(query=query)

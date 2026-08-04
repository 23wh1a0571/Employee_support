import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "./data/chroma_db")

def search_company_policies(query: str, top_k: int = 2) -> str:
    """Performs semantic similarity search over company policy documents."""
    if not os.path.exists(VECTOR_DB_DIR):
        return "Policy vector database is not initialized. Please run build_index.py first."

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings
    )

    results = vector_db.similarity_search(query, k=top_k)
    
    if not results:
        return "No relevant policy documents found matching your query."

    formatted_context = []
    for idx, doc in enumerate(results, 1):
        title = doc.metadata.get("title", "Policy Document")
        formatted_context.append(f"--- Document {idx}: {title} ---\n{doc.page_content}")

    return "\n\n".join(formatted_context)
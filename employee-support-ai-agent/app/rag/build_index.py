import os
import io
import shutil
import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "./data/chroma_db")

def load_csv(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # If the whole file or lines are wrapped in outer quotes, strip them cleanly
    cleaned_lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('"') and line.endswith('"') and line.count('"') % 2 != 0:
            line = line[1:-1]
        cleaned_lines.append(line)

    clean_content = "\n".join(cleaned_lines)
    return pd.read_csv(io.StringIO(clean_content))

def build_vector_index():
    print("Building RAG Vector Index with Local Embeddings...")
    
    if os.path.exists(VECTOR_DB_DIR):
        shutil.rmtree(VECTOR_DB_DIR)

    policy_file = "data/policies/company_policy.csv"
    if not os.path.exists(policy_file):
        raise FileNotFoundError(f"Policy CSV file not found at '{policy_file}'.")

    print(f"Loading policies from: {policy_file}")
    df = load_csv(policy_file)
    print(f"Loaded {len(df)} rows from CSV.")

    if df.empty:
        raise ValueError("Policy DataFrame is empty. Please check company_policy.csv.")

    documents = []
    for _, row in df.iterrows():
        content = f"Title: {row.get('title', '')}\nCategory: {row.get('category', '')}\nSummary: {row.get('summary', '')}\nDetails: {row.get('content', '')}"
        metadata = {
            "policy_id": str(row.get('policy_id', '')),
            "title": str(row.get('title', '')),
            "category": str(row.get('category', ''))
        }
        documents.append(Document(page_content=content, metadata=metadata))

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )
    
    print(f"Successfully indexed {len(documents)} policy documents into ChromaDB at '{VECTOR_DB_DIR}'.")

if __name__ == "__main__":
    build_vector_index()
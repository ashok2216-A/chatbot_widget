import sys
import os
import requests

# Navigate up from  subagents/rag/  →  backend/
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

# Expose: backend/rag-service  (Pinecone client + config)
sys.path.insert(0, os.path.join(_BACKEND_DIR, "rag-service"))
# Expose: backend/  (logger)
sys.path.insert(0, _BACKEND_DIR)

from pinecone_client import get_index   # type: ignore
from config import OPENROUTER_API_KEY   # type: ignore
from logger import get_logger           # type: ignore

logger = get_logger("RAG_Tool")


def rag_tool(query: str) -> str:
    """Uses embeddings to retrieve documents from the knowledge base matching the query.

    Args:
        query: The search phrase to look up in the professional database
               (e.g. 'skills', 'projects', 'career history').
    """
    logger.info("rag_tool triggered")
    index = get_index()

    # Fetch embeddings via OpenRouter REST (avoids conflicting SDK imports)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openai/text-embedding-3-small",
        "input": query,
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers=headers,
        json=data,
    )
    response.raise_for_status()
    query_embedding = response.json()["data"][0]["embedding"]

    # Pinecone SDK v3 query
    results = index.query(
        vector=query_embedding,
        top_k=10,
        include_metadata=True,
    )

    docs = [m.metadata["text"] for m in results.matches]
    logger.info(f"Retrieved {len(docs)} document chunks from Pinecone.")
    return "\n".join(docs)

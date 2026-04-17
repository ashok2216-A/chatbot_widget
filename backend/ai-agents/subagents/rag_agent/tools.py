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
    """Uses embeddings to retrieve documents from the knowledge base matching the query."""
    logger.info(f"rag_tool triggered for query: {query}")
    
    try:
        index = get_index()
        
        # 1. Fetch embeddings via OpenRouter
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "openai/text-embedding-3-small",
            "input": query,
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            query_embedding = response.json()["data"][0]["embedding"]
        except requests.exceptions.HTTPError as err:
            logger.error(f"Embedding API HTTP error: {err}")
            return f"[ERROR] The portfolio database search failed (Embedding API). Status: {response.status_code}"
        except Exception as err:
            logger.error(f"Embedding API general error: {err}")
            return f"[ERROR] Failed to process your search query. Please ensure OPENROUTER_API_KEY is valid."

        # 2. Pinecone SDK v3 query
        try:
            results = index.query(
                vector=query_embedding,
                top_k=7,
                include_metadata=True,
            )
            
            docs = [m.metadata["text"] for m in results.matches if "text" in m.metadata]
            if not docs:
                return "I searched the professional database but couldn't find specific details regarding that query."
            
            logger.info(f"Retrieved {len(docs)} document chunks.")
            return "\n\n---\n\n".join(docs)
            
        except Exception as err:
            logger.error(f"Pinecone query error: {err}")
            return "[ERROR] Connection to the knowledge base (Pinecone) failed. Please check your PINECONE_API_KEY."

    except Exception as exc:
        logger.error(f"Critical RAG tool failure: {exc}")
        return f"[ERROR] An unexpected error occurred while searching: {str(exc)}"

import sys
import os
import requests

# Mount the rag-service directory so we can import the Pinecone connection setup
sys.path.append(os.path.join(os.path.dirname(__file__), '../../rag-service'))
from pinecone_client import get_index  # type: ignore
from config import OPENROUTER_API_KEY  # type: ignore

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from logger import get_logger

logger = get_logger("RAG_Tool")

def rag_tool(query: str) -> str:
    """Uses embeddings to retrieve documents from the knowledge base matching the query.
    
    Args:
        query: The search phrase to look up in the professional database (e.g. 'skills', 'projects', 'career history').
    """
    logger.info(f"Tool triggered with query")
    index = get_index()

    # Pure REST API injection to fetch Embeddings without conflicting modules
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/text-embedding-3-small",
        "input": query
    }
    response = requests.post("https://openrouter.ai/api/v1/embeddings", headers=headers, json=data)
    response.raise_for_status()
    query_embedding = response.json()["data"][0]["embedding"]

    # Pinecone SDK v3 query
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )
    
    
    docs = [m.metadata["text"] for m in results.matches]
    logger.info(f"Successfully retrieved {len(docs)} document chunks from Pinecone.")
    return "\n".join(docs)

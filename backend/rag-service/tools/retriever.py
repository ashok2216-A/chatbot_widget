import requests
from pinecone_client import get_index
from config import OPENROUTER_API_KEY

EMBED_MODEL = "openai/text-embedding-3-small"

def retrieve(query, top_k=5):
    index = get_index()

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": EMBED_MODEL,
        "input": query
    }
    response = requests.post("https://openrouter.ai/api/v1/embeddings", headers=headers, json=data)
    response.raise_for_status()
    query_embedding = response.json()["data"][0]["embedding"]

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    docs = [m.metadata["text"] for m in results.matches]
    return "\n".join(docs)

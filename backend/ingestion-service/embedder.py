import requests
import sys
import os
from config import OPENROUTER_API_KEY

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("Embedder")

EMBED_MODEL = "openai/text-embedding-3-small"

def embed_text(text):
    logger.debug(f"Requesting embeddings from OpenRouter via {EMBED_MODEL}...")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": EMBED_MODEL,
        "input": text
    }
    response = requests.post("https://openrouter.ai/api/v1/embeddings", headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

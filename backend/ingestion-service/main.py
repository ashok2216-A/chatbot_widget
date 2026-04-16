import hashlib
import sys
import os
from scraper import scrape
from embedder import embed_text
from pinecone_client import get_index
from db import get_hashes, save_hash

# Mount backend root to grab the logger
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("Ingestion_Pipeline")

URLS = [
    "https://ashok2216-a.github.io/ashok2216_myportfolio.github.io/"
]

def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()

def chunk_text(text, size=800, overlap=100):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i+size])
    return chunks

def ingest():
    logger.info("Starting ingestion pipeline...")
    index = get_index()
    existing_hashes = get_hashes()
    logger.info(f"Loaded {len(existing_hashes)} existing document hashes.")

    for url in URLS:
        logger.info(f"Scraping URL: {url}")
        text = scrape(url)
        chunks = chunk_text(text)

        vectors = []

        for chunk in chunks:
            h = hash_text(chunk)

            if h in existing_hashes:
                logger.debug(f"Skipping identical chunk (Hash: {h[:8]}...)")
                continue

            vectors.append({
                "id": h,  # deterministic ID
                "values": embed_text(chunk),
                "metadata": {
                    "text": chunk,
                    "source": url,
                    "page_type": "general",
                    "category": "unknown",
                    "last_updated": "2026-04-16",
                    "hash": h
                }
            })

            save_hash(h)

        if vectors:
            logger.warning(f"Upserting {len(vectors)} new vectors into Pinecone database...")
            index.upsert(vectors)
            logger.info("Upsert completed successfully.")
        else:
            logger.info("No new vectors to upsert. Database is completely up to date!")

if __name__ == "__main__":
    try:
        ingest()
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}", exc_info=True)

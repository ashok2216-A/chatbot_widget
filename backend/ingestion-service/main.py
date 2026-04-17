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
    "https://myminibuds.in/"
]

def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()

def chunk_text(text, size=1000, overlap=200):
    # Simple recursive-inspired splitter: try to split by paragraph, then sentence
    import re
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) < size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    
    if current_chunk: chunks.append(current_chunk.strip())
    
    # Final check: if any chunk is still too big, force a hard split
    final_chunks = []
    for c in chunks:
        if len(c) > size:
            for i in range(0, len(c), size - overlap):
                final_chunks.append(c[i:i+size])
        else:
            final_chunks.append(c)
    return final_chunks

def infer_category(text):
    t = text.lower()
    if any(k in t for k in ["project", "built with", "github", "developed"]): return "project"
    if any(t.count(k) > 0 for k in ["skill", "expert", "proficient", "technology"]): return "skill"
    if any(k in t for k in ["degree", "university", "college", "education"]): return "education"
    if any(k in t for k in ["work", "experience", "responsibility", "position"]): return "experience"
    return "general"

def ingest():
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info("Starting High-Precision Ingestion Pipeline...")
    index = get_index()
    existing_hashes = get_hashes()

    for url in URLS:
        logger.info(f"Scraping URL: {url}")
        site_data = scrape(url)
        text = site_data["text"]
        title = site_data["title"]
        
        chunks = chunk_text(text)
        vectors = []

        for chunk in chunks:
            h = hash_text(chunk)
            if h in existing_hashes:
                logger.debug(f"Skipping up-to-date chunk (Hash: {h[:8]}...)")
                continue

            category = infer_category(chunk)

            vectors.append({
                "id": h,
                "values": embed_text(chunk),
                "metadata": {
                    "text": chunk,
                    "source": url,
                    "title": title,
                    "category": category,
                    "last_updated": today,
                    "hash": h
                }
            })
            save_hash(h)

        if vectors:
            logger.warning(f"Upserting {len(vectors)} new high-precision vectors into Pinecone...")
            index.upsert(vectors)
            logger.info("Sync completed successfully.")
        else:
            logger.info("All data is currently optimized and up to date.")

if __name__ == "__main__":
    try:
        ingest()
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}", exc_info=True)

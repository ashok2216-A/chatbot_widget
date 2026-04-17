import os
import sys
from pinecone import Pinecone, ServerlessSpec
from config import *

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("PineconeDB")

def get_index():
    logger.debug(f"Connecting to Pinecone Database: '{INDEX_NAME}'...")
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        logger.warning(f"Index '{INDEX_NAME}' not found! Creating new Serverless Index...")
        pc.create_index(
            name=INDEX_NAME, 
            dimension=1536,
            metric="cosine", 
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        logger.info(f"Database '{INDEX_NAME}' successfully created.")

    logger.debug("Successfully connected to Pinecone Index.")
    return pc.Index(INDEX_NAME)

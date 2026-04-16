from pinecone import Pinecone
from config import *

def get_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(INDEX_NAME)

import os
import chromadb
from chromadb.config import Settings

# Store chroma DB locally in backend/chroma_data
CHROMA_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")

class ChromaClient:
    def __init__(self):
        os.makedirs(CHROMA_DATA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=CHROMA_DATA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
    def get_or_create_collection(self, collection_name: str):
        return self.client.get_or_create_collection(name=collection_name)
        
    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass

chroma_client = ChromaClient()

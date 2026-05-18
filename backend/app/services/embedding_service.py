from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self):
        # Load a small, fast local model. 
        # This will download the model the first time it runs.
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of strings.
        """
        if not texts:
            return []
            
        embeddings = self.model.encode(texts)
        # Convert numpy arrays to lists
        return embeddings.tolist()

embedding_service = EmbeddingService()

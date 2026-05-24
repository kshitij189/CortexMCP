import torch
from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self):
        # Restrict PyTorch to a single thread to save CPU/memory on containerized host environments
        torch.set_num_threads(1)
        
        # Load a small, fast local model. 
        # Model is pre-downloaded during Docker build stage.
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

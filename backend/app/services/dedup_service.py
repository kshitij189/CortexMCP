import uuid
from typing import List
from app.vectorstore.chroma_client import chroma_client
from app.services.embedding_service import embedding_service

class DedupService:
    def __init__(self):
        self.chunk_size = 1000 # Characters per chunk
        self.similarity_threshold = 0.85 # Threshold for deduplication

    def chunk_text(self, text: str) -> List[str]:
        """Splits text into smaller chunks."""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    def get_unique_context(self, job_id: str, texts: List[str]) -> str:
        """
        Takes a list of raw texts, chunks them, embeds them, 
        and uses ChromaDB to filter out highly similar chunks.
        Returns a concatenated string of unique chunks.
        """
        if not texts:
            return ""
            
        collection_name = f"job_{job_id.replace('-', '_')}"
        
        # Clean up any previous attempts
        chroma_client.delete_collection(collection_name)
        collection = chroma_client.get_or_create_collection(collection_name)
        
        unique_chunks = []
        
        for text in texts:
            chunks = self.chunk_text(text)
            if not chunks:
                continue
                
            embeddings = embedding_service.generate_embeddings(chunks)
            
            for i, chunk in enumerate(chunks):
                chunk_embedding = embeddings[i]
                
                # Check if collection is empty
                if collection.count() == 0:
                    self._add_to_collection(collection, chunk, chunk_embedding)
                    unique_chunks.append(chunk)
                    continue
                    
                # Query for similar chunks
                results = collection.query(
                    query_embeddings=[chunk_embedding],
                    n_results=1,
                    include=["distances"]
                )
                
                distances = results.get("distances", [[]])[0]
                
                # In ChromaDB (using L2 distance), smaller distance = higher similarity.
                # Distance threshold depends on the embedding model, typically < 0.3 for high similarity with normalized vectors.
                is_duplicate = False
                if distances and distances[0] < 0.5:
                    is_duplicate = True
                    
                if not is_duplicate:
                    self._add_to_collection(collection, chunk, chunk_embedding)
                    unique_chunks.append(chunk)

        # Cleanup collection after job to save disk space
        chroma_client.delete_collection(collection_name)
        
        return "\n...\n".join(unique_chunks)

    def _add_to_collection(self, collection, text: str, embedding: List[float]):
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text]
        )

dedup_service = DedupService()

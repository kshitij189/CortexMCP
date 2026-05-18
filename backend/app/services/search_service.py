import os
from typing import List, Dict, Any
from tavily import TavilyClient

# Fallback API keys should be handled via environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

class SearchService:
    def __init__(self):
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a search using Tavily.
        Returns a list of dictionaries containing 'url', 'title', and 'snippet'.
        """
        if not self.tavily_client:
            print("Warning: TAVILY_API_KEY not set. Returning mock results.")
            return self._mock_search(query)
            
        try:
            response = self.tavily_client.search(
                query=query, 
                search_depth="advanced",
                max_results=num_results
            )
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "snippet": item.get("content", item.get("snippet", ""))
                })
            return results
            
        except Exception as e:
            print(f"Tavily search failed: {e}")
            return []

    def _mock_search(self, query: str) -> List[Dict[str, Any]]:
        """Mock results for testing when no API key is available."""
        return [
            {
                "url": "https://example.com/ai-agents-2026",
                "title": "State of AI Agents in 2026",
                "snippet": "AI agents have evolved significantly, now possessing..."
            },
            {
                "url": "https://example.com/autonomous-research",
                "title": "Autonomous Research Pipelines",
                "snippet": "Building an asynchronous RAG pipeline using FastAPI and Celery..."
            }
        ]

search_service = SearchService()

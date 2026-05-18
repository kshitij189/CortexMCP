import requests
from typing import Optional
from app.utils.text_cleaner import clean_html

class ScraperService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = 10

    def scrape_url(self, url: str) -> Optional[str]:
        """
        Fetches the HTML content of a URL and extracts clean text.
        Returns the cleaned text, or None if the request fails.
        """
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check if successful and content is HTML
            if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
                raw_html = response.text
                return clean_html(raw_html)
            
            print(f"Scraper skipped {url}: Status {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
            return None
            
        except requests.RequestException as e:
            print(f"Scraper failed for {url}: {e}")
            return None

scraper_service = ScraperService()

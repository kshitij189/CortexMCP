import re
from bs4 import BeautifulSoup

def clean_html(raw_html: str) -> str:
    """
    Extract readable text from raw HTML using BeautifulSoup.
    Removes scripts, styles, navigation, headers, and footers.
    """
    if not raw_html:
        return ""
        
    soup = BeautifulSoup(raw_html, "lxml")
    
    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
        tag.decompose()
        
    # Get text
    text = soup.get_text(separator=" ", strip=True)
    
    # Normalize whitespace (replace multiple spaces/newlines with a single space)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def truncate_text(text: str, max_chars: int = 15000) -> str:
    """
    Truncates text to a maximum character limit to avoid blowing up LLM context windows.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [Content Truncated]"

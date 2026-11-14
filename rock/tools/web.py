import httpx
from typing import List, Dict, Any, Optional

class WebTools:
    """
    Search and fetch web content for the Researcher agent.
    """

    @staticmethod
    def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Executes a web search query. Falls back gracefully if duckduckgo_search is unavailable.
        """
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
                for item in raw:
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("href", ""),
                        "body": item.get("body", "")
                    })
            return results
        except Exception as e:
            # Fallback mock/simulated result if no network/package
            return [{"title": "Search Query", "href": "web", "body": f"Results for: {query} (search provider: {str(e)})"}]

    @staticmethod
    def fetch_url(url: str, timeout: int = 10) -> str:
        """
        Fetches text content from a given URL.
        """
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": "rock.ai/0.1.0"})
                resp.raise_for_status()
                text = resp.text
                if len(text) > 8000:
                    return text[:8000] + "\n...[truncated]"
                return text
        except Exception as e:
            return f"Error fetching URL '{url}': {str(e)}"

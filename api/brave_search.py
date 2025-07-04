import requests
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class BraveSearchAPI:
    """Brave Search API integration"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    @staticmethod
    def search(query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Perform web search using Brave Search API"""
        if not Config.BRAVE_API_KEY:
            logger.error("Brave API key not configured")
            return []
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": Config.BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": count,
            "result_filter": "web",
            "safesearch": "moderate"
        }
        
        try:
            response = requests.get(BraveSearchAPI.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for result in data.get("web", {}).get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("description", ""),
                    "url": result.get("url", ""),
                    "published": result.get("age", ""),
                    "source": result.get("profile", {}).get("name", "web")
                })
            
            logger.info(f"Retrieved {len(results)} search results for: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error performing web search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in web search: {e}")
            return []
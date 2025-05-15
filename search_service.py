import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_second: float = 0.8):  # Slightly less than 1 to be safe
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = datetime.min
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = datetime.now()
            time_since_last_request = (now - self.last_request_time).total_seconds()
            
            if time_since_last_request < self.min_interval:
                wait_time = self.min_interval - time_since_last_request
                logger.info(f"Rate limit: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = datetime.now()

class BraveSearchService:
    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY not found in environment variables")
        
        logger.info("Initializing BraveSearchService with API key: %s...", self.api_key[:5])
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        self.rate_limiter = RateLimiter()
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial retry delay in seconds

    async def _make_request(self, client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request with retry logic and rate limiting."""
        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.acquire()
                
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                
                # Log the response status and headers for debugging
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds before retry.")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    retry_after = int(e.response.headers.get('Retry-After', self.retry_delay * (attempt + 1)))
                    logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds before retry.")
                    await asyncio.sleep(retry_after)
                    continue
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"Request failed. Retrying in {wait_time} seconds. Error: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform a search using Brave Search API with rate limiting and retry logic.
        """
        try:
            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Prepare search parameters
            params = {
                "q": query,
                "offset": offset,
                "limit": per_page,
                "search_lang": "en",
                "safesearch": "moderate"
            }

            # Add additional filters if provided
            if filters:
                if filters.get("min_date"):
                    params["since"] = filters["min_date"]
                if filters.get("max_date"):
                    params["until"] = filters["max_date"]
                if filters.get("language"):
                    params["search_lang"] = filters["language"][0]

            logger.info(f"Making search request to Brave Search API with params: {params}")
            
            # Make the API request with retry logic
            async with httpx.AsyncClient() as client:
                data = await self._make_request(client, self.base_url, params)
                
                logger.info(f"Received {len(data.get('web', {}).get('results', []))} results")

            # Transform the results to match our application's format
            results = []
            for item in data.get("web", {}).get("results", []):
                result = {
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "snippet": item.get("description"),
                    "score": item.get("score", 0),
                    "domain": item.get("url", "").split("/")[2] if item.get("url") else "",
                    "language": item.get("language", "en"),
                    "metadata": {
                        "published_date": item.get("published_date"),
                        "age": item.get("age"),
                        "type": item.get("type", "web")
                    },
                    "last_updated": item.get("published_date", "")
                }
                results.append(result)

            return {
                "results": results,
                "total": data.get("web", {}).get("total", 0),
                "page": page,
                "per_page": per_page,
                "total_pages": (data.get("web", {}).get("total", 0) + per_page - 1) // per_page
            }

        except httpx.HTTPError as e:
            error_msg = f"HTTP error during search: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def get_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions from Brave Search API with rate limiting and retry logic.
        """
        try:
            async with httpx.AsyncClient() as client:
                data = await self._make_request(
                    client,
                    "https://api.search.brave.com/res/v1/suggest",
                    {"q": query}
                )
                return data.get("suggestions", [])
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return [] 
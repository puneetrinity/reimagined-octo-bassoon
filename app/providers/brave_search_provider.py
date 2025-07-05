# app/providers/brave_search_provider.py
"""
Brave Search API provider with standardized interface.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.providers.base_provider import (
    BaseProvider,
    ProviderConfig,
    ProviderError,
    ProviderResult,
)


@dataclass
class SearchQuery:
    text: str
    max_results: int = 10
    language: str = "en"
    country: str = "US"
    search_type: str = "web"  # web, news, images
    safe_search: str = "moderate"  # off, moderate, strict
    time_range: Optional[str] = None


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0
    published_date: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BraveSearchProvider(BaseProvider):
    def __init__(self, config: ProviderConfig, logger: Optional[logging.Logger] = None):
        if not config.base_url:
            config.base_url = "https://api.search.brave.com/res/v1"
        if config.cost_per_request == 0.0:
            config.cost_per_request = 0.008
        super().__init__(config, logger)
        self._endpoints = {
            "web": f"{config.base_url}/web/search",
            "news": f"{config.base_url}/news/search",
            "images": f"{config.base_url}/images/search",
        }
        self._demo_mode = False

    async def initialize(self) -> None:
        if not self.config.api_key:
            raise ProviderError(
                message="Brave Search API key is required",
                provider=self.get_provider_name(),
                error_code="MISSING_API_KEY",
            )
            
        # Check for demo/test keys
        is_demo_key = (
            self.config.api_key.startswith("demo_") or 
            self.config.api_key == "your_brave_key_here"
        )
        
        self._session = await self._create_session()
        try:
            if is_demo_key:
                # Skip API test for demo keys and mark as demo mode
                self._initialized = True
                self._demo_mode = True
                self.logger.info(f"Initialized {self.get_provider_name()} in demo mode")
            else:
                await self._test_api_connection()
                self._initialized = True
                self._demo_mode = False
                self.logger.info(f"Initialized {self.get_provider_name()}")
        except Exception as e:
            await self.cleanup()
            if is_demo_key:
                # For demo keys, initialize anyway but in demo mode
                self._initialized = True
                self._demo_mode = True
                self.logger.warning(f"Initialized {self.get_provider_name()} in demo mode due to API error: {str(e)}")
            else:
                raise ProviderError(
                    message=f"Failed to initialize Brave Search: {str(e)}",
                    provider=self.get_provider_name(),
                    error_code="INITIALIZATION_FAILED",
                    original_error=e,
                )

    async def cleanup(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        self._initialized = False

    def is_available(self) -> bool:
        return bool(self.config.api_key) and self._initialized

    def get_provider_name(self) -> str:
        return "brave_search"

    async def search(self, query: SearchQuery) -> ProviderResult:
        if not self.is_available():
            raise ProviderError(
                message="Provider not initialized or unavailable",
                provider=self.get_provider_name(),
                error_code="PROVIDER_UNAVAILABLE",
            )
        self._validate_search_query(query)

        # Handle demo mode
        if getattr(self, '_demo_mode', False):
            return await self._demo_search(query)

        async def _search_operation():
            endpoint = self._endpoints.get(query.search_type, self._endpoints["web"])
            params = {
                "q": query.text,
                "count": min(query.max_results, 20),
                "country": query.country,
                "search_lang": query.language,
                "ui_lang": query.language,
                "safesearch": query.safe_search,
            }
            if query.time_range:
                params["freshness"] = query.time_range
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.config.api_key,
                "User-Agent": "AI-Search-System/1.0",
            }
            async with self._session.get(
                endpoint, params=params, headers=headers
            ) as response:
                if response.status == 429:
                    raise ProviderError(
                        message="Rate limit exceeded",
                        provider=self.get_provider_name(),
                        error_code="RATE_LIMIT_EXCEEDED",
                    )
                elif response.status == 401:
                    raise ProviderError(
                        message="Invalid API key",
                        provider=self.get_provider_name(),
                        error_code="INVALID_API_KEY",
                    )
                elif response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(
                        message=f"API request failed: {response.status} - {error_text}",
                        provider=self.get_provider_name(),
                        error_code=f"HTTP_{response.status}",
                    )
                data = await response.json()
                results = self._parse_search_results(data, query.search_type)
                return results

        return await self._execute_with_retry(_search_operation)

    def _validate_search_query(self, query: SearchQuery) -> None:
        if not query.text.strip():
            raise ProviderError(
                message="Search query cannot be empty",
                provider=self.get_provider_name(),
                error_code="INVALID_QUERY",
            )
        if query.max_results <= 0 or query.max_results > 50:
            raise ProviderError(
                message="max_results must be between 1 and 50",
                provider=self.get_provider_name(),
                error_code="INVALID_PARAMETERS",
            )

    def _parse_search_results(
        self, data: Dict[str, Any], search_type: str
    ) -> List[SearchResult]:
        results = []
        if search_type == "web":
            web_results = data.get("web", {}).get("results", [])
            for item in web_results:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="brave_search",
                    published_date=item.get("age"),
                    metadata={
                        "language": item.get("language"),
                        "family_friendly": item.get("family_friendly", True),
                        "page_rank": item.get("page_rank", 0),
                    },
                )
                results.append(result)
        elif search_type == "news":
            news_results = data.get("news", {}).get("results", [])
            for item in news_results:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="brave_search",
                    published_date=item.get("age"),
                    metadata={
                        "category": item.get("category"),
                        "breaking": item.get("breaking", False),
                    },
                )
                results.append(result)
        return results

    async def _test_api_connection(self) -> None:
        test_query = SearchQuery(text="test", max_results=1)
        test_params = {"q": test_query.text, "count": 1}
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.config.api_key,
            "User-Agent": "AI-Search-System/1.0",
        }
        async with self._session.get(
            self._endpoints["web"], params=test_params, headers=headers
        ) as response:
            if response.status not in [200, 429]:
                raise Exception(f"API test failed: {response.status}")

    async def _demo_search(self, query: SearchQuery) -> ProviderResult:
        """Demo search implementation for testing without real API keys"""
        # Simulate realistic search results
        demo_results = [
            SearchResult(
                title=f"Demo Result 1: {query.text} - Official Documentation",
                url="https://docs.example.com/official",
                snippet=f"Official documentation and guides about {query.text}. Comprehensive information with examples and best practices.",
                source="brave_search_demo",
                relevance_score=0.95,
                metadata={"demo": True, "rank": 1}
            ),
            SearchResult(
                title=f"Demo Result 2: {query.text} - Tutorial Guide",
                url="https://tutorial.example.com/guide",
                snippet=f"Step-by-step tutorial for {query.text}. Learn the fundamentals with practical examples.",
                source="brave_search_demo",
                relevance_score=0.88,
                metadata={"demo": True, "rank": 2}
            ),
            SearchResult(
                title=f"Demo Result 3: {query.text} - Research & Analysis",
                url="https://research.example.com/analysis",
                snippet=f"In-depth research and analysis of {query.text}. Academic insights and expert opinions.",
                source="brave_search_demo",
                relevance_score=0.82,
                metadata={"demo": True, "rank": 3}
            )
        ]
        
        # Limit results to requested amount
        results = demo_results[:query.max_results]
        
        from app.providers.base_provider import ProviderResult
        return ProviderResult(
            success=True,
            data=results,
            cost=0.0,  # Demo mode is free
            execution_time=0.1,  # Fast demo response
            metadata={
                "provider": self.get_provider_name(),
                "demo_mode": True,
                "total_results": len(results),
                "query": query.text
            }
        )

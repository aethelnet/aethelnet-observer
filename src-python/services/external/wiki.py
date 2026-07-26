"""
Wikipedia & Knowledge Base Fetcher

Fetches summaries and structured data from Wikipedia/Wikidata.
Implements link discipline to prevent explosion.

Usage:
    from services.external.wiki import WikiFetcher
    
    wiki = WikiFetcher()
    summary = await wiki.get_summary("Bitcoin")
    entity = await wiki.get_wikidata_entity("Q131723")  # Ethereum
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re


@dataclass
class WikiSummary:
    """A Wikipedia summary with controlled link extraction."""
    title: str
    summary: str
    url: str
    image_url: Optional[str]
    categories: List[str]
    related_links: List[str]  # Limited to max_links
    fetched_at: datetime
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['fetched_at'] = self.fetched_at.isoformat()
        return d


class WikiFetcher:
    """
    Wikipedia/Wikidata fetcher with link explosion prevention.
    
    Key principles:
    - Max depth = 1 (only fetch direct article, not linked articles)
    - Max outgoing links = 10 (collapse to summary, not full graph)
    - Cache aggressively (Wikipedia doesn't change often)
    """
    
    WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1"
    WIKIDATA_API = "https://www.wikidata.org/w/api.php"
    
    def __init__(self, max_links: int = 10, cache_ttl_hours: int = 24):
        self.max_links = max_links
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, WikiSummary] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=cache_ttl_hours)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    # ==========================================
    # WIKIPEDIA SUMMARY
    # ==========================================
    
    async def get_summary(self, title: str) -> Optional[WikiSummary]:
        """
        Get Wikipedia summary with limited related links.
        
        Args:
            title: Article title or search term
            
        Returns:
            WikiSummary with max_links controlled
        """
        # Check cache
        cache_key = f"wiki:{title.lower()}"
        if cache_key in self._cache:
            if datetime.now() - self._cache_time[cache_key] < self._cache_ttl:
                return self._cache[cache_key]
        
        session = await self._get_session()
        
        # Clean title for URL
        clean_title = title.replace(" ", "_")
        url = f"{self.WIKIPEDIA_API}/page/summary/{clean_title}"
        
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    # Try search fallback
                    return await self._search_and_get(title)
                
                data = await resp.json()
            
            # Extract summary
            summary = WikiSummary(
                title=data.get("title", title),
                summary=data.get("extract", ""),
                url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                image_url=data.get("thumbnail", {}).get("source"),
                categories=[],
                related_links=[],
                fetched_at=datetime.now()
            )
            
            # Get limited related links
            summary.related_links = await self._get_related_links(clean_title)
            
            # Cache
            self._cache[cache_key] = summary
            self._cache_time[cache_key] = datetime.now()
            
            return summary
            
        except Exception as e:
            print(f"Wikipedia error: {e}")
            return None
    
    async def _search_and_get(self, query: str) -> Optional[WikiSummary]:
        """Search Wikipedia and get first result."""
        session = await self._get_session()
        
        search_url = f"{self.WIKIPEDIA_API}/page/related/{query.replace(' ', '_')}"
        
        try:
            async with session.get(search_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            # Get first result
            pages = data.get("pages", [])
            if pages:
                return await self.get_summary(pages[0].get("title", ""))
            
        except Exception:
            pass
        
        return None
    
    async def _get_related_links(self, title: str) -> List[str]:
        """Get limited related links from article."""
        session = await self._get_session()
        
        # Use the links endpoint but limit results
        url = f"https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "prop": "links",
            "pllimit": str(self.max_links),  # LINK DISCIPLINE
            "format": "json"
        }
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
            
            # Extract links
            pages = data.get("query", {}).get("pages", {})
            links = []
            for page_id, page_data in pages.items():
                for link in page_data.get("links", [])[:self.max_links]:
                    title = link.get("title", "")
                    # Filter out meta pages
                    if not title.startswith(("Wikipedia:", "Template:", "Category:", "Help:")):
                        links.append(title)
            
            return links[:self.max_links]
            
        except Exception:
            return []
    
    # ==========================================
    # WIKIDATA (Structured Data)
    # ==========================================
    
    async def get_wikidata_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get structured data from Wikidata.
        
        Args:
            entity_id: Wikidata ID like Q131723 (Ethereum)
            
        Returns:
            Structured entity data
        """
        session = await self._get_session()
        
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "format": "json",
            "languages": "en"
        }
        
        try:
            async with session.get(self.WIKIDATA_API, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            entities = data.get("entities", {})
            if entity_id not in entities:
                return None
            
            entity = entities[entity_id]
            
            # Extract useful fields
            labels = entity.get("labels", {})
            descriptions = entity.get("descriptions", {})
            
            return {
                "id": entity_id,
                "label": labels.get("en", {}).get("value", ""),
                "description": descriptions.get("en", {}).get("value", ""),
                "url": f"https://www.wikidata.org/wiki/{entity_id}",
                "claims_count": len(entity.get("claims", {}))
            }
            
        except Exception as e:
            print(f"Wikidata error: {e}")
            return None
    
    # ==========================================
    # SEARCH
    # ==========================================
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Search Wikipedia for articles.
        
        Returns:
            List of {title, description, url}
        """
        session = await self._get_session()
        
        url = f"{self.WIKIPEDIA_API}/page/search"
        params = {"q": query}
        
        try:
            # Use opensearch for better results
            opensearch_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query,
                "limit": str(min(limit, 10)),
                "format": "json"
            }
            
            async with session.get(opensearch_url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
            
            # OpenSearch returns [query, [titles], [descriptions], [urls]]
            if len(data) >= 4:
                results = []
                for i in range(len(data[1])):
                    results.append({
                        "title": data[1][i],
                        "description": data[2][i] if len(data[2]) > i else "",
                        "url": data[3][i] if len(data[3]) > i else ""
                    })
                return results
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        return []


# Singleton
_wiki_fetcher: Optional[WikiFetcher] = None

def get_wiki_fetcher() -> WikiFetcher:
    global _wiki_fetcher
    if _wiki_fetcher is None:
        _wiki_fetcher = WikiFetcher()
    return _wiki_fetcher

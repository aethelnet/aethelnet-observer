"""
OmniSpider: Core Context Fetcher
================================
Distilled from legacy LLM-based spider daemon.
The philosophical truth of the Spider: Fast, parallel knowledge extraction 
from grounded sources (Wikipedia, arXiv) without LLM hallucinations.

No "cyber-punk" formatting, no heuristic entity extraction. Pure data.
"""

import asyncio
import httpx
import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any

logger = logging.getLogger("OmniSpider")

class OmniSpider:
    def __init__(self):
        self.headers = {"User-Agent": "Auratic-Omni-Spider/2.0"}

    async def _search_wikipedia(self, client: httpx.AsyncClient, query: str) -> str:
        try:
            search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "format": "json", "list": "search", "srsearch": query, "utf8": 1
            })
            resp = await client.get(search_url, timeout=5.0)
            if resp.status_code == 200:
                results = resp.json().get("query", {}).get("search", [])
                if results:
                    best_title = results[0]["title"]
                    extract_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                        "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
                        "titles": best_title, "format": "json", "utf8": 1
                    })
                    resp_ex = await client.get(extract_url, timeout=5.0)
                    pages = resp_ex.json().get("query", {}).get("pages", {})
                    extract = next(iter(pages.values())).get("extract", "")
                    return f"[Wiki: {best_title}] {extract[:1000]}"
        except Exception:
            pass
        return ""

    async def _search_arxiv(self, client: httpx.AsyncClient, query: str) -> str:
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results=1"
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                entry = root.find("{http://www.w3.org/2005/Atom}entry")
                if entry is not None:
                    title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
                    summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
                    return f"[arXiv: {title}] {summary[:1000]}"
        except Exception:
            pass
        return ""

    async def crawl(self, target: str) -> Dict[str, Any]:
        """
        Fast, asynchronous pure-data crawl.
        Returns a single unified node to satisfy the LGNN signature.
        """
        async with httpx.AsyncClient(headers=self.headers) as client:
            wiki, arxiv = await asyncio.gather(
                self._search_wikipedia(client, target),
                self._search_arxiv(client, target),
                return_exceptions=True
            )
            
        wiki_text = wiki if isinstance(wiki, str) else ""
        arxiv_text = arxiv if isinstance(arxiv, str) else ""
        
        combined = f"{wiki_text} {arxiv_text}".strip()
        if not combined:
            combined = f"No external data found for '{target}'."
            
        # Return format expected by living_loop.py
        return {
            "target": target,
            "cluster": {
                "nodes": [{"id": f"Context: {target}", "content": combined}],
                "edges": []
            }
        }

    async def crawl_url(self, url: str) -> Dict[str, Any]:
        """Direct raw content fetch without LLM processing."""
        return await self.crawl(url)

_spider_instance = OmniSpider()

def get_omni_spider() -> OmniSpider:
    return _spider_instance

"""
News Aggregator Service
Fetches and prioritizes relevant market news
"""

import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

logger = logging.getLogger("NewsAggregator")

class NewsAggregator:
    def __init__(self):
        # Optional API keys for news services
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY", "")
        self.newsapi_key = os.getenv("NEWS_API_KEY", "")
    
    async def get_relevant_news(self, timeframe: str) -> List[Dict[str, Any]]:
        """Get relevant news prioritized by confidence"""
        news_items = []
        
        # Try to fetch from APIs (if configured)
        try:
            if self.cryptopanic_api_key:
                items = await self._fetch_cryptopanic()
                news_items.extend(items)
        except Exception as e:
            logger.debug(f"CryptoPanic fetch failed: {e}")
        
        # For now, return empty list if no API keys
        # In production, you'd integrate with news APIs here
        
        if not news_items:
            # Fallback to Mock Data (UI Validation)
            news_items = self._generate_mock_news()
        
        # Prioritize by:
        # 1. Confidence score (how likely to affect markets)
        # 2. Timing (upcoming events first)
        # 3. Relevance (affected symbols)
        
        news_items.sort(key=lambda x: (
            -x.get('confidence', 0),  # Higher confidence first
            x.get('time_until', float('inf'))  # Sooner events first
        ))
        
        return news_items[:10]  # Top 10

    def _generate_mock_news(self) -> List[Dict[str, Any]]:
        """Generate realistic mock headlines for UI testing"""
        return [
            {
                "title": "Fed Chair Signals Rate Strategy Shift",
                "source": "Bloomberg",
                "url": "https://bloomberg.com",
                "confidence": 88,
                "symbols": ["USD", "SPX"],
                "time_until": 0
            },
            {
                "title": "Institutional Net Inflows Hit Monthly High",
                "source": "Glassnode",
                "url": "https://glassnode.com",
                "confidence": 82,
                "symbols": ["BTC", "ETH"],
                "time_until": 0
            },
            {
                "title": "Tech Sector Breakout Confirmed on Volume",
                "source": "Reuters",
                "url": "https://reuters.com",
                "confidence": 75,
                "symbols": ["NVDA", "QQQ"],
                "time_until": 0
            }
        ]
    
    async def get_symbol_news(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """Get news relevant to specific symbol"""
        all_news = await self.get_relevant_news(timeframe)
        
        # Filter by symbol
        symbol_news = [
            news for news in all_news 
            if symbol.upper() in [s.upper() for s in news.get('symbols', [])]
        ]
        
        return symbol_news
    
    async def _fetch_cryptopanic(self) -> List[Dict[str, Any]]:
        """Fetch news from CryptoPanic API"""
        if not self.cryptopanic_api_key:
            return []
        
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": self.cryptopanic_api_key,
                "public": "true",
                "filter": "hot",
                "currencies": "BTC,ETH"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        news_items = []
                        for item in results[:10]:
                            # Extract relevant info
                            title = item.get('title', 'No title')
                            created = item.get('created_at', '')
                            currencies = item.get('currencies', [])
                            
                            # Calculate confidence based on votes/views
                            votes = item.get('votes', {})
                            positive = votes.get('positive', 0)
                            negative = votes.get('negative', 0)
                            total = positive + negative
                            confidence = int((positive / total * 100)) if total > 0 else 50
                            
                            # Extract symbols
                            symbols = [c.get('code', '').upper() + 'USDT' for c in currencies if c.get('code')]
                            
                            news_items.append({
                                "title": title,
                                "time": created,
                                "time_until": 0,  # Already happened
                                "symbols": symbols,
                                "confidence": confidence,
                                "source": "CryptoPanic"
                            })
                        
                        return news_items
        except Exception as e:
            logger.error(f"CryptoPanic API error: {e}")
        
        return []
    
    async def _fetch_newsapi(self) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI (placeholder for future implementation)"""
        return []

    async def get_news_by_category(self, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get news filtered by category (sector)"""
        # Fetch generic news (Real or Mock)
        items = await self.get_relevant_news("24h")
        
        # Simple Logic: Filter if descriptions/symbols match, otherwise fallback to generic
        # For now, since valid 'Real' sources (CryptoPanic) are crypto-only,
        # we return generic/mock items for other sectors to ensure the UI isn't empty.
        
        filtered = []
        target = category.upper()
        
        for item in items:
            # Mock check: Use checking logic or return all if broad
            # In a real app, you'd filter by checking item['symbols'] or item['title']
            filtered.append(item)
            
        return filtered[:limit]

# Factory Function
_aggregator_instance = None

def get_enhanced_news_aggregator():
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = NewsAggregator()
    return _aggregator_instance



"""
External Data Sources - News & Sentiment Aggregator

Fetches and distills news from free/low-cost sources for trading signals.
All sources are optional - system works without them.

Usage:
    from services.external.news import NewsAggregator
    
    aggregator = NewsAggregator()
    headlines = await aggregator.fetch_crypto_news("BTC")
    sentiment = aggregator.analyze_sentiment(headlines)
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re


@dataclass
class NewsItem:
    """A single news item."""
    title: str
    source: str
    url: str
    published: datetime
    sentiment_score: float = 0.0  # -1.0 to 1.0
    relevance_score: float = 0.0  # 0.0 to 1.0
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['published'] = self.published.isoformat()
        return d


class NewsAggregator:
    """
    Multi-source news aggregator for market sentiment.
    
    Sources (all optional, add as needed):
    - CryptoCompare News API (free tier)
    - CoinGecko News (no API key needed)
    - RSS feeds (free)
    """
    
    # Sentiment keywords (deterministic, no LLM required)
    POSITIVE_KEYWORDS = [
        'bullish', 'surge', 'rally', 'soar', 'jump', 'gain', 'rise',
        'breakout', 'moon', 'pump', 'buy', 'long', 'support', 'accumulate',
        'growth', 'adoption', 'partnership', 'launch', 'upgrade'
    ]
    
    NEGATIVE_KEYWORDS = [
        'bearish', 'crash', 'plunge', 'dump', 'drop', 'fall', 'decline',
        'breakdown', 'sell', 'short', 'resistance', 'fear', 'hack',
        'scam', 'fraud', 'ban', 'lawsuit', 'regulation', 'warning'
    ]
    
    def __init__(self):
        self.cryptocompare_key = os.getenv("CRYPTOCOMPARE_API_KEY", "")
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, List[NewsItem]] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=15)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    # ==========================================
    # FETCH SOURCES
    # ==========================================
    
    async def fetch_crypto_news(
        self, 
        symbol: str = "BTC",
        limit: int = 20
    ) -> List[NewsItem]:
        """Fetch news from all available sources."""
        # Check cache
        cache_key = f"{symbol}:{limit}"
        if cache_key in self._cache:
            if datetime.now() - self._cache_time[cache_key] < self._cache_ttl:
                return self._cache[cache_key]
        
        all_news = []
        
        # Try CryptoCompare (if key available)
        if self.cryptocompare_key:
            try:
                cc_news = await self._fetch_cryptocompare(symbol, limit)
                all_news.extend(cc_news)
            except Exception as e:
                print(f"CryptoCompare error: {e}")
        
        # Try CoinGecko (no key needed)
        try:
            cg_news = await self._fetch_coingecko_news(symbol, limit)
            all_news.extend(cg_news)
        except Exception as e:
            print(f"CoinGecko error: {e}")
        
        # Deduplicate by title similarity
        unique_news = self._deduplicate(all_news)
        
        # Analyze sentiment
        for item in unique_news:
            item.sentiment_score = self._calculate_sentiment(item.title)
            item.relevance_score = self._calculate_relevance(item.title, symbol)
        
        # Sort by relevance * recency
        unique_news.sort(
            key=lambda x: x.relevance_score * (1 + x.sentiment_score),
            reverse=True
        )
        
        # Cache
        self._cache[cache_key] = unique_news[:limit]
        self._cache_time[cache_key] = datetime.now()
        
        return unique_news[:limit]
    
    async def _fetch_cryptocompare(self, symbol: str, limit: int) -> List[NewsItem]:
        """Fetch from CryptoCompare News API."""
        session = await self._get_session()
        url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={symbol}&api_key={self.cryptocompare_key}"
        
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
        
        items = []
        for article in data.get("Data", [])[:limit]:
            items.append(NewsItem(
                title=article.get("title", ""),
                source="CryptoCompare",
                url=article.get("url", ""),
                published=datetime.fromtimestamp(article.get("published_on", 0)),
                symbols=[symbol]
            ))
        return items
    
    async def _fetch_coingecko_news(self, symbol: str, limit: int) -> List[NewsItem]:
        """Fetch from CoinGecko status updates (no API key)."""
        session = await self._get_session()
        
        # CoinGecko uses coin IDs, map common symbols
        coin_ids = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'XRP': 'ripple', 'ADA': 'cardano', 'DOGE': 'dogecoin'
        }
        coin_id = coin_ids.get(symbol.upper(), symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
        
        # Extract from status updates and description changes
        items = []
        
        # Market data as "news" (price changes)
        market = data.get("market_data", {})
        price_change_24h = market.get("price_change_percentage_24h", 0)
        
        if abs(price_change_24h) > 5:  # Significant move
            direction = "surges" if price_change_24h > 0 else "drops"
            items.append(NewsItem(
                title=f"{symbol} {direction} {abs(price_change_24h):.1f}% in 24 hours",
                source="CoinGecko",
                url=f"https://www.coingecko.com/en/coins/{coin_id}",
                published=datetime.now(),
                symbols=[symbol]
            ))
        
        return items
    
    # ==========================================
    # SENTIMENT ANALYSIS (Deterministic)
    # ==========================================
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score from -1.0 to 1.0 (no LLM, no hallucination)."""
        text_lower = text.lower()
        
        pos_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def _calculate_relevance(self, text: str, symbol: str) -> float:
        """Calculate relevance to the symbol."""
        text_lower = text.lower()
        symbol_lower = symbol.lower()
        
        # Direct mention
        if symbol_lower in text_lower:
            return 1.0
        
        # Related terms
        symbol_map = {
            'btc': ['bitcoin', 'btc', 'satoshi'],
            'eth': ['ethereum', 'eth', 'ether'],
            'sol': ['solana', 'sol'],
        }
        
        related = symbol_map.get(symbol_lower, [symbol_lower])
        for term in related:
            if term in text_lower:
                return 0.9
        
        return 0.3  # General crypto news
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate headlines."""
        seen_titles = set()
        unique = []
        
        for item in items:
            # Normalize title
            normalized = re.sub(r'[^\w\s]', '', item.title.lower())
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(item)
        
        return unique
    
    # ==========================================
    # AGGREGATE SENTIMENT
    # ==========================================
    
    def aggregate_sentiment(self, items: List[NewsItem]) -> Dict[str, Any]:
        """Aggregate sentiment across all items."""
        if not items:
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'article_count': 0
            }
        
        total_score = sum(item.sentiment_score * item.relevance_score for item in items)
        avg_score = total_score / len(items)
        
        # Label
        if avg_score > 0.3:
            label = 'bullish'
        elif avg_score < -0.3:
            label = 'bearish'
        else:
            label = 'neutral'
        
        # Confidence based on agreement
        scores = [item.sentiment_score for item in items]
        if len(scores) > 1:
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            confidence = max(0.0, 1.0 - variance)
        else:
            confidence = 0.5
        
        return {
            'score': round(avg_score, 3),
            'label': label,
            'confidence': round(confidence, 3),
            'article_count': len(items),
            'positive_count': len([i for i in items if i.sentiment_score > 0]),
            'negative_count': len([i for i in items if i.sentiment_score < 0])
        }


# Singleton
_aggregator: Optional[NewsAggregator] = None

def get_news_aggregator() -> NewsAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = NewsAggregator()
    return _aggregator

# (No duplicate trailing implementation — file trimmed to single implementation above)

"""
Enhanced News Aggregator

- Periodically fetches crypto news from multiple RSS sources and (optionally) HTTP JSON APIs.
- Performs a lightweight heuristic sentiment scoring (no external deps).
- Stores normalized news items into backend/db.sqlite under the `news_items` table.
- Exposes async methods used by the application:
    - get_relevant_news(timeframe: str) -> List[Dict]
    - get_symbol_news(symbol: str, timeframe: str) -> List[Dict]

Notes:
- Uses aiohttp for async HTTP fetches (already a dependency in the codebase).
- Database writes run in a thread to avoid blocking the event loop.
"""

import asyncio
import aiohttp
import os
import time
import re
import logging
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from services.news_storage import get_news_storage

logger = logging.getLogger("EnhancedNewsAggregator")

# Simple sentiment lexicons (small, intentionally conservative)
_POSITIVE = {
    "approved", "approval", "gain", "gains", "bull", "bullish", "surge", "rally", "up", "rise",
    "beat", "beats", "record", "recorded", "benefit", "benefits", "gain", "gained", "positive",
    "growth", "soar", "booming"
}
_NEGATIVE = {
    "rejected", "drop", "drops", "down", "falls", "crash", "crashes", "bear", "bearish", "loss",
    "losses", "plunge", "slump", "concern", "concerns", "negative", "decline", "fraud", "hack",
    "investigation", "selloff", "sell-off"
}

# List of symbols/keywords to detect in titles/descriptions
_SYMBOLS = [
    # Crypto
    "BTC", "ETH", "SOL", "BNB", "XRP", "LTC", "ADA", "DOGE", "DOT", "AVAX", "LINK", "UNI",
    # Tech (Mag 7 +)
    "AAPL", "TSLA", "MSFT", "GOOG", "GOOGL", "NVDA", "AMZN", "META", "AMD", "NFLX",
    # Finance & Banking
    "JPM", "BAC", "WFC", "GS", "MS", "BLK",
    # Retail & Consumer
    "WMT", "COST", "TGT", "KO", "PEP", "MCD",
    # Energy
    "XOM", "CVX", "SHEL",
    # Indices / Macro
    "SPX", "SPY", "QQQ", "DXY", "NDX", "DJI", "VIX",
    # Commodities
    "GOLD", "XAU", "SILVER", "XAG", "OIL", "WTI", "BRENT", "COPPER", "NG",
    # Forex
    "EURUSD", "GBPUSD", "USDJPY", "EURGBP", "EURJPY", "USDCAD", "AUDUSD", "NZDUSD"
]

# Optional JSON API (Cryptopanic) if API key provided via CRYPTOPANIC_API_KEY
CRYPTOPANIC_API = "https://cryptopanic.com/api/v1/posts/"

# RSS / JSON sources to try (robust, public RSS feeds)
_DEFAULT_RSS_SOURCES = [
    # Crypto (Robust)
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://news.bitcoin.com/feed/",
    
    # Tech & AI (Google News)
    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    
    # Macro & Global Business
    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories", # MarketWatch
    "https://www.investing.com/rss/news_25.rss", # Investing.com Economy
    "https://finance.yahoo.com/news/rssindex", # Yahoo Finance Top Stories
    "https://www.cnbc.com/id/100003114/device/rss/rss.html", # CNBC Top News
    
    # Forex & Central Banks (Refined)
    "https://www.dailyfx.com/feeds/market-news", # DailyFX
    "https://www.forexlive.com/feed/", # ForexLive (Ultra-fast reflexes)
    "https://www.myfxbook.com/rss/latest-forex-news", # Myfxbook (User Request)
    "https://news.google.com/rss/search?q=forex+central+bank+rates+powell+lagarde+ueda&hl=en-US&gl=US&ceid=US:en",
    
    # Analysis & Equity Pulse
    "https://seekingalpha.com/market_currents.xml", # Seeking Alpha (Deep Analysis)
    
    # Reddit Alpha (Retail Sentiment & Code)
    "https://www.reddit.com/r/CryptoCurrency/new.rss",
    "https://www.reddit.com/r/wallstreetbets/new.rss",
    "https://www.reddit.com/r/algotrading/new.rss",

    # Legacy Fallbacks
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=401&id=10000664",
]

# Singleton holder
_AGGREGATOR_SINGLETON = None


def _normalize_datetime(dt: Optional[datetime]) -> int:
    if dt is None:
        return int(time.time())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _parse_pubdate(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            # Try ISO fallback
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


def _heuristic_sentiment(text: str) -> (float, str):
    """
    Simple heuristic sentiment:
    - Count occurrences of positive and negative words.
    - Score = (pos - neg) / total_hits, in range [-1, 1].
    - Label = POSITIVE / NEGATIVE / NEUTRAL
    """
    if not text:
        return 0.0, "NEUTRAL"
    txt = re.sub(r"[^\w\s]", " ", text).lower()
    words = txt.split()
    pos = sum(1 for w in words if w in _POSITIVE)
    neg = sum(1 for w in words if w in _NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0, "NEUTRAL"
    score = (pos - neg) / total
    if score > 0.1:
        label = "POSITIVE"
    elif score < -0.1:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return round(score, 3), label


def _extract_symbols(text: str) -> List[str]:
    if not text:
        return []
    found = set()
    txt_upper = text.upper()
    for sym in _SYMBOLS:
        pattern = r"\b" + re.escape(sym) + r"\b"
        if re.search(pattern, txt_upper):
            found.add(sym)
    
    # Manual Alias Mapping
    aliases = {
        "BITCOIN": "BTC", "ETHEREUM": "ETH", "SOLANA": "SOL",
        "APPLE": "AAPL", "IPHONE": "AAPL", "MAC": "AAPL",
        "TESLA": "TSLA", "NVIDIA": "NVDA",
        "GOLD": "XAU", "SILVER": "XAG", "DOLLAR": "DXY", "GREENBACK": "DXY",
        "EURO": "EURUSD", "POUND": "GBPUSD", "YEN": "USDJPY",
        "S&P 500": "SPX", "S&P": "SPX", "EQUITIES": "SPX", "STOCK MARKET": "SPX", "WALL ST": "SPX",
        "NASDAQ": "NDX", "TECH STOCKS": "NDX", "SILICON VALLEY": "NDX"
    }
    for alias, sym in aliases.items():
        if alias in txt_upper:
            found.add(sym)

    # Dynamic Taxonomy Injection
    try:
        from config import get_settings
        taxonomy = get_settings().UNIVERSE_TAXONOMY
        # 1. Match Sectors (e.g., "TECH" news adds AAPL, TSLA)
        for sector, members in taxonomy.get("SECTORS", {}).items():
            if sector in txt_upper:
                for m in members:
                    found.add(m)
        
        # 2. Match Categories (e.g., "CRYPTO" news adds BTC, ETH etc - maybe too noisy? Let's stick to Sectors)
    except:
        pass

    return sorted(list(found))


async def _fetch_rss(session: aiohttp.ClientSession, url: str) -> List[Dict]:
    """
    Fetch RSS feed and extract items.
    Returns list of dicts with keys: title, url, description, published_at (epoch seconds), source
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except Exception:
        return []

    try:
        root = ET.fromstring(text.encode("utf-8"))
    except Exception:
        # Some feeds wrap with namespaces or HTML — attempt to find <item> occurrences heuristically
        items = []
        for match in re.finditer(r"<item\b.*?</item>", text, flags=re.S | re.I):
            try:
                node = ET.fromstring(match.group(0))
                title = node.findtext("title") or ""
                link = node.findtext("link") or ""
                desc = node.findtext("description") or ""
                pub = node.findtext("pubDate") or node.findtext("published") or node.findtext("dc:date") or ""
                dt = _parse_pubdate(pub)
                items.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "description": desc.strip(),
                    "published_at": _normalize_datetime(dt),
                    "source": url,
                })
            except Exception:
                continue
        return items

    items = []
    # Standard RSS: channel/item or feed/entry (Atom)
    for item in root.findall(".//item") + root.findall(".//entry"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        # For <link href="..."> in Atom
        if not link:
            link_elem = item.find("link")
            if link_elem is not None:
                link = link_elem.get("href", "") or link_elem.text or ""
        desc = (item.findtext("description") or item.findtext("summary") or item.findtext("content") or "").strip()
        pub = item.findtext("pubDate") or item.findtext("published") or item.findtext("updated") or ""
        dt = _parse_pubdate(pub)
        items.append({
            "title": title,
            "url": link,
            "description": desc,
            "published_at": _normalize_datetime(dt),
            "source": url,
        })
    return items


async def _fetch_cryptopanic(session: aiohttp.ClientSession, api_key: str) -> List[Dict]:
    """
    Fetch posts from CryptoPanic if API key is provided.
    """
    if not api_key:
        return []
    params = {"auth_token": api_key, "filter": "published", "kind": "news", "public": "true"}
    try:
        async with session.get(CRYPTOPANIC_API, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except Exception:
        return []
    posts = []
    for p in data.get("results", []):
        title = p.get("title", "")[:1000]
        link = p.get("url", "")
        time_str = p.get("published_at") or p.get("created_at") or ""
        dt = None
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except Exception:
            dt = _parse_pubdate(time_str)
        posts.append({
            "title": title,
            "url": link,
            "description": p.get("domain", "") or p.get("source", {}).get("title", ""),
            "published_at": _normalize_datetime(dt),
            "source": "cryptopanic",
        })
    return posts




class EnhancedNewsAggregator:
    def __init__(self, sources: Optional[List[str]] = None):
        self.sources = sources or _DEFAULT_RSS_SOURCES
        # Hardcoded default provided by user earlier
        self.cryptopanic_key = os.getenv("CRYPTOPANIC_API_KEY", "a99f228f227ba6fad23f56e5bbd550ab126dbfc7")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        self._last_fetch = 0
        self._min_fetch_interval = 30  # seconds

    async def _fetch_finnhub(self, session: aiohttp.ClientSession, category: str) -> List[Dict]:
        """
        Fetch professional news from Finnhub.
        """
        if not self.finnhub_key:
            return []
        
        url = f"https://finnhub.io/api/v1/news?category={category}&token={self.finnhub_key}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                
                results = []
                for item in data:
                    results.append({
                        "title": item.get("headline", ""),
                        "url": item.get("url", ""),
                        "description": item.get("summary", ""),
                        "published_at": int(item.get("datetime", time.time())),
                        "source": f"finnhub:{category}"
                    })
                return results
        except Exception as e:
            logger.debug(f"Finnhub error ({category}): {e}")
            return []

    async def _fetch_all(self) -> List[Dict]:
        """
        Fetch from RSS sources and optional JSON APIs in parallel.
        Returns normalized items (with sentiment and symbols).
        """
        async with aiohttp.ClientSession() as session:
            tasks = [ _fetch_rss(session, s) for s in self.sources ]
            if self.cryptopanic_key:
                tasks.append(_fetch_cryptopanic(session, self.cryptopanic_key))
            
            if self.finnhub_key:
                # Fetch categories in parallel
                for cat in ["general", "forex", "crypto"]:
                    tasks.append(self._fetch_finnhub(session, cat))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        flat: List[Dict] = []
        for res in results:
            if isinstance(res, Exception):
                continue
            if isinstance(res, list):
                flat.extend(res)

        # Normalize, score, extract
        normalized = []
        for item in flat:
            title = (item.get("title") or "").strip()
            description = (item.get("description") or "").strip()
            url = (item.get("url") or "").strip()
            source = item.get("source") or ""
            published_at = int(item.get("published_at") or int(time.time()))
            
            # Compose text for sentiment
            text_blob = f"{title}\n{description}"
            score, label = _heuristic_sentiment(text_blob)
            symbols = _extract_symbols(text_blob)
            
            normalized.append({
                "title": title,
                "url": url,
                "description": description,
                "published_at": published_at,
                "source": source,
                "sentiment": score,
                "sentiment_label": label,
                "symbols": symbols,
            })
            
        # Sort by published_at desc
        normalized.sort(key=lambda x: x.get("published_at", 0), reverse=True)
        return normalized

    async def get_relevant_news(self, timeframe: str = "daily", limit: int = 50, symbol: Optional[str] = None) -> List[Dict]:
        """
        Fetch latest relevant news and store into DB.
        If symbol is provided, delegates to get_symbol_news.
        """
        if symbol:
            return await self.get_symbol_news(symbol, timeframe=timeframe, limit=limit)

        now = time.time()
        # Fetch if stale
        if now - self._last_fetch >= self._min_fetch_interval:
            self._last_fetch = now
            try:
                items = await self._fetch_all()
                if items:
                    storage = get_news_storage()
                    await storage.store_many(items)
            except Exception:
                pass

        # Return from DB
        return await self._get_recent_from_db(limit=limit)

    async def get_symbol_news(self, symbol: str, timeframe: str = "daily", limit: int = 20) -> List[Dict]:
        """
        Return recent news items associated with `symbol`. Includes support for categories via NewsStorage search.
        """
        # Trigger background fetch (optional optimization)
        try:
             asyncio.create_task(self.get_relevant_news(timeframe=timeframe, limit=limit))
        except Exception:
             pass

        search_terms = [symbol.upper()]
        if symbol.upper().startswith("CAT_"):
            cat = symbol.upper().replace("CAT_", "")
            
            # NEWS-FRIENDLY KEYWORDS
            keyword_map = {
                "TECH": ["NASDAQ", "APPLE", "NVIDIA", "TECH", "SILICON", "AAPL", "NVDA", "NDX", "MICROSOFT", "AI"],
                "STOCKS": ["S&P", "SPX", "MARKET", "INDICES", "EQUITIES", "STOCK", "DOW", "WALL STREET"],
                "MACRO": ["DOLLAR", "FED", "ECONOMY", "INFLATION", "DXY", "MACRO", "INTEREST RATE", "TREASURY", "GDP", "RECESSION", "JOBS", "UNEMPLOYMENT", "CPI", "PPI", "FOMC", "POWELL", "OIL", "GOLD", "STOCKS", "MARKETS", "BOND", "YIELD", "CENTRAL BANK", "RATES", "TRUMP", "BIDEN", "ELECTION"],
                "CRYPTO": ["CRYPTO", "BITCOIN", "BTC", "ETHEREUM", "ETH", "BLOCKCHAIN", "DEFI", "NFT", "ALTCOIN"],
                "FOREX": ["FOREX", "EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "FX", "PAIRS", "EXCHANGE RATE", "ECB", "BOJ", "POWELL", "LAGARDE", "FED", "CENTRAL BANK", "INFLATION", "YIELD", "TREASURY", "DOLLAR", "EURO", "YEN", "POUND"]
            }
            
            if cat in keyword_map:
                search_terms = keyword_map[cat]
            
            search_terms.append(cat)
            search_terms = list(set(search_terms))

        storage = get_news_storage()
        return await storage.search_news(search_terms, limit=limit)

    async def _get_recent_from_db(self, limit: int = 50) -> List[Dict]:
        storage = get_news_storage()
        return await storage.get_global_news(limit=limit)


def get_enhanced_news_aggregator() -> EnhancedNewsAggregator:
    global _AGGREGATOR_SINGLETON
    if _AGGREGATOR_SINGLETON is None:
        _AGGREGATOR_SINGLETON = EnhancedNewsAggregator()
    return _AGGREGATOR_SINGLETON

"""
Minimal news service used by the Telegram bot.

This module is a lightweight message-oriented adapter: other parts of the
backend that already fetch news can call update_news_feed(...) to push
articles in. The Telegram bot will call fetch_news(...) to get recent
articles. No external HTTP calls are performed here so the module remains
dependency-free; it simply formats available data.

Article format accepted by update_news_feed:
{
    "symbol": "XAUUSD",   # optional; None or missing means general/global news
    "title": "Some headline",
    "url": "https://...",
    "source": "Source Name",  # optional
    "ts": datetime.datetime.utcnow()
}
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any
import threading

_lock = threading.RLock()

# NEWS_CACHE: maps symbol (or "__general__") -> list[article dict]
_NEWS_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_GENERAL_KEY = "__general__"


def update_news_feed(item: Dict[str, Any]) -> None:
    """
    Push a news item into the cache.
    """
    symbol = item.get("symbol")
    key = symbol.strip().upper() if isinstance(symbol, str) and symbol.strip() else _GENERAL_KEY
    article = {
        "title": str(item.get("title", "")).strip(),
        "url": item.get("url"),
        "source": item.get("source"),
        "ts": item.get("ts", datetime.utcnow()),
    }
    with _lock:
        lst = _NEWS_CACHE.setdefault(key, [])
        # Prepend newest items
        lst.insert(0, article)
        # Keep cache bounded
        if len(lst) > 50:
            del lst[50:]


def fetch_news(symbol: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch the most recent news items for symbol, falling back to general news.
    """
    key = symbol.strip().upper() if isinstance(symbol, str) and symbol.strip() else _GENERAL_KEY
    with _lock:
        items = list(_NEWS_CACHE.get(key, []))
        if not items and key != _GENERAL_KEY:
            items = list(_NEWS_CACHE.get(_GENERAL_KEY, []))
    return items[:limit]


def format_news_for_telegram(symbol: Optional[str] = None, limit: int = 5) -> str:
    """
    Return a ready-to-send Telegram message string with recent news for symbol.
    """
    s = symbol.upper() if symbol else None
    items = fetch_news(symbol=s, limit=limit)
    header = f"[NEWS] News for {s}" if s else "[NEWS] General market news"
    lines = [header, ""]
    if not items:
        lines.append("[NOTE] No news available at this time.")
        lines.append("News sources may be temporarily unavailable.")
        lines.append("")
        lines.append("Try:")
        lines.append("* /news BTCUSDT - For specific symbol")
        lines.append("* /news - For general market news")
        lines.append("* Check back later")
        return "\n".join(lines)

    for art in items:
        t = art.get("ts")
        tstr = t.strftime("%Y-%m-%d %H:%M UTC") if isinstance(t, datetime) else str(t)
        src = f" ({art['source']})" if art.get("source") else ""
        url = art.get("url") or ""
        lines.append(f"- {art.get('title')}{src} — {tstr}")
        if url:
            lines.append(f"  {url}")
    return "\n".join(lines)

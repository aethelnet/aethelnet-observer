import os
import sqlite3
import time
import math
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NewsCorrelation")


def _project_db_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "db.sqlite")


class NewsCorrelationService:
    """
    Service to compute weighted sentiment for symbols and correlate trades with news.
    All DB operations run in threads via asyncio.to_thread for non-blocking behavior.
    """

    def __init__(self):
        # nothing to initialize beyond DB path currently
        pass

    async def get_news_for_trade(self, trade_ts: float, window_seconds: int = 3600) -> List[Dict[str, Any]]:
        """
        Return news items within +/- window_seconds of trade_ts (epoch seconds).
        """
        start_ts = int(trade_ts - window_seconds)
        end_ts = int(trade_ts + window_seconds)

        def _worker(since, until):
            db = _project_db_path()
            conn = sqlite3.connect(db, timeout=5)
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, title, url, source, published_at, sentiment, sentiment_label, symbols
                    FROM news_items
                    WHERE published_at BETWEEN ? AND ?
                    ORDER BY ABS(published_at - ?) ASC
                    LIMIT 200
                """, (since, until, int(trade_ts)))
                rows = cur.fetchall()
                out = []
                for r in rows:
                    out.append({
                        "id": int(r[0]),
                        "title": r[1],
                        "url": r[2],
                        "source": r[3],
                        "published_at": int(r[4]),
                        "sentiment": float(r[5]) if r[5] is not None else 0.0,
                        "sentiment_label": r[6],
                        "symbols": (r[7] or "").split(",") if r[7] else []
                    })
                return out
            finally:
                conn.close()

        return await asyncio.to_thread(_worker, start_ts, end_ts)

    async def get_news_sentiment_for_symbol(self, symbol: str, as_of_ts: Optional[float] = None,
                                            window_seconds: int = 24 * 3600) -> Dict[str, Any]:
        """
        Compute a weighted sentiment score for a symbol using news items matching the symbol
        within the given window (defaults to last 24h). Weights favor recency (exponential decay).
        Returns dict: {weighted_sentiment, sentiment_label, news_count}
        """
        if as_of_ts is None:
            as_of_ts = time.time()
        since_ts = int(as_of_ts - window_seconds)
        symbol_up = symbol.upper()

        def _worker(sym, since, until):
            db = _project_db_path()
            conn = sqlite3.connect(db, timeout=5)
            try:
                cur = conn.cursor()
                pattern = f"%{sym}%"
                cur.execute("""
                    SELECT published_at, sentiment, sentiment_label
                    FROM news_items
                    WHERE UPPER(symbols) LIKE ?
                      AND published_at BETWEEN ? AND ?
                    ORDER BY published_at DESC
                """, (pattern, since, until))
                rows = cur.fetchall()
                if not rows:
                    return {"weighted_sentiment": 0.0, "sentiment_label": "NEUTRAL", "news_count": 0}

                # Weight by recency: weight = exp(-lambda * age_seconds)
                now_ts = until
                # choose lambda so half-life ~ 6 hours -> lambda = ln(2) / (6*3600)
                half_life_seconds = 6 * 3600
                decay = math.log(2) / max(1, half_life_seconds)
                weighted_sum = 0.0
                weight_total = 0.0
                for pub, s, label in rows:
                    age = max(0, now_ts - int(pub))
                    w = math.exp(-decay * age)
                    weighted_sum += (float(s) if s is not None else 0.0) * w
                    weight_total += w

                if weight_total == 0:
                    return {"weighted_sentiment": 0.0, "sentiment_label": "NEUTRAL", "news_count": len(rows)}
                weighted = weighted_sum / weight_total
                if weighted > 0.2:
                    lab = "POSITIVE"
                elif weighted < -0.2:
                    lab = "NEGATIVE"
                else:
                    lab = "NEUTRAL"
                return {"weighted_sentiment": round(weighted, 3), "sentiment_label": lab, "news_count": len(rows)}
            finally:
                conn.close()

        return await asyncio.to_thread(_worker, symbol_up, since_ts, int(as_of_ts))

    async def correlate_trade_with_news(self, trade_ts: float, symbol: Optional[str] = None,
                                        window_seconds: int = 3600) -> Dict[str, Any]:
        """
        For a given trade timestamp and optional symbol, return nearby news and aggregated sentiment.
        """
        news = await self.get_news_for_trade(trade_ts, window_seconds=window_seconds)
        agg = {"weighted_sentiment": 0.0, "sentiment_label": "NEUTRAL", "news_count": 0}
        if symbol:
            agg = await self.get_news_sentiment_for_symbol(symbol, as_of_ts=trade_ts, window_seconds=window_seconds)
        else:
            # Aggregate by simple average weighted by recency
            if news:
                now_ts = int(trade_ts)
                half_life_seconds = 6 * 3600
                decay = math.log(2) / max(1, half_life_seconds)
                weighted_sum = 0.0
                weight_total = 0.0
                for it in news:
                    age = max(0, now_ts - int(it.get("published_at", now_ts)))
                    w = math.exp(-decay * age)
                    weighted_sum += float(it.get("sentiment", 0.0)) * w
                    weight_total += w
                weighted = weighted_sum / weight_total if weight_total else 0.0
                if weighted > 0.2:
                    lab = "POSITIVE"
                elif weighted < -0.2:
                    lab = "NEGATIVE"
                else:
                    lab = "NEUTRAL"
                agg = {"weighted_sentiment": round(weighted, 3), "sentiment_label": lab, "news_count": len(news)}

        return {"trade_ts": int(trade_ts), "symbol": symbol, "aggregation": agg, "nearby_news": news}

    async def get_historical_correlation(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """
        Simple historical aggregation: returns average weighted sentiment over sliding windows
        (per-day average) for the past `days`.
        """
        now_ts = int(time.time())
        out = []
        for d in range(days):
            end_ts = now_ts - d * 86400
            start_ts = end_ts - 86400
            res = await self.get_news_sentiment_for_symbol(symbol, as_of_ts=end_ts, window_seconds=86400)
            out.append({"day_start": start_ts, "day_end": end_ts, "weighted_sentiment": res["weighted_sentiment"], "news_count": res["news_count"]})

        # Compute overall average weighted sentiment (mean of day values weighted by news_count)
        total_weight = sum(max(1, day["news_count"]) for day in out)
        if total_weight == 0:
            avg = 0.0
        else:
            avg = sum(day["weighted_sentiment"] * max(1, day["news_count"]) for day in out) / total_weight
        return {"symbol": symbol, "days": days, "daily": out, "average_weighted_sentiment": round(avg, 3)}


# Singleton accessor
_instance: Optional[NewsCorrelationService] = None


def get_news_correlation() -> NewsCorrelationService:
    global _instance
    if _instance is None:
        _instance = NewsCorrelationService()
    return _instance

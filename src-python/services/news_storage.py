import time
import logging
import asyncio
from typing import List, Dict, Optional
from sqlalchemy import or_
from services.data.schema import NewsItem
from services.data_manager import get_data_manager

logger = logging.getLogger("NewsStorage")

class NewsStorage:
    """
    Persistence layer for News Items using main Database (Postgres/SQLite) via DataManager.
    Replaces old raw-sqlite implementation to support centralized robust storage.
    """
    def __init__(self):
        # Table creation is handled by DataManager init
        pass

    async def store_news(self, item: Dict) -> Optional[int]:
        def _worker(it: Dict):
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                url = (it.get("url") or "").strip()
                title = (it.get("title") or "").strip()
                published_at = int(it.get("published_at") or int(time.time()))
                
                # Dedupe
                existing = None
                if url:
                    existing = session.query(NewsItem).filter_by(url=url).first()
                else:
                    existing = session.query(NewsItem).filter_by(title=title, published_at=published_at).first()
                
                if existing:
                    return None
                
                symbols_list = it.get("symbols") or []
                symbols_str = ",".join(symbols_list) if isinstance(symbols_list, list) else str(symbols_list)
                
                new_item = NewsItem(
                    title=title,
                    url=url,
                    source=it.get("source") or "",
                    published_at=published_at,
                    sentiment=float(it.get("sentiment") or 0.0),
                    sentiment_label=it.get("sentiment_label") or "NEUTRAL",
                    symbols=symbols_str,
                    created_at=int(time.time())
                )
                session.add(new_item)
                session.commit()
                # session.refresh(new_item) # Optimization: don't need refresh for ID if we trust it
                return new_item.id
        
        try:
            return await asyncio.to_thread(_worker, item)
        except Exception:
            logger.exception("Failed to store news item")
            return None

    async def store_many(self, items: List[Dict]) -> int:
        # Optimized bulk insert possible, but iterative is safer for individual dedupe logic unless we do bulk check
        inserted = 0
        for it in items:
            if await self.store_news(it):
                inserted += 1
        return inserted

    async def get_news_by_symbol(self, symbol: str, limit: int = 50) -> List[Dict]:
        def _worker(sym: str, limit: int):
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                # SQLAlchemy LIKE
                query = session.query(NewsItem).filter(NewsItem.symbols.ilike(f"%{sym}%"))\
                        .order_by(NewsItem.published_at.desc()).limit(limit)
                return [self._to_dict(row) for row in query.all()]
        return await asyncio.to_thread(_worker, symbol, limit)

    async def get_news_by_timeframe(self, since_ts: int, until_ts: Optional[int] = None, limit: int = 100) -> List[Dict]:
        def _worker(since_ts, until_ts, limit):
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                q = session.query(NewsItem).filter(NewsItem.published_at >= since_ts)
                if until_ts:
                    q = q.filter(NewsItem.published_at <= until_ts)
                q = q.order_by(NewsItem.published_at.desc()).limit(limit)
                return [self._to_dict(row) for row in q.all()]
        return await asyncio.to_thread(_worker, since_ts, until_ts, limit)

    async def search_news(self, search_terms: List[str], limit: int = 50) -> List[Dict]:
        """
        Complex search for the aggregator (OR conditions logic).
        Migrated from enhanced_news_aggregator raw SQL.
        """
        def _worker(terms, limit):
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                # 1. Search Symbols OR
                conds = [NewsItem.symbols.ilike(f"%{t}%") for t in terms]
                q = session.query(NewsItem).filter(or_(*conds)).order_by(NewsItem.published_at.desc()).limit(limit)
                res = q.all()
                
                # 2. If empty, search Titles OR
                if not res:
                    conds_title = [NewsItem.title.ilike(f"%{t}%") for t in terms]
                    q = session.query(NewsItem).filter(or_(*conds_title)).order_by(NewsItem.published_at.desc()).limit(limit)
                    res = q.all()
                    
                return [self._to_dict(r) for r in res]
        return await asyncio.to_thread(_worker, search_terms, limit)
        
    async def get_global_news(self, limit: int = 50) -> List[Dict]:
        def _worker():
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                 return [self._to_dict(r) for r in session.query(NewsItem).order_by(NewsItem.published_at.desc()).limit(limit).all()]
        return await asyncio.to_thread(_worker)

    async def count(self) -> int:
        def _worker():
            dm = get_data_manager()
            with dm.SessionLocal() as session:
                return session.query(NewsItem).count()
        return await asyncio.to_thread(_worker)

    def _to_dict(self, row: NewsItem) -> Dict:
        return {
            "id": row.id,
            "title": row.title,
            "url": row.url,
            "source": row.source,
            "published_at": row.published_at,
            "sentiment": row.sentiment,
            "sentiment_label": row.sentiment_label,
            "symbols": (row.symbols or "").split(",") if row.symbols else []
        }

_news_storage_instance: Optional[NewsStorage] = None

def get_news_storage() -> NewsStorage:
    global _news_storage_instance
    if _news_storage_instance is None:
        _news_storage_instance = NewsStorage()
    return _news_storage_instance

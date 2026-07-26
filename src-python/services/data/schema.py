
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class OHLCV(Base):
    __tablename__ = 'ohlcv'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    interval = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    __table_args__ = (
        UniqueConstraint('symbol', 'interval', 'timestamp', name='uix_symbol_interval_timestamp'),
    )

class SymbolRegistry(Base):
    __tablename__ = 'symbol_registry'
    symbol = Column(String, primary_key=True)
    base_asset = Column(String)
    quote_asset = Column(String)
    category = Column(String)
    sector = Column(String)
    status = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)


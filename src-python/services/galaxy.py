
"""
Galaxy Service
The structural backbone of the Universe.
Provides dynamic querying of the Universe Graph (Lexicon + Relationships).
"""
import asyncio
import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

class GalaxyService:
    def __init__(self):
        self.lexicon_path = "backend/data/universe_lexicon.json"
        self.lexicon: Dict[str, Dict] = {}
        self.logger = logging.getLogger("GalaxyService")
        self._load_lexicon()

    def _load_lexicon(self):
        """Loads the Universe Lexicon into memory."""
        try:
            if os.path.exists(self.lexicon_path):
                with open(self.lexicon_path, 'r') as f:
                    self.lexicon = json.load(f)
            else:
                self.logger.warning(f"Lexicon not found at {self.lexicon_path}")
        except Exception as e:
            self.logger.error(f"Failed to load lexicon: {e}")

    def get_asset_details(self, symbol: str) -> Dict:
        """Returns full metadata for a symbol."""
        return self.lexicon.get(symbol.upper(), {})

    def get_cluster_members(self, sector_code: str) -> List[str]:
        """
        Returns a list of symbols belonging to a specific sector/cluster.
        Mappings:
        - CRYPTO -> Sector: 'Crypto'
        - FOREX -> Sector: 'Forex'
        - STOCKS -> Sector: 'Equity'
        - MACRO -> Sector: 'Commodities/Futures' OR 'Index'
        """
        sector_code = sector_code.upper()
        members = []
        
        for sym, data in self.lexicon.items():
            sec = data.get('sector', '').lower()
            
            if sector_code == "CRYPTO" and "crypto" in sec:
                members.append(sym)
            elif sector_code == "FOREX" and "forex" in sec:
                members.append(sym)
            elif sector_code == "STOCKS" and "equity" in sec:
                members.append(sym)
            elif sector_code == "MACRO" and ("commodities" in sec or "index" in sec or "futures" in sec):
                members.append(sym)
        
        # FALLBACK: If lexicon is sparse, augment from settings.UNIVERSE_TAXONOMY.SECTORS
        if len(members) < 5:
            try:
                from config import get_settings
                settings = get_settings()
                taxonomy = settings.UNIVERSE_TAXONOMY.get("SECTORS", {})
                extra = taxonomy.get(sector_code, [])
                for sym in extra:
                    if sym not in members:
                        members.append(sym)
            except Exception:
                pass
                
        # Heuristic sort (Major assets first)
        # We can use a priority list or market cap if available, for now manual priority
        priority = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "GBPJPY=X", "EURJPY=X", "NVDA", "AAPL", "TSLA", "^GSPC", "GC=F"]
        
        members.sort(key=lambda s: priority.index(s) if s in priority else 999)
        return members

    def get_active_session_assets(self, session_id: str) -> Dict:
        """
        Returns assets relevant to a trading session.
        Returns Dict with keys: 'name', 'assets', 'indices'
        """
        session_id = session_id.upper()
        
        # In the future, this could be attribute-based in Lexicon
        # For now, we filter Lexicon based on asset type + heuristic
        
        assets = []
        indices = []
        name = session_id
        
        if session_id == "ASIA":
            name = "ASIA / PACIFIC"
            # JPY, Crypto (24/7), Hang Seng logic if we had it
            # Lexicon filter: JPY, Maybe KRW?
            assets = [s for s in self.lexicon if "JPY" in s]
            indices = ["^N225", "^HSI"] # Examples
            
        elif session_id == "EUROPE":
            name = "LONDON / EUROPE"
            # EUR, GBP
            assets = [s for s in self.lexicon if "EUR" in s or "GBP" in s]
            indices = ["^FTSE", "^GDAXI"]
            
        elif session_id == "US":
            name = "NEW YORK"
            # USD, Stocks, Grid
            assets = [s for s in self.lexicon if "USD" in s and "=X" in s] # Forex pairs with USD
            # Add top stocks
            stocks = self.get_cluster_members("STOCKS")
            assets.extend(stocks[:5])
            indices = ["^GSPC", "^IXIC", "^VIX"]

        # Filter indices to only those in Lexicon
        valid_indices = [i for i in indices if i in self.lexicon]
        
        # Fallbacks for indices if not in lexicon (mock for structure)
        if not valid_indices:
             valid_indices = indices

        return {
            "name": name,
            "assets": assets[:6], # Cap visual list
            "indices": valid_indices
        }

_galaxy_service = None

def get_galaxy_service():
    global _galaxy_service
    if not _galaxy_service:
        _galaxy_service = GalaxyService()
    return _galaxy_service

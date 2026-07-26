
import logging
from typing import Any, Optional, Dict, List
from config import get_settings

class BaseHandler:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    def is_admin(self, chat_id: int) -> bool:
        """Check if a chat_id is in the Admin whitelist."""
        settings = get_settings()
        
        # 1. Primary Admin (TELEGRAM_CHAT_ID)
        primary_admin = getattr(settings, "TELEGRAM_CHAT_ID", None)
        if primary_admin and str(chat_id) == str(primary_admin):
            return True
        
        # 2. Whitelist (TELEGRAM_WHITELIST_IDS)
        whitelist_str = getattr(settings, "TELEGRAM_WHITELIST_IDS", None)
        if whitelist_str:
            whitelist = [x.strip() for x in whitelist_str.split(",") if x.strip()]
            if str(chat_id) in whitelist:
                return True
        
        return False

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", include_donation: bool = False, reply_markup: dict = None, disable_web_page_preview: bool = True):
        return await self.bot.send_message(chat_id, text, parse_mode, include_donation, reply_markup, disable_web_page_preview)

    async def fetch_api(self, endpoint: str) -> Any:
        # Delegate to bot core which handles the base URL and session
        return await self.bot.fetch_api_data(endpoint)

    def get_backend_url(self) -> str:
        return self.bot.backend_url

    # FRACTAL NAVIGATION MAP (The "Nokia" Ring)
    # Main Ring: HOME → PRICE → CLUSTERS → STATS → OPPS → WIKI → YARN → (back to HOME)
    NAV_GRAPH = {
        # Main Ring Nodes (PRICE -> SCAN -> WALLET -> NEWS -> EVENTS -> YARN -> PRICE)
        "START":     {"prev": "YARN",     "next": "PRICE",    "up": None,       "label": "HOME"},
        "PRICE":     {"prev": "START",    "next": "SCAN",     "up": "START",    "label": "PRICE"},
        "SCAN":      {"prev": "PRICE",    "next": "WALLET",   "up": "START",    "label": "SCAN"},
        "WALLET":    {"prev": "SCAN",     "next": "NEWS",     "up": "START",    "label": "WALLET"},
        "NEWS":      {"prev": "WALLET",   "next": "EVENTS",   "up": "START",    "label": "NEWS"},
        "EVENTS":    {"prev": "NEWS",     "next": "YARN",     "up": "START",    "label": "EVENTS"},
        "YARN":      {"prev": "EVENTS",   "next": "PRICE",    "up": "START",    "label": "YARN"},
        
        # Sub-Menus (Inherit Ring Neighbors)
        "CLUSTERS":  {"prev": "START",    "next": "SCAN",     "up": "PRICE",    "label": "CLUSTERS"},
        
        # Leaf Nodes (Drilldowns)
        "SYMBOL":    {"prev": "PRICE",    "next": "SCAN",     "up": "PRICE",    "label": "TICKER"},
        "TRADES":    {"prev": "SCAN",     "next": "NEWS",     "up": "WALLET",   "label": "LOG"},
        "DOCS":      {"prev": "SCAN",     "next": "YARN",     "up": "WIKI",     "label": "DOCS"},
    }
    
    # Callback Maps (Node → Actual Router Command)
    CMD_MAP = {
        "START": "START",
        "PRICE": "PRICE_LANDING",
        "SCAN": "OPPORTUNITIES",
        "WALLET": "WALLET_STATS",
        "NEWS": "NEWS_HUB",
        "EVENTS": "CALENDAR_VIEW",
        "YARN": "YARN_GLOBAL",
        # Sub-features
        "CLUSTERS": "CLUSTER_CRYPTO", 
        "STATS": "STATS", 
        "OPPS": "OPPORTUNITIES",
        "WIKI": "KNOWLEDGE_HUB",
        "DOCS": "KNOWLEDGE_HUB",
        "TRADES": "TRADE_LOG",
        "POSITIONS": "POSITIONS",
    }

    def _get_home_button(self) -> List[Dict]:
        """Returns standard home row."""
        return self._get_cyclical_nav("START")
    
    def _get_nav_row(self, back_callback: str = None) -> List[Dict]:
        """Legacy compatibility wrapper."""
        # If back_callback implies a node, use it, else default to START
        return self._get_cyclical_nav("SYMBOL" if back_callback else "START")

    def _get_cyclical_nav(self, current_node: str) -> List[Dict]:
        """
        Generates [ < PREV ] [ ^ UP ] [ NEXT > ] navigation row.
        Allows T9-style scrolling through the bot's features.
        """
        node_def = self.NAV_GRAPH.get(current_node, self.NAV_GRAPH["START"])
        
        prev_node = node_def.get("prev", "START")
        next_node = node_def.get("next", "START")
        up_node = node_def.get("up", "START")
        
        # Resolve Commands
        prev_cmd = self.CMD_MAP.get(prev_node, "START")
        next_cmd = self.CMD_MAP.get(next_node, "START")
        up_cmd = self.CMD_MAP.get(up_node, "START")
        
        # Nokia Aesthetic: [ < ] [ ^ ] [ > ]
        # Or explicit: [ < PRICE ] [ ^ HOME ] [ STATS > ]
        # User said "simple keys... in and out... jump".
        # Let's use Symbolic Arrows for compactness + Label if space permits?
        # Telegram buttons are small.
        # Let's try: [ < PREV ] [ ^ UP ] [ NEXT > ] + Donation
        
        row = []
        # PREV
        prev_lbl = self.NAV_GRAPH[prev_node]["label"]
        row.append({"text": f"« {prev_lbl}", "callback_data": prev_cmd})
        
        # UP
        if up_cmd:
             row.append({"text": "○", "callback_data": "START"}) # Always Home
        
        # NEXT
        next_lbl = self.NAV_GRAPH[next_node]["label"]
        row.append({"text": f"{next_lbl} »", "callback_data": next_cmd})
        
        return row

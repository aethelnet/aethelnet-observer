import re
import logging
from typing import Optional, Tuple
from config.settings import get_settings

logger = logging.getLogger("SymbolNormalizer")

class EthicalConstraintException(Exception):
    """
    Raised when a user attempts to interact with a blocked "unethical" asset.
    Contains the rich context (impact, news) and suggested alternative.
    """
    def __init__(self, symbol: str, context: dict = None):
        self.symbol = symbol
        self.context = context or {}
        # Backwards compatibility fields for simpler access
        self.alternative = self.context.get("alternative")
        self.impact = self.context.get("impact")
        self.narrative = self.context.get("narrative") # Key field for Curated Context
        self.news_hook = self.context.get("news_hook")
        
        super().__init__(f"Value Alignment: Blocked {symbol}. Suggestion: {self.alternative}")

class SymbolNormalizer:
    """
    Central authority for Symbol Standardization.
    Handles:
    1. Input Sanitization (No junk chars)
    2. Dialect Translation (Chat -> System -> Yahoo/Binance)
    3. Failure Prevention (Blacklisting known broken symbols)
    """
    
    # Strict Allowlist: A-Z, 0-9, ., -, =, ^
    # Rejects emojis, Chinese chars, etc.
    VALID_PATTERN = re.compile(r"^[A-Z0-9.\-=^]+$")
    
    # Known testnet limitations or broken API mappings
    BLACKLIST = {
        "TRYUSDT", "ZARUSDT", "UAHUSDT", "NGNUSDT", "RUBUSDT" # Fiat pairs often broken on testnets
    }

    def __init__(self):
        self.settings = get_settings()
        self.aliases = self.settings.SYMBOL_ALIASES
        # Create reverse map for lookup (Nickname -> Real)
        self.reverse_aliases = {v.upper(): k for k, v in self.aliases.items()}
        
    def sanitize(self, input_symbol: str) -> Optional[str]:
        """
        Clean raw user input. 
        Returns None if invalid/garbage.
        """
        if not input_symbol: return None
        
        # 1. Basic Clean
        s = input_symbol.strip().upper()
        
        # 2. Regex Check
        if not self.VALID_PATTERN.match(s):
            logger.debug(f"[Sanitize] Rejected invalid chars: {s}")
            return None
            
        return s

    def normalize(self, symbol: str) -> str:
        """
        Converts Nicknames/Aliases to SYSTEM standard.
        e.g. "GOLD" -> "GC=F"
             "SPY"  -> "ES=F" (Futures preference) or "SPY" (Stock) depending on map
        """
        # Initialize
        s = symbol.upper()
        
        # 0. TYPO CORRECTION (Layer 0)
        # Handle common user dysgraphia e.g. "GPB" -> "GBP"
        TYPO_MAP = {
            "GPB": "GBP",
            "JYP": "JPY",
            "UDS": "USD", 
            "EUE": "EUR",
            "ERU": "EUR",
            "BITCOIN": "BTC",
            "ETHEREUM": "ETH"
        }
        
        # Typos in prefixes (e.g. GPBJPY -> GBPJPY)
        for typo, correct in TYPO_MAP.items():
            if s.startswith(typo):
                s = s.replace(typo, correct, 1) # Only replace first occurrence (prefix)
                break
                
        # 1. Alias Resolution (Nickname -> Real)
        if s in self.reverse_aliases:
            return self.reverse_aliases[s]
            
        # 2. AUTO-FOREX DETECTION (Heuristic)
        # If it's exactly 6 letters and looks like a currency pair (e.g. "GBPJPY") 
        # but wasn't in the alias map, we assume it's Yahoo Forex format = "GBPJPY=X"
        if len(s) == 6 and s.isalpha():
            # Basic validation of currencies to avoid false positives on stocks like "GOOGLE" (6 chars)
            # but usually tickers are < 5. 6 chars is almost always Forex or crypto.
            # Let's check if it contains known currency codes.
            KNOWN_FIAT = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF", "CNY", "HKD", "SGD"}
            base = s[:3]
            quote = s[3:]
            
            if base in KNOWN_FIAT or quote in KNOWN_FIAT:
                # Likely a Forex pair missed by alias list
                return f"{s}=X"
            
        return s
    
    def to_display(self, symbol: str) -> str:
        """
        Converts SYSTEM standard to Human Readable.
        e.g. "GC=F" -> "GOLD"
        """
        # Strip Yahoo suffix for cleaner display if no alias exists
        name = self.aliases.get(symbol, symbol)
        if name == symbol and symbol.endswith("=X"):
             return symbol[:-2] # "GBPJPY=X" -> "GBPJPY"
        return name

    def to_system(self, symbol: str) -> str:
        """
        Standardizes symbols to internal system format (mostly USDC-based for crypto).
        """
        if not symbol: return ""
        
        # 0. Normalize first (handles aliases)
        s = self.normalize(symbol)

        # 1. Standardize Crypto (ensure USDC suffix for known crypto)
        # If it doesn't have a quote, and it's not a known stock/forex, append USDC
        if not any(c in s for c in ["=", "^", "-"]):
            if not s.endswith(("USDT", "USDC", "BUSD")):
                # Check if it's a 1-4 char ticker (likely stock or crypto base)
                # For this simple normalizer, we assume anything without a suffix is a base
                return f"{s}USDC"
            elif s.endswith("USDT"):
                return s.replace("USDT", "USDC")
                
        return s

    def to_hyperliquid(self, symbol: str) -> str:
        """
        Converts SYSTEM standard to Hyperliquid format (usually base asset only).
        e.g. "BTCUSDC" -> "BTC", "kPEPEUSDC" -> "kPEPE"
        """
        if not symbol: return ""
        s = symbol
        
        # Strip USDC/USDT
        if s.endswith("USDC"):
            s = s[:-4]
        elif s.endswith("USDT"):
            s = s[:-4]
            
        return s

    def to_yahoo(self, symbol: str) -> str:
        """
        Convert System/Binance format to Yahoo Finance format.
        """
        # 1. Check if explicitly defined in aliases (some might be implicit)
        # For now, we assume System Standard IS Yahoo Standard for TradFi
        
        # 2. Crypto Mappings for Yahoo
        # Binance: BTCUSDT -> Yahoo: BTC-USD
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}-USD"
        elif symbol.endswith("USDC"):
            base = symbol[:-4]
            return f"{base}-USD"
        elif symbol.endswith("USD"):
            return f"{symbol}-USD" # Rare
            
        return symbol

    def to_binance(self, symbol: str) -> Optional[str]:
        """
        Convert System format to Binance format.
        Returns None if not a valid Binance symbol (e.g. TradFi).
        """
        # If it has =, ^, - it is likely TradFi
        if any(c in symbol for c in ["=", "^", "-"]):
            return None
            
        # Crypto usually ends with these
        valid_quotes = ("USDT", "USDC", "BUSD", "BTC", "ETH", "BNB")
        if symbol.endswith(valid_quotes):
            # Binance does not allow lowercase letters in symbols
            if any(c.islower() for c in symbol):
                return None
            return symbol
            
        # If it doesn't have a crypto quote, it's likely a stock (GOOGL, TSLA, AAPL)
        return None

    def get_ethical_context(self, symbol: str) -> Optional[dict]:
        """
        Returns the ethical context for a symbol if it exists.
        Does NOT raise exceptions (Soft Intervention Mode).
        """
        if not self.settings.ETHICAL_TRADING_ENABLED:
            return None

        s = symbol.upper()
        
        # Check against blacklist context
        # We check full matches and prefixes (e.g. RUB for RUBUSD)
        blocked_context = None
        
        # Check direct match
        if s in self.settings.ETHICAL_ASSET_CONTEXT:
             blocked_context = self.settings.ETHICAL_ASSET_CONTEXT[s]
             
        # Check prefixes if no direct match
        if not blocked_context:
            for bad_prefix, ctx in self.settings.ETHICAL_ASSET_CONTEXT.items():
                if len(bad_prefix) > 2 and s.startswith(bad_prefix):
                    blocked_context = ctx
                    break
        
        return blocked_context

    def check_ethical_constraints(self, symbol: str):
        """
        [DEPRECATED] Hard block enforcement.
        Kept for backward compatibility if needed, but logic moved to get_ethical_context.
        """
        ctx = self.get_ethical_context(symbol)
        if ctx:
             raise EthicalConstraintException(symbol, ctx)

# Singleton
_normalizer = None

def get_symbol_normalizer():
    global _normalizer
    if _normalizer is None:
        _normalizer = SymbolNormalizer()
    return _normalizer

"""
Symbol Resolver Service
Detects symbol type and routes to appropriate data source
"""

import logging
from typing import Dict, Any, Optional, Tuple
import re

logger = logging.getLogger("SymbolResolver")

class SymbolResolver:
    """
    Resolves symbol types and provides data source routing.
    Supports crypto, forex, stocks, commodities, and indices.
    """
    
    # Crypto patterns
    CRYPTO_QUOTES = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'EUR', 'GBP', 'JPY']
    CRYPTO_BASES = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'LINK', 'AVAX', 'MATIC', 'UNI', 'ATOM', 'LTC']
    
    # Forex patterns (major pairs)
    FOREX_MAJORS = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
    FOREX_COMMODITY = ['AUDUSD', 'USDCAD', 'NZDUSD']
    FOREX_EXOTICS = ['EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY']
    
    # Commodity patterns
    COMMODITY_SYMBOLS = {
        'XAUUSD': 'XAUUSD=X',  # Gold
        'XAGUSD': 'XAGUSD=X',  # Silver
        'GC': 'GC=F',  # Gold futures
        'CL': 'CL=F',  # Crude oil futures
        'NG': 'NG=F',  # Natural gas
    }
    
    # Stock patterns (common indicators)
    STOCK_INDICATORS = ['^', '=']  # Indices use ^, forex uses =X
    
    def __init__(self):
        pass
    
    def detect_symbol_type(self, symbol: str) -> str:
        """
        Detect symbol type: crypto, forex, stock, commodity, or index
        
        Returns: 'crypto', 'forex', 'stock', 'commodity', 'index', or 'unknown'
        """
        symbol_upper = symbol.upper().strip()
        
        # Remove common suffixes for analysis
        clean_symbol = symbol_upper
        
        # Check for index (starts with ^)
        if symbol_upper.startswith('^'):
            return 'index'
        
        # Check for Yahoo format (=X for forex, =F for futures)
        if '=X' in symbol_upper or '=F' in symbol_upper:
            if '=F' in symbol_upper:
                return 'commodity'
            return 'forex'
        
        # Check for commodity symbols
        if symbol_upper in self.COMMODITY_SYMBOLS:
            return 'commodity'
        
        # Check if it's a known commodity format
        for commodity_key in self.COMMODITY_SYMBOLS.keys():
            if symbol_upper.startswith(commodity_key):
                return 'commodity'
        
        # Check for crypto patterns
        # Crypto typically has quote currency suffix
        for quote in self.CRYPTO_QUOTES:
            if symbol_upper.endswith(quote) and len(symbol_upper) > len(quote):
                base = symbol_upper[:-len(quote)]
                if base in self.CRYPTO_BASES or len(base) >= 2:
                    return 'crypto'
        
        # Check for forex patterns
        # Forex pairs are typically 6-7 characters (EURUSD, GBPUSD, etc.)
        if len(symbol_upper) >= 6 and len(symbol_upper) <= 7:
            # Check if it matches forex pattern (3-4 base + 3 quote)
            if symbol_upper in self.FOREX_MAJORS or symbol_upper in self.FOREX_COMMODITY or symbol_upper in self.FOREX_EXOTICS:
                return 'forex'
            # Check if it's a forex-like pattern (USD, EUR, GBP, JPY, etc.)
            if any(symbol_upper.startswith(prefix) for prefix in ['EUR', 'GBP', 'AUD', 'NZD', 'USD']) and \
               any(symbol_upper.endswith(suffix) for suffix in ['USD', 'JPY', 'CHF', 'CAD', 'EUR', 'GBP']):
                return 'forex'
        
        # Check for stock patterns
        # Stocks are typically 1-5 uppercase letters, no numbers (except some like S&P 500 = ^GSPC)
        if len(symbol_upper) <= 5 and symbol_upper.isalpha():
            # Exclude common crypto bases that are short
            if symbol_upper not in ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'LINK', 'AVAX', 'MATIC', 'UNI', 'ATOM', 'LTC']:
                return 'stock'
        
        # Default: try as crypto (most common in this system)
        return 'crypto'
    
    def normalize_symbol(self, symbol: str, target_format: str = 'auto') -> str:
        """
        Normalize symbol to different exchange formats.
        
        Args:
            symbol: Original symbol
            target_format: 'binance', 'yahoo', 'ccxt', or 'auto'
        
        Returns:
            Normalized symbol string
        """
        symbol_upper = symbol.upper().strip()
        symbol_type = self.detect_symbol_type(symbol_upper)
        
        # Auto-detect target format based on symbol type
        if target_format == 'auto':
            if symbol_type == 'forex' or symbol_type == 'commodity':
                target_format = 'yahoo'
            elif symbol_type == 'stock' or symbol_type == 'index':
                target_format = 'yahoo'
            else:
                target_format = 'binance'
        
        # Handle Yahoo format conversions
        if target_format == 'yahoo':
            # Already in Yahoo format
            if '=X' in symbol_upper or '=F' in symbol_upper:
                return symbol_upper
            
            # Convert forex to Yahoo format
            if symbol_type == 'forex':
                if '=X' not in symbol_upper:
                    return f"{symbol_upper}=X"
            
            # Convert commodities to Yahoo format
            if symbol_type == 'commodity':
                if symbol_upper in self.COMMODITY_SYMBOLS:
                    return self.COMMODITY_SYMBOLS[symbol_upper]
                # Try common commodity formats
                if symbol_upper == 'XAUUSD':
                    return 'XAUUSD=X'
                elif symbol_upper == 'XAGUSD':
                    return 'XAGUSD=X'
                elif symbol_upper.startswith('GC'):
                    return 'GC=F'
                elif symbol_upper.startswith('CL'):
                    return 'CL=F'
            
            # Stocks and indices already work with Yahoo
            return symbol_upper
        
        # Handle Binance format (remove Yahoo suffixes)
        elif target_format == 'binance':
            # Remove Yahoo suffixes
            symbol_clean = symbol_upper.replace('=X', '').replace('=F', '')
            return symbol_clean
        
        # Handle CCXT format (add / separator for pairs)
        elif target_format == 'ccxt':
            symbol_clean = symbol_upper.replace('=X', '').replace('=F', '')
            
            # For crypto pairs, add /
            for quote in self.CRYPTO_QUOTES:
                if symbol_clean.endswith(quote) and len(symbol_clean) > len(quote):
                    base = symbol_clean[:-len(quote)]
                    return f"{base}/{quote}"
            
            # For forex, add /
            if symbol_type == 'forex' and len(symbol_clean) >= 6:
                # Try to split (e.g., EURUSD -> EUR/USD)
                if symbol_clean.startswith('USD'):
                    quote = symbol_clean[:3]
                    base = symbol_clean[3:]
                    return f"{base}/{quote}"
                else:
                    base = symbol_clean[:3]
                    quote = symbol_clean[3:]
                    return f"{base}/{quote}"
            
            return symbol_clean
        
        return symbol_upper
    
    def get_data_source(self, symbol: str) -> Tuple[str, str]:
        """
        Get recommended data source and normalized symbol for a given symbol.
        
        Returns:
            Tuple of (data_source, normalized_symbol)
            data_source: 'binance', 'yahoo', 'ccxt', or 'unknown'
        """
        symbol_type = self.detect_symbol_type(symbol)
        
        if symbol_type == 'crypto':
            # Try Binance first, then CCXT
            normalized = self.normalize_symbol(symbol, 'binance')
            return ('binance', normalized)
        
        elif symbol_type in ['forex', 'commodity', 'stock', 'index']:
            normalized = self.normalize_symbol(symbol, 'yahoo')
            return ('yahoo', normalized)
        
        else:
            # Unknown type, try as crypto
            normalized = self.normalize_symbol(symbol, 'binance')
            return ('binance', normalized)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol format is valid (basic validation).
        """
        if not symbol or len(symbol) < 2:
            return False
        
        symbol_upper = symbol.upper().strip()
        
        # Allow alphanumeric, =, /, ^, - characters
        if not re.match(r'^[A-Z0-9=/^-]+$', symbol_upper):
            return False
        
        return True

# Singleton
_resolver_instance = None

def get_symbol_resolver() -> SymbolResolver:
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = SymbolResolver()
    return _resolver_instance


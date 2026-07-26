import sys
import os

# Add the project root to the python path
sys.path.insert(0, '/var/home/nhrlyn/Projects/auratic-systems-prime')

from services.symbol_normalizer import get_symbol_normalizer

normalizer = get_symbol_normalizer()
print(f"Normalizer aliases: {normalizer.aliases}")

symbol = "KASUSDC"
hl_ticker = normalizer.to_hyperliquid(symbol)
print(f"Input: {symbol} -> HL Ticker: {hl_ticker}")

sys.exit(0)

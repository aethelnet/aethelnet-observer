import os
import sys
# Add project root to path
sys.path.append(os.getcwd())

from config.settings import get_settings, get_trading_symbols

settings = get_settings()
symbols = get_trading_symbols(settings)
print(f"Current symbols in list: {symbols}")
print(f"XRPUSDC in list? {'XRPUSDC' in symbols}")

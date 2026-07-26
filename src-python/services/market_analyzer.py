
"""
Market Analyzer Service (Facade)
This module has been refactored into backend/services/analysis/
This file remains for backward compatibility.
"""

from services.analysis import MarketAnalyzer as NewMarketAnalyzer

class MarketAnalyzer(NewMarketAnalyzer):
    pass

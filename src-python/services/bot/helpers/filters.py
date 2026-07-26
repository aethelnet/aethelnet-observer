import logging
from typing import List, Dict, Any

logger = logging.getLogger("BotIntelFilter")

class BotIntelFilter:
    """
    Operative data filtering for Simple Mode.
    Tailors the intelligence stream (Opportunities, Symbols, News, Calendar) 
    to the selected preset: SPECTER, APEX, SHADOW, or CORE.
    """

    @staticmethod
    def filter_opportunities(opportunities: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        """
        Filters a list of opportunities based on the style.
        """
        if not style or style == 'ALL':
            return opportunities

        filtered = []
        for opp in opportunities:
            if BotIntelFilter._matches_style(opp, style):
                filtered.append(opp)
        
        return filtered

    @staticmethod
    def _matches_style(opp: Dict[str, Any], style: str) -> bool:
        """
        Logic for matching an opportunity to a style.
        SPECTER = Momentum (high-velocity breakouts, trending markets)
        APEX = Trend following (multi-timeframe confirmation)
        SHADOW = Reversals (Z-Score deviations, oversold/overbought)
        CORE = Balanced/Macro (global assets, commodities, indices)
        """
        # Common attributes
        symbol = opp.get('symbol', '')
        score = float(opp.get('score', 0))
        confidence = float(opp.get('confidence', 0))
        regime = opp.get('regime', 'UNKNOWN')
        factors = str(opp.get('factors', [])).upper()
        
        # SPECTER: Momentum / High-Velocity Breakouts
        if style == 'SPECTER':
            is_momentum = "MOMENTUM" in factors or "BREAKOUT" in factors or "SURGE" in factors or "VELOCITY" in factors
            # High score in trending regime = momentum play
            return is_momentum or (regime == 'TREND' and score > 0.7)

        # APEX: Trend Following (Slower, Higher Win-Rate)
        if style == 'APEX':
            is_trend = "TREND" in factors or "CONTINUATION" in factors or "HIGHER HIGH" in factors or "LOWER LOW" in factors
            # Trend regime with moderate+ confidence
            return (regime == 'TREND' or is_trend) and confidence > 0.6

        # SHADOW: Reversals / Counter-Trend (Z-Score Snaps)
        if style == 'SHADOW':
            is_reversal = "REVERSAL" in factors or "DIVERGENCE" in factors or "OVERSOLD" in factors or "OVERBOUGHT" in factors or "MEAN REVERSION" in factors
            # Range regime or extreme scores suggest snap-back potential
            return is_reversal or (regime == 'RANGE' and abs(score) > 0.8)

        # CORE: Macro / Global Assets (Commodities, Forex, Indices)
        if style == 'CORE':
            from config import get_settings
            settings = get_settings()
            global_assets = settings.UNIVERSE_TAXONOMY.get("CATEGORIES", {}).get("GLOBAL", [])
            
            is_global = any(asset in symbol for asset in global_assets)
            if not is_global:
                global_prefixes = settings.UNIVERSE_TAXONOMY.get("PREFIXES", {}).get("GLOBAL", [])
                is_global = any(symbol.startswith(pre) for pre in global_prefixes) or "=F" in symbol or "^" in symbol
            
            return is_global

        return True

    @staticmethod
    def filter_symbols(symbols: List[str], style: str) -> List[str]:
        """
        Filters the asset list based on style.
        For example, CORE only shows macro assets.
        """
        if not style or style == 'ALL':
            return symbols
            
        if style == 'CORE':
            from config import get_settings
            settings = get_settings()
            global_assets = settings.UNIVERSE_TAXONOMY.get("CATEGORIES", {}).get("GLOBAL", [])
            global_prefixes = settings.UNIVERSE_TAXONOMY.get("PREFIXES", {}).get("GLOBAL", [])
            
            filtered = []
            for s in symbols:
                is_global = any(asset in s for asset in global_assets) or \
                            any(s.startswith(pre) for pre in global_prefixes) or \
                            "=F" in s or "^" in s
                if is_global:
                    filtered.append(s)
            return filtered
            
        # For other styles, we might not filter the symbol list itself, 
        # or we might filter by volatility (future enhancement).
        return symbols

    @staticmethod
    def filter_news(news_items: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        """Filters news headlines based on style."""
        if not style or style == 'ALL':
            return news_items
            
        filtered = []
        for item in news_items:
            title = str(item.get('title', '')).upper()
            content = str(item.get('content', '')).upper()
            combined = title + " " + content
            
            if style == 'CORE':
                from config import get_settings
                settings = get_settings()
                global_assets = settings.UNIVERSE_TAXONOMY.get("CATEGORIES", {}).get("GLOBAL", [])
                keywords = ["MACRO", "FED", "GOLD", "STOCKS", "INFLATION", "CPI", "USD"] + global_assets
                if any(k.upper() in combined for k in keywords):
                    filtered.append(item)
            
            elif style == 'SPECTER':
                # Momentum / Breakout News
                keywords = ["BREAKOUT", "SURGE", "RALLY", "MOMENTUM", "SPIKE", "PUMP", "SOAR", "EXPLODE"]
                if any(k.upper() in combined for k in keywords):
                    filtered.append(item)
            
            elif style == 'APEX':
                # Trend Following News
                keywords = ["TREND", "BULLISH", "BEARISH", "CONTINUATION", "HIGHER HIGH", "LOWER LOW", "SUSTAINED"]
                if any(k.upper() in combined for k in keywords):
                    filtered.append(item)
            
            elif style == 'SHADOW':
                # Reversals / Counter-Trend News
                keywords = ["REVERSAL", "OVERSOLD", "OVERBOUGHT", "DIVERGENCE", "BOUNCE", "SUPPORT", "RESISTANCE", "PULLBACK"]
                if any(k.upper() in combined for k in keywords):
                    filtered.append(item)
                    
        # If filtering is too aggressive, return original list (don't leave hub silent)
        return filtered if filtered else news_items[:3]

    @staticmethod
    def filter_calendar(events: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        """Filters economic events based on style."""
        if not style or style == 'ALL':
            return events
            
        filtered = []
        for event in events:
            impact = event.get('impact', 'Low')
            title = str(event.get('title', '')).upper()
            
            if style == 'CORE':
                # CORE wants High/Medium macro events (balanced view)
                if impact in ['High', 'Medium']:
                    filtered.append(event)
            elif style == 'SPECTER':
                # SPECTER (momentum) - High impact events that cause spikes
                if impact == 'High':
                    filtered.append(event)
            elif style == 'APEX':
                # APEX (trend) - Medium/High that confirm direction
                if impact in ['High', 'Medium']:
                    filtered.append(event)
            elif style == 'SHADOW':
                # SHADOW (reversals) - Any event that could cause pivot
                filtered.append(event)
                    
        return filtered if filtered else events[:2]

    @staticmethod
    def filter_scoreboard(scores: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        """Filters user/trader rankings or achievements based on style focus."""
        # Scoreboard filtering might be less strictly about data and more about 
        # symbols. If the rankings are based on specific symbols, we can filter those.
        # For now, we'll return all, but we could filter by symbol focus in the future.
        return scores

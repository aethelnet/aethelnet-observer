"""
Sector Clustering Service
Groups symbols into sectors using basic classification, detailed sectors, and correlation analysis
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

logger = logging.getLogger("SectorClusterer")

class SectorClusterer:
    """
    Clusters trading symbols into sectors using multiple methods:
    1. Basic sector classification (crypto, forex, stocks, commodities)
    2. Detailed sector classification (Layer1, DeFi, Tech stocks, etc.)
    3. Correlation-based clustering (groups symbols that move together)
    """
    
    # Basic sector mappings
    BASIC_SECTORS = {
        'crypto': ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'LINK', 'AVAX', 'MATIC', 'UNI', 'ATOM', 'LTC'],
        'forex': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD', 'XAGUSD'],
        'stocks': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'BAC', 'XOM', 'CVX'],
        'commodities': ['GC', 'CL', 'NG', 'XAU', 'XAG'],
        'indices': ['^GSPC', '^DJI', '^IXIC', '^VIX']
    }
    
    # Detailed sector mappings
    DETAILED_SECTORS = {
        # Crypto sub-sectors
        'Layer1': ['BTC', 'ETH', 'SOL', 'AVAX', 'ATOM', 'DOT', 'ADA'],
        'DeFi': ['UNI', 'AAVE', 'MKR', 'COMP', 'SUSHI', 'CRV'],
        'Meme': ['DOGE', 'SHIB', 'PEPE', 'FLOKI'],
        'Stablecoins': ['USDT', 'USDC', 'BUSD', 'DAI'],
        'Exchange': ['BNB', 'FTT', 'HT', 'OKB'],
        'Layer2': ['MATIC', 'ARB', 'OP'],
        
        # Stock sectors
        'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC'],
        'Finance': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS'],
        'Energy': ['XOM', 'CVX', 'SLB', 'COP'],
        'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABT', 'TMO'],
        'Consumer': ['AMZN', 'TSLA', 'NKE', 'SBUX', 'MCD'],
        
        # Forex categories
        'Majors': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
        'CommodityCurrencies': ['AUDUSD', 'USDCAD', 'NZDUSD'],
        'Metals': ['XAUUSD', 'XAGUSD', 'XPDUSD', 'XPTUSD'],
        'Exotics': ['EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY'],
    }
    
    def __init__(self):
        self.correlation_cache: Dict[str, Dict[str, float]] = {}
        self.cluster_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.last_update = None
        self.update_interval = int(os.getenv("CLUSTER_UPDATE_INTERVAL", "3600"))  # 1 hour default
        self.correlation_window_days = int(os.getenv("CORRELATION_WINDOW_DAYS", "30"))
    
    def get_basic_sector(self, symbol: str) -> str:
        """
        Classify symbol into basic sector: crypto, forex, stocks, commodities, indices
        """
        symbol_upper = symbol.upper()
        
        # Check indices first (they have ^ prefix)
        if symbol_upper.startswith('^'):
            return 'indices'
        
        # Check forex (currency pairs)
        if any(pair in symbol_upper for pair in self.BASIC_SECTORS['forex']):
            return 'forex'
        
        # Check commodities
        for commodity in self.BASIC_SECTORS['commodities']:
            if commodity in symbol_upper:
                return 'commodities'
        
        # Check stocks (typically 1-5 letters, no numbers)
        if len(symbol_upper) <= 5 and symbol_upper.isalpha():
            # Exclude crypto bases
            if symbol_upper not in self.BASIC_SECTORS['crypto']:
                return 'stocks'
        
        # Check crypto (has USDT, USDC, etc. suffix or is a known crypto base)
        for crypto_base in self.BASIC_SECTORS['crypto']:
            if symbol_upper.startswith(crypto_base) or crypto_base in symbol_upper:
                return 'crypto'
        
        # Default to crypto (most common in trading systems)
        return 'crypto'
    
    def get_detailed_sector(self, symbol: str) -> Optional[str]:
        """
        Classify symbol into detailed sector (Layer1, DeFi, Technology, etc.)
        """
        symbol_upper = symbol.upper()
        
        # Remove common suffixes for matching
        base_symbol = symbol_upper.replace('USDT', '').replace('USDC', '').replace('=X', '').replace('=F', '')
        
        # Check all detailed sectors
        for sector, symbols in self.DETAILED_SECTORS.items():
            for sector_symbol in symbols:
                if sector_symbol in symbol_upper or base_symbol == sector_symbol:
                    return sector
        
        return None
    
    def get_all_basic_clusters(self) -> Dict[str, List[str]]:
        """
        Get all symbols grouped by basic sectors.
        Returns: {sector_name: [list of symbols]}
        """
        clusters = defaultdict(list)
        
        # This would ideally come from actual market data
        # For now, return structure based on known symbols
        for sector, symbols in self.BASIC_SECTORS.items():
            clusters[sector] = symbols
        
        return dict(clusters)
    
    def get_all_detailed_clusters(self) -> Dict[str, List[str]]:
        """
        Get all symbols grouped by detailed sectors.
        """
        clusters = defaultdict(list)
        
        for sector, symbols in self.DETAILED_SECTORS.items():
            clusters[sector] = symbols
        
        return dict(clusters)
    
    async def get_correlation_clusters(self, symbols: Optional[List[str]] = None, min_correlation: float = 0.7) -> List[Dict[str, Any]]:
        """
        Group symbols by price correlation.
        Symbols with correlation > min_correlation are grouped together.
        
        Args:
            symbols: List of symbols to analyze (if None, uses available data)
            min_correlation: Minimum correlation threshold (0.0 to 1.0)
        
        Returns:
            List of cluster dictionaries with symbols and correlation info
        """
        try:
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            # Get symbols to analyze
            if symbols is None:
                # Get symbols from websocket buffer or use default set
                try:
                    from services.websocket_manager import get_websocket_manager
                    ws_manager = get_websocket_manager()
                    if hasattr(ws_manager, 'buffer'):
                        symbols = list(ws_manager.buffer.keys())
                    else:
                        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
                except:
                    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
            
            # Get historical price data for correlation calculation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.correlation_window_days)
            
            price_data = {}
            for symbol in symbols[:50]:  # Limit to 50 symbols for performance
                try:
                    historical = dm.get_data(symbol, "1d", start=start_date)
                    if historical and len(historical) >= 20:  # Need at least 20 data points
                        prices = [h.get('close', 0) for h in historical if 'close' in h]
                        if len(prices) >= 20:
                            price_data[symbol] = prices
                except Exception as e:
                    logger.debug(f"Could not get data for {symbol}: {e}")
            
            if len(price_data) < 2:
                return []  # Need at least 2 symbols for correlation
            
            # Calculate correlation matrix
            correlation_matrix = self._calculate_correlation_matrix(price_data)
            
            # Group symbols by correlation
            clusters = self._group_by_correlation(correlation_matrix, min_correlation)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error calculating correlation clusters: {e}")
            return []
    
    def _calculate_correlation_matrix(self, price_data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate Pearson correlation coefficient between all symbol pairs.
        """
        symbols = list(price_data.keys())
        correlation_matrix = {}
        
        for i, sym1 in enumerate(symbols):
            correlation_matrix[sym1] = {}
            prices1 = np.array(price_data[sym1])
            
            # Calculate percentage returns for correlation
            returns1 = np.diff(prices1) / prices1[:-1]
            
            for sym2 in symbols[i:]:
                prices2 = np.array(price_data[sym2])
                
                # Align lengths
                min_len = min(len(returns1), len(prices2) - 1)
                if min_len < 10:  # Need at least 10 data points
                    correlation = 0.0
                else:
                    returns2 = np.diff(prices2[:min_len+1]) / prices2[:min_len]
                    returns1_aligned = returns1[:min_len]
                    
                    # Calculate correlation
                    if len(returns1_aligned) == len(returns2) and len(returns1_aligned) > 1:
                        correlation = np.corrcoef(returns1_aligned, returns2)[0, 1]
                        if np.isnan(correlation):
                            correlation = 0.0
                    else:
                        correlation = 0.0
                
                correlation_matrix[sym1][sym2] = correlation
                if sym1 != sym2:
                    if sym2 not in correlation_matrix:
                        correlation_matrix[sym2] = {}
                    correlation_matrix[sym2][sym1] = correlation
        
        return correlation_matrix
    
    def _group_by_correlation(self, correlation_matrix: Dict[str, Dict[str, float]], min_correlation: float) -> List[Dict[str, Any]]:
        """
        Group symbols into clusters based on correlation matrix.
        Uses a simple clustering algorithm: symbols with high correlation form clusters.
        """
        clusters = []
        processed = set()
        
        symbols = list(correlation_matrix.keys())
        
        for symbol in symbols:
            if symbol in processed:
                continue
            
            # Find all symbols highly correlated with this one
            cluster_symbols = [symbol]
            cluster_correlations = []
            
            for other_symbol in symbols:
                if other_symbol == symbol or other_symbol in processed:
                    continue
                
                corr = correlation_matrix.get(symbol, {}).get(other_symbol, 0.0)
                if corr >= min_correlation:
                    cluster_symbols.append(other_symbol)
                    cluster_correlations.append({
                        'symbol': other_symbol,
                        'correlation': corr
                    })
            
            if len(cluster_symbols) > 1:  # Only create clusters with 2+ symbols
                # Calculate average correlation
                avg_correlation = np.mean([correlation_matrix.get(cluster_symbols[0], {}).get(s, 0.0) 
                                          for s in cluster_symbols[1:]])
                
                clusters.append({
                    'type': 'correlation',
                    'name': f"Correlation Cluster ({len(cluster_symbols)} symbols)",
                    'symbols': cluster_symbols,
                    'average_correlation': float(avg_correlation),
                    'correlations': cluster_correlations,
                    'size': len(cluster_symbols)
                })
                
                # Mark symbols as processed
                processed.update(cluster_symbols)
        
        # Sort by cluster size (largest first)
        clusters.sort(key=lambda x: x['size'], reverse=True)
        
        return clusters
    
    async def get_cluster_summary(self, cluster_type: str = "all") -> Dict[str, Any]:
        """
        Get summary of all clusters.
        
        Args:
            cluster_type: 'basic', 'detailed', 'correlation', or 'all'
        
        Returns:
            Dictionary with cluster summaries
        """
        summary = {
            'basic_sectors': {},
            'detailed_sectors': {},
            'correlation_clusters': []
        }
        
        if cluster_type in ['basic', 'all']:
            basic_clusters = self.get_all_basic_clusters()
            for sector, symbols in basic_clusters.items():
                summary['basic_sectors'][sector] = {
                    'symbol_count': len(symbols),
                    'symbols': symbols[:10]  # Limit for display
                }
        
        if cluster_type in ['detailed', 'all']:
            detailed_clusters = self.get_all_detailed_clusters()
            for sector, symbols in detailed_clusters.items():
                summary['detailed_sectors'][sector] = {
                    'symbol_count': len(symbols),
                    'symbols': symbols[:10]
                }
        
        if cluster_type in ['correlation', 'all']:
            correlation_clusters = await self.get_correlation_clusters()
            summary['correlation_clusters'] = correlation_clusters[:10]  # Top 10
        
        return summary
    
    def get_symbol_clusters(self, symbol: str) -> Dict[str, Any]:
        """
        Get all cluster information for a specific symbol.
        """
        basic_sector = self.get_basic_sector(symbol)
        detailed_sector = self.get_detailed_sector(symbol)
        
        return {
            'symbol': symbol,
            'basic_sector': basic_sector,
            'detailed_sector': detailed_sector,
            'basic_sector_symbols': self.BASIC_SECTORS.get(basic_sector, []),
            'detailed_sector_symbols': self.DETAILED_SECTORS.get(detailed_sector, []) if detailed_sector else []
        }

# Singleton
_clusterer_instance = None

def get_sector_clusterer() -> SectorClusterer:
    global _clusterer_instance
    if _clusterer_instance is None:
        _clusterer_instance = SectorClusterer()
    return _clusterer_instance


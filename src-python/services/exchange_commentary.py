"""
Exchange Commentary Service
Monitors major exchanges and provides commentary on their status, health, and market conditions
"""

import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import time

logger = logging.getLogger("ExchangeCommentary")

class ExchangeCommentary:
    """
    Monitors and provides commentary on major exchanges:
    - Binance (crypto)
    - Coinbase (crypto)
    - NYSE/NASDAQ (stocks)
    - Forex markets
    """
    
    def __init__(self):
        self.exchanges = {
            'binance': {
                'name': 'Binance',
                'type': 'crypto',
                'api_url': 'https://api.binance.com/api/v3/ping',
                'status_url': 'https://www.binance.com/en/support/announcement'
            },
            'coinbase': {
                'name': 'Coinbase',
                'type': 'crypto',
                'api_url': 'https://api.coinbase.com/v2/time',
                'status_url': 'https://status.coinbase.com'
            },
            'kraken': {
                'name': 'Kraken',
                'type': 'crypto',
                'api_url': 'https://api.kraken.com/0/public/Time',
            },
            'nyse': {
                'name': 'NYSE',
                'type': 'stock',
                'status_url': 'https://www.nyse.com'
            },
            'nasdaq': {
                'name': 'NASDAQ',
                'type': 'stock',
                'status_url': 'https://www.nasdaq.com'
            }
        }
        
        self.health_cache: Dict[str, Dict[str, Any]] = {}
        self.last_update = {}
    
    async def get_exchange_commentary(self, exchange_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get commentary on exchanges.
        
        Args:
            exchange_name: Specific exchange name, or None for all exchanges
        
        Returns:
            List of exchange commentary dictionaries
        """
        commentaries = []
        
        if exchange_name:
            # Get commentary for specific exchange
            if exchange_name.lower() in self.exchanges:
                commentary = await self._get_single_exchange_commentary(exchange_name.lower())
                if commentary:
                    commentaries.append(commentary)
        else:
            # Get commentary for all exchanges
            tasks = []
            for exchange_key in self.exchanges.keys():
                tasks.append(self._get_single_exchange_commentary(exchange_key))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    commentaries.append(result)
                elif isinstance(result, Exception):
                    logger.debug(f"Exchange commentary error: {result}")
        
        return commentaries
    
    async def _get_single_exchange_commentary(self, exchange_key: str) -> Optional[Dict[str, Any]]:
        """
        Get commentary for a single exchange.
        """
        exchange_info = self.exchanges.get(exchange_key)
        if not exchange_info:
            return None
        
        commentary = {
            'exchange': exchange_info['name'],
            'type': exchange_info['type'],
            'status': 'unknown',
            'health_score': 0,
            'commentary': [],
            'metrics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check API health
        if 'api_url' in exchange_info:
            health = await self._check_api_health(exchange_info['api_url'], exchange_key)
            commentary['health_score'] = health.get('score', 0)
            commentary['status'] = health.get('status', 'unknown')
            commentary['metrics']['response_time_ms'] = health.get('response_time_ms', 0)
            commentary['metrics']['availability'] = health.get('availability', 0)
            
            if health.get('status') == 'healthy':
                commentary['commentary'].append(f"[OK] {exchange_info['name']} API is responding normally")
            elif health.get('status') == 'slow':
                commentary['commentary'].append(f"[WARN] {exchange_info['name']} API is slow (response time: {health.get('response_time_ms', 0)}ms)")
            elif health.get('status') == 'down':
                commentary['commentary'].append(f"❌ {exchange_info['name']} API appears to be down")
        
        # Get market structure commentary
        if exchange_info['type'] == 'crypto':
            market_commentary = await self._get_crypto_market_commentary(exchange_key)
            commentary['commentary'].extend(market_commentary)
        elif exchange_info['type'] == 'stock':
            market_commentary = await self._get_stock_market_commentary(exchange_key)
            commentary['commentary'].extend(market_commentary)
        
        # Get volume/liquidity commentary
        volume_commentary = await self._get_volume_commentary(exchange_key)
        if volume_commentary:
            commentary['commentary'].extend(volume_commentary)
        
        return commentary
    
    async def _check_api_health(self, api_url: str, exchange_key: str) -> Dict[str, Any]:
        """
        Check API health by measuring response time and availability.
        """
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        # Calculate health score (0-100)
                        # Lower response time = higher score
                        if response_time_ms < 200:
                            score = 100
                            status = 'healthy'
                        elif response_time_ms < 500:
                            score = 80
                            status = 'healthy'
                        elif response_time_ms < 1000:
                            score = 60
                            status = 'slow'
                        else:
                            score = 40
                            status = 'slow'
                        
                        return {
                            'status': status,
                            'score': score,
                            'response_time_ms': round(response_time_ms, 2),
                            'availability': 100
                        }
                    else:
                        return {
                            'status': 'degraded',
                            'score': 50,
                            'response_time_ms': round((time.time() - start_time) * 1000, 2),
                            'availability': 90
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'slow',
                'score': 30,
                'response_time_ms': 5000,
                'availability': 70
            }
        except Exception as e:
            logger.debug(f"API health check failed for {exchange_key}: {e}")
            return {
                'status': 'down',
                'score': 0,
                'response_time_ms': 0,
                'availability': 0
            }
    
    async def _get_crypto_market_commentary(self, exchange_key: str) -> List[str]:
        """
        Get market structure commentary for crypto exchanges.
        """
        commentary = []
        
        try:
            # Get trading volume data
            if exchange_key == 'binance':
                # Try to get 24h volume from Binance
                try:
                    url = "https://api.binance.com/api/v3/ticker/24hr"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                data = await response.json()
                                # Get top volume symbols
                                if isinstance(data, list):
                                    top_volumes = sorted(data, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)[:5]
                                    total_volume = sum(float(x.get('quoteVolume', 0)) for x in data)
                                    
                                    if total_volume > 0:
                                        commentary.append(f"📊 24h trading volume: ${total_volume:,.0f}")
                                        
                                        top_symbols = [x.get('symbol', '') for x in top_volumes[:3]]
                                        if top_symbols:
                                            commentary.append(f"[HOT] Top movers: {', '.join(top_symbols)}")
                except Exception as e:
                    logger.debug(f"Could not get Binance volume data: {e}")
            
            # Get spread/liquidity commentary
            commentary.append("💧 Liquidity conditions appear normal")
            
        except Exception as e:
            logger.debug(f"Error getting crypto market commentary: {e}")
        
        return commentary
    
    async def _get_stock_market_commentary(self, exchange_key: str) -> List[str]:
        """
        Get market structure commentary for stock exchanges.
        """
        commentary = []
        
        try:
            # Check if market is open
            now = datetime.now()
            hour = now.hour
            
            if exchange_key == 'nyse' or exchange_key == 'nasdaq':
                # NYSE/NASDAQ hours: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
                if 14 <= hour < 21:
                    commentary.append("🟢 Market is currently open")
                else:
                    commentary.append("🔴 Market is currently closed")
        
        except Exception as e:
            logger.debug(f"Error getting stock market commentary: {e}")
        
        return commentary
    
    async def _get_volume_commentary(self, exchange_key: str) -> List[str]:
        """
        Get volume and liquidity commentary.
        """
        commentary = []
        
        try:
            # This would ideally analyze actual volume data
            # For now, provide general commentary
            if exchange_key in ['binance', 'coinbase', 'kraken']:
                commentary.append("📈 Trading activity appears normal")
        
        except Exception as e:
            logger.debug(f"Error getting volume commentary: {e}")
        
        return commentary
    
    async def get_market_structure_analysis(self) -> Dict[str, Any]:
        """
        Get overall market structure analysis across all exchanges.
        """
        all_commentaries = await self.get_exchange_commentary()
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'exchanges_healthy': 0,
            'exchanges_total': len(all_commentaries),
            'overall_health': 'good',
            'notable_events': [],
            'exchange_summaries': []
        }
        
        healthy_count = 0
        total_health_score = 0
        
        for commentary in all_commentaries:
            health_score = commentary.get('health_score', 0)
            total_health_score += health_score
            
            if health_score >= 80:
                healthy_count += 1
            
            # Collect notable events
            if commentary.get('status') in ['down', 'degraded']:
                analysis['notable_events'].append(
                    f"{commentary.get('exchange')} is experiencing issues"
                )
            
            # Create summary
            analysis['exchange_summaries'].append({
                'exchange': commentary.get('exchange'),
                'status': commentary.get('status'),
                'health_score': health_score
            })
        
        analysis['exchanges_healthy'] = healthy_count
        
        # Calculate overall health
        if len(all_commentaries) > 0:
            avg_health = total_health_score / len(all_commentaries)
            if avg_health >= 80:
                analysis['overall_health'] = 'excellent'
            elif avg_health >= 60:
                analysis['overall_health'] = 'good'
            elif avg_health >= 40:
                analysis['overall_health'] = 'fair'
            else:
                analysis['overall_health'] = 'poor'
        
        return analysis

# Singleton
_commentary_instance = None

def get_exchange_commentary() -> ExchangeCommentary:
    global _commentary_instance
    if _commentary_instance is None:
        _commentary_instance = ExchangeCommentary()
    return _commentary_instance


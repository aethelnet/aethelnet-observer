"""
Investing.com Economic Calendar Provider
Fetches economic events from Investing.com for consensus comparison.
"""
import aiohttp
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time as time_mod

logger = logging.getLogger("InvestingCalendar")

# Sector keyword mapping (shared with ForexFactory)
SECTOR_KEYWORDS = {
    "MACRO": ["GDP", "CPI", "FED", "FOMC", "INFLATION", "EMPLOYMENT", "INTEREST", "TREASURY", 
              "PMI", "RATE", "PAYROLL", "CONSUMER", "RETAIL", "HOUSING", "DURABLE", "JOBLESS"],
    "CRYPTO": ["BITCOIN", "CRYPTO", "ETF", "DIGITAL", "BLOCKCHAIN", "BTC", "ETHEREUM", "SEC"],
    "TECH": ["TECH", "EARNINGS", "NASDAQ", "MANUFACTURING", "INDUSTRIAL", "FACTORY"],
    "FOREX": ["EUR", "USD", "JPY", "GBP", "CAD", "AUD", "NZD", "CHF", "ECB", "BOE", "BOJ", "CENTRAL BANK", "CURRENCY"]
}


class InvestingCalendar:
    """
    Fetches economic calendar from Investing.com.
    Uses web scraping as they don't have a public API.
    """
    BASE_URL = "https://www.investing.com/economic-calendar/"
    
    def __init__(self):
        self._cache: List[Dict] = []
        self._last_fetch = 0
        self._cache_ttl = 14400  # 4 hours
        self._min_fetch_interval = 1800  # 30 min
        
    def _auto_tag_sector(self, title: str) -> str:
        """Auto-detect sector from event title."""
        title_upper = title.upper()
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw in title_upper for kw in keywords):
                return sector
        return "MACRO"
    
    def _parse_economic_value(self, value_str: str) -> Optional[float]:
        """Parse economic value strings."""
        if not value_str or value_str.strip() in ['N/A', '', '-', '...']:
            return None
        
        value_str = value_str.strip().upper()
        multiplier = 1.0
        
        if value_str.endswith('%'):
            value_str = value_str[:-1]
        elif value_str.endswith('K'):
            value_str = value_str[:-1]
            multiplier = 1000
        elif value_str.endswith('M'):
            value_str = value_str[:-1]
            multiplier = 1_000_000
        elif value_str.endswith('B'):
            value_str = value_str[:-1]
            multiplier = 1_000_000_000
            
        try:
            return float(value_str.replace(',', '')) * multiplier
        except ValueError:
            return None

    async def fetch_calendar(self) -> None:
        """Fetches calendar data from Investing.com."""
        now = time_mod.time()
        
        if now - self._last_fetch < self._min_fetch_interval and self._cache:
            logger.debug("[INVESTING] Skipping fetch - within rate limit window")
            return
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.investing.com/",
        }
        
        try:
            # Calculate date range (this week)
            today = datetime.utcnow()
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=6)  # Sunday
            
            url = f"{self.BASE_URL}"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        html = await response.text()
                        self._parse_html(html)
                        self._last_fetch = now
                        logger.info(f"[INVESTING] Fetched {len(self._cache)} events")
                    elif response.status == 403:
                        logger.warning("[INVESTING] Blocked (403). Using cached data.")
                    else:
                        logger.warning(f"[INVESTING] Status {response.status}")
        except asyncio.TimeoutError:
            logger.warning("[INVESTING] Timeout. Using cached data.")
        except Exception as e:
            logger.warning(f"[INVESTING] Fetch error: {e}")
    
    def _parse_html(self, html: str) -> None:
        """Parses Investing.com calendar HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            events = []
            
            # Find calendar table rows
            table = soup.find('table', {'id': 'economicCalendarData'})
            if not table:
                # Try alternative selector
                table = soup.find('table', class_=re.compile(r'genTbl.*'))
            
            if not table:
                logger.warning("[INVESTING] Could not find calendar table")
                return
                
            rows = table.find_all('tr', class_=re.compile(r'js-event-item'))
            
            current_date = None
            
            for row in rows:
                try:
                    # Extract date (might be in a header row)
                    date_cell = row.find('td', class_='date')
                    if date_cell and date_cell.text.strip():
                        current_date = self._parse_date(date_cell.text.strip())
                    
                    # Extract time
                    time_cell = row.find('td', class_='time')
                    time_str = time_cell.text.strip() if time_cell else ''
                    
                    # Extract country
                    flag = row.find('td', class_='flagCur')
                    country = ''
                    if flag:
                        span = flag.find('span')
                        if span and span.get('title'):
                            country = span.get('title', '')[:3].upper()
                    
                    # Extract event title
                    event_cell = row.find('td', class_='event')
                    title = event_cell.text.strip() if event_cell else 'Unknown'
                    
                    # Extract impact (stars)
                    impact_cell = row.find('td', class_='sentiment')
                    impact = 'Low'
                    if impact_cell:
                        bulls = impact_cell.find_all('i', class_='grayFullBullishIcon')
                        if len(bulls) >= 3:
                            impact = 'High'
                        elif len(bulls) >= 2:
                            impact = 'Medium'
                    
                    # Extract actual, forecast, previous
                    actual_cell = row.find('td', class_='act')
                    forecast_cell = row.find('td', class_='fore')
                    previous_cell = row.find('td', class_='prev')
                    
                    actual = actual_cell.text.strip() if actual_cell else ''
                    forecast = forecast_cell.text.strip() if forecast_cell else ''
                    previous = previous_cell.text.strip() if previous_cell else ''
                    
                    # Calculate surprise
                    surprise = None
                    actual_val = self._parse_economic_value(actual)
                    forecast_val = self._parse_economic_value(forecast)
                    if actual_val is not None and forecast_val is not None:
                        surprise = actual_val - forecast_val
                    
                    if current_date and title != 'Unknown':
                        events.append({
                            'title': title,
                            'country': country,
                            'date': current_date,
                            'time': time_str,
                            'impact': impact,
                            'forecast': forecast,
                            'previous': previous,
                            'actual': actual,
                            'surprise': surprise,
                            'sector': self._auto_tag_sector(title),
                            'source': 'investing',
                            'timestamp': self._to_timestamp(current_date, time_str)
                        })
                except Exception as e:
                    continue
                    
            self._cache = events
            
        except Exception as e:
            logger.error(f"[INVESTING] HTML Parsing Error: {e}")
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY-MM-DD format."""
        try:
            # Try common formats
            for fmt in ['%b %d, %Y', '%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return datetime.utcnow().strftime('%Y-%m-%d')
        except:
            return datetime.utcnow().strftime('%Y-%m-%d')
    
    def _to_timestamp(self, date_str: str, time_str: str) -> int:
        """Convert to Unix timestamp."""
        try:
            # Try to parse time
            if time_str and ':' in time_str:
                full_str = f"{date_str} {time_str}"
                for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d %I:%M%p', '%Y-%m-%d %I:%M %p']:
                    try:
                        dt = datetime.strptime(full_str, fmt)
                        return int(dt.timestamp())
                    except ValueError:
                        continue
            # Fallback: just date
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return int(dt.timestamp())
        except:
            return 0
    
    async def get_events(self, limit: int = 50) -> List[Dict]:
        """Returns cached events."""
        now_ts = time_mod.time()
        
        if now_ts - self._last_fetch > self._cache_ttl or not self._cache:
            await self.fetch_calendar()
            
        return self._cache[:limit]
    
    def get_cached_events(self) -> List[Dict]:
        """Returns cached events without fetching."""
        return self._cache


# Singleton
_investing_instance = None

def get_investing_calendar():
    global _investing_instance
    if _investing_instance is None:
        _investing_instance = InvestingCalendar()
    return _investing_instance

import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
import threading

logger = logging.getLogger("YahooConnector")
# Silence yfinance board spam (Internal JSON error blobs)
logging.getLogger('yfinance').setLevel(logging.CRITICAL)


class YahooConnector:
    """
    The Bridge to Traditional Finance.
    Wraps 'yfinance' to provide data in the same format as Binance Client.
    """
    
    def __init__(self):
        self._lock = threading.Lock()

    def get_historical_klines(self, symbol: str, interval: str, start_str: str, end_str: str = None) -> list:
        """
        Mimics Binance's get_historical_klines but for Yahoo Finance.
        Returns list of lists: [timestamp, open, high, low, close, volume, ...]
        """
        # 1. Map Interval
        # Binance: 1m, 5m, 1h, 1d
        # Yahoo: 1m, 5m, 1h, 1d
        if interval == '1m': yf_interval = '1m'
        elif interval == '5m': yf_interval = '5m'
        elif interval == '1h': yf_interval = '1h'
        elif interval == '1d': yf_interval = '1d'
        else: yf_interval = '1d' # Default
        
        # 2. Map Dates
        # valid formats: '1 Jan 2020', '2020-01-01'
        # yfinance expects YYYY-MM-DD
        # We need to parse strict Binance strings usually passed here using dateparser or generic
        # Ideally, we convert start_str to datetime object first
        
        try:
            # Flexible parsing
            start_dt = pd.to_datetime(start_str)
            end_dt = pd.to_datetime(end_str) if end_str else datetime.utcnow()
        except:
            logger.error(f"Failed to parse dates: {start_str} - {end_str}")
            return []

        logger.info(f"Fetching {symbol} from Yahoo ({start_dt} -> {end_dt})")
        
        # 3. Fetch
        # yfinance download
        try:
            df = yf.download(
                tickers=symbol,
                start=start_dt,
                end=end_dt,
                interval=yf_interval,
                progress=False,
                auto_adjust=False # We want raw OHLC usually, or adjusted? 
                # Traders usually trade raw price for constraints, but for history adjusted is better for splits.
                # Crypto doesn't split. Stocks do. Let's use Auto Adjust = True usually for backtest PnL?
                # But 'close' vs 'adj close'... let's stick to standard OHLC.
            )
            
            if df.empty:
                logger.debug(f"Yahoo: No data found for {symbol}")
                return []
                
            # 4. Format to "Binance-like" list of lists
            # [timestamp, open, high, low, close, volume, close_time, ...]
            # Yahoo index is Datetime
            
            output = []
            for index, row in df.iterrows():
                # Timestamp in ms
                ts = int(index.timestamp() * 1000)
                
                # Handling multi-level headers if multiple tickers (shouldn't happen here)
                # Helper to safely extract scalar from potentially weird yfinance row
                def get_val(r, key):
                     try:
                         val = r[key]
                         # Check if it has .iloc (Series)
                         if hasattr(val, 'iloc'):
                             return float(val.iloc[0])
                         return float(val)
                     except:
                         return 0.0

                try:
                    # Try UpperCase first (Standard)
                    o = get_val(row, 'Open')
                    h = get_val(row, 'High')
                    l = get_val(row, 'Low')
                    c = get_val(row, 'Close')
                    v = get_val(row, 'Volume')
                    
                    # If all zero, try lowercase
                    if o == 0 and c == 0:
                        o = get_val(row, 'open')
                        h = get_val(row, 'high')
                        l = get_val(row, 'low')
                        c = get_val(row, 'close')
                        v = get_val(row, 'volume')
                except:
                    o, h, l, c, v = 0, 0, 0, 0, 0
                
                # Binance columns:
                # 0: Open time
                # 1: Open
                # 2: High
                # 3: Low
                # 4: Close
                # 5: Volume
                # 6: Close time (approx Open + interval)
                # ...
                
                record = [
                    ts, # 0
                    o, # 1
                    h, # 2
                    l, # 3
                    c, # 4
                    v, # 5
                    ts + 60000, # 6 (Dummy close time for 1m)
                    0, 0, 0, 0, 0 # Ignore rest
                ]
                output.append(record)
                
            return output
            
        except Exception as e:
            logger.error(f"YFinance Error: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        """
        Fetches the single latest price for a stock/ETF.
        """
        with self._lock:
            try:
                # yfinance Request
                # 'period=1d' and 'interval=1m' is efficient
                # ARGUMENT UPDATE: 'auto_adjust' defaults to True in future versions.
                # We explicitly set it to False to keep current behavior consistent if desired,
                # but yfinance warns usually if we don't handle it at all. 
                # Or we can accept default. Let's set auto_adjust=True to be future-proof for price history.
                df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
                if df.empty: 
                    logger.debug(f"Yahoo: No price data for {symbol}")
                    return 0.0

                
                # Get last row 'Close'
                last_row = df.iloc[-1]
                
                try:
                    # FIXED: Access safely for scalar or Series
                    val = last_row['Close']
                    if hasattr(val, 'iloc'):
                        price = float(val.iloc[0])
                    else:
                        price = float(val)
                    
                    # [DEBUG] TRAP THE GHOST ($99.37)
                    if 99.30 < price < 99.45:
                         logger.critical(f"[GHOST TRAP] {symbol} returned {price}. DF Cols: {df.columns}. Raw Val: {val}")
                         
                except:
                    # Try handling if it's a Series/Scalar confusion
                    price = float(last_row.iloc[0]) if hasattr(last_row, 'iloc') else float(last_row) # fallback?
                
                return price
            except Exception as e:
                # logger.error(f"Yahoo Price Fetch Error for {symbol}: {e}")
                return 0.0

    def get_ticker_stats(self, symbol: str) -> dict:
        """
        Fetch detailed 24h stats for a stock.
        Returns dict matching Binance format: price, change_pct, high, low, volume, quote_volume.
        """
        try:
            ticker = yf.Ticker(symbol)
            # Get 2 days of history to calculate change
            hist = ticker.history(period="5d") # 5d to handle weekends safer
            
            if hist.empty:
                logger.debug(f"Yahoo: No ticker stats for {symbol}")
                return None
                
            # Latest candle
            current = hist.iloc[-1]
            
            # Helper to safely extract float
            def safe_float(val):
                if hasattr(val, 'iloc'):
                    return float(val.iloc[0])
                return float(val)

            price = safe_float(current['Close'])
            
            # Previous Close (for change calculation)
            if len(hist) >= 2:
                prev_close = safe_float(hist.iloc[-2]['Close'])
                change_pct = ((price - prev_close) / prev_close) * 100
            else:
                change_pct = 0.0

            return {
                'price': price,
                'change_pct': change_pct,
                'high': safe_float(current['High']),
                'low': safe_float(current['Low']),
                'volume': safe_float(current['Volume']),
                'quote_volume': safe_float(current['Volume']) * price, # Est. Dollar Volume
                'trades': 0 # Yahoo doesn't give trade count easily
            }
        except Exception as e:
            logger.error(f"Yahoo Ticker Stats Error for {symbol}: {e}")
            return None

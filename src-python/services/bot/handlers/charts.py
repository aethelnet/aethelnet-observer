import asyncio
import pandas as pd
import logging
import time
import io
from datetime import datetime
from services.bot.handlers.base import BaseHandler
from services.data_manager import get_data_manager
from services.chart_generator import get_chart_generator
from services.opportunity_cache import get_opportunity_cache

logger = logging.getLogger("TelegramBot")

class ChartsHandler(BaseHandler):
    async def _get_klines_for_chart(self, symbol: str, limit_hours: int = 72) -> list:
        try:
            dm = get_data_manager()
            # Extended Alias Map for Yahoo Fallback
            YAHOO_MAP = {
                'BTCUSDT': 'BTC-USD', 'ETHUSDT': 'ETH-USD', 'SOLUSDT': 'SOL-USD',
                'XAUUSDT': 'GC=F', 'XAUUSD': 'GC=F', 'GOLD': 'GC=F',
                'XAGUSDT': 'SI=F', 'XAGUSD': 'SI=F', 'SILVER': 'SI=F',
                'EURUSDT': 'EUR=X', 'GBPUSDT': 'GBP=X', 'JPYUSDT': 'JPY=X',
                'SPX': '^GSPC', 'NDX': '^IXIC', 'US30': '^DJI', 'DXY': 'DX-Y.NYB'
            }
            
            # Helper to detect TradFi
            def is_tradfi(s):
                return len(s) <= 4 or "^" in s or "=" in s or s in ['SPX', 'NDX', 'VIX', 'DXY']

            target_symbol = YAHOO_MAP.get(symbol, symbol)
            
            # Time Window
            end_ms = int(time.time() * 1000)
            start_ms = end_ms - (limit_hours * 60 * 60 * 1000)
            
            # METHOD 1: Binance (Primary for Crypto)
            if not is_tradfi(symbol) and "USDT" in symbol:
                try:
                    # Try synchronous fetch wrapped in thread
                    data = await asyncio.to_thread(dm.client.get_historical_klines, symbol, '1h', start_ms, end_ms)
                    if data and len(data) > 10:
                        return data
                except Exception as e:
                    logger.warning(f"Binance fetch failed for {symbol}, trying fallback: {e}")

            # METHOD 2: Yahoo Finance (Fallback & TradFi)
            # Adjust start/end for Yahoo (requires string dates usually or specific timestamp format)
            # Wrapper likely handles timestamps, but let's be safe
            try:
                # Yahoo often needs format YYYY-MM-DD for get_historical_klines wrapper in data_manager
                s_dt = datetime.fromtimestamp(start_ms/1000).strftime('%Y-%m-%d')
                e_dt = datetime.fromtimestamp(end_ms/1000 + 86400).strftime('%Y-%m-%d')
                
                # Check if we need to swap symbol for Yahoo
                y_symbol = YAHOO_MAP.get(symbol, symbol)
                if y_symbol == symbol and "USDT" in symbol:
                     y_symbol = symbol.replace("USDT", "-USD")
                
                data = await asyncio.to_thread(dm.yahoo.get_historical_klines, y_symbol, '1h', s_dt, e_dt)
                if data: return data
            except Exception as e:
                logger.error(f"Yahoo fallback failed for {symbol}: {e}")
                
            return []
        except Exception as e:
            logger.error(f"Chart Data Handle Error: {e}")
            return []

    async def send_chart(self, chat_id: int, symbol: str):
        # 1. Send "Loading" feedback immediately (The "Loading Window")
        status_msg = await self.bot.send_message(chat_id, f"<b>[LOAD] Drawing Market Structure: {symbol}...</b>")
        status_msg_id = status_msg.get("result", {}).get("message_id") if isinstance(status_msg, dict) else None

        try:
            # 2. Fetch Data
            klines = await self._get_klines_for_chart(symbol)
            
            # (Logic continues but using status_msg_id for error feedback)
            if not klines or len(klines) < 20:
                if status_msg_id: await self.bot.edit_message_text(chat_id, status_msg_id, f"[!] Insufficient data for {symbol}.")
                return

            # 3. Process Data
            df = pd.DataFrame(klines).iloc[:, :6]
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') # Ensure datetime
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # 4. Config Chart
            extra_lines = []
            zones = []
            chart_title = f"{symbol} • 72H Structure"
            
            # Fetch Context
            cache = get_opportunity_cache()
            active_opp = cache.get_opportunity(symbol)
            if active_opp:
                side = active_opp.get('opportunity_type', 'NEUTRAL')
                chart_title = f"{symbol} • {side} SETUP"
                
                # Plot Entry/Target/Stop
                if 'entry_price_min' in active_opp:
                     zones.append({'y_min': active_opp['entry_price_min'], 'y_max': active_opp['entry_price_max'], 'color': '#00a800', 'alpha': 0.15, 'label': 'ENTRY'})
                if 'target_price' in active_opp:
                     extra_lines.append({'y': active_opp['target_price'], 'color': '#00ff00', 'style': '--', 'label': 'TARGET'})
                if 'stop_loss_price' in active_opp:
                     extra_lines.append({'y': active_opp['stop_loss_price'], 'color': '#ff0000', 'style': '--', 'label': 'STOP'})

            gen = get_chart_generator()
            chart_img = await asyncio.to_thread(
                gen.generate_chart, 
                symbol,
                df, 
                title=chart_title,
                extra_lines=extra_lines,
                zones=zones
            )
            
            if chart_img:
                # chart_img is already a BytesIO buffer
                chart_img.seek(0)
                
                # Delete status message
                await self.bot.delete_message(chat_id, status_msg_id)
                
                # Send Photo
                await self.bot.send_photo(chat_id, photo=chart_img, caption=f"<b>{symbol} Market Structure</b>\n<i>Generated via Auratic Visual Engine</i>", parse_mode="HTML")
            else:
                 await self.bot.edit_message_text(chat_id, status_msg_id, "[!] Failed to render chart.")

        except Exception as e:
            logger.error(f"Chart Gen Error: {e}")
            await self.bot.edit_message_text(chat_id, status_msg_id, f"[!] Error prompting visual engine: {e}")

    async def handle_chart_command(self, chat_id: int, args: list):
        """Handle /chart command."""
        if not args:
            msg = "Usage: /chart <SYMBOL> (e.g. /chart BTC)"
            await self.send_message(chat_id, msg)
            return

        from services.symbol_normalizer import get_symbol_normalizer
        normalizer = get_symbol_normalizer()
        
        raw_symbol = args[0].upper()
        clean_symbol = normalizer.sanitize(raw_symbol)
        
        if not clean_symbol:
            await self.send_message(chat_id, "[X] Invalid symbol format.")
            return

        await self.send_chart(chat_id, clean_symbol)

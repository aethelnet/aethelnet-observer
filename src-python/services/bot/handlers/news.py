
from services.bot.handlers.base import BaseHandler
from services.bot.formatters import format_news

class NewsHandler(BaseHandler):
    async def handle_news(self, chat_id: int, symbol: str = None, sector: str = None, message_id: int = None):
        try:
            # --- AUTO-DETECTION ---
            # If user types /news forex, detect it's a sector, not a ticker.
            sectors = ["MACRO", "CRYPTO", "TECH", "FOREX", "STOCKS"]
            if symbol and symbol.upper() in sectors:
                sector = symbol.upper()
                symbol = None

            url = "/api/news"
            if symbol:
                url += f"?symbol={symbol.upper()}"
            elif sector:
                # Map News Sectors to API Search Categories
                # Category tags like CAT_TECH, CAT_MACRO, etc.
                url += f"?symbol=CAT_{sector.upper()}"
            
            news_items = await self.fetch_api(url)
            items = news_items if isinstance(news_items, list) else []
            
            # Dynamic Title
            if symbol: title = f"[ NEWS ] {symbol.upper()}"
            elif sector: title = f"[ NEWS ] {sector.upper()}"
            else: title = "[ MARKET NEWS ]"
            
            if not items:
                message = (
                    f"<b>{title}</b>\n"
                    "<code>════════════════════════════════</code>\n\n"
                    "<i>No recent news affecting this sector.</i>\n\n"
                    "<b>[TIP]</b> Low news = less volatility.\n"
                    "Good for steady trend-following strategies.\n\n"
                    "<code>════════════════════════════════</code>"
                )
            else:
                message = (
                    f"<b>{title}</b>\n"
                    "<code>════════════════════════════════</code>\n\n"
                )
                
                for item in items[:8]:
                    headline = item.get('title', 'News')
                    if len(headline) > 85:
                        headline = headline[:82] + "..."
                    
                    url = item.get('url') or item.get('link') or "#"
                    source = item.get('source', 'Intel')[:15]
                    sentiment = item.get('sentiment', 0)
                    
                    # Sentiment icon
                    if sentiment > 0.3:
                        icon = "[+]"
                    elif sentiment < -0.3:
                        icon = "[-]"
                    else:
                        icon = "[~]"
                    
                    message += f"{icon} <a href='{url}'>{headline}</a>\n"
                    message += f"   <i>({source})</i>\n"
                
                message += (
                    "\n<code>════════════════════════════════</code>\n"
                    "<b>Conviction:</b> [+]=Bullish [-]=Bearish [~]=Neutral\n"
                    "<i>Tap headlines to open full thread</i>"
                )
            
            # Navigation
            if symbol:
                keyboard = {"inline_keyboard": [
                    [{"text": f"« BACK TO {symbol.upper()}", "callback_data": f"PRICE_{symbol.upper()}"}],
                    self._get_home_button()
                ]}
            else:
                # Main Hub with Sector Buttons
                keyboard = {"inline_keyboard": [
                    [
                        {"text": "◆ MACRO", "callback_data": "NEWS_CAT_MACRO"},
                        {"text": "◈ CRYPTO", "callback_data": "NEWS_CAT_CRYPTO"},
                    ],
                    [
                        {"text": "▽ TECH", "callback_data": "NEWS_CAT_TECH"},
                        {"text": "⇄ FOREX", "callback_data": "NEWS_CAT_FOREX"}
                    ],
                    [{"text": "⟳ REFRESH", "callback_data": "NEWS_GLOBAL"}],
                    self._get_cyclical_nav("NEWS")
                ]}
            
            if message_id:
                await self.bot.edit_message_text(chat_id, message_id, message, reply_markup=keyboard, disable_web_page_preview=True)
            else:
                await self.bot.send_message(chat_id, message, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as e:
            self.logger.error(f"News error: {e}")
            await self.send_message(chat_id, "[ NEWS ] <i>News temporarily unavailable. Try again soon.</i>")

    async def handle_verify(self, chat_id: int, symbol: str):
        if not symbol:
            await self.send_message(chat_id, "Usage: /verify <SYMBOL>")
            return
            
        try:
            data = await self.fetch_api(f"/api/verification/symbol/{symbol.upper()}")
            if not data:
                await self.send_message(chat_id, f"[X] No data for {symbol}")
                return
                
            sentiment = data.get('sentiment', {})
            alignment = data.get('alignment', 'NEUTRAL')
            
            # Alignment icon
            if 'BUY' in alignment or 'BULL' in alignment:
                icon = "[+]"
            elif 'SELL' in alignment or 'BEAR' in alignment:
                icon = "[-]"
            else:
                icon = "[~]"
            
            message = (
                f"<b>[ CHECK ] : {symbol.upper()}</b>\n"
                "<code>════════════════════════════════</code>\n\n"
                f"<b>Sentiment Score:</b> <code>{sentiment.get('weighted_sentiment', 0):.2f}</code>\n"
                f"<b>Alignment:</b> {icon} <code>{alignment}</code>\n\n"
                "<b>[TIP]</b> Higher scores = stronger conviction\n"
                "<code>════════════════════════════════</code>"
            )
            
            await self.send_message(chat_id, message)
        except Exception:
            await self.send_message(chat_id, "[OK] <i>Verification temporarily unavailable.</i>")



from services.bot.handlers.base import BaseHandler
from services.bot.formatters import format_market_summary # reusing parts if needed

class MLHandler(BaseHandler):
    async def handle_predictions(self, chat_id: int, symbol: str = None):
        # Reuse handle_market_update logic but filter output?
        # Or explicit fetch.
        # format_market_summary handles predictions.
        # I'll create a simple loop and format manually if simple.
        # Or I missed format_predictions_list in formatters.py.
        # I'll use format_symbol_details if symbol is present.
        
        try:
            url = "/api/predictions"
            if symbol: url += f"?symbol={symbol.upper()}"
            
            preds = await self.fetch_api(url)
            if not preds:
                 await self.send_message(chat_id, "No predictions.")
                 return
                 
            message = (
                "<b>[ MARKET PROGNOSIS ]</b>\n"
                "<code>════════════════════════════════</code>\n\n"
            )
            
            items = preds if isinstance(preds, list) else [preds]
            count = 0
            for item in items[:5]:
                sym = item.get('symbol')
                ps = item.get('predictions', [])
                if ps:
                    best = ps[0]
                    direction = best.get('direction', 'NEUTRAL')
                    price = best.get('predicted_price', 0)
                    
                    icon = "[+]" if direction == "UP" else "[-]" if direction == "DOWN" else "[=]"
                    message += f"{icon} <b>{sym}</b> → <code>${price:,.2f}</code>\n"
                    count += 1
            
            if count == 0:
                message += "<i>No strong predictions active.</i>\n"
                
            message += (
                "\n<code>════════════════════════════════</code>\n"
                "<b>[TIP]</b> Predictions are probabilities, not certainties.\n"
                "<i>Combine with your own research.</i>"
            )
            
            keyboard = {"inline_keyboard": [self._get_cyclical_nav("OPPS")]}
            await self.bot.send_message(chat_id, message, reply_markup=keyboard)
        except Exception:
            await self.send_message(chat_id, "[X] Predictions failed.")

    async def handle_opportunities(self, chat_id: int, symbol: str = None, message_id: int = None):
        try:
            url = "/api/opportunities"
            if symbol: url += f"?symbol={symbol.upper()}"
            
            opps = await self.fetch_api(url)
            items = opps if isinstance(opps, list) else [opps] if opps else []
            
            if not items:
                message = (
                    "<b>[ OPPORTUNITY SCAN ]</b>\n"
                    "<code>════════════════════════════════</code>\n\n"
                    "<i>No high-confidence setups detected right now.</i>\n\n"
                    "The AI continuously scans for:\n"
                    "• Mean reversion setups\n"
                    "• Trend continuations\n"
                    "• Volume breakouts\n\n"
                    "<code>════════════════════════════════</code>\n"
                    "<i>Check back soon or explore prices</i>"
                )
            else:
                message = (
                    "<b>[ OPPORTUNITY SCAN ]</b>\n"
                    "<code>════════════════════════════════</code>\n\n"
                    f"<b>{len(items[:5])} Active Setup(s)</b>\n\n"
                )
                
                for item in items[:5]:
                    sym = item.get('symbol', 'N/A')
                    otype = item.get('opportunity_type', 'Detection')
                    conf = int(item.get('confidence', 0) * 100)
                    
                    # Emoji based on type
                    if 'BUY' in otype.upper() or 'REVERSAL' in otype.upper():
                        icon = "[+]"
                    elif 'SELL' in otype.upper():
                        icon = "[-]"
                    else:
                        icon = "[~]"
                    
                    message += f"{icon} <b>{sym}</b>: {otype} ({conf}%)\n"
                
                message += (
                    "\n<code>════════════════════════════════</code>\n"
                    "<i>Tap symbol buttons for details</i>"
                )
            
            # Navigation keyboard
            keyboard = [
                [{"text": "[ PRICES ]", "callback_data": "PRICE_LANDING"}],
                self._get_cyclical_nav("OPPS")
            ]
            
            if message_id:
                await self.bot.edit_message_text(chat_id, message_id, message, reply_markup={"inline_keyboard": keyboard})
            else:
                await self.bot.send_message(chat_id, message, reply_markup={"inline_keyboard": keyboard})
                
        except Exception as e:
            self.logger.error(f"Opportunities failed: {e}")
            await self.send_message(chat_id, "[X] Scan temporarily unavailable.")

    async def handle_physics(self, chat_id: int, symbol: str = None):
        # Similar logic
        # Physics data is embedded in predictions response usually
        await self.handle_predictions(chat_id, symbol)

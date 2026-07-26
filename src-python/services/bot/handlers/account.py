
import asyncio
from services.bot.handlers.base import BaseHandler
from services.bot.formatters import format_wallet_summary, format_positions, format_trades, format_shadow_status

class AccountHandler(BaseHandler):
    async def handle_wallet(self, chat_id: int):
        # === SECURITY GATE ===
        if not self.is_admin(chat_id):
            await self.send_message(chat_id, "<b>[ ! ] ACCESS DENIED</b>\n\n<i>Administrator credentials required for Financial Ops.</i>")
            return
        
        try:
            # DIRECT CALL - Bypass HTTP to avoid loopback failures
            from api.wallet import get_wallet_summary
            wallet_data = await get_wallet_summary()
            
            message = format_wallet_summary(wallet_data)
            
            # Navigation Matrix
            keyboard = {"inline_keyboard": [
                [
                    {"text": "[ POSITIONS ]", "callback_data": "POSITIONS"},
                    {"text": "[ HISTORY ]", "callback_data": "HISTORY_LOG"},
                    {"text": "[ SYNC ]", "callback_data": "WALLET_SYNC"}
                ],
                [
                    {"text": "[ SHADOW AUDIT ]", "callback_data": "SHADOW_STATUS"}
                ],
                self._get_home_button()
            ]}
            await self.bot.send_message(chat_id, message, reply_markup=keyboard)
        except Exception as e:
            import traceback
            self.logger.error(f"Wallet error: {e}\n{traceback.format_exc()}")
            await self.send_message(chat_id, "[ WALLET ] <i>Wallet data temporarily unavailable.</i>")

    async def handle_positions(self, chat_id: int):
        # === SECURITY GATE ===
        if not self.is_admin(chat_id):
            await self.send_message(chat_id, "<b>[ ! ] ACCESS DENIED</b>\n\n<i>Administrator credentials required for Tactical Audit.</i>")
            return
        
        try:
            # DIRECT CALL - Bypass HTTP
            from api.dashboard import get_positions
            positions = await get_positions()
            # Reuse logic or call enhanced formatters if available
            positions_list = positions if isinstance(positions, list) else []
            
            # --- AG: ENRICH WITH LIVE DATA ---
            # Positions from tracker don't have current price/pnl. We must inject it.
            if positions_list:
                from services.data_manager import get_data_manager
                import time
                dm = get_data_manager()
                
                # Fetch stats for all symbols in parallel (or just loop for now as it's likely few)
                for pos in positions_list:
                    symbol = pos.get('symbol')
                    if not symbol: continue
                    
                    # Fetch live stats
                    stats = await asyncio.to_thread(dm.get_ticker_stats, symbol)
                    current_price = 0.0
                    
                    if stats:
                        current_price = stats.get('price', stats.get('last_price', 0.0))
                    
                    if current_price > 0:
                        pos['current_price'] = current_price
                        entry = pos.get('entry_price', 0)
                        qty = pos.get('quantity', 0)
                        # Calculate PnL: (Current - Entry) * Qty (Works for neg qty SHORT too)
                        # Actually standard: 
                        # LONG (qty>0): (Curr - Entry) * Qty
                        # SHORT (qty<0): (Entry - Curr) * abs(Qty) = (Entry - Curr) * -Qty = (Curr - Entry) * Qty
                        # So the formula (Curr - Entry) * Qty works for both if Qty is signed.
                        # BUT tracker stores size as unsigned usually? No, tracker.py says:
                        # "quantity": float(p.get("quantity", p.get("qty", 0.0)))
                        # And terminal says: Q = -amt/price for SELL. So Quantity is signed.
                        
                        pos['unrealized_pnl'] = (current_price - entry) * qty
                        
                        # Add hold time if missing
                        if 'hold_time_seconds' not in pos and 'entry_time' in pos:
                            pos['hold_time_seconds'] = time.time() - pos['entry_time']
                            
            message = format_positions(positions_list)
            
            keyboard = {"inline_keyboard": [self._get_home_button()]}
            await self.bot.send_message(chat_id, message, reply_markup=keyboard)
        except Exception as e:
            self.logger.error(f"Positions error: {e}")
            await self.send_message(chat_id, "<b>[ ! ]</b> <i>Active positions data unavailable.</i>")

    async def handle_trades(self, chat_id: int, limit: int = 10):
        self.logger.error(f"!!! DEBUG: HANDLER_TRADES CALLED for {chat_id} !!!")
        if not self.is_admin(chat_id):
            await self.send_message(chat_id, "<b>[ ! ] ACCESS DENIED</b>\n\n<i>Administrator credentials required for Forensic Log access.</i>")
            return
        
        # --- TEST SIGNAL (USER REQ) ---
        await self.send_message(chat_id, "<b>[ 🚨 ] DEBUG SIGNAL: HISTORY BUTTON CLICKED</b>\n<i>Functionality linked. Fetching rows...</i>")

        try:
            from services.trade_logger import get_archive
            archive = get_archive()
            trades = archive.get_recent_trades(limit=limit)
            message = format_trades(trades, limit=limit)
            
            keyboard = {"inline_keyboard": [
                [{"text": "« BACK", "callback_data": "WALLET_STATS"}],
                self._get_nav_row()
            ]}
            await self.bot.send_message(chat_id, message, reply_markup=keyboard)
        except Exception as e:
            self.logger.error(f"Trades error: {e}")
            await self.send_message(chat_id, "[ ! ] <i>Historical trade log unavailable.</i>")
    async def handle_shadow(self, chat_id: int):
        # === SECURITY GATE ===
        if not self.is_admin(chat_id):
            await self.send_message(chat_id, "<b>[ ! ] ACCESS DENIED</b>\n\n<i>Administrator credentials required for Shadow Audit.</i>")
            return
        
        try:
            # DIRECT CALL - Bypass HTTP
            from api.dashboard import get_shadow_status
            shadow = await get_shadow_status()
            message = format_shadow_status(shadow)
            
            keyboard = {"inline_keyboard": [
                [{"text": "« BACK", "callback_data": "WALLET_STATS"}],
                self._get_home_button()
            ]}
            await self.bot.send_message(chat_id, message, reply_markup=keyboard)
        except Exception as e:
            self.logger.error(f"Shadow error: {e}")
            await self.send_message(chat_id, "<b>[ SHADOW ]</b> <i>System audit unavailable.</i>")
    
    async def handle_performance(self, chat_id: int):
        await self.handle_shadow(chat_id)

    async def handle_sync_command(self, chat_id: int):
        """
        Forces a manual hydration of the tracker from the wallet.
        Solves 'ghost positions' and 'orphaned trades'.
        """
        if not self.is_admin(chat_id):
            await self.send_message(chat_id, "<b>[ ! ] ACCESS DENIED</b>")
            return

        status_msg = await self.send_message(chat_id, "<b>[ 🔄 ] SYNCING WALLET STATE...</b>\n<i>Fetching real balances & history...</i>")
        
        try:
            from services.tracker import get_performance_tracker
            tracker = get_performance_tracker()
            
            # Run Sync
            await tracker.sync_with_wallet()
            
            # Report Success
            msg_id = status_msg.get('result', {}).get('message_id')
            if msg_id:
                await self.bot.edit_message_text(
                    chat_id, 
                    msg_id, 
                    "<b>[ ✅ ] SYNC COMPLETE</b>\n\n• Ghosts Purged\n• Orphans Adopted\n• Timestamps Restored\n\n<i>Check /positions to verify.</i>"
                )
            # Refresh Wallet View
            await self.handle_wallet(chat_id)
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            msg_id = status_msg.get('result', {}).get('message_id')
            if msg_id:
                await self.bot.edit_message_text(
                    chat_id, 
                    msg_id, 
                    f"<b>[ ❌ ] SYNC FAILED</b>\n\nError: {str(e)}"
                )

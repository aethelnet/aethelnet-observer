
import logging
import asyncio
from typing import Optional
from services.bot.handlers.base import BaseHandler
from services.data_manager import get_data_manager
from services.paper_broker import get_broker

logger = logging.getLogger("TerminalHandler")

class TerminalHandler(BaseHandler):
    """
    The Execution Cockpit (Terminal).
    The Single Source of Truth for operations (Buy/Sell/Close/Manage).
    """

    async def _get_current_price(self, symbol: str) -> float:
        """Helper to get price with defensive extraction."""
        dm = get_data_manager()
        ticker = await asyncio.to_thread(dm.get_ticker_stats, symbol)
        if ticker and isinstance(ticker, dict):
            p = ticker.get('price', ticker.get('last_price', 0.0))
            if isinstance(p, dict):
                p = p.get('price', p.get('last_price', 0.0))
            return float(p)
        return 0.0

    async def handle_terminal(self, chat_id: int, symbol: str, message_id: int = None):
        """
        Renders the Terminal Interface.
        Checks for Open Positions -> Shows PnL/Close.
        Checks for No Position -> Shows Buy/Sell.
        """
        try:
            symbol = symbol.upper()
            broker = get_broker()
            dm = get_data_manager()
            
            # Fetch Real-Time Data (Defensive Extraction)
            price = await self._get_current_price(symbol)
            
            # Fetch Account State
            balance = float(broker.get_balance(chat_id))
            position = broker.get_position_detailed(chat_id, symbol)
            
            # --- HEADER ---
            msg = (
                f"<b>[ TERMINAL ] :: {symbol}</b>\n"
                "<code>════════════════════════════════</code>\n"
            )
            
            # --- STATUS READOUT ---
            if position:
                # ACTIVE POSITION
                # Defensive Casting to prevent 'dict.__format__' errors if state is corrupted
                entry = float(position.get('entry_price', 0.0))
                size = float(position.get('size', 0.0))
                price = float(price)
                
                side = "LONG" if size > 0 else "SHORT"
                
                # Live PnL Parsing
                # Value = Size * Current Price
                # Cost = Size * Entry
                # PnL = (Size * Current) - (Size * Entry) -> Size * (Current - Entry)
                curr_val = size * price
                entry_val = size * entry
                pnl = curr_val - entry_val
                entry_abs = abs(entry_val)
                pnl_pct = (pnl / entry_abs) * 100 if entry_abs != 0 else 0.0
                
                # Visual Sign
                sign = "+" if pnl >= 0 else "-"
                
                msg += (
                    f"STATUS   : <b>ACTIVE {side}</b>\n"
                    f"ENTRY    : <code>${entry:,.2f}</code>\n"
                    f"MARK     : <code>${price:,.2f}</code>\n"
                    f"SIZE     : <code>{abs(size):.4f} {symbol}</code>\n"
                    "<code>────────────────────────────────</code>\n"
                    f"PnL      : <b>{sign}${abs(pnl):,.2f} ({sign}{abs(pnl_pct):.2f}%)</b>\n"
                )

                if position.get('sl') or position.get('tp'):
                    sl_val = position.get('sl', 'N/A')
                    tp_val = position.get('tp', 'N/A')
                    msg += (
                        f"STOP LOSS: <code>{sl_val}</code>\n"
                        f"TAKE PROF: <code>{tp_val}</code>\n"
                    )

                msg += "<code>────────────────────────────────</code>\n"
                
                # Active Controls
                keyboard = [
                    [
                        {"text": "TRADINGVIEW", "url": f"https://www.tradingview.com/chart/?symbol={symbol}"},
                        {"text": "MT5", "url": "https://trade.mql5.com/trade"}
                    ],
                    [
                        {"text": "CLOSE POSITION", "callback_data": f"TRADE_CLOSE_{symbol}"},
                        {"text": "EDIT RISK", "callback_data": f"TRADE_RISK_{symbol}"}
                    ],
                    [
                         {"text": f"ADD SIZE", "callback_data": f"TRADE_ADD_{symbol}"}
                    ]
                ]
            else:
                # NO POSITION
                msg += (
                    f"STATUS   : <b>FLAT</b>\n"
                    f"PRICE    : <code>${price:,.2f}</code>\n"
                    f"BALANCE  : <code>${balance:,.2f}</code>\n"
                    "<code>────────────────────────────────</code>\n"
                    "<i>System ready. Use buttons or type:</i>\n"
                    f"<code>/long {symbol} 1000 sl:1%</code>\n"
                    f"<code>/short {symbol} 5k tp:2%</code>\n"
                )
                
                # Order Controls
                keyboard = [
                    [
                        {"text": "TRADINGVIEW", "url": f"https://www.tradingview.com/chart/?symbol={symbol}"},
                        {"text": "MT5", "url": "https://trade.mql5.com/trade"}
                    ],
                    [
                        {"text": "BUY 1k", "callback_data": f"TRADE_BUY_{symbol}"},
                        {"text": "BUY 5k", "callback_data": f"TRADE_BUY-5000_{symbol}"},
                        {"text": "BUY MAX", "callback_data": f"TRADE_BUY-MAX_{symbol}"}
                    ],
                    [
                        {"text": "SELL 1k", "callback_data": f"TRADE_SELL_{symbol}"},
                        {"text": "SELL 5k", "callback_data": f"TRADE_SELL-5000_{symbol}"},
                        {"text": "SELL MAX", "callback_data": f"TRADE_SELL-MAX_{symbol}"}
                    ],
                    [
                        {"text": "SET ALERT", "callback_data": f"ALERT_SET_{symbol}"}
                    ]
                ]

            msg += "\n"
            
            # Back Navigation
            keyboard.append([
                {"text": "[ REFRESH ]", "callback_data": f"TERMINAL_{symbol}"},
                {"text": f"« STATS", "callback_data": f"STATS_{symbol}"}
            ])
            
            markup = {"inline_keyboard": keyboard}
            
            if message_id:
                try:
                    await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=markup)
                except Exception:
                    await self.bot.send_message(chat_id, msg, reply_markup=markup)
            else:
                await self.bot.send_message(chat_id, msg, reply_markup=markup)

        except Exception as e:
            self.logger.error(f"Terminal Error: {e}")
            await self.send_message(chat_id, "[!] Terminal Malfunction.")

    async def handle_trade_command(self, chat_id: int, symbol: str, action: str, message_id: int = None):
        """
        Executes the trade action and refreshes the terminal.
        """
        try:
            broker = get_broker()
            
            # Get Price
            price = await self._get_current_price(symbol)
            
            if price == 0:
                await self.send_message(chat_id, "[!] Error: No Price Data.")
                return

            success = False
            msg = ""
            
            if action.startswith("BUY"):
                # Format: BUY (default 1000) or BUY-5000 or BUY-MAX
                parts = action.split("-")
                direction = parts[0]
                
                if len(parts) > 1 and parts[1] == "MAX":
                    # Max Size logic
                    amt = broker.get_balance(chat_id) * 0.95 
                elif len(parts) > 1 and parts[1].isdigit():
                    amt = float(parts[1])
                else:
                    amt = 1000.0
                
                qty = amt / price
                success, reason = broker.open_position(chat_id, symbol, qty, price)
                msg = f"Opened LONG {symbol} (${amt:,.0f})" if success else f"Failed: {reason}"
                
            elif action.startswith("SELL"):
                parts = action.split("-")
                
                if len(parts) > 1 and parts[1] == "MAX":
                    amt = broker.get_balance(chat_id) * 0.95
                elif len(parts) > 1 and parts[1].isdigit():
                    amt = float(parts[1])
                else:
                    amt = 1000.0
                
                qty = -amt / price
                success, reason = broker.open_position(chat_id, symbol, qty, price)
                msg = f"Opened SHORT {symbol} (${amt:,.0f})" if success else f"Failed: {reason}"
                
            elif action == "CLOSE":
                success, reason = broker.close_position(chat_id, symbol, price)
                msg = f"Closed {symbol}" if success else f"Failed: {reason}"
                
            elif action == "ADD":
                 # MVP: Add another $1000 generic
                 # Check direction first
                 pos = broker.get_position_detailed(chat_id, symbol)
                 if pos:
                     current_qty = pos['size']
                     direction = 1 if current_qty > 0 else -1
                     qty = (1000.0 / price) * direction
                     success, reason = broker.open_position(chat_id, symbol, qty, price) # Merges into existing
                     msg = f"Added to {symbol}" if success else f"Failed: {reason}"
            
            # Send Toast (Ephemeral Notification) via Answer Callback if possible, 
            # but we are in message editing flow.
            # Ideally we show an alert. 
            # For now, we just refresh the terminal, and maybe append a status line?
            # Actually, handle_terminal writes the whole message.
            
            elif action == "RISK":
                 # Inform user about slash commands
                 msg = (
                     "<b>[ RISK MANAGEMENT ]</b>\n"
                     "<code>────────────────────────────────</code>\n"
                     "Auratic v2 uses <b>CLI Protocol</b> for risk.\n"
                     "Reply to this message with:\n\n"
                     f"<code>/long {symbol} SL:1% TP:3%</code>\n"
                     f"<code>/short {symbol} SL:2%</code>\n\n"
                     "<i>Stop Loss and Take Profit will trigger automatically.</i>"
                 )
                 await self.send_message(chat_id, msg)
                 return

            # Let's refresh the terminal state
            await self.handle_terminal(chat_id, symbol, message_id)
            
            # Send a separate small notification if failed (optional)
            if not success:
                 await self.bot.answer_callback_query(callback_query_id=None, text=msg, show_alert=True)

        except Exception as e:
            self.logger.error(f"Trade Execution Error: {e}")
            
    async def handle_alert_command(self, chat_id: int, symbol: str, message_id: int = None):
        # Stub for Alert
        # In future: Launch a keypad to type price?
        await self.bot.send_message(chat_id, f"Alert feature coming to {symbol} in v2.1.")

    async def handle_cli_trade(self, chat_id: int, command: str, args: list):
        """
        Processes Slash Commands: /buy, /sell, /long, /short (Live or Paper)
        Syntax: /long [symbol] [amount] [sl:...] [tp:...]
        """
        try:
            from config import get_settings
            from services.paper_broker import get_broker
            from services.data_manager import get_data_manager
            from services.symbol_normalizer import get_symbol_normalizer

            settings = get_settings()
            cmd_lower = command.lower()
            broker = get_broker()

            if cmd_lower == "/reset":
                if hasattr(broker, 'reset_account'):
                    broker.reset_account(chat_id)
                else:
                    broker.positions = {}
                    broker.wallet.balance = {"USDT": 100000.0}
                    broker.save_state()
                await self.send_message(chat_id, "<b>SYSTEM RESET</b>\nPaper account restored to $10,000.")
                return

            if not args:
                await self.send_message(chat_id, "Usage: <code>/long symbol amount [sl:nnn] [tp:nnn]</code>")
                return
            
            # --- LIVE EXECUTION PATH FOR CLOSE ---
            # Parse symbol first
            normalizer = get_symbol_normalizer()
            raw_symbol = args[0].upper()
            symbol = normalizer.normalize(raw_symbol)
            
            if not symbol:
                await self.send_message(chat_id, f"[!] Unrecognized symbol: {raw_symbol}")
                return

            if settings.EXECUTION_ENABLED and not settings.BINANCE_TESTNET:
                is_close = cmd_lower in ["/close", "/exit"]
                if is_close:
                     try:
                         from brokers.router import OmniRouter
                         router = OmniRouter()
                         
                         pos_qty = await router.get_position(symbol)
                         if not pos_qty or abs(pos_qty) == 0:
                             await self.send_message(chat_id, f"[!] No live position for {symbol}.")
                             return
                         
                         side = "SELL" if pos_qty > 0 else "BUY"
                         qty = abs(pos_qty)
                         
                         if len(args) > 1 and args[1].endswith("%"):
                             try:
                                 pct = float(args[1][:-1]) / 100.0
                                 qty *= pct
                             except: pass

                         await self.send_message(chat_id, f"<b>[EXEC] CLOSING LIVE {symbol} ({qty:.5f})...</b>")
                         res = await router.place_order(symbol, side, "MARKET", qty)
                         
                         if res:
                             status = res.get('status', 'FILLED')
                             avg = res.get('average', 0.0)
                             await self.send_message(chat_id, f"<b>[OK] CLOSED {symbol}</b>\nFill: {status} @ ${avg:,.2f}")
                         else:
                             # Fallback for DUST / Ghosts (CLI Path)
                             if qty < 10.0:
                                 await self.send_message(chat_id, f"<b>[!] CLOSE FAILED / MARKET REJECTED</b>\nPosition likely too small (Dust).\nRemoving from bot tracker...")
                                 from services.tracker import PerformanceTracker
                                 tracker = PerformanceTracker()
                                 tracker.close_position(symbol, 0.0)
                             else:
                                 await self.send_message(chat_id, f"<b>[!] EXECUTION FAILED</b>\nRouter returned no result.")
                     except Exception as e:
                         logger.error(f"Live CLI Error: {e}")
                         await self.send_message(chat_id, f"[!] Error: {e}")
                     return

                if cmd_lower in ["/buy", "/sell", "/long", "/short"]:
                     await self.send_message(chat_id, f"<b>[SAFETY]</b> Live Entry via CLI disabled.\nUse <code>/auto</code> to engage the engine.")
                     return

            # --- PAPER EXECUTION PATH (Fallthrough) ---
            dm = get_data_manager()
            broker = get_broker() # Refresh to ensure scope

            # Re-normalize just in case (already done above but scope is fine)
            
            # 1. Parse Arguments (Legacy Logic)
            rem_args = args[1:]
            amount = 1000.0  # Default
            sl = None
            tp = None
            
            for arg in rem_args:
                arg = arg.lower()
                if arg.startswith("sl:"):
                    sl = arg.replace("sl:", "")
                elif arg.startswith("tp:"):
                    tp = arg.replace("tp:", "")
                elif arg.replace(".", "").isdigit():
                    amount = float(arg)
                elif arg.endswith("k") and arg[:-1].replace(".", "").isdigit():
                    amount = float(arg[:-1]) * 1000
                elif arg.endswith("%") and arg[:-1].replace(".", "").isdigit():
                    balance = broker.get_balance(chat_id)
                    pct = float(arg[:-1]) / 100.0
                    amount = balance * pct

            # 2. Get Price
            price = await self._get_current_price(symbol)
            if price == 0:
                await self.send_message(chat_id, f"[!] No price data for {symbol}.")
                return

            # 3. Execution
            is_close = cmd_lower in ["/close", "/exit"]
            is_buy = cmd_lower in ["/buy", "/long"]
            is_risk_update = cmd_lower in ["/sl", "/tp"] # Simplified for brevity

            if is_risk_update:
                pos = broker.get_position_detailed(chat_id, symbol)
                if not pos:
                    await self.send_message(chat_id, f"[!] No active position.")
                    return
                # ... (Risk update logic skipped for brevity in this patch, assume user primarily wants CLOSE fix) ...
                # Actually I should include it or the user loses functionality.
                # I'll include the essential parts.
                val = rem_args[0] if rem_args else None
                field = "sl" if cmd_lower == "/sl" else "tp"
                broker.positions[symbol][field] = val
                await self.send_message(chat_id, f"<b>RISK UPDATED (Paper)</b>")
                return

            if is_close:
                pos = broker.get_position_detailed(chat_id, symbol)
                if not pos or pos['size'] == 0:
                    await self.send_message(chat_id, f"[!] No active position.")
                    return
                direction = -1 if pos['size'] > 0 else 1
                qty = abs(pos['size']) * direction
                success, reason = broker.open_position(chat_id, symbol, qty, price)
                msg = f"<b>CLOSED</b> {symbol} @ ${price:,.2f}"
            else:
                qty = (amount / price) if is_buy else -(amount / price)
                success, reason = broker.open_position(chat_id, symbol, qty, price, sl=sl, tp=tp)
                msg = f"<b>SUCCESS</b> {symbol} @ ${price:,.2f}"
            
            if success:
                await self.send_message(chat_id, msg)
                await self.handle_terminal(chat_id, symbol)
            else:
                await self.send_message(chat_id, f"<b>FAILED</b>: {reason}")

        except Exception as e:
            self.logger.error(f"CLI Trade Error: {e}")
            await self.send_message(chat_id, "[!] Execution Malfunction.")


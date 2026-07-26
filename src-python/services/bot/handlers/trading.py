
import logging
import asyncio
import time
import hashlib
from typing import Optional, Dict, List, Any
from services.bot.handlers.base import BaseHandler
from services.opportunity_cache import get_opportunity_cache
from services.pidgin_poet import PidginPoet
from services.aesthetic_service import ASCIIArt
from services.social_service import get_social_service
from services.leaderboard_service import get_leaderboard_service
from services.bot.helpers.filters import BotIntelFilter
from services.data_manager import get_data_manager
from services.wallet import get_wallet
from services.paper_broker import get_broker
from datetime import datetime

logger = logging.getLogger("TradingHandler")

class TradingHandler(BaseHandler):
    """
    Handles Scoreboard, Opportunities, and Trading Execution logic.
    Refactored from legacy TradingMixin.
    """

    async def handle_opportunities(self, chat_id: int, symbol_filter: str = None, mode: str = "AUTO"):
        """Display active trading opportunities."""
        try:
            cache = get_opportunity_cache()
            opps_raw = cache.get_all_opportunities()
            
            # Fetch user context via bot (if needed) or direct from DM
            dm = get_data_manager()
            # Note: user_id is chat_id for direct messages usually
            style = await asyncio.to_thread(dm.get_user_intel_style, chat_id)
            simple_mode = await asyncio.to_thread(dm.get_user_simple_mode, chat_id)
            
            # Apply symbol filter first
            if symbol_filter:
                opps = [o for o in opps_raw if o['symbol'] == symbol_filter]
            else:
                opps = opps_raw
            
            # Apply style filter (SPECTER, APEX, SHADOW, CORE)
            # Skip filtering in ALL mode (simple_mode == 2)
            if simple_mode != 2 and style:
                opps = BotIntelFilter.filter_opportunities(opps, style)

            total_items = len(opps)
            
            show_pidgin = False
            if mode == "PIDGIN":
                show_pidgin = True
            elif mode == "LIST":
                show_pidgin = False
            else: # AUTO
                # Always show PIDGIN if list empty.
                show_pidgin = (total_items == 0)
                # If explicit request for pidgin comes in, mode will be PIDGIN.

            if show_pidgin:
                await self._render_pidgin_view(chat_id, symbol_filter)
            else:
                await self._render_list_view(chat_id, opps, symbol_filter)
                
        except Exception as e:
            logger.error(f"Opportunities Error: {e}")
            await self.send_message(chat_id, f"[!] Signal Scan Error: {e}")

    async def _render_pidgin_view(self, chat_id: int, symbol_filter: str):
        dm = get_data_manager()
        target_sym = symbol_filter if (symbol_filter and "USDT" in symbol_filter) else "BTCUSDT"
        mood = dm.get_market_mood(target_sym)

        narrative, exclamation = PidginPoet.compose(
            volatility=mood['volatility'], 
            trend_strength=mood['trend_strength'], 
            recent_change=mood['recent_change']
        )
        
        t = time.time()
        seed_val = int(t)
        fractal = ASCIIArt.generate_mandelbrot(width=30, height=8, iterations=20+(seed_val%10), zoom=0.9, center_x=-0.7, center_y=0)
        
        msg = (
            f"<pre>{fractal}</pre>\n\n<b>{exclamation}</b>\n\n"
            f"<b>[ TARGET: {symbol_filter or 'GLOBAL'} ]</b>\n{narrative}\n\n"
            "<code>════════════════════════════════</code>\n"
            f"<b>[ TIME: {datetime.utcnow().strftime('%H:%M:%S')} UTC ]</b>\n"
            f"<b>[ STATUS: {'MONITORING' if not symbol_filter else 'NO SETUP'} ]</b>"
        )
        
        keyboard = self._get_std_buttons(symbol_filter)
        await self.bot.send_message(chat_id, msg, reply_markup={"inline_keyboard": keyboard})

    async def _render_list_view(self, chat_id: int, opps: List[Dict], symbol_filter: str):
        msg, kb_data = self._build_list_response(opps, symbol_filter)
        await self.bot.send_message(chat_id, msg, reply_markup=kb_data)

    def _get_std_buttons(self, symbol_filter: str) -> List[List[Dict]]:
        lb_cb = f"LEADERBOARD_SYM_{symbol_filter}" if symbol_filter else "LEADERBOARD"
        upvote_cb = f"UPVOTE_{symbol_filter}" if symbol_filter else "UPVOTE_GLOBAL"
        downvote_cb = f"DOWNVOTE_{symbol_filter}" if symbol_filter else "DOWNVOTE_GLOBAL"
        yarn_cb = f"YARN_{symbol_filter}" if symbol_filter else "YARN_GLOBAL"
        
        rows = [
            [{"text": "TRADER SCOREBOARD", "callback_data": lb_cb}]
        ]
        
        trades_cb = f"OPPS_LIST_{symbol_filter}" if symbol_filter else "OPPS_LIST"
        sub_cb = f"TOGGLE_SUB_{symbol_filter}" if symbol_filter else "TOGGLE_SUB_GLOBAL"
        rows.append([
            {"text": "TRACK", "callback_data": sub_cb},
            {"text": "HISTORY", "callback_data": "TRADE_LOG"}
        ])
        
        nav = self._get_cyclical_nav("YARN" if symbol_filter else "OPPS")
        rows.append(nav)
        return rows

    def _build_list_response(self, opps, symbol_filter):
        alpha_opps = []  # Above Profit Line (Valid Setups)
        danger_opps = [] # Below Profit Line (Traps/Danger)
        
        for opp in opps:
            tier, name, is_valid = self._classify_tier(opp)
            opp['_tier_code'] = tier
            opp['_tier_name'] = name
            
            # Classification Logic
            # "Alpha" = Positive/Neutral setups (Buy/Sell) with decent confidence
            # "Danger" = Low confidence, high volatility, or contradictory signals
            if is_valid: 
                alpha_opps.append(opp)
            else:
                danger_opps.append(opp)
            
        tier_rank = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
        alpha_opps.sort(key=lambda x: (tier_rank.get(x['_tier_code'], 0), x.get('confidence', 0)), reverse=True)
        # Sort danger by volatility or raw score magnitude (biggest risks first)
        danger_opps.sort(key=lambda x: abs(float(x.get('z_score', 0))), reverse=True)

        filter_tag = f":: {symbol_filter}" if symbol_filter else "[GLOBAL]"
        msg = f"<b>[ ACTIVE SIGNALS {filter_tag} ]</b>\n"
        
        # 1. THE OPPORTUNITIES (Active & Brewing)
        count = 0
        for opp in alpha_opps: # Show all valid, let user scroll
            code = opp['_tier_code']
            badge = f"[{opp['_tier_name']}]"
            sym = opp['symbol']
            direction = opp.get('opportunity_type', 'HOLD')
            z = float(opp.get('z_score', 0))
            
            # Formatting: [PRIME] BTC BUY (Vector:+3.2)
            msg += f"{badge} <b>{sym}</b> {direction} (Vector:<code>{z:+.1f}</code>)\n"
            count += 1
            
        if not alpha_opps:
            msg += "<i>No clean setups detected.</i>\n"

        # 2. THE PROFIT LINE
        msg += "\n<code>════════ [ PROFIT LINE ] ═══════</code>\n"
        
        # 3. THE TRAPS (Danger Zone)
        # "sorta like hey if you were thinking about entering any of these... stop"
        if danger_opps:
            msg += "<b>[ DANGER ZONE / TRAPS ]</b>\n"
            for opp in danger_opps[:5]: # Top 5 risks
                sym = opp['symbol']
                direction = opp.get('opportunity_type', 'HOLD')
                z = float(opp.get('z_score', 0))
                msg += f"[ ! ] <b>{sym}</b> {direction}? (Vector:<code>{z:+.1f}</code>) -> <i>Avoid</i>\n"
        else:
             msg += "<i>No immediate traps detected.</i>\n"

        scan_ts = datetime.utcnow().strftime('%H:%M:%S')
        msg += f"\n<code>[ SCAN_HEARTBEAT ] :: {scan_ts} UTC</code>"

        keyboard = self._get_std_buttons(symbol_filter)
        return msg, {"inline_keyboard": keyboard}

    def _classify_tier(self, opp):
        """
        Classifies signals into Tiers and Valid/Danger buckets.
        Returns: (Tier, Name, IsValid)
        """
        conf = opp.get('confidence', 0)
        z = abs(float(opp.get('z_score', 0)))
        
        # Valid Logic:
        # Must have minimal confidence OR very strong signal
        # If signal is weak (< 0.5) it's noise/trap
        
        if z < 0.5: return 'D', "NOISE", False
        
        if conf >= 0.95 and z >= 3.0: return 'S', "LEGENDARY", True
        if conf >= 0.85: return 'A', "PRIME", True
        if conf >= 0.70: return 'B', "VIABLE", True
        if conf >= 0.50: return 'C', "BREWING", True
        
        # If we are here, it has decent Z-score but low confidence -> TRAP
        return 'D', "TRAP", False

    def _get_social_display(self, symbol: str) -> str:
        try:
            svc = get_social_service()
            yarns = svc.get_yarns(symbol, limit=2)
            votes = svc.get_karma(symbol)
            txt = f"\n<b>[ COMMUNITY VOICE (Karma: {votes}) ]</b>\n"
            if not yarns: return txt + "<i>(No gist yet.)</i>\n"
            for y in yarns:
                txt += f"• <b>{y['username'][:10]}</b>: {y['text']}\n"
            return txt
        except: return ""

    async def handle_leaderboard(self, chat_id: int, symbol: str = None, message_id: int = None):
        """Display the Trader Scoreboard."""
        try:
            ls = get_leaderboard_service()
            traders = await ls.get_top_traders(limit=5, symbol=symbol)
            
            ctx_label = symbol if symbol else 'GLOBAL'
            msg = f"<b>[ TRADER SCOREBOARD :: {ctx_label} ]</b>\n"
            msg += "<code>════════════════════════════════</code>\n\n"
            
            if not traders:
                msg += "<i>Scoreboard currently offline.</i>"
            else:
                msg += f"Intelligence feed for {ctx_label} liquidity.\n\n"
                for t in traders:
                    # Strategy Tag
                    tag = t.get('strategy', 'SCALPER')
                    source = t.get('source', 'ORACLE')
                    
                    msg += (
                        f"<b>ID:</b> <code>{t['id']} ({source})</code>\n"
                        f"<b>ROI:</b> <code>{t['roi']:.1f}%</code> | <b>WIN:</b> <code>{t['win_rate']:.1f}%</code>\n"
                        f"<b>TAG:</b> {tag}\n"
                        f"<b>TL;DR:</b> {t.get('tldr', 'Monitoring market heartbeat.')}\n"
                    )
                    
                    # Allocations
                    allocs = t.get('allocations', [])
                    if allocs:
                        msg += "<b>ALLOCS:</b> "
                        alloc_strs = [f"{a['asset']} {a['pct']:.0f}%" for a in allocs[:3]]
                        msg += ", ".join(alloc_strs) + "\n"
                    
                    msg += "<code>────────────────────────────────</code>\n"
            
            msg += "\n<b>[TIP]</b> Follow traders with high WIN% for consistency.\n"
        
            keyboard = {"inline_keyboard": [self._get_cyclical_nav("OPPS")]}
            
            if message_id:
                try:
                    await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=keyboard)
                except Exception: # Catch specific exception if possible, or general.
                    # If edit fails (e.g., message too old, or not found), send a new message
                    await self.bot.send_message(chat_id, msg, reply_markup=keyboard)
            else:
                await self.bot.send_message(chat_id, msg, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Scoreboard Error: {e}")
            await self.send_message(chat_id, "[!] Scoreboard unavailable.")

    async def handle_execute(self, chat_id: int, symbol: str = None):
        """Generalized execution hub."""
        msg = (
            "<b>[ EXECUTION HUB ]</b>\n"
            "<code>════════════════════════════════</code>\n"
            "Status: <code>[ READY ]</code>\n"
            "Server: <code>AURATIC_PRIME_L1</code>\n\n"
            "<i>Execution protocols initialized.</i>"
        )
        from config import get_settings
        settings = get_settings()
        
        keyboard = [
            [{"text": "∿ MONITOR", "callback_data": "MONITOR_LIVE"}],
            [{"text": "MT5 WEB TERMINAL", "url": settings.MT5_WEBTRADER_URL}],
            self._get_cyclical_nav("OPPS")
        ]
        await self.bot.send_message(chat_id, msg, reply_markup={"inline_keyboard": keyboard})

    async def handle_monitor(self, chat_id: int, message_id: int = None):
        """Displays the live-updating trade execution monitor."""
        msg, kb = await self._build_monitor_response(chat_id)
        
        # Start/Renew Refresh Job
        job_name = f"monitor_{chat_id}"
        current_jobs = self.bot.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs: job.schedule_removal()
        
        self.bot.job_queue.run_repeating(
            self.watch_monitor_job,
            interval=3,
            first=3,
            chat_id=chat_id,
            name=job_name,
            data={'message_id': message_id or 0, 'last_hash': hashlib.md5(msg.encode()).hexdigest(), 'lifespan': 60}
        )
        
        if message_id:
            try: await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=kb)
            except: pass
        else:
            await self.bot.send_message(chat_id, msg, reply_markup=kb)

    async def handle_close_position(self, chat_id: int, symbol: str):
        """Execute manual close for a specific symbol (Live or Paper)."""
        try:
            from config import get_settings
            from services.wallet import get_wallet
            from services.paper_broker import get_broker
            
            settings = get_settings()
            
            # --- LIVE EXECUTION PATH ---
            # Try to route to OmniRouter if we are in LIVE mode (and presumably Admin/Authorized)
            if settings.EXECUTION_ENABLED and not settings.BINANCE_TESTNET:
                try:
                    from brokers.router import OmniRouter
                    # Instantiate Router (Lightweight wrapper)
                    router = OmniRouter()
                    
                    # 1. Get Live Position Quantity
                    pos_qty = await router.get_position(symbol)
                    
                    if pos_qty is None or abs(pos_qty) == 0:
                         await self.bot.answer_callback_query(chat_id, f"No live position for {symbol}", show_alert=True)
                         return

                    # 2. Determine Closing Side
                    side = "SELL" if pos_qty > 0 else "BUY"
                    qty_abs = abs(pos_qty)
                    
                    # 3. Execute Market Close
                    await self.bot.answer_callback_query(chat_id, f"Closing Live {symbol}...", show_alert=False)
                    notify_msg = await self.bot.send_message(chat_id, f"<b>[EXEC] CLOSING {symbol}...</b>")
                    
                    # Parameters for OmniRouter
                    # place_order is async
                    res = await router.place_order(symbol, side, "MARKET", qty_abs)
                    
                    if res:
                        # Log success
                        details = ""
                        if isinstance(res, dict):
                            fill_price = res.get('average', res.get('price', 0))
                            details = f"@ ${fill_price:,.2f}"
                        await self.bot.edit_message_text(chat_id, notify_msg.message_id, f"<b>[OK] CLOSED {symbol}</b> {details}\nPosition liquidated.")
                    else:
                        # Fallback for DUST / Ghosts
                        # If router returns None, it might be too small to trade.
                        # Check quantity vs approx dust limit (e.g. $5)
                        # Since we can't easily check price here without another call, use simple logic:
                        if qty_abs < 10.0: # Assuming simple heuristic for "small quantity" depending on asset
                             logger.warning(f"Close failed for {symbol} (Qty {qty_abs}). Likely dust.")
                             # Purge from tracker to clean UI?
                             # For now, just inform user.
                             await self.bot.edit_message_text(chat_id, notify_msg.message_id, f"<b>[!] CLOSE FAILED / MARKET REJECTED</b>\nPosition likely too small (Dust).\n<i>Use Binance 'Convert Small Assets' feature.</i>\n\nRemoving from bot tracker...")
                             from services.tracker import PerformanceTracker
                             tracker = PerformanceTracker()
                             tracker.close_position(symbol, 0.0)
                        else:
                             await self.bot.edit_message_text(chat_id, notify_msg.message_id, f"<b>[!] CLOSE FAILED</b>\nRouter returned no confirmation.")
                        
                except Exception as e:
                    logger.error(f"Live Close Error: {e}")
                    await self.bot.send_message(chat_id, f"<b>[!] LIVE EXECUTION ERROR</b>\n{e}")
                return

            # --- PAPER EXECUTION PATH ---
            wallet = get_wallet()
            broker = get_broker(wallet)
            
            # Check current position (Paper)
            # Use get_position_detailed to handle potential implementation differences
            # If get_position() returns float, great. If detailed dict, extract size.
            # Reading existing code: broker.get_position(symbol) returned float.
            pos = broker.get_position(symbol)
            qty = pos 
            
            if abs(qty) == 0:
                await self.bot.answer_callback_query(chat_id, f"No active position for {symbol}", show_alert=True)
                return
            
            # Determine Action
            side = "SELL" if qty > 0 else "BUY"
            
            # Execute Market Close
            broker.place_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=abs(qty)
            )
            
            # Paper fills are simulated, usually instant or next tick.
            await self.bot.answer_callback_query(chat_id, f"Closing {symbol}...", show_alert=False)
            await self.bot.send_message(chat_id, f"<b>[CLOSE] Order Submitted:</b> {symbol}\n<i>Paper fill pending tick...</i>")
            
        except Exception as e:
            logger.error(f"Manual Close Error: {e}")
            await self.bot.answer_callback_query(chat_id, f"Close Failed: {e}", show_alert=True)

    async def handle_karma_vote(self, chat_id: int, user_id: int, symbol: str, direction: str):
        """Handle social sentiment voting (+1/-1)."""
        try:
            svc = get_social_service()
            reaction = "UPVOTE" if direction == "UP" else "DOWNVOTE"
            success = svc.set_sentiment(user_id, symbol, reaction)
            
            if success:
                sign = "+" if direction == "UP" else "-"
                await self.bot.answer_callback_query(chat_id, f"{sign}1 Karma for {symbol}")
            else:
                await self.bot.answer_callback_query(chat_id, "Vote failed to register.")
        except Exception as e:
            logger.error(f"Karma Error: {e}")
            await self.bot.answer_callback_query(chat_id, "Vote Error")

    async def handle_risk_adjustment(self, chat_id: int, direction: str):
        """Adjusts risk parameters (Aggression/Position Sizing)."""
        try:
            dm = get_data_manager()
            # We need to implement a setter in DM or Update directly here
            # For now, let's mock the adjustment confirmation to satisfy the 'WIP' requirement,
            # but ideally we connect to UserBotSettings.
            
            # Ideally we connect to UserBotSettings.
            
            # Using raw SQL or session for expediency:
            db = dm.SessionLocal()
            try:
                from services.data.schema import UserBotSettings
                settings = db.query(UserBotSettings).filter(UserBotSettings.user_id == chat_id).first()
                if not settings:
                     # Create defaults
                     settings = UserBotSettings(user_id=chat_id, max_position_size=0.05)
                     db.add(settings)
                
                current = settings.max_position_size or 0.05
                change = 0.01 if direction == "UP" else -0.01
                new_val = max(0.01, min(1.0, current + change)) # Clamp 1% to 100%
                
                settings.max_position_size = new_val
                db.commit()
                
                alert = ""
                if new_val > 0.20:
                    alert = "\n⚠️ <b>[WARNING] HIGH RISK ENGAGED</b>"
                
                await self.bot.answer_callback_query(chat_id, f"Risk calibrated: {new_val*100:.0f}% Position Size{alert}", show_alert=(new_val > 0.20))
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Risk Adj Error: {e}")
            await self.bot.answer_callback_query(chat_id, "Risk adjustment unavailable.")

    async def _build_monitor_response(self, chat_id: int = 0):
        """Constructs the monitor status message with progress bar."""
        try:
            wallet = get_wallet()
            broker = get_broker(wallet)
            
            # Find first active position for THIS user
            pos = None
            user_positions = broker.get_positions(chat_id)
            for symbol, p in user_positions.items():
                if abs(p.get('quantity', 0)) > 0:
                    pos = p
                    pos['symbol'] = symbol # Inject symbol name
                    break
            
            if not pos:
                msg = (
                    "<b>[ EXECUTION MONITOR ]</b>\n"
                    "<code>════════════════════════════════</code>\n\n"
                    "<b>NO ACTIVE TRADES</b>\n"
                    "<i>The machine is hunting in the shadows...</i>\n\n"
                    "<code>[ AWAITING_SIGNAL ]</code>"
                )
                keyboard = [[{"text": "SCAN NOW", "callback_data": "OPPORTUNITIES"}, {"text": "○", "callback_data": "START"}]]
                return msg, {"inline_keyboard": keyboard}

            symbol = pos['symbol']
            pnl = pos.get('unrealized_pnl', 0.0)
            side = "LONG" if pos['quantity'] > 0 else "SHORT"
            entry = pos.get('avg_price', 0.0)
            
            # Progress bar logic from trade_monitor.py
            target_pnl = 20.0 # Standard MVP target
            risk_cap = 1000.0
            pnl_pct = (pnl / risk_cap) * 100.0
            progress = pnl / target_pnl
            
            # Visual Progress Bar
            length = 20
            visual_range = progress + 1.0 # 0 to 2
            bar_pos = int(length * (visual_range / 2.0))
            mid = length // 2
            
            if progress >= 0:
                bar = '-' * mid + '|' + '█' * max(0, bar_pos - mid - 1) + '-' * max(0, length - bar_pos)
            else:
                bar = '-' * max(0, mid - bar_pos) + '█' * max(0, bar_pos) + '|' + '-' * max(0, length - mid - 1)
                
            if progress == 0: bar = '-' * mid + '|' + '-' * (length - mid - 1)
            bar_str = f"[{bar[:length]}] {progress:+.1%}"
            
            msg = (
                f"<b>[ EXECUTION MONITOR : {symbol} ]</b>\n"
                f"<code>════════════════════════════════</code>\n"
                f"S/L SIDE : <b>{side}</b>\n"
                f"ENTRY    : <code>${entry:,.2f}</code>\n"
                f"PNL ($)  : <b>${pnl:+.2f}</b>\n"
                f"PNL (%)  : <code>{pnl_pct:+.2f}%</code>\n"
                f"<code>══════════════ TARGET ══════════</code>\n"
                f"<code>{bar_str}</code>\n"
                f"<code>════════════════════════════════</code>\n"
                f"<i>Refreshing live...</i>"
            )
            
            # Multi-User Paper Trading Enabled
            keyboard = []
            keyboard.append([{"text": "[X] CLOSE POSITION", "callback_data": f"CLOSE_{symbol}"}])
            
            # Note: Risk adjustment buttons removed to avoid confusion with /risk command.
            # See handle_risk() in system.py for authoritative risk config.

            keyboard.append(self._get_nav_row())
            return msg, {"inline_keyboard": keyboard}
        except Exception as e:
            return f"Monitor Error: {e}", None

    async def watch_monitor_job(self, context):
        job = context.job
        chat_id = job.chat_id
        data = job.data
        data['lifespan'] -= 1
        if data['lifespan'] <= 0:
            job.schedule_removal()
            return
            
        msg, kb = await self._build_monitor_response(chat_id)
        if not kb: return
        
        current_hash = hashlib.md5(msg.encode()).hexdigest()
        if current_hash != data.get('last_hash'):
            try:
                if data['message_id']:
                    await self.bot.edit_message_text(job.chat_id, data['message_id'], msg, reply_markup=kb)
                else:
                    sent = await self.bot.send_message(job.chat_id, msg, reply_markup=kb)
                    data['message_id'] = sent.message_id
                data['last_hash'] = current_hash
            except: pass

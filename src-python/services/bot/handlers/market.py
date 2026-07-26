"""
Market Handler
Manages market data updates, symbol queries, and session information.
"""
# pylint: disable=broad-exception-caught, logging-fstring-interpolation, too-many-locals
# pylint: disable=import-outside-toplevel, too-many-statements, line-too-long
# pylint: disable=redefined-outer-name, reimported, unused-import, unused-variable
# pylint: disable=unused-argument

import asyncio
from datetime import datetime
from typing import List, Optional
from services.bot.handlers.base import BaseHandler
from services.bot.formatters import format_market_summary, format_symbol_details, get_chart_links
from services.symbol_normalizer import get_symbol_normalizer
from services.subscription_manager import get_subscription_manager
from services.news_aggregator import get_enhanced_news_aggregator
from services.symbol_normalizer import EthicalConstraintException
from config.strings import BotStrings

class MarketHandler(BaseHandler):
    """
    Handles market-related commands and updates.
    """
    async def handle_market_update(self, chat_id: int, timeframe: str, symbols: Optional[List[str]] = None):
        """Send general market update."""
        if not await self.bot.check_backend_health():
            await self.send_message(chat_id, "[!] Backend Offline")
            return

        try:
            # Fetch broad market data and predictions in parallel
            tasks = [
                self.fetch_api("/api/dashboard/market-data"),
                self.fetch_api("/api/dashboard/metrics"),
                self.fetch_api("/api/opportunities"),
                self.fetch_api("/api/predictions"),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter exceptions
            results = [r if not isinstance(r, Exception) else None for r in results]
            market_data, metrics, opportunities, predictions = results

            # Determine focus symbols
            focus_symbols = []
            if symbols and len(symbols) > 0:
                focus_symbols = [s.upper() for s in symbols]
            else:
                focus_symbols = self.bot.default_symbols.copy()
                # Add top movers if available
                if isinstance(market_data, list) and market_data:
                    top_movers = [d.get('symbol') for d in market_data[:10] if d.get('symbol')]
                    for t in top_movers:
                        if t and t.upper() not in focus_symbols:
                            focus_symbols.append(t.upper())
                focus_symbols = focus_symbols[:15]

            # Format and send
            message = format_market_summary(
                timeframe,
                market_data if isinstance(market_data, list) else [],
                metrics if isinstance(metrics, dict) else {},
                opportunities if isinstance(opportunities, list) else [],
                predictions if isinstance(predictions, list) else ([predictions] if predictions else []),
                focus_symbols
            )

            await self.send_message(chat_id, message)

        except Exception as e:
            self.logger.error(f"Failed to market update: {e}")
            await self.send_message(chat_id, "[X] Failed to generate market update.")

    async def handle_price_tab(self, chat_id: int, message_id: int = None, user_id: int = None):
        """Refined Price Intelligence Landing with live stats and integrated navigation."""
        u_id = user_id or chat_id
        normalizer = get_symbol_normalizer()
        sub_manager = get_subscription_manager()

        # 1. DEFINE CORE ASSETS
        popular_crypto = ["BTCUSDC", "ETHUSDC"]
        popular_global = ["GC=F", "ES=F"]

        # 2. FETCH USER SUBSCRIPTIONS (Tracked Assets)
        user_subs = sub_manager.get_user_subscriptions(u_id)
        subscribed_symbols = [s.target for s in user_subs if s.subscription_type == "PRICE"]

        # 3. FETCH LIVE DATA
        market_data_list = await self.fetch_api("/api/dashboard/market-data")
        ticker_map = {d['symbol']: d for d in market_data_list} if isinstance(market_data_list, list) else {}

        # 3b. Resolve Aliases in Ticker Map (e.g. Map 'BTCUSDC' entry to 'BTC' key)
        # This allows lookup by both 'BTC' and 'BTCUSDC'
        for k, v in list(ticker_map.items()): # Iterate copy
            display_sym = normalizer.to_display(k)
            if display_sym != k:
                ticker_map[display_sym] = v

        def format_ticker_line(sym):
            # Normalize input symbol (e.g. 'SOL' -> 'SOLUSDC' -> Lookup)
            # Try direct lookup, then alias lookup
            data = ticker_map.get(sym)
            if not data:
                # Type fallback: SOL -> SOLUSDC
                binance_sym = normalizer.to_binance(sym)
                if binance_sym:
                    data = ticker_map.get(binance_sym)

            # Final fallback: Normalize Alias map
            if not data:
                # If 'SOL' is passed, checks if 'SOL' is in map (added in 3b)
                data = ticker_map.get(normalizer.to_display(sym), {})

            price = data.get('price', 0)
            change = data.get('change_pct', data.get('change_24h', 0))
            display = normalizer.to_display(sym)

            p_str = f"${price:,.0f}" if price > 1 else f"${price:,.4f}"
            c_str = f"{change:+.1f}%"
            icon = "▴" if change > 0 else "▾"
            return f"• <code>{p_str:<10} {c_str:<7} {icon}</code> /{display}\n"

        from services.aesthetic_service import ASCIIArt

        # 0. FRACTAL HEADER (Aesthetics Restoration)
        fractal = ASCIIArt.generate_mandelbrot(width=32, height=6, iterations=15)

        # 4. CONSTRUCT MESSAGE
        msg = (
            f"<pre>{fractal}</pre>\n\n"
            + BotStrings.PRICE_LANDING_HEADER
        )

        msg += "<b>[ POPULAR ASSETS ]</b>\n"
        for s in popular_crypto + popular_global:
            msg += format_ticker_line(s)

        if subscribed_symbols:
            msg += "\n<b>[ YOUR SUBSCRIPTIONS ]</b>\n"
            for s in subscribed_symbols[:5]: # Cap for brevity
                if s not in (popular_crypto + popular_global):
                    msg += format_ticker_line(s)

        msg += BotStrings.PRICE_LANDING_FOOTER

        # 5. BUILD BUTTONS (Named clusters only - clean layout)
        keyboard = [
            # Cluster navigation with names
            [
                {"text": "◈ CRYPTO", "callback_data": "CLUSTER_CRYPTO"},
                {"text": "⇄ FOREX", "callback_data": "CLUSTER_FOREX"}
            ],
            [
                {"text": "▽ STOCKS", "callback_data": "CLUSTER_STOCKS"},
                {"text": "◆ MACRO", "callback_data": "CLUSTER_MACRO"}
            ],
            # Refresh Action
            [{"text": "⟳ REFRESH DATA", "callback_data": "PRICE_LANDING"}],
            # Cyclical Nav
            self._get_cyclical_nav("PRICE")
        ]

        if message_id:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=msg,
                parse_mode="HTML",
                reply_markup={"inline_keyboard": keyboard}
            )
        else:
            await self.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="HTML",
                reply_markup={"inline_keyboard": keyboard}
            )

    async def handle_symbol_query(self, chat_id: int, symbol: str, timeframe: str):
        """Send symbol-specific update with rich interactivity."""
        # Skipped redundant health check to prevent flaky timeouts
        # if not await self.bot.check_backend_health():
        #     await self.send_message(chat_id, "[!] Backend Offline")
        #     return

        try:
            symbol_upper = symbol.upper()
            normalizer = get_symbol_normalizer()
            display_name = normalizer.to_display(symbol_upper)

            # Fetch ALL available data
            tasks = [
                self.fetch_api("/api/dashboard/market-data"),
                self.fetch_api(f"/api/predictions?symbol={symbol_upper}"),
                self.fetch_api(f"/api/opportunities?symbol={symbol_upper}")
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r if not isinstance(r, Exception) else None for r in results]
            market_data_list, predictions_data, opportunities_data = results

            # Extract specific symbol data from list
            symbol_data = None
            if isinstance(market_data_list, list):
                symbol_data = next((d for d in market_data_list if d.get('symbol', '').upper() == symbol_upper), None)

            # FALLBACK: If not in main list (User queried specific stock like NVDA)
            if not symbol_data:
                from services.data_manager import get_data_manager
                dm = get_data_manager()
                # Run in thread to avoid blocking
                stats = await asyncio.to_thread(dm.get_ticker_stats, symbol_upper)
                if stats:
                    # Adapt format to match market-data API structure
                    symbol_data = {
                        'symbol': symbol_upper,
                        'price': stats.get('price', 0),
                        'change_24h': stats.get('change_pct', 0),
                        'volume': stats.get('volume', 0),
                        'signal': 0, # No engine signal for ad-hoc
                        'signal_strength': 'NEUTRAL',
                        'last_update': datetime.utcnow().isoformat()
                    }

            # Chart links
            chart_links = get_chart_links(
                symbol_upper,
                self.bot.tradingview_affiliate_id,
                self.bot.binance_affiliate_id
            )

            # FETCH STYLE
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            active_style = await asyncio.to_thread(dm.get_user_intel_style, chat_id)

            # FETCH DIVINE METRICS (Brain)
            from services.brain import get_engine
            engine = get_engine()
            divine_metrics = await asyncio.to_thread(engine.get_divine_metrics, symbol_upper)

            # FETCH AUTO-PILOT STATE
            auto_pilot = getattr(engine.live_manager, 'is_auto_pilot_active', False)

            message = format_symbol_details(
                display_name, # Use nickname for header if available
                symbol_data,
                predictions_data,
                opportunities_data if isinstance(opportunities_data, list) else [],
                chart_links,
                style=active_style or "CORE",
                divine_metrics=divine_metrics,
                auto_pilot=auto_pilot
            )

            # Check if user has subscription for this symbol (toggle button logic)
            from services.subscription_manager import get_subscription_manager
            sm = get_subscription_manager()
            user_subs = sm.get_user_subscriptions(chat_id)  # chat_id = user_id for DMs
            is_subscribed = any(s.target == symbol_upper and s.subscription_type == "PRICE" for s in user_subs)
            
            # Find sub_id if subscribed (for unsubscribe)
            sub_id = None
            if is_subscribed:
                for s in user_subs:
                    if s.target == symbol_upper and s.subscription_type == "PRICE":
                        sub_id = s.id
                        break
            
            # RICH INLINE KEYBOARD (Nokia v2 Matrix)
            # RICH INLINE KEYBOARD (Refined Layout)
            # "Launchers" that open new windows
            keyboard = [
                # Row 1: The "Inspect" Suite
                [
                    {"text": "[ STATS ]", "callback_data": f"STATS_{symbol_upper}"},
                    {"text": "[ NEWS ]", "callback_data": f"NEWS_{symbol_upper}"},
                    {"text": "[ EVENTS ]", "callback_data": f"CAL_AUTO_{symbol_upper}"} 
                ],
                # Row 2: Action Suite (Toggle based on sub status)
                [
                    {"text": "DROP ALERT" if is_subscribed else "SET ALERT", 
                     "callback_data": f"unsubscribe_{sub_id}" if is_subscribed else f"ALERT_{symbol_upper}"},
                ],
                # Row 2: The "Deep Intel" Suite (Wiki + Public)
                [
                    {"text": "[ WIKI ]", "callback_data": f"KNOWLEDGE_HUB_{symbol_upper}"},
                    {"text": "[ YARN ]", "callback_data": f"YARN_{symbol_upper}"}
                ],
                # Row 3: Navigation
                self._get_cyclical_nav("SYMBOL")
            ]

            await self.bot.send_message(chat_id, message, reply_markup={"inline_keyboard": keyboard})

        except Exception as e:
            await self.send_message(chat_id, f"[X] Error fetching data for {symbol}")

    async def handle_cluster_view(self, chat_id: int, cluster: str, message_id: int = None):
        """
        Displays a sector/cluster overview using Galaxy Service.
        """
        from services.aesthetic_service import ASCIIArt
        from config import get_settings
        from services.galaxy import get_galaxy_service
        
        settings = get_settings()
        normalizer = get_symbol_normalizer()
        galaxy = get_galaxy_service() # Dynamic Engine

        # Fetch Dynamic Members
        members = galaxy.get_cluster_members(cluster)
        
        if not members:
            # Fallback if sector empty or invalid
            await self.send_message(chat_id, f"[X] Sector void/empty: {cluster}")
            return
            
        # Fetch market data
        market_data_list = await self.fetch_api("/api/dashboard/market-data")
        ticker_map = {d['symbol']: d for d in market_data_list} if isinstance(market_data_list, list) else {}
        
        # Aggregate stats
        total_change = 0
        valid_count = 0
        symbol_lines = []
        
        for sym in members:
            # Resolve data
            data = ticker_map.get(sym) or ticker_map.get(normalizer.to_binance(sym) or '', {})
            display = normalizer.to_display(sym)
            
            if not data: 
                # Show offline/pending state instead of hiding
                symbol_lines.append(f"[?] <code>{display:8}</code> {'---':>10} 0.0%")
                continue
            
            price = data.get('price', 0)
            change = data.get('change_pct', data.get('change_24h', 0))
            
            if price > 0:
                p_str = f"${price:,.2f}" if price < 1000 else f"${price:,.0f}" # Compact since we show many
                total_change += change
                valid_count += 1
                
                # Format line
                icon = "[+]" if change > 0 else "[-]" if change < 0 else "[ ]"
                symbol_lines.append(f"{icon} <code>{display:8}</code> {p_str:>10} {change:+.1f}%")

        avg_change = total_change / valid_count if valid_count > 0 else 0
        trend = "BULLISH" if avg_change > 1 else "BEARISH" if avg_change < -1 else "NEUTRAL"

        # Build message
        fractal = ASCIIArt.generate_mandelbrot(width=28, height=5, iterations=20)

        msg = (
            f"<pre>{fractal}</pre>\n\n"
            + BotStrings.CLUSTER_HEADER.format(cluster=cluster.upper(), trend=trend, avg_change=avg_change)
        )

        for line in symbol_lines:
            msg += f"{line}\n"

        msg += (
            "\n<code>══════════════════════════════</code>\n"
            "<i>Tap a symbol for details</i>"
        )

        # Member symbol buttons (top 3 only for cleaner layout)
        keyboard = []
        row = []
        for sym in members[:3]:  # Limit to 3 for cleaner view
            display = normalizer.to_display(sym)
            row.append({"text": display, "callback_data": f"PRICE_{sym}"})
        if row:
            keyboard.append(row)

        # Show remaining count as "more" if needed
        if len(members) > 3:
            remaining = [normalizer.to_display(s) for s in members[3:]]
            more_row = [{"text": d, "callback_data": f"PRICE_{members[3+i]}"} for i, d in enumerate(remaining[:2])]
            if more_row:
                keyboard.append(more_row)

        # Looping layer navigation (prev cluster / news / next cluster)
        cluster_order = ["CRYPTO", "FOREX", "STOCKS", "MACRO"]
        try:
            idx = cluster_order.index(cluster.upper())
            prev_cluster = cluster_order[(idx - 1) % len(cluster_order)]
            next_cluster = cluster_order[(idx + 1) % len(cluster_order)]
        except ValueError:
            prev_cluster = "CRYPTO"
            next_cluster = "FOREX"
        
        # Navigation Buttons (using prev_cluster/next_cluster defined above)
        keyboard.append([
            {"text": "◂", "callback_data": f"CLUSTER_{prev_cluster}"},
            {"text": "◔", "callback_data": f"NEWS_{cluster.upper()}"},
            {"text": "▸", "callback_data": f"CLUSTER_{next_cluster}"}
        ])

        # Navigation Ring
        keyboard.append(self._get_cyclical_nav("CLUSTERS"))

        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup={"inline_keyboard": keyboard})
        else:
            await self.bot.send_message(chat_id, msg, reply_markup={"inline_keyboard": keyboard})

    async def handle_subscription_manager(self, chat_id: int):
        """
        Manages user subscriptions (Trac KMeans / Tracked Assets).
        """
        from services.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        subs = sm.get_user_subscriptions(chat_id)
        
        if not subs:
            msg = (
                "<b>[ SUBSCRIPTION MANAGER ]</b>\n"
                "<code>════════════════════════════════</code>\n"
                "<i>You are not tracking any assets.</i>\n\n"
                "<b>[TIP]</b> Tap <code>[ ⊕ TRACK ]</code> on any symbol to add it."
            )
            keyboard = {"inline_keyboard": [[{"text": "🔙 BACK", "callback_data": "START"}]]}
        else:
            msg = (
                "<b>[ SUBSCRIPTION MANAGER ]</b>\n"
                "<code>════════════════════════════════</code>\n"
                "<i>Tracking active assets. Tap to Untrack.</i>\n\n"
            )
            
            # Button Grid (2 cols)
            keyboard_rows = []
            row = []
            for sub in subs:
                # Callback: TOGGLE_SUB_SYMBOL
                row.append({"text": f"❌ {sub}", "callback_data": f"TOGGLE_SUB_{sub}"})
                if len(row) == 2:
                    keyboard_rows.append(row)
                    row = []
            if row: keyboard_rows.append(row)
            
            keyboard_rows.append([{"text": "🔙 BACK", "callback_data": "START"}])
            keyboard = {"inline_keyboard": keyboard_rows}
            
        await self.bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")

    async def handle_session(self, chat_id: int, session: str, message_id: int = None):
        """
        Display exchange session info with relevant symbols.
        Sessions: ASIA (Tokyo/HK), EUROPE (London/Frankfurt), US (NYC/Chicago)
        """
        from services.aesthetic_service import ASCIIArt
        from datetime import datetime, timezone

        # Define sessions with hours (UTC) and key symbols
        sessions = {
            "ASIA": {
                "name": "ASIA",
                "exchanges": "Tokyo | Hong Kong | Sydney",
                "hours": "00:00 - 09:00 UTC",
                "symbols": ["BTCUSDC", "ETHUSDC", "XRPUSDC"],
                "indices": ["NI225", "HSI"]
            },
            "EUROPE": {
                "name": "EUROPE",
                "exchanges": "London | Frankfurt | Paris",
                "hours": "07:00 - 16:00 UTC",
                "symbols": ["EURUSD=X", "GBPUSD=X", "GC=F"],
                "indices": ["FTSE", "DAX"]
            },
            "US": {
                "name": "AMERICAS",
                "exchanges": "New York | Chicago",
                "hours": "13:30 - 20:00 UTC",
                "symbols": ["ES=F", "NQ=F", "CL=F"],
                "indices": ["SPX", "NDX", "VIX"]
            }
        }

        s = sessions.get(session.upper())
        if not s:
            await self.send_message(chat_id, f"[X] Unknown session: {session}")
            return

        # Check if session is active
        now = datetime.now(timezone.utc)
        hour = now.hour

        active_session = "CLOSED"
        if 0 <= hour < 9:
            active_session = "ASIA"
        elif 7 <= hour < 16:
            active_session = "EUROPE"
        elif 13 <= hour < 20:
            active_session = "US"

        is_active = session.upper() == active_session
        status = "ACTIVE" if is_active else "CLOSED"

        fractal = ASCIIArt.generate_mandelbrot(width=24, height=4, iterations=15)

        msg = (
            f"<pre>{fractal}</pre>\n\n"
            + BotStrings.SESSION_TEMPLATE.format(name=s['name'], status=status, exchanges=s['exchanges'], hours=s['hours'])
        )

        for sym in s['symbols']:
            msg += f"  <code>{sym}</code>\n"

        msg += (
            "\n<code>══════════════════════════</code>\n"
            f"<i>Current: {now.strftime('%H:%M')} UTC</i>"
        )

        # Buttons for symbols
        keyboard = []
        row = []
        for sym in s['symbols']:
            row.append({"text": sym.split("=")[0][:6], "callback_data": f"PRICE_{sym}"})
            if len(row) >= 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Session nav
        keyboard.append([
            {"text": "[AS]", "callback_data": "SESSION_ASIA"},
            {"text": "[EU]", "callback_data": "SESSION_EUROPE"},
            {"text": "[US]", "callback_data": "SESSION_US"}
        ])
        keyboard.append([
            {"text": "←", "callback_data": "PRICE_LANDING"},
            {"text": "○", "callback_data": "START"}
        ])

        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup={"inline_keyboard": keyboard})
        else:
            await self.bot.send_message(chat_id, msg, reply_markup={"inline_keyboard": keyboard})

    async def handle_calendar(self, chat_id: int, sector: str = None, message_id: int = None):
        """Display economic calendar events - limited to high-impact for overview."""
        from services.aesthetic_service import ASCIIArt
        from services.economic_calendar import get_economic_calendar

        calendar = get_economic_calendar()
        await calendar.fetch_calendar()

        # For front page (no sector): only high-impact, max 3
        # For sector views: show more
        if sector:
            upcoming = await calendar.get_upcoming_events(limit=6, sector_filter=sector)
            title = f"{sector.upper()} EVENTS"
        else:
            # Try high impact first, but fallback to any upcoming if empty
            upcoming = await calendar.get_upcoming_events(limit=6, impact_filter='H')
            if not upcoming:
                upcoming = await calendar.get_upcoming_events(limit=6)
            title = "MARKET PULSE" if not upcoming else "HIGH IMPACT EVENTS"

        fractal = ASCIIArt.generate_mandelbrot(width=24, height=4, iterations=15)

        msg = (
            f"<pre>{fractal}</pre>\n\n"
            + BotStrings.CALENDAR_HEADER.format(title=title)
        )

        if upcoming:
            for ev in upcoming[:3]:  # Max 3 shown
                impact = ev.get('impact', 'M')
                imp_icon = "[H]" if impact == 'H' else "[M]" if impact == 'M' else "[L]"
                ev_title = ev.get('title', 'Event')[:28]
                time_str = ev.get('time', '--:--')[:5]
                date_raw = ev.get('date', '')
                try:
                    # Robust parsing: handles YYYY-MM-DD, MM-DD-YYYY, and others
                    if "-" in date_raw:
                        parts = date_raw.split("-")
                        if len(parts[0]) == 4: # YYYY-MM-DD
                            dt_obj = datetime.strptime(date_raw, "%Y-%m-%d")
                        else: # MM-DD-YYYY or DD-MM-YYYY (assuming US-centric FF fmt if not ISO)
                            dt_obj = datetime.strptime(date_raw, "%m-%d-%Y")
                    else:
                        dt_obj = datetime.now()
                    date_fmt = dt_obj.strftime("%m/%d")
                except:
                    # Fallback to safe slice if parsing fails
                    date_fmt = date_raw[5:].replace("-", "/") if len(date_raw) > 5 else date_raw
                
                msg += f"{imp_icon} <code>{date_fmt} {time_str}</code> {ev_title}\n"

            if len(upcoming) > 3:
                msg += f"\n<i>+{len(upcoming)-3} more events</i>\n"
        else:
            if sector:
                msg += f"<i>No upcoming {sector} events found.</i>\n"
            else:
                msg += "<i>No significant upcoming events. Market is calm.</i>\n"

        msg += (
            "\n<code>══════════════════════════</code>\n"
            "<b>[PULSE]</b> [H]=High [M]=Med [L]=Low\n"
            "<i>Intelligence synced from Global Calendars</i>"
        )

        # Sector filter buttons (only shown on front-page view)
        # Sector filter buttons (only shown on front-page view)
        if sector:
            keyboard = [
                # Just back to main Calendar + Home
                [{"text": "« ALL EVENTS", "callback_data": "EVENTS_VIEW"}],
                self._get_home_button()
            ]
        else:
            keyboard = [
                [
                    {"text": "◆ MACRO", "callback_data": "EVENTS_MACRO"},
                    {"text": "◈ CRYPTO", "callback_data": "EVENTS_CRYPTO"},
                ],
                [
                    {"text": "▽ TECH", "callback_data": "EVENTS_TECH"},
                    {"text": "⇄ FOREX", "callback_data": "EVENTS_FOREX"}
                ],
                # Ring Nav for Main View
                self._get_cyclical_nav("EVENTS")
            ]

        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup={"inline_keyboard": keyboard})
        else:
            await self.bot.send_message(chat_id, msg, reply_markup={"inline_keyboard": keyboard})


    async def handle_toggle_subscription(self, chat_id: int, user_id: int, symbol: str):
        """Toggles subscription for a symbol (Default: PRICE type)."""
        sm = get_subscription_manager()
        subs = sm.get_user_subscriptions(user_id)

        # Check if already subscribed to this symbol (any type, but prioritize PRICE)
        # We'll just check if ANY active subscription exists for this target
        existing = next((s for s in subs if s.target == symbol), None)

        if existing:
            success = sm.remove_subscription(user_id, existing.id)
            if success:
                await self.bot.answer_callback_query(chat_id, f"[OFF] Unsubscribed from {symbol}")
            else:
                await self.bot.answer_callback_query(chat_id, "[ERR] Error unsubscribing")
        else:
            success = sm.add_subscription(user_id, chat_id, "PRICE", symbol)
            if success:
                await self.bot.answer_callback_query(chat_id, f"[ON] Subscribed to {symbol}")
            else:
                await self.bot.answer_callback_query(chat_id, "[ERR] Error subscribing")

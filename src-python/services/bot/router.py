
import logging
from services.bot.handlers.system import SystemHandler
from services.bot.handlers.market import MarketHandler
from services.bot.handlers.account import AccountHandler
from services.bot.handlers.news import NewsHandler
from services.bot.handlers.stats import StatsHandler
from services.bot.handlers.ml import MLHandler
from services.bot.handlers.trading import TradingHandler
from services.bot.handlers.divine import DivineHandler
from services.bot.handlers.charts import ChartsHandler
from services.bot.handlers.subscription import SubscriptionHandler
from services.bot.handlers.yarn import YarnHandler
from services.bot.handlers.terminal import TerminalHandler
from services.bot.handlers.beacon import BeaconHandler
from services.symbol_normalizer import get_symbol_normalizer
from services.data_manager import get_data_manager

"""
THE BOT CORTEX (Router)
=======================
This is the switchboard. It routes user commands (TEXT/CALLBACKS) to specific Handlers.

HOW TO ADD A SNIPPET:
1. Create a method in the appropriate Handler (e.g. TradingHandler).
2. Register the command or callback here in `route_message` or `route_callback`.
3. Done. The Core handles the rest.

DO NOT put complex logic here. Route it.
"""

class CommandRouter:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("CommandRouter")
        
        # Initialize handlers
        self.system = SystemHandler(bot)
        self.market = MarketHandler(bot)
        self.account = AccountHandler(bot)
        self.news = NewsHandler(bot)
        self.stats = StatsHandler(bot)
        self.ml = MLHandler(bot)
        self.trading = TradingHandler(bot)
        self.divine = DivineHandler(bot)
        self.charts = ChartsHandler(bot)
        self.subscription = SubscriptionHandler(bot)
        self.yarn = YarnHandler(bot)
        self.terminal = TerminalHandler(bot)
        self.beacon = BeaconHandler(bot)

    async def route_command(self, command: str, args: list, chat_id: int, user_id: int = None, username: str = "Anon"):
        cmd = command.lower()
        self.logger.info(f"Routing '{cmd}' for {chat_id}")

        # [CENSUS] Track User Activity
        try:
            # Prefer unique user_id if available (for precise counting in groups)
            # Fallback to chat_id for DMs/Anons
            census_id = user_id if user_id else chat_id
            get_data_manager().update_user_activity(census_id)
        except:
            pass
        
        try:
            if cmd == "/start":
                await self.system.handle_start(chat_id)
            elif cmd == "/help":
                await self.system.handle_help(chat_id)
            elif cmd == "/commands":
                await self.system.handle_commands(chat_id)
            elif cmd == "/status":
                await self.system.handle_status(chat_id)
            # SOCIAL / YARN
            elif cmd in ["/yarn", "/comment"]:
                if args:
                    text = f"{command} {' '.join(args)}"
                    await self.yarn.handle_yarn_command(chat_id, user_id, username, text)
                else:
                     await self.system.send_message(chat_id, "Usage: /yarn <SYMBOL> <MESSAGE>")
            elif cmd == "/stats":
                await self.stats.handle_stats(chat_id, args)
            elif cmd in ["/buy", "/long", "/sell", "/short", "/close", "/exit", "/sl", "/tp", "/reset"]:
                await self.terminal.handle_cli_trade(chat_id, cmd, args)
            elif cmd == "/chart":
                await self.charts.handle_chart_command(chat_id, args)
            elif cmd == "/config":
                await self.system.handle_config(chat_id)
            elif cmd == "/info":
                await self.system.handle_info(chat_id)
            elif cmd == "/ip":
                await self.system.handle_ip(chat_id)
            elif cmd == "/beacon":
                await self.beacon.handle_beacon(chat_id)
            elif cmd == "/symbols":
                await self.system.handle_symbols(chat_id)
            elif cmd in ["/knowledge", "/wiki", "/docs"]:
                symbol = " ".join(args) if args else None
                await self.system.handle_knowledge_hub(chat_id, symbol=symbol)
            elif cmd == "/risk":
                await self.system.handle_risk(chat_id, args)
                
            elif cmd == "/daily":
                await self.market.handle_market_update(chat_id, "24h")
            elif cmd == "/hourly":
                await self.market.handle_market_update(chat_id, "1h")
            elif cmd == "/weekly":
                await self.market.handle_market_update(chat_id, "7d")
            elif cmd == "/price":
                if args:
                    normalizer = get_symbol_normalizer()
                    symbol = normalizer.normalize(args[0])
                    if symbol:
                        await self.market.handle_symbol_query(chat_id, symbol, "24h")
                    else:
                        await self.system.send_message(chat_id, "Usage: /price <SYMBOL> (e.g. /price BTC)")
                else:
                    await self.market.handle_price_tab(chat_id)
            elif cmd == "/symbol":
                if args:
                    normalizer = get_symbol_normalizer()
                    symbol = normalizer.normalize(args[0])
                    await self.market.handle_symbol_query(chat_id, symbol, "24h")
                else:
                    await self.system.send_message(chat_id, "Usage: /symbol <SYMBOL>")
            elif cmd == "/clusters":
                sector = args[0] if args else "all"
                await self.market.handle_clusters(chat_id, sector)
                
            elif cmd == "/wallet":
                await self.account.handle_wallet(chat_id)
            elif cmd == "/positions":
                await self.account.handle_positions(chat_id)
            elif cmd == "/trades":
                await self.account.handle_trades(chat_id)
            elif cmd == "/shadow":
                await self.account.handle_shadow(chat_id)
            elif cmd == "/performance":
                await self.account.handle_performance(chat_id)
            elif cmd == "/sync":
                await self.account.handle_sync_command(chat_id)

            elif cmd == "/events":
                sector = args[0] if args else None
                await self.market.handle_calendar(chat_id, sector=sector)

            elif cmd == "/news":
                symbol = args[0] if args else None
                await self.news.handle_news(chat_id, symbol)
            elif cmd == "/verify":
                if args:
                    await self.news.handle_verify(chat_id, args[0])
                else:
                    await self.system.send_message(chat_id, "Usage: /verify <SYMBOL>")

            elif cmd == "/predictions":
                symbol = args[0] if args else None
                await self.ml.handle_predictions(chat_id, symbol)
            elif cmd in ["/opportunities", "/scan", "/opps", "/signals"]:
                 symbol = args[0] if args else None
                 await self.trading.handle_opportunities(chat_id, symbol)
            elif cmd == "/scoreboard":
                 await self.trading.handle_leaderboard(chat_id)
            elif cmd == "/execute":
                 if args:
                     await self.terminal.handle_terminal(chat_id, symbol=args[0])
                 else:
                     await self.trading.handle_execute(chat_id)
            elif cmd == "/monitor":
                 await self.trading.handle_monitor(chat_id)

            elif cmd == "/physics":
                 if args:
                     normalizer = get_symbol_normalizer()
                     symbol = normalizer.normalize(args[0])
                     await self.ml.handle_physics(chat_id, symbol)
                 else:
                     await self.ml.handle_physics(chat_id, None)

            elif cmd == "/divine":
                 if args:
                     normalizer = get_symbol_normalizer()
                     symbol = normalizer.normalize(args[0])
                     await self.divine.handle_divine(chat_id, symbol)
                 else:
                     await self.divine.handle_divine(chat_id, None)
            
            else:
                # Fallback for dynamic symbol commands (e.g. /BTC, /ETH)
                if cmd.startswith("/") and len(cmd) > 1:
                    # Treat as symbol lookup
                    raw_symbol = cmd[1:] # Strip '/'
                    normalizer = get_symbol_normalizer()
                    # Check if it looks like a ticker (simple heuristic)
                    if raw_symbol.isalnum() or "=" in raw_symbol or "^" in raw_symbol:
                        symbol = normalizer.normalize(raw_symbol)
                        await self.market.handle_symbol_query(chat_id, symbol, "24h")
        except Exception as e:
            self.logger.error(f"Command routing error for '{cmd}': {e}", exc_info=True)
            await self.system.send_message(chat_id, f"[ERROR] Command failed: {type(e).__name__}")

    async def route_callback(self, data: str, chat_id: int, message_id: int, user_id: int):
        """Dispatches callback query data to the correct handler."""
        self.logger.info(f"Routing callback '{data}' for {chat_id}")
        
        # [CENSUS] Track User Activity
        try:
            # Prefer unique user_id if available (for precise counting in groups)
            # Fallback to chat_id for DMs/Anons
            census_id = user_id if user_id else chat_id
            get_data_manager().update_user_activity(census_id)
        except:
            pass
        
        if data == "START":
            await self.system.handle_start(chat_id, message_id=message_id) # Main menu can edit
        elif data == "HELP":
            await self.system.handle_help(chat_id, message_id=message_id)
        elif data == "COMMANDS_VIEW":
            await self.system.handle_commands(chat_id, message_id=message_id)
        elif data == "IP_AUDIT":
            await self.system.handle_ip(chat_id)
        elif data.startswith("CONFIG_"):
            if data == "CONFIG_VIEW":
                await self.system.handle_config(chat_id, message_id=message_id)
            else:
                await self.system.handle_config_action(chat_id, action=data, message_id=message_id)
        elif data == "TOGGLE_TRADING_MODE":
            await self.system.handle_mode_switch(chat_id)
            
        # --- LAUNCHERS (New "Window" Behavior) ---
        # Strategy: Send "Loading..." message first, then pass its ID to handler to EDIT.
        # This creates the "Opening new window" effect requested.
        
        elif data.startswith("KNOWLEDGE_HUB_") or data.startswith("WIKI_"):
            symbol = data.replace("KNOWLEDGE_HUB_", "").replace("WIKI_", "")
            loading = await self.system.send_message(chat_id, f"<b>[LOAD] Accessing Vault for {symbol}...</b>")
            lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
            await self.system.handle_knowledge_hub(chat_id, symbol=symbol, message_id=lid)

        elif data in ["KNOWLEDGE_HUB", "WIKI", "DOCS"]:
            loading = await self.system.send_message(chat_id, "<b>[LOAD] Opening Knowledge Base...</b>")
            lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
            await self.system.handle_knowledge_hub(chat_id, message_id=lid)
            
        elif data == "PRICE_LANDING":
             await self.market.handle_price_tab(chat_id, message_id=message_id, user_id=user_id)
        
        elif data.startswith("PRICE_"):
             # Back button or direct navigation from other tabs
             symbol = data.replace("PRICE_", "")
             await self.market.handle_symbol_query(chat_id, symbol, "24h")

        elif data.startswith("STATS_"):
             # Launch Stats Window
             parts = data.split("_")
             symbol = parts[1]
             loading = await self.system.send_message(chat_id, f"<b>[LOAD] Computing Cockpit Analytics: {symbol}...</b>")
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
             await self.stats.handle_stats(chat_id, parts[1:], message_id=lid)

        elif data.startswith("ALERT_"):
             symbol = data.replace("ALERT_", "")
             # Actually create the subscription (wire to real SUBS system)
             await self.subscription.handle_subscribe(chat_id, user_id, f"subscribe_PRICE_{symbol}")

        elif data == "NEWS_HUB":
             loading = await self.system.send_message(chat_id, "<b>[LOAD] Fetching Global Headlines...</b>")
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
             await self.news.handle_news(chat_id, message_id=lid)
             
        elif data.startswith("NEWS_"):
             # Support symbol specific or categorized news
             # Patterns: NEWS_BTC, NEWS_CAT_TECH, NEWS_GLOBAL
             symbol = None
             sector = None
             
             if data == "NEWS_GLOBAL":
                 pass
             elif data.startswith("NEWS_CAT_"):
                 sector = data.replace("NEWS_CAT_", "")
             else:
                 symbol = data.replace("NEWS_", "")
             
             loading = await self.system.send_message(chat_id, f"<b>[LOAD] Syncing {symbol or sector or 'Market'} Intel...</b>")
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
             await self.news.handle_news(chat_id, symbol=symbol, sector=sector, message_id=lid)

        elif data.startswith("CAL"):
             # Support global or symbol-auto
             symbol = None
             sector = None
             if data.startswith("CAL_AUTO_"):
                 symbol = data.replace("CAL_AUTO_", "")
                 from config import get_settings
                 # Map symbol to sector
                 tax = get_settings().UNIVERSE_TAXONOMY
                 for s, members in tax.get("SECTORS", {}).items():
                     if symbol in members:
                         sector = s
                         break
                 if not sector:
                     # Check prefixes
                     prefixes = tax.get("PREFIXES", {})
                     if any(symbol.startswith(p) for p in prefixes.get("CRYPTO", [])): sector = "CRYPTO"
                     elif any(symbol.startswith(p) for p in prefixes.get("GLOBAL", [])): sector = "MACRO"

             loading = await self.system.send_message(chat_id, "<b>[LOAD] Syncing Economic Events...</b>")
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
             await self.market.handle_calendar(chat_id, sector=sector, message_id=lid)

        elif data.startswith("CLUSTER_"):
             cluster = data.replace("CLUSTER_", "")
             # Clusters often want to Edit the current message for a smooth transition
             await self.market.handle_cluster_view(chat_id, cluster, message_id=message_id)

        elif data.startswith("LEADERBOARD"):
             # Patterns: LEADERBOARD_GLOBAL, LEADERBOARD_SYM_BTC
             symbol = data.replace("LEADERBOARD_SYM_", "").replace("LEADERBOARD_GLOBAL", "")
             if not symbol or symbol == data: symbol = None
             
             loading = await self.system.send_message(chat_id, f"<b>[LOAD] Syncing Global ROI Leaderboard...</b>")
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else None
             await self.trading.handle_leaderboard(chat_id, symbol=symbol, message_id=lid)

        # COMBINED PUBLIC TAB (Yarn + Scan)
        elif "PUBLIC_" in data or "YARN_" in data:
             symbol = data.replace("PUBLIC_", "").replace("YARN_", "")
             if symbol == "GLOBAL": symbol = None
             
             txt = f"<b>[LOAD] Tuning into {symbol or 'GLOBAL'} frequency...</b>"
             loading = await self.system.send_message(chat_id, txt)
             lid = loading.get("result", {}).get("message_id") if isinstance(loading, dict) else getattr(loading, "message_id", None)
             await self.yarn.handle_yarn(chat_id, symbol=symbol, message_id=lid)

        # ... other handlers ...

        # ... keeps other logic ...

        elif data == "OPPORTUNITIES" or data == "OPPS_LIST":
             await self.trading.handle_opportunities(chat_id)
        elif data.startswith("OPPS_LIST_"):
             symbol = data.replace("OPPS_LIST_", "")
             # If user explicitly asks for JUST Scan, we can still show it, or redirect to Public?
             # User said "remove functionality linked to scan... replace with... scan"
             # I'll force Scan to be a new window too just in case.
             await self.trading.handle_opportunities(chat_id, symbol_filter=symbol)
             
        elif data.startswith("EXECUTE_HUB_"):
             symbol = data.replace("EXECUTE_HUB_", "")
             await self.terminal.handle_terminal(chat_id, symbol=symbol, message_id=message_id)

        elif data.startswith("TERMINAL_"):
             symbol = data.replace("TERMINAL_", "")
             await self.terminal.handle_terminal(chat_id, symbol=symbol, message_id=message_id)

        elif data.startswith("TRADE_"):
             # Format: TRADE_ACTION_SYMBOL (e.g. TRADE_BUY_BTC, TRADE_CLOSE_ETH)
             parts = data.split("_")
             if len(parts) >= 3:
                 action = parts[1] # BUY, SELL, CLOSE, RISK, ADD
                 symbol = parts[2]
                 await self.terminal.handle_trade_command(chat_id, symbol, action, message_id=message_id)

        elif data.startswith("ALERT_SET_"):
             symbol = data.replace("ALERT_SET_", "")
             await self.terminal.handle_alert_command(chat_id, symbol, message_id=message_id)

        elif data == "MONITOR_LIVE":
             await self.trading.handle_monitor(chat_id)
             
        elif data.startswith("CHART_"):
             symbol = data.replace("CHART_", "")
             await self.charts.send_chart(chat_id, symbol)
             
        elif data.startswith("DIVINE_REFRESH_"):
             # Divine Refresh often wants to Edit, but let's see. 
             # Usually keep refresh in-place.
             symbol = data.replace("DIVINE_REFRESH_", "")
             await self.divine.handle_divine(chat_id, symbol, message_id=message_id) 
        
        elif data.startswith("DIVINE_FORCE_"):
             symbol = data.replace("DIVINE_FORCE_", "")
             
             # --- SECURITY CHECK ---
             from config import get_settings
             settings = get_settings()
             admin_id = str(settings.TELEGRAM_CHAT_ID) if settings.TELEGRAM_CHAT_ID else ""
             whitelist = settings.TELEGRAM_WHITELIST_IDS.split(",") if settings.TELEGRAM_WHITELIST_IDS else []
             
             user_id_str = str(chat_id)
             is_admin = (user_id_str == admin_id) or (user_id_str in whitelist)
             
             if not is_admin:
                 # Silent fail or generic confusion to prevent DoS probing
                 await self.bot.answer_callback_query(callback_query_id, text="System Busy [Priority Queue Full]")
                 return

             # 1. Show "Dreaming..." state
             await self.bot.edit_message_text(chat_id, message_id, "<b>[DMT DRIP] Inducing Epiphany...</b>", parse_mode="HTML")
             # 2. Force Pattern Update (Async)
             try:
                 from services.episode_pattern_matcher import get_episode_pattern_matcher
                 matcher = get_episode_pattern_matcher()
                 await matcher.update_patterns(force=True, include_theoretical=True)
             except Exception as e:
                 self.logger.error(f"Force Epiphany failed: {e}")
             
             # 3. Refresh View
             await self.divine.handle_divine(chat_id, symbol, message_id=message_id) 

        elif data == "STATS_REFRESH_WALLET":
             await self.stats.handle_stats(chat_id, [], message_id=message_id)
        elif data.startswith("EVENTS_"):
            sector = data.replace("EVENTS_", "")
            if sector == "VIEW": sector = None
            
            # --- SYMBOL TO SECTOR AUTO-MAP ---
            # If user clicked a button for a symbol, map it to a sector for the calendar
            if sector and sector not in ["MACRO", "CRYPTO", "TECH", "FOREX"]:
                from config import get_settings
                settings = get_settings()
                tax = settings.UNIVERSE_TAXONOMY
                # Check sectors
                found = False
                for s, members in tax.get("SECTORS", {}).items():
                    if sector in members:
                        sector = s
                        found = True
                        break
                if not found:
                    # Check prefixes
                    prefixes = tax.get("PREFIXES", {})
                    if any(sector.startswith(p) for p in prefixes.get("CRYPTO", [])): sector = "CRYPTO"
                    elif any(sector.startswith(p) for p in prefixes.get("GLOBAL", [])): sector = "MACRO"
            
            await self.market.handle_calendar(chat_id, sector=sector, message_id=message_id)
        elif data.startswith("KARMA_UP_") or data.startswith("KARMA_DOWN_"):
             is_up = data.startswith("KARMA_UP_")
             direction = "UP" if is_up else "DOWN"
             symbol = data.replace("KARMA_UP_", "").replace("KARMA_DOWN_", "")
             await self.yarn.handle_karma_vote(chat_id, user_id, symbol, direction, message_id=message_id)

        elif data == "HYPER_FRACTAL":
             await self.system.handle_hyper_fractal(chat_id, message_id=message_id)
        elif data == "HYPER_SUMMARY":
             await self.system.handle_hyper_summary(chat_id, message_id=message_id, user_id=user_id)
        elif data == "CINEMA_FRACTAL":
             await self.system.handle_cinema_fractal(chat_id, message_id=message_id, user_id=user_id)
        elif data.startswith("CINEMA_"):
             # CINEMA_PLAY, CINEMA_PAUSE, CINEMA_NEXT, CINEMA_BACK
             await self.system.handle_cinema_control(chat_id, action=data, message_id=message_id)
        elif data.startswith("SYMBOLS_TAB_"):
             await self.system.handle_symbols(chat_id, data=data, message_id=message_id)
        elif "TOGGLE_SIMPLE_MODE" in data or "SET_STYLE_" in data:
             await self.system.handle_mode_toggle(chat_id, data, message_id, user_id)

        elif data.startswith("TOGGLE_SUB_"):
             symbol = data.replace("TOGGLE_SUB_", "")
             if symbol == "GLOBAL": symbol = None
             if symbol:
                await self.market.handle_toggle_subscription(chat_id, user_id, symbol)
             else:
                await self.bot.answer_callback_query(chat_id, "Cannot subscribe to GLOBAL context.")

        elif data.startswith("CLOSE_"):
             symbol = data.replace("CLOSE_", "")
             await self.trading.handle_close_position(chat_id, symbol)

        elif data.split("_")[0] == "RISK": # RISK_UP, RISK_DOWN
             direction = data.split("_")[-1]
             await self.trading.handle_risk_adjustment(chat_id, direction)
        elif data == "HISTORY_LOG":
             self.logger.error(f"!!! DEBUG: ROUTER HIT HISTORY_LOG for {chat_id} !!!")
             # await self.bot.answer_callback_query(chat_id, "Fetching terminal trade log...") 
             await self.account.handle_trades(chat_id)
        
        elif data == "WALLET_STATS":
             await self.account.handle_wallet(chat_id)
        elif data == "WALLET_SYNC":
             await self.account.handle_sync_command(chat_id)
             
        elif data == "POSITIONS":
             await self.account.handle_positions(chat_id)

        elif data.startswith("SESSION_"):
             session = data.replace("SESSION_", "")
             await self.market.handle_session(chat_id, session, message_id=message_id)
        
        # --- SUBSCRIPTION MANAGEMENT ---
        elif data == "MANAGE_SUBS":
             await self.subscription.handle_manage_subscriptions(chat_id, user_id, message_id=message_id)

        elif data.startswith("SUB_INT_"):
             # Adjustment (e.g. SUB_INT_DEC_60)
             await self.subscription.handle_interval_adjust(chat_id, user_id, data, message_id=message_id)

        elif data == "TOGGLE_PAUSE":
             await self.subscription.handle_toggle_pause(chat_id, user_id, message_id=message_id)

        elif data.startswith("unsubscribe_"):
             await self.subscription.handle_unsubscribe(chat_id, user_id, data, message_id=message_id)
        
        else:
            self.logger.warning(f"Unhandled callback: {data}")

    async def route_message(self, text: str, chat_id: int, user_id: int, username: str = "Anon", reply_to_message: dict = None):
        """Handles plain text messages (e.g. ticker names) and contextual replies."""
        
        # 1. Check for Contextual Reply (YARN)
        if reply_to_message:
            reply_text = reply_to_message.get("text", "")
            if "[ YARN ]" in reply_text:
                try:
                    # Extract Symbol from Header: "[ YARN ] SYMBOL"
                    header_line = reply_text.split("\n")[0]
                    # Split by closing bracket payload
                    if "]" in header_line:
                        symbol_part = header_line.split("]")[-1].strip()
                        # Handle GLOBAL THREAD vs Specific
                        target_symbol = symbol_part.split()[0] if symbol_part and "GLOBAL" not in symbol_part else "GLOBAL"
                    else:
                        target_symbol = "GLOBAL"

                    # Construct synthetic command
                    synthetic_cmd = f"/yarn {target_symbol} {text}"
                    await self.yarn.handle_yarn_command(chat_id, user_id, username, synthetic_cmd)
                    return
                except Exception as e:
                    self.logger.error(f"Yarn reply routing failed: {e}")

        # 2. Symbol Lookup Logic
        clean_text = text.strip().upper()
        
        # Simple symbol matcher (e.g. BTC, ETH, GOLD)
        # Avoid matching long sentences
        if len(clean_text) <= 10 and " " not in clean_text:
             # Normalize first (e.g. GOLD -> GC=F)
             normalizer = get_symbol_normalizer()
             symbol = normalizer.normalize(clean_text)
             
             # If normalization changed it or it's a known short ticker
             if symbol:
                 await self.market.handle_symbol_query(chat_id, symbol, "24h")
             else:
                 await self.system.send_message(chat_id, f"❓ {clean_text} unknown.")
        else:
             # Ignore or silent
             pass

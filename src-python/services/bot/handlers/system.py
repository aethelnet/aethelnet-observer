
"""
System Handler
Manages core system interactions, help menus, and status checks.
"""
# pylint: disable=broad-exception-caught, logging-fstring-interpolation, too-many-locals
# pylint: disable=import-outside-toplevel, too-many-statements, line-too-long
# pylint: disable=bare-except, function-redefined, no-member, undefined-variable
# pylint: disable=redefined-outer-name, reimported, unused-import, unused-variable

import asyncio
import time
import math
import random
import hashlib
import io
from datetime import datetime
from services.bot.handlers.base import BaseHandler
from services.bot.formatters import format_config, format_system_status
from services.aesthetic_service import ASCIIArt
from services.data_manager import get_data_manager
from services.opportunity_cache import get_opportunity_cache
from services.bot.summary_composer import SummaryComposer
from services.knowledge_service import get_knowledge_service
from config.strings import BotStrings

class SystemHandler(BaseHandler):
    def __init__(self, bot):
        super().__init__(bot)
        # Persistent memory for Dream State (ChatID -> Frame)
        self.dream_states = {}

    def _get_behelit_icon(self) -> str:
        """Fetch the current lore-based icon for the Behelit state."""
        try:
            from services.brain import get_engine
            engine = get_engine()
            btc_state = engine.states.get("BTCUSDT", {})
            regime = btc_state.get('regime', 'EQUI')
            
            mapping = {
                "EQUI": "⨀", "JOY": "⏀", "SAD": "⏁", "ANGER": "⊗"
            }
            crowns = {
                "EQUI": ("⫷ ─ ⟐ ─", "─ ⟐ ─ ⫸"),
                "JOY": ("⫷ ─ ▴ ─", "─ ▴ ─ ⫸"),
                "SAD": ("⫷ ─ ▾ ─", "─ ▾ ─ ⫸"),
                "ANGER": ("≪ ─ ◈ ─", "─ ◈ ─ ≫")
            }
            main_sym = mapping.get(regime, "⟐")
            left, right = crowns.get(regime, ("·─", "─·"))
            return f"{left} {main_sym} {right}"
        except:
            return "·─ ⟐ ─·"

    async def handle_start(self, chat_id: int, message_id: int = None, user_id: int = None):
        """Clean, welcoming start menu with clear value prop and donation visibility."""
        dm = get_data_manager()
        u_id = user_id or chat_id
        
        # Get evolving fractal parameters based on session state
        params = await asyncio.to_thread(dm.get_fractal_params, u_id)
        
        # KILL ALL ANIMATIONS ON START
        try:
            for job_name in [f"hyper_{chat_id}", f"cinema_{chat_id}"]:
                for job in self.bot.job_queue.get_jobs_by_name(job_name):
                    job.schedule_removal()
        except: pass
        
        # [CRYPTIC SEED]: Explicit coordinates for "Alien Structure" look
        # Replaces generic params to guarantee a "Cool/Cryptic" first impression.
        fractal = ASCIIArt.generate_mandelbrot(
            width=52,  # Wide cinematic
            height=20, # Tall enough for detail
            iterations=150, # High iteration for noise/glitch texture
            zoom=2500.0,    # Deep zoom into structure
            center_x=-0.7436438870371587, 
            center_y=0.1318259042053119   # Seahorse Valley Deep Dive
        )
        
        # Get User Stats
        stats = await asyncio.to_thread(dm.get_user_stats)
        total_p = stats.get('total', 0)
        active_p = stats.get('active', 0)

        msg = (
            f"<pre>{fractal}</pre>\n\n"
            + BotStrings.WELCOME_MESSAGE
            + f"\n\n<blockquote><b>NETWORK</b>: {total_p} Units | {active_p} Active (24h)</blockquote>"
        )
        
        # Button grid: main actions (Nokia v2 Hub)
        keyboard = [
            # Row 1: Core Markets
            [
                {"text": "[ PRICE ]", "callback_data": "PRICE_LANDING"},
                {"text": "[ SCAN ]", "callback_data": "OPPORTUNITIES"},
                {"text": "[ WALLET ]", "callback_data": "WALLET_STATS"}
            ],
            # Row 2: Intel & Social
            [
                {"text": "[ NEWS ]", "callback_data": "NEWS_HUB"},
                {"text": "[ EVENTS ]", "callback_data": "CALENDAR_VIEW"},
                {"text": "[ YARN ]", "callback_data": "YARN_GLOBAL"}
            ],
            # Row 3: Support & Community
            [
                {"text": "[ SUBS ]", "callback_data": "MANAGE_SUBS"},
                {"text": "[ HELP ]", "callback_data": "HELP"},
                {"text": "[ COMMUNITY ]", "url": "https://t.me/ProphitEngine"}
            ]
        ]
        
        reply_markup = {"inline_keyboard": keyboard}
        
        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            await self.send_markup(chat_id, msg, reply_markup, disable_web_page_preview=True)

    def _load_lexicon(self) -> dict:
        """
        Loads the 'Lexicon' (curated knowledge).
        In a full system, this would load from a JSON/YAML file.
        For now, we return a hardcoded 'Primer' for major assets.
        """
        try:
            import json
            import os
            path = "backend/data/universe_lexicon.json"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Bi-directional Indexing: Map both display symbols (BTC) and raw tickers (BTCUSDC)
                    indexed = {}
                    from services.symbol_normalizer import get_symbol_normalizer
                    normalizer = get_symbol_normalizer()
                    
                    for raw, doc in data.items():
                        indexed[raw.upper()] = doc
                        display = normalizer.to_display(raw.upper())
                        if display != raw.upper():
                            indexed[display] = doc
                        
                        # Also index common variations (BTCUSD, BTCUSDT for BTCUSDC entry)
                        for suffix in ["USDC", "USDT", "USD", "BUSD"]:
                            if raw.upper().endswith(suffix):
                                base = raw.upper().replace(suffix, "")
                                indexed[base] = doc
                                # Also add other suffix combos
                                for alt_suffix in ["USDC", "USDT", "USD"]:
                                    indexed[base + alt_suffix] = doc
                                break
                            
                    return indexed
        except Exception as e:
            self.logger.error(f"Failed to load lexicon: {e}")

        return {
            "BTC": {
                "name": "Bitcoin",
                "sector": "Store of Value",
                "archetype": "The King",
                "strategy": "Trend Following",
                "desc": "The pristine collateral of the digital age. High correlation to global liquidity. Cycles are defined by the Halving."
            },
            "ETH": {
                "name": "Ethereum",
                "sector": "Smart Contracts",
                "archetype": "The World Computer",
                "strategy": "Beta Rotation",
                "desc": "The backbone of DeFi and NFTs. Moves with high beta to BTC during risk-on. Infinite supply but deflationary burn mechanism."
            },
            "SOL": {
                "name": "Solana",
                "sector": "L1 / Speed",
                "archetype": "The Speed Demon",
                "strategy": "Momentum / PVP",
                "desc": "High throughput, low latency. The casino of choice for retail speculation. Prone to explosive moves and congestion."
            },
            "BNB": {
                "name": "Binance Coin",
                "sector": "Exchange Token",
                "archetype": "The House",
                "strategy": "Utility / Burn",
                "desc": "Powering the Binance ecosystem. Deflationary burns. Regulatory risk proxy."
            },
            "XRP": {
                "name": "Ripple",
                "sector": "Payments",
                "archetype": "The Banker",
                "strategy": "Event Driven",
                "desc": "The standard for cross-border settlements. Price action is heavily driven by legal news and partnerships."
            }
        }

    async def handle_knowledge_hub(self, chat_id: int, message_id: int = None, symbol: str = None):
        """
        The Knowledge Hub (Wiki/Docs/Lore).
        - If 'symbol' matches a Lexicon entry: Show Intel.
        - If 'symbol' is a search query: Search Vault.
        - Default: Show Hub Menu.
        """
        ks = get_knowledge_service()
        
        # 1. Input Provided (Symbol or Search Query)
        if symbol:
            symbol_upper = symbol.upper()
            # Normalize for Lexicon (BTCUSDC, BTCUSDT or nicknames -> BTC)
            # Use nicknames reversed if it's a nickname
            lookup_key = symbol_upper
            suffixes = ["USDT", "USDC", "=X", "=F"]
            for sfx in suffixes:
                if lookup_key.endswith(sfx):
                    lookup_key = lookup_key.replace(sfx, "")
                    break
            
            # Special case for indices/^ prefixes
            if lookup_key.startswith("^"): lookup_key = lookup_key[1:]

            lexicon = await asyncio.to_thread(self._load_lexicon)
            
            # A. Check Lexicon (Try normalized lookup_key, then display_key, then raw symbol)
            # EXCEPTION: 'VALUE' and 'ALIGNMENT' should bypass Lexicon and go straight to Vault (Manifesto)
            if lookup_key in ["VALUE", "ALIGNMENT", "VALUE ALIGNMENT"]:
                data = None
            else:
                data = lexicon.get(lookup_key) or lexicon.get(symbol_upper)
            
            # Check for CATEGORY queries (MACRO, CRYPTO, TECH, FOREX)
            CATEGORY_PAGES = {
                "MACRO": {
                    "header": "[ MACRO & ECONOMICS ]",
                    "content": (
                        "<b>CORE DATA SOURCES</b>\n"
                        "• <a href='https://fred.stlouisfed.org/'>FRED</a> - US Economic Data\n"
                        "• <a href='https://tradingeconomics.com/'>Trading Economics</a> - Global Calendar\n"
                        "• <a href='https://www.bls.gov/'>BLS</a> - Employment & Inflation\n\n"
                        "<b>KEY CONCEPTS</b>\n"
                        "• <b>CPI</b> - Consumer Price Index (Inflation)\n"
                        "• <b>NFP</b> - Non-Farm Payrolls (Jobs)\n"
                        "• <b>FOMC</b> - Fed rate decisions\n"
                        "• <b>Yield Curve</b> - Recession indicator\n\n"
                        "<b>STRATEGY</b>\n"
                        "<i>Macro traders position based on central bank policy divergence and economic cycle timing.</i>"
                    )
                },
                "CRYPTO": {
                    "header": "[ CRYPTO & ON-CHAIN ]",
                    "content": (
                        "<b>ON-CHAIN ANALYTICS</b>\n"
                        "• <a href='https://glassnode.com/'>Glassnode</a> - Whale Flows\n"
                        "• <a href='https://cryptoquant.com/'>CryptoQuant</a> - Exchange Reserves\n"
                        "• <a href='https://dune.com/browse/dashboards'>Dune</a> - Custom Queries\n\n"
                        "<b>RESEARCH</b>\n"
                        "• <a href='https://messari.io/research'>Messari</a> - Institutional Reports\n"
                        "• <a href='https://defillama.com/'>DefiLlama</a> - TVL & Protocol Data\n\n"
                        "<b>KEY METRICS</b>\n"
                        "• <b>MVRV</b> - Market Value / Realized Value\n"
                        "• <b>NUPL</b> - Net Unrealized Profit/Loss\n"
                        "• <b>Exchange Outflows</b> - Accumulation signal\n\n"
                        "<i>On-chain = seeing the blockchain's actual state, not just price.</i>"
                    )
                },
                "STOCKS": {
                    "header": "[ EQUITIES & TECH ]",
                    "content": (
                        "<b>FILINGS & DATA</b>\n"
                        "• <a href='https://www.sec.gov/edgar/searchedgar/companysearch'>SEC EDGAR</a> - 10-K, 10-Q, 8-K\n"
                        "• <a href='http://openinsider.com/'>OpenInsider</a> - Form 4 Filings\n"
                        "• <a href='https://finviz.com/screener.ashx'>Finviz</a> - Stock Screener\n\n"
                        "<b>KEY CONCEPTS</b>\n"
                        "• <b>P/E Ratio</b> - Price to Earnings\n"
                        "• <b>EPS</b> - Earnings Per Share\n"
                        "• <b>Beta</b> - Volatility relative to market\n"
                        "• <b>IV</b> - Implied Volatility (Options)\n\n"
                        "<b>STRATEGY</b>\n"
                        "<i>Follow the money. Cluster insider buying at 52-week lows is the strongest signal.</i>"
                    )
                },
                "FOREX": {
                    "header": "[ FOREX & RATES ]",
                    "content": (
                        "<b>RATE MARKETS</b>\n"
                        "• <a href='https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html'>CME FedWatch</a> - Rate Expectations\n"
                        "• <a href='https://www.forexfactory.com/calendar'>Forex Factory</a> - Economic Calendar\n\n"
                        "<b>EDUCATION</b>\n"
                        "• <a href='https://www.babypips.com/learn/forex/what-is-a-pip'>What is a Pip?</a>\n"
                        "• <a href='https://www.babypips.com/learn/forex'>BabyPips School</a> - From Zero\n"
                        "• <a href='https://www.dailyfx.com/education'>DailyFX Education</a> - Intermediate\n\n"
                        "<b>MAJOR PAIRS</b>\n"
                        "• <b>EUR/USD</b> - \"The Fiber\" (Most Liquid)\n"
                        "• <b>GBP/USD</b> - \"The Cable\" (Volatile)\n"
                        "• <b>USD/JPY</b> - \"The Gopher\" (Rate Sensitive)\n\n"
                        "<i>FX is a game of relative strength between economies.</i>"
                    )
                },
                "GLOSSARY": {
                    "header": "[ METRIC GLOSSARY ]",
                    "content": (
                        "<b>BASIC TERMS</b>\n"
                        "• <b>Bullish / Bearish</b>: Market bias toward appreciation or depreciation.\n"
                        "• <b>PnL</b>: Profit and Loss. Net financial result of trading operations.\n"
                        "• <b>Equity</b>: Real-time liquidation value (Cash + Active Trade Value).\n"
                        "• <b>Free / Locked</b>: Capital availability vs capital committed to margin.\n\n"
                        "<b>CORE SYSTEM METRICS</b>\n"
                        "• <b>Resonance (Psi)</b>: Measuring deviation from the mean. Scores > 2.0 indicate extreme 'exhaustion' and reversal probability.\n"
                        "• <b>Regime</b>: Gaussian classification of market environment (Calm, Volatile, or Crash).\n"
                        "• <b>Council Weight</b>: The ratio of bot autonomy vs manual control (100% = Full Auto).\n"
                        "• <b>Phase (Hilbert)</b>: Cyclical timing. Tracks the journey from Trough (-1.0) to Peak (1.0).\n"
                        "• <b>Stability</b>: Harmonic cohesion. High stability suggests clean trends; low stability indicates erratic noise.\n\n"
                        "<b>ADVANCED KINETICS</b>\n"
                        "• <b>Velocity</b>: The speed at which Resonance entropy is shifting.\n"
                        "• <b>Force</b>: Momentum acceleration weighted by liquid mass.\n"
                        "• <b>Strain</b>: Market tension indicating the trend is overextended.\n"
                        "• <b>Squeeze</b>: Volatility compression preceding high-energy breakouts.\n"
                        "• <b>Flow</b>: Aggregated liquidity direction and whale positioning.\n"
                        "• <b>Entropy</b>: Signal noise ratio. High entropy indicates unpredictable chaos.\n\n"
                        "<b>EXECUTION & RISK</b>\n"
                        "• <b>Stop Loss / Profit Target</b>: Automated risk-mitigation and exit protocols.\n"
                        "• <b>Position Size</b>: Capital percentage allocated to a single trade instance.\n"
                        "• <b>Signal Threshold</b>: The minimum deviation (Resonance) required for entry.\n"
                        "• <b>Persistence</b>: Confirmation ticks required to validate a signal and filter noise.\n"
                        "• <b>Win Rate / Drawdown</b>: Performance metrics tracking success ratio and capital safety.\n\n"
                        "<i>Configure these parameters in /risk or /config.</i>"
                    )
                }
            }
            
            if symbol_upper in CATEGORY_PAGES:
                cat = CATEGORY_PAGES[symbol_upper]
                header = f"<b>{cat['header']}</b>"
                content = cat['content']
                keyboard = [
                    [{"text": "« BACK TO HUB", "callback_data": "KNOWLEDGE_HUB"}],
                    self._get_home_button()
                ]
            elif data:
                header = f"<b>[ KNOWLEDGE: {lookup_key} ]</b>"
                content = (
                    f"<b>PROFILE</b>\n"
                    f"• Name: <code>{data.get('name', symbol_upper)}</code>\n"
                    f"• Sector: <code>{data.get('sector', 'Unknown')}</code>\n"
                    f"• Archetype: <code>{data.get('archetype', 'Asset')}</code>\n\n"
                    "<b>STRATEGY</b>\n"
                    f"• Bias: <code>{data.get('strategy', 'General')}</code>\n\n"
                    "<b>WIKI ABSTRACT</b>\n"
                    f"<i>{data.get('desc', '')}</i>"
                )
                keyboard = []
                
                # 1. Alternative Button (Soft Intervention / Conscious Choice) - TOP PRIORITY
                alt = data.get("alternative")
                if alt:
                    keyboard.append([{"text": f"BUILD {alt}", "callback_data": f"PRICE_{alt}"}])

                # UNIVERSAL: Always provide access to the Value Manifest
                keyboard.append([{"text": "{ VALUES }", "callback_data": "KNOWLEDGE_HUB_Value Alignment"}])
                
                # 3. Cyclical Nav
                keyboard.append(self._get_cyclical_nav("SYMBOL"))
            
            # B. Semantic Search in Vault
            else:
                # Ensure vault is ingested if we have no docs (Recovery mechanism)
                if not ks.documents:
                    await asyncio.to_thread(ks.ingest_vault)
                
                # Boost relevance for Value Alignment (Target the Philosophy, not the Config)
                search_query = symbol
                if symbol.upper() in ["VALUE ALIGNMENT", "VALUE", "ALIGNMENT"]:
                    search_query = "Philosophy Gestalt Regenerative Finance voting on the future shape of the world"
                
                results = await asyncio.to_thread(ks.search, search_query, top_k=2)
                
                # SELF-HEALING V2: If Value Alignment search fails, the index is likely stale.
                # Force a rebuild and try again.
                if not results and symbol.upper() in ["VALUE ALIGNMENT", "VALUE", "ALIGNMENT"]:
                     await asyncio.to_thread(ks.ingest_vault, force_rebuild=True)
                     results = await asyncio.to_thread(ks.search, search_query, top_k=2)
                
                if results:
                    header = f"<b>[ ARCHIVES: '{symbol}' ]</b>"
                    content = ""
                    for i, r in enumerate(results):
                        snippet = r['content'][:500].replace("<", "&lt;").replace(">", "&gt;") + "..."
                        content += f"<b>{i+1}. {r['source']}</b>\n<i>{snippet}</i>\n\n"
                    content += "<i>(Source: The Vault)</i>"
                else:
                    header = f"<b>[ KNOWLEDGE: {symbol_upper} ]</b>"
                    content = (
                        "<b>UNKNOWN ENTITY</b>\n"
                        "• No Lexicon entry found.\n"
                        "• No Vault files matched query.\n\n"
                        "<i>Try a different keyword or symbol.</i>"
                    )
                
                keyboard = [
                    [{"text": "« BACK TO HUB", "callback_data": "KNOWLEDGE_HUB"}],
                    self._get_home_button()
                ]

        # 2. Main Hub Menu
        else:
            doc_count = len(ks.documents)
            
            header = "<b>[ KNOWLEDGE HUB ]</b>"
            content = (
                "<b>TRADING PRINCIPLES</b>\n"
                "Universal truths that apply to all markets.\n\n"
                
                "<b>1. RISK MANAGEMENT</b>\n"
                "• Never risk more than 1-2% of capital per trade\n"
                "• Define your exit before you enter\n"
                "• Position sizing > picking the right direction\n\n"
                
                "<b>2. MARKET STRUCTURE</b>\n"
                "• Price moves in trends and ranges\n"
                "• Higher timeframes dominate lower ones\n"
                "• Liquidity attracts price (gaps get filled)\n\n"
                
                "<b>3. EDGE PRESERVATION</b>\n"
                "• An edge is statistical, not guaranteed\n"
                "• Win rate matters less than risk/reward\n"
                "• Consistency beats heroics\n\n"
                
                "<b>4. PSYCHOLOGY</b>\n"
                "• The market rewards patience\n"
                "• FOMO and revenge trading destroy accounts\n"
                "• Journal your trades, learn from losses\n\n"
                
                "<i>Select a category below for curated resources and links.</i>"
            )
            keyboard = [
                # Quick Category Searches
                [
                    {"text": "[ MACRO ]", "callback_data": "WIKI_MACRO"},
                    {"text": "[ CRYPTO ]", "callback_data": "WIKI_CRYPTO"},
                ],
                [
                    {"text": "[ STOCKS ]", "callback_data": "WIKI_STOCKS"},
                    {"text": "[ FOREX ]", "callback_data": "WIKI_FOREX"}
                ],
                [
                    {"text": "[ GLOSSARY ]", "callback_data": "WIKI_GLOSSARY"},
                    {"text": "{ VALUES }", "callback_data": "WIKI_VALUE"}
                ],
                # Nav
                self._get_home_button()
            ]

        msg = f"{header}\n<code>════════════════════════════════</code>\n\n{content}"
        
        reply_markup = {"inline_keyboard": keyboard}
        
        if message_id:
             try:
                 await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=reply_markup, parse_mode="HTML")
             except:
                 await self.bot.send_message(chat_id, msg, reply_markup=reply_markup, parse_mode="HTML")
        else:
             await self.bot.send_message(chat_id, msg, reply_markup=reply_markup, parse_mode="HTML")
            
    def _classify_asset(self, sym):
        if "USD" in sym or "BTC" in sym or "ETH" in sym: return "CRYPTO"
        if "=F" in sym: return "FUTURES"
        return "EQUITY"

    async def handle_help(self, chat_id: int, message_id: int = None):
        dm = get_data_manager()
        active_style = await asyncio.to_thread(dm.get_user_intel_style, chat_id)
        simple_mode = await asyncio.to_thread(dm.get_user_simple_mode, chat_id)
        
        if simple_mode == 1:
            header = "<b>[ AURATIC SIMPLE GUIDE ]</b>"
            content = BotStrings.HELP_SIMPLE
        else:
            style = active_style or "CORE"
            header = f"<b>[ {style} MANUAL ]</b>"
            
            if style == "WARREN":
                content = BotStrings.HELP_WARREN
            elif style == "QUANT":
                content = BotStrings.HELP_QUANT
            else: # CORE
                content = BotStrings.HELP_CORE

        msg = f"{header}\n<code>════════════════════════════════</code>\n\n{content}"
        
        # Config Logic (Cycling)
        if simple_mode == 1:
            mode_label = "[ MODE: SIMPLE ]"
        elif simple_mode == 2:
            mode_label = "[ MODE: GOD ]"
        else:
            mode_label = "[ MODE: ADVANCED ]"
        
        styles = ["CORE", "WARREN", "QUANT"]
        current_style = active_style if active_style in styles else "CORE"
        try:
            next_idx = (styles.index(current_style) + 1) % len(styles)
        except:
            next_idx = 1
        next_style = styles[next_idx]

        icon = self._get_behelit_icon()
        from config import get_settings
        settings = get_settings()
        admin_id_str = getattr(settings, "TELEGRAM_CHAT_ID", "0")
        is_admin = str(chat_id) == admin_id_str

        # Row 1: Config (Top) - User Request
        keyboard = [
            [
                {"text": mode_label, "callback_data": "TOGGLE_SIMPLE_MODE"},
                {"text": f"[ STYLE: {current_style} ]", "callback_data": f"SET_STYLE_{next_style}"}
            ]
        ]

        # Row 2: Intel & Social
        keyboard.append([
            {"text": "[ COMMANDS ]", "callback_data": "COMMANDS_VIEW"}, 
            {"text": "[ KNOWLEDGE ]", "callback_data": "KNOWLEDGE_HUB"}
        ])
        # Row 3: Admin & Fuel
        row_3 = []
        if is_admin:
            row_3.append({"text": "[ CONFIG ]", "callback_data": "CONFIG_VIEW"})
            
        row_3.append({"text": "[ CHARGE ]", "url": settings.DONATION_URL})
        keyboard.append(row_3)

        # Row 4: Fractal Center
        keyboard.append([{"text": icon, "callback_data": "HYPER_FRACTAL"}])

        # Row 5: Circle (Bottom)
        keyboard.append(self._get_home_button())

        reply_markup = {"inline_keyboard": keyboard}
        
        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=reply_markup)
        else:
            await self.send_markup(chat_id, msg, reply_markup)

    async def handle_commands(self, chat_id: int, message_id: int = None):
        """Displays the full list of available commands."""
        palette = (
            "<b>[ COMMAND PALETTE: CORE SYNTAX ]</b>\n"
            "<code>════════════════════════════════</code>\n\n"
            "<b>1. MARKET TELEMETRY (REAL-TIME)</b>\n"
            "• <code>/price [SYM]</code>: Check price/pulse (e.g. <code>/price BTC</code>)\n"
            "• <code>/stats [SYM]</code>: Computation of cockpit metrics (RSI, Resonance)\n"
            "• <code>/chart [SYM]</code>: Generate visual technical plot\n"
            "• <code>/daily | /hourly | /weekly</code>: Heatmap summaries\n"
            "• <code>/clusters [SECTOR]</code>: List assets in category (e.g. <code>/clusters TECH</code>)\n\n"
            "<b>2. INSIGHT & SIGNALS (ML)</b>\n"
            "• <code>/scan | /signals</code>: Multi-model opportunity detection\n"
            "• <code>/predictions [SYM]</code>: Price vector forecasting (XGBoost/RNN)\n"
            "• <code>/divine [SYM]</code>: Pattern analogue matching (KD-Tree)\n"
            "• <code>/physics [SYM]</code>: Fluid Dynamics (DMD) trajectory analysis\n"
            "• <code>/monitor</code>: Live stream of global model conviction flux\n"
            "• <code>/scoreboard</code>: ROI leaderboard and strategy bias per asset\n\n"
            "<b>3. GLOBAL HEADLINES (INTEL)</b>\n"
            "• <code>/news [SYM|SECTOR]</code>: Sector news (e.g. <code>/news forex</code> or <code>/news AAPL</code>)\n"
            "• <code>/verify [SYM]</code>: Cross-source sentiment confirmation scan\n"
            "• <code>/events [SYM|SECTOR]</code>: Economic calendar (mapped to sector)\n\n"
            "<b>4. EXECUTION TERMINAL (TRADING)</b>\n"
            "• <code>/buy [SYM] [SIZE]</code>: Open Long (e.g. <code>/buy ETH 0.05</code>)\n"
            "• <code>/sell [SYM] [SIZE]</code>: Open Short (e.g. <code>/sell BTC 0.10</code>)\n"
            "• <code>/close [SYM]</code>: Liquidate specific position\n"
            "• <code>/sl [SYM] [PRICE]</code>: Set Stop Loss barrier\n"
            "• <code>/tp [SYM] [PRICE]</code>: Set Take Profit target\n"
            "• <code>/riskPERSISTENCE [TICKS]</code>: Set confirmation wait (Espresso/Coffee)\n"
            "• <code>/risk [size|stop|target] [VAL]</code>: Calibrate global risk parameters\n\n"
            "<b>5. ACCOUNT & FORENSIC AUDIT</b>\n"
            "• <code>/wallet | /bal</code>: Real-time equity & holdings audit\n"
            "• <code>/positions</code>: Open exposure and PnL monitoring\n"
            "• <code>/trades</code>: Forensic log of historical order execution\n"
            "• <code>/shadow</code>: Virtual performance of the Espresso engine\n"
            "• <code>/ip</code>: IP whitelist and security configuration matrix\n"
            "• <code>/status</code>: Core service health (Binary check)\n\n"
            "<b>6. THE VAULT (KNOWLEDGE)</b>\n"
            "• <code>/wiki [TERM]</code>: Glossary lookup (e.g. <code>/wiki RESONANCE</code>)\n"
            "• <code>/knowledge | /docs</code>: Access the full Research Hub\n"
            "• <code>/yarn [SYM] [MSG]</code>: Link message to global symbol frequency\n"
            "• <code>/start</code>: Re-initialize Control Center hub\n\n"
            "<i>Note: All commands are strictly case-insensitive. Brackets [ ] denote optional arguments.</i>"
        )
        
        keyboard = [
            [{"text": "« BACK TO HELP", "callback_data": "HELP"}]
        ]
        keyboard.append(self._get_home_button())
        reply_markup = {"inline_keyboard": keyboard}
        
        if message_id:
             await self.bot.edit_message_text(chat_id, message_id, palette, reply_markup=reply_markup, parse_mode="HTML")
        else:
             await self.send_markup(chat_id, palette, reply_markup)

    async def handle_status(self, chat_id: int):
        # [optimization] Skip pre-check to avoid 'Offline' false positives during load
        # if not await self.bot.check_backend_health():
        #      await self.send_message(chat_id, "[!] Backend Offline")
        #      return
        try:
            tasks = [self.fetch_api("/api/dashboard/status"), self.fetch_api("/api/dashboard/metrics")]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            status, metrics = [r if not isinstance(r, Exception) else {} for r in results]
            await self.send_message(chat_id, format_system_status(status, metrics))
        except:
            await self.send_message(chat_id, "[X] Status failed.")

    async def handle_symbols(self, chat_id: int, data: str = "SYMBOLS_TAB_CRYPTO", message_id: int = None):
        """
        Browse the extensive Asset Universe (Elite 60).
        """
        from config.settings import get_settings, get_trading_symbols
        settings = get_settings()
        all_symbols = get_trading_symbols(settings)
        
        # Determine Category
        # Default to CRYPTO if first load, else parse from data
        is_global = "GLOBAL" in data
        tab_name = "GLOBAL" if is_global else "CRYPTO"
        
        # Filter Symbols
        # We rely on simple logic: if it has '=' or '^' or is a known stock, it's Global.
        # Otherwise it's Crypto.
        # Faster than parsing taxonomy every time.
        taxonomy = settings.UNIVERSE_TAXONOMY.get("PREFIXES", {})
        global_prefixes = tuple(taxonomy.get("GLOBAL", ["GC=", "ES=", "^", "EUR", "GBP", "JPY", "XAU", "XAG"]))
        
        filtered_list = []
        for s in all_symbols:
            # Check if Global
            is_glob_sym = s.startswith(global_prefixes) or s in ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "META", "AMZN", "NFLX", "SMCI", "COIN", "MSTR", "ARKK", "BITO", "AMD"]
            
            if is_global and is_glob_sym:
                filtered_list.append(s)
            elif not is_global and not is_glob_sym:
                filtered_list.append(s)
                
        # Pagination
        page = 0
        if "_PAGE_" in data:
            try: page = int(data.split("_PAGE_")[-1])
            except: pass
            
        items_per_page = 20
        total_pages = math.ceil(len(filtered_list) / items_per_page)
        # Circular page navigation
        if page >= total_pages: page = 0
        if page < 0: page = total_pages - 1
            
        start = page * items_per_page
        subset = filtered_list[start:start+items_per_page]
        
        msg = f"<b>[ {tab_name} UNIVERSE :: PAGE {page+1}/{total_pages} ]</b>\n"
        msg += "<code>════════════════════════════════</code>\n"
        
        # Parallel Fetch for Speed
        dm = get_data_manager()
        from services.symbol_normalizer import get_symbol_normalizer
        from services.brain import get_engine
        
        normalizer = get_symbol_normalizer()
        engine = get_engine()
        
        import asyncio
        
        async def fetch_item(s):
             stats = await asyncio.to_thread(dm.get_ticker_stats, s)
             return s, stats

        # Run all fetches concurrently
        results = await asyncio.gather(*(fetch_item(s) for s in subset))
        
        for s, stats in results:
             price = stats.get('price', 0) if stats else 0
             change = stats.get('change_pct', 0) if stats else 0
             # Match market.py icon style
             icon = "▴" if change >= 0 else "▾"
             
             # Fetch Brain Intel (Resonance)
             brain_state = engine.states.get(s, {})
             z_score = brain_state.get('z_score', 0.0)
             z_str = f"Ψ:{z_score:+.1f}"
             
             # Normalize for Display (Nicknames)
             # e.g. ^GSPC -> SPX, BTCUSDC -> BTC
             # We assume normalizer.to_display() handles strict replacements from settings
             # For crypto, we still need to strip standard suffixes if not aliased
             
             nickname = normalizer.to_display(s)
             if nickname == s and (s.endswith("USDC") or s.endswith("USDT")):
                 nickname = s.replace("USDC", "").replace("USDT", "")
             
             # Format Columns (Monospace)
             # Matches /price format: • $PRICE    CHANGE   ICON   /CMD
             p_str = f"${price:,.0f}" if price > 1.0 else f"${price:.2f}"
             c_str = f"{change:+.1f}%"
             
             # Align columns: Price(10) Change(7) Icon(1)
             data_block = f"{p_str:<10} {c_str:<7} {icon}"
             
             # Command (Right)
             cmd = f"/{nickname}"
             
             msg += f"• <code>{data_block}</code> {cmd}\n"
        
        msg += "\n<i>Tap commands (e.g. /BTC) to view intelligence.</i>"
        
        # Build Navigation Keyboard (ASCII Only)
        # [ CRYPTO ] [ GLOBAL ]
        # [ < ] [ > ]
        
        base_data = f"SYMBOLS_TAB_{tab_name}"
        toggle_data = "SYMBOLS_TAB_CRYPTO" if is_global else "SYMBOLS_TAB_GLOBAL"
        # Label reflects CURRENT view, clicking switches it
        current_view_label = f"{tab_name}"
        
        # Row 1: Navigation
        nav_row = [
            {"text": "<", "callback_data": f"{base_data}_PAGE_{page-1}"},
            {"text": ">", "callback_data": f"{base_data}_PAGE_{page+1}"}
        ]
        
        # Row 2: Controls (Current View Toggle + Home)
        control_row = [
            {"text": current_view_label, "callback_data": toggle_data},
            {"text": "○", "callback_data": "START"}
        ]
        
        keyboard = [nav_row, control_row]
        
        reply_markup = {"inline_keyboard": keyboard}
        
        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, msg, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await self.send_markup(chat_id, msg, reply_markup)

    async def handle_mode_toggle(self, chat_id: int, data: str, message_id: int, user_id: int):
        dm = get_data_manager()
        u_id = user_id or chat_id
        if "TOGGLE_SIMPLE_MODE" in data:
            mode = await asyncio.to_thread(dm.get_user_simple_mode, u_id)
            new_mode = (mode + 1) % 3 # Toggle 0 -> 1 -> 2 (Simple -> Advanced -> God)
            await asyncio.to_thread(dm.set_user_simple_mode, u_id, new_mode)
        elif "SET_STYLE" in data:
            style = data.split("_")[-1]
            await asyncio.to_thread(dm.set_user_intel_style, u_id, style)
            
            await asyncio.to_thread(dm.set_user_intel_style, u_id, style)
            
        # Redirect back to HELP to keep context
        await self.handle_help(chat_id, message_id=message_id)

    async def handle_hyper_fractal(self, chat_id: int, message_id: int):
        """Launches the Hyperstate Visualizer."""
        try:
            msg, kb = await self._build_hyper_response()
            if not kb:
                await self.bot.edit_message_text(chat_id, message_id, "[WARN] Visualization unavailable.")
                return
            
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=kb)
            
            # START DYNAMIC WATCHER
            job_name = f"hyper_{chat_id}"
            # Kill conflicting Cinema job
            for job in self.bot.job_queue.get_jobs_by_name(f"cinema_{chat_id}"): job.schedule_removal()
            # Kill existing Hyper job to restart
            for job in self.bot.job_queue.get_jobs_by_name(job_name): job.schedule_removal()
            
            self.bot.job_queue.run_repeating(
                self.watch_hyper_job, interval=10, first=10,
                data={'chat_id': chat_id, 'message_id': message_id, 'lifespan': 30, 'last_hash': hashlib.md5(msg.encode()).hexdigest()},
                name=job_name
            )
        except Exception as e:
            self.logger.error(f"Hyper Fractal Error: {e}")
            await self.bot.edit_message_text(chat_id, message_id, "[WARN] Visualization Sync Failure.")

    async def _build_hyper_response(self):
        """Generates the Hyperstate message and keyboard."""
        try:
            cache = get_opportunity_cache()
            all_opps = cache.get_all_opportunities()
            opp_count = len(all_opps)
            
            now = time.time()
            flux_entropy = int(hashlib.md5(str(now).encode()).hexdigest(), 16) % 100
            flux_factor = (flux_entropy / 100.0) * 0.40
            
            base_x, base_y = -0.75, 0.1
            orbit_radius = 0.05 + (flux_factor * 0.1)
            chaos_angle = flux_factor * math.pi 
            
            drift_x = base_x + (math.cos(chaos_angle) * orbit_radius)
            drift_y = base_y + (math.sin(chaos_angle) * orbit_radius)
            
            zoom = 0.8 + (opp_count * 0.3)
            iter_count = 35 + (opp_count * 8)
            
            fractal = ASCIIArt.generate_mandelbrot(
                width=48, height=18, iterations=int(iter_count), 
                zoom=zoom, center_x=drift_x, center_y=drift_y
            )
            
            from services.brain import get_engine
            engine = get_engine()
            btc_state = engine.states.get("BTCUSDT", {})
            current_regime = btc_state.get('regime', 'STABLE')
            
            msg = (
                f"<pre>{fractal}</pre>\n\n"
                f"<b>[ SYSTEM HYPER-STATE VISUALIZER ]</b>\n"
                f"<code>════════════════════════════════</code>\n"
                f"<code>BEHELIT      : {current_regime}</code>\n"
                f"<code>OPS DETECTED : {opp_count}</code>\n"
                f"<code>CACHE PULSE  : {iter_count} Hz</code>\n"
                f"<code>════════════════════════════════</code>\n\n"
                f"<b>LAST UPDATE: {datetime.utcnow().strftime('%H:%M:%S')} UTC</b>"
            )
            
            keyboard = [[{"text": "■", "callback_data": "HYPER_SUMMARY"}, {"text": "◬", "callback_data": "CINEMA_FRACTAL"}, {"text": "○", "callback_data": "START"}]]
            return msg, {"inline_keyboard": keyboard}
        except Exception as e:
            self.logger.error(f"Hyper Build Error: {e}")
            return "ERROR", None

    async def watch_hyper_job(self, context):
        job = context.job
        data = job.data
        data['lifespan'] -= 1
        if data['lifespan'] <= 0:
            job.schedule_removal()
            return
            
        msg, kb = await self._build_hyper_response()
        if not kb: return
        
        current_hash = hashlib.md5(msg.encode()).hexdigest()
        if current_hash != data.get('last_hash'):
            try:
                await self.bot.edit_message_text(job.chat_id, data['message_id'], msg, reply_markup=kb)
                data['last_hash'] = current_hash
            except: pass

    async def handle_hyper_summary(self, chat_id: int, message_id: int, user_id: int):
        """Displays the Global State Hyper-Summary using SummaryComposer."""
        try:
            # Mock interaction stats for now to match the desired output
            mock_stats = {
                'total_interactions': 5,
                'tabs_visited': ['PRICES', 'OPPS', 'NEWS', 'STATS', 'CHART'],
                'visited_symbols': {'BTCUSDT', 'ETHUSDT'}
            }
            
            res = await SummaryComposer.generate_achievement_summary(user_id, mock_stats)
            msg = res["text"]
            
            # Simple Back button
            keyboard = [[{"text": "« BACK [VISUALIZER]", "callback_data": "HYPER_FRACTAL"}], [{"text": "○", "callback_data": "START"}]]
            
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup={"inline_keyboard": keyboard})
            
        except Exception as e:
            self.logger.error(f"Hyper Summary Error: {e}")
            await self.bot.edit_message_text(chat_id, message_id, "[WARN] Summary Sync Failed.")

    async def handle_cinema_fractal(self, chat_id: int, message_id: int, user_id: int):
        """Launches the NEURAL DREAM STATE (formerly Cinema)."""
        # RESUME FROM LAST FRAME
        start_frame = self.dream_states.get(chat_id, 0)
        
        # Initial State: PLAYING FORWARD
        paused = False
        direction = 1
        
        msg, kb = await self._build_cinema_fractal(start_frame, paused, direction)
        
        job_name = f"cinema_{chat_id}"
        
        # Kill Conflicting Hyper job
        for job in self.bot.job_queue.get_jobs_by_name(f"hyper_{chat_id}"): job.schedule_removal()
        # Kill existing Cinema job
        current_jobs = self.bot.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs: job.schedule_removal()
        
        self.bot.job_queue.run_repeating(
            self.watch_cinema_job,
            interval=3,
            first=3,
            chat_id=chat_id,
            name=job_name,
            data={
                'message_id': message_id,
                'user_id': user_id,
                'frame': start_frame,
                'direction': direction,
                'paused': paused,
                'lifespan': 100
            }
        )
        await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=kb)

    async def handle_cinema_control(self, chat_id: int, action: str, message_id: int):
        """
        Handles Play, Pause, Forward, Backward.
        action: CINEMA_PLAY, CINEMA_PAUSE, CINEMA_BACK, CINEMA_NEXT
        """
        job_name = f"cinema_{chat_id}"
        jobs = self.bot.job_queue.get_jobs_by_name(job_name)
        if not jobs: return # Job expired
        
        job = jobs[0]
        data = job.data
        
        if action == "CINEMA_PAUSE":
            data['paused'] = True
        elif action == "CINEMA_PLAY":
            data['paused'] = False
            data['direction'] = 1
        elif action == "CINEMA_BACK":
            data['paused'] = False
            data['direction'] = -1
        elif action == "CINEMA_NEXT":
            data['paused'] = False
            data['direction'] = 1
            data['frame'] += 1 # Instant skip
            
        # Immediate UI Update
        msg, kb = await self._build_cinema_fractal(data['frame'], data['paused'], data['direction'])
        try:
            await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=kb)
        except: pass

    async def _build_cinema_fractal(self, frame: int, paused: bool, direction: int):
        t = frame * 0.1
        journeys = [(-0.745, 0.186, 0.01), (-0.16, 1.0405, 0.005), (-1.25066, 0.02012, 0.02)]
        jid = (frame // 40) % len(journeys)
        bx, by, bz = journeys[jid]

        cx = bx + math.sin(t) * 0.002
        cy = by + math.cos(t * 0.7) * 0.002
        zoom = bz * (1 + math.sin(t * 0.3) * 0.1)

        fractal = ASCIIArt.generate_mandelbrot(width=48, height=22, iterations=70, zoom=1/zoom, center_x=cx, center_y=cy)
        
        state_icon = "[ // PAUSED // ]" if paused else ("[ >> PLAYING ]" if direction > 0 else "[ << REWIND ]")

        msg = (
            f"<pre>{fractal}</pre>\n"
            f"<b>[ NEURAL DREAM STATE :: {state_icon} ]</b>\n"
            f"<code>FRAME {frame:04d} | {datetime.utcnow().strftime('%H:%M:%S')} UTC</code>"
        )
        
        # Cinema Controls
        # [ << ] [ >/|| ] [ >> ]
        play_pause_btn = {"text": "[ // ]", "callback_data": "CINEMA_PAUSE"} if not paused else {"text": "[ >> ]", "callback_data": "CINEMA_PLAY"}
        
        controls = [
            {"text": "[ < ]", "callback_data": "CINEMA_BACK"},
            play_pause_btn,
            {"text": "[ > ]", "callback_data": "CINEMA_NEXT"}
        ]
        
        nav = [{"text": "← EXIT", "callback_data": "HYPER_FRACTAL"}, {"text": "○", "callback_data": "START"}]
        
        keyboard = [controls, nav]
        return msg, {"inline_keyboard": keyboard}

    async def watch_cinema_job(self, context):
        job = context.job
        data = job.data
        
        if not data.get('paused', False):
            direction = data.get('direction', 1)
            data['frame'] += direction
        
        data['lifespan'] -= 1
        
        # Auto-Kill Empty Sessions
        if data['lifespan'] <= 0:
            job.schedule_removal()
            return

        # Render Update
        msg, kb = await self._build_cinema_fractal(data['frame'], data['paused'], data.get('direction', 1))
        
        try:
            # We don't check hash here because frame always changes if playing
            if not data.get('paused', False):
                 await self.bot.edit_message_text(job.chat_id, data['message_id'], msg, reply_markup=kb)
        except Exception: 
            pass
        
        # SAVE STATE
        self.dream_states[job.chat_id] = data['frame']
        
        if data['lifespan'] <= 0:
            job.schedule_removal()
            return

        msg, kb = await self._build_cinema_fractal(data['frame'], data['user_id'])
        try:
            await self.bot.edit_message_text(job.chat_id, data['message_id'], msg, reply_markup=kb)
        except:
             pass



    async def handle_config(self, chat_id: int, message_id: int = None):
        from config import get_settings
        settings = get_settings()
        admin_id_str = getattr(settings, "TELEGRAM_CHAT_ID", "0")
        if str(chat_id) != admin_id_str:
            await self.send_message(chat_id, "<i>[!] Access Denied: Command restricted to System Admin.</i>")
            return
            
        # Dynamic State
        from services.brain import get_engine
        engine = get_engine()
        mgr = getattr(engine, 'live_manager', None)
        
        auto = False
        exec_state = False
        mode = "UNKNOWN"
        
        if mgr:
             auto = getattr(mgr, 'is_auto_pilot_active', False)
             exec_state = getattr(mgr, 'is_execution_active', False)
             stealth_state = getattr(mgr, 'is_stealth_active', True)
             mode = getattr(mgr, 'execution_mode', 'PAPER')
             
        msg = (
            f"<b>[ SYSTEM CONFIGURATION ]</b>\n"
            f"<code>════════════════════════════════</code>\n"
            f"<b>TIME:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"<b>MODE:</b> <code>{mode}</code>\n"
            f"<b>AUTO-PILOT:</b> <code>{'ON' if auto else 'OFF'}</code>\n"
            f"<b>STEALTH (SNAKE):</b> <code>{'ON' if stealth_state else 'OFF'}</code>\n"
            f"<b>EXECUTION:</b> <code>{'ACTIVE' if exec_state else 'PAUSED'}</code>\n"
            f"<code>════════════════════════════════</code>\n"
        )
        
        # Buttons
        kb = []
        
        # Row 1: Auto Pilot
        ap_txt = "[ DISABLE AUTO-PILOT ]" if auto else "[ ENABLE AUTO-PILOT ]"
        kb.append([{"text": ap_txt, "callback_data": "CONFIG_TOGGLE_AUTOPILOT"}])
        
        # Row 2: Stealth Mode
        st_txt = "[ DISABLE STEALTH (RAT) ]" if stealth_state else "[ ENABLE STEALTH (SNAKE) ]"
        kb.append([{"text": st_txt, "callback_data": "CONFIG_TOGGLE_STEALTH"}])

        # Row 3: Execution
        ex_txt = "[ // HALT EXECUTION // ]" if exec_state else "[ >> RESUME EXECUTION ]"
        kb.append([{"text": ex_txt, "callback_data": "CONFIG_TOGGLE_EXECUTION"}])
        
        # Row 3: Audit
        kb.append([{"text": "[ SECURITY AUDIT ]", "callback_data": "IP_AUDIT"}])

        # Row 4: Navigation
        kb.append([{"text": "< REFRESH STATE >", "callback_data": "CONFIG_VIEW"}])
        
        reply_markup = {"inline_keyboard": kb}
        
        if message_id:
             # Use explicit keywords to be safe with python-telegram-bot signatures
             try:
                 await self.bot.edit_message_text(
                     text=msg,
                     chat_id=chat_id, 
                     message_id=message_id, 
                     parse_mode="HTML", 
                     reply_markup=reply_markup
                 )
             except Exception as e:
                 self.logger.error(f"Config Edit Failed: {e}")
                 # Fallback to fresh message if edit fails (e.g. too old)
                 await self.send_message(chat_id, msg, reply_markup=reply_markup)
        else:
             await self.send_message(chat_id, msg, reply_markup=reply_markup)

    async def handle_config_action(self, chat_id: int, action: str, message_id: int):
        from services.brain import get_engine
        engine = get_engine()
        mgr = getattr(engine, 'live_manager', None)
        if not mgr:
             await self.bot.answer_callback_query(chat_id, "Manager unavailable.")
             return

        if action == "CONFIG_TOGGLE_AUTOPILOT":
             new_state = not mgr.is_auto_pilot_active
             mgr.set_auto_pilot(new_state)
             await self.bot.answer_callback_query(chat_id, f"Auto-Pilot: {new_state}")
             
        elif action == "CONFIG_TOGGLE_EXECUTION":
             new_state = not mgr.is_execution_active
             mgr.set_execution_state(new_state)
             await self.bot.answer_callback_query(chat_id, f"Execution: {new_state}")

        elif action == "CONFIG_TOGGLE_STEALTH":
             new_state = not mgr.is_stealth_active
             mgr.set_stealth_mode(new_state)
             state_name = "SNAKE" if new_state else "RAT"
             await self.bot.answer_callback_query(chat_id, f"Mode: {state_name}")
             
        # Refresh View
        await self.handle_config(chat_id, message_id)

    async def handle_risk(self, chat_id: int, args: list):
        """Admin command to adjust risk parameters and view Kill Switch status."""
        from config import get_settings
        settings = get_settings()
        from services.tracker import get_performance_tracker
        tracker = get_performance_tracker()
        
        # Security: check if admin
        admin_id_str = getattr(settings, "TELEGRAM_CHAT_ID", "0")
        if str(chat_id) != admin_id_str:
            await self.send_message(chat_id, "<i>[!] Command restricted to System Admin.</i>")
            return

        if not args:
            # --- KILL SWITCH DASHBOARD ---
            max_daily_loss = getattr(settings, 'MAX_DAILY_LOSS', 500.0)
            current_pnl = tracker.get_daily_pnl()
            
            # Calculate Usage
            # If PnL is positive, we are safe (0% usage of loss limit)
            # If PnL is negative, usage = abs(pnl) / limit
            usage_pct = 0.0
            if current_pnl < 0:
                usage_pct = abs(current_pnl) / max_daily_loss
            
            usage_pct = min(1.0, usage_pct)
            
            # Progress Bar [▓▓▓░░░░░░░]
            bars = 10
            filled = int(usage_pct * bars)
            bar_str = "▓" * filled + "░" * (bars - filled)
            
            status = "🟢 ACTIVE"
            if current_pnl <= -max_daily_loss:
                status = "🔴 HALTED (KILL SWITCH TRIGGERED)"
            elif usage_pct > 0.8:
                status = "🟡 WARNING"

            msg = (
                f"<b>[ 🛡️ RISK MANAGEMENT SUBSYSTEM ]</b>\n"
                f"<code>════════════════════════════════</code>\n\n"
                f"<b>[ KILL SWITCH STATUS ]</b>\n"
                f"STATUS: <b>{status}</b>\n"
                f"LIMIT : <code>${max_daily_loss:,.2f}</code> (Max Loss)\n"
                f"PNL   : <code>${current_pnl:,.2f}</code> (24h)\n"
                f"USAGE : <code>[{bar_str}] {usage_pct*100:.1f}%</code>\n\n"
                f"<b>[ STATIC PARAMETERS ]</b>\n"
                f"• MAX SIZE    : <code>{settings.MAX_POSITION_SIZE*100}%</code>\n"
                f"• STOP LOSS   : <code>{settings.STOP_LOSS*100}%</code>\n"
                f"• PROFIT TGT  : <code>{settings.PROFIT_TARGET*100}%</code>\n"
                f"• Z-THRESHOLD : <code>{settings.SIGNAL_THRESHOLD:.2f}</code> (Min Conviction)\n"
                f"• CONFIRMATIONS: <code>{getattr(settings, 'SIGNAL_PERSISTENCE', 2)}</code> (Ticks)\n\n"
                f"<i>To adjust: /risk [size|stop|target|signal|persistence] [value]</i>"
            )
            await self.send_message(chat_id, msg)
            return

        # ... existing adjustment logic ...
        param = args[0].lower()
        if len(args) < 2:
            await self.send_message(chat_id, "Usage: /risk [size|stop|target] [value]")
            return
            
        try:
            val = float(args[1])
            key = None
            
            # Parameter Mapping
            if param in ["size", "max_size"]:
                key = "MAX_POSITION_SIZE"
                if val > 1.0: val /= 100.0
                settings.MAX_POSITION_SIZE = val
                
            elif param in ["stop", "sl", "stop_loss"]:
                key = "STOP_LOSS" 
                if val > 1.0: val /= 100.0
                settings.STOP_LOSS = val
                
            elif param in ["target", "tp", "profit"]:
                key = "PROFIT_TARGET"
                if val > 1.0: val /= 100.0
                settings.PROFIT_TARGET = val
                
            elif param in ["signal", "threshold", "z"]:
                key = "SIGNAL_THRESHOLD"
                if val > 10.0: val /= 100.0  # Allow "65" to be 0.65
                settings.SIGNAL_THRESHOLD = val
                
            elif param in ["persistence", "confirmations", "ticks", "wait"]:
                key = "SIGNAL_PERSISTENCE"
                val = int(val)
                setattr(settings, "SIGNAL_PERSISTENCE", val)

            if key:
                # Persistence (Robust .env update with proper path resolution)
                import os
                from pathlib import Path
                
                # Priority: 1. ENV_PATH setting, 2. File-relative, 3. CWD fallback
                env_path = getattr(settings, 'ENV_PATH', None)
                if not env_path or not os.path.exists(env_path):
                    # Use path relative to this file's location (backend/services/bot/handlers -> backend -> project root)
                    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
                    env_path = base_dir / ".env"
                    
                env_path = str(env_path)
                self.logger.info(f"[RISK] Persisting {key}={val} to {env_path}")
                
                try:
                    # Read existing or start fresh
                    lines = []
                    if os.path.exists(env_path):
                        with open(env_path, 'r') as f:
                            lines = f.readlines()
                    
                    new_lines = []
                    found = False
                    for line in lines:
                        if line.strip().startswith(f"{key}="):
                            new_lines.append(f"{key}={val}\n")
                            found = True
                        else:
                            new_lines.append(line)
                            
                    if not found:
                        new_lines.append(f"\n{key}={val}\n")
                        
                    with open(env_path, 'w') as f:
                        f.writelines(new_lines)
                        
                    await self.send_message(chat_id, f"[OK] <b>{key}</b> updated to <code>{val}</code>\n<i>(Persisted to .env)</i>")
                except Exception as e:
                    self.logger.error(f"Persistence Failed for {env_path}: {e}")
                    await self.send_message(chat_id, f"[OK] <b>{key}</b> updated in memory (Disk save failed: {str(e)[:50]}).")
            else:
                await self.send_message(chat_id, "Unknown parameter. Use: size, stop, target, signal")

        except ValueError:
            await self.send_message(chat_id, "Invalid numeric format.")
             
    async def handle_info(self, chat_id: int):
        await self.send_message(chat_id, "<b>Auratic Intelligence</b>\nTransparency First.")

    async def handle_ip(self, chat_id: int):
        """Displays server IP and a 'Bot Online' status badge in Forensic style."""
        from config import get_settings
        from services.wallet import get_wallet
        settings = get_settings()
        admin_id_str = getattr(settings, "TELEGRAM_CHAT_ID", "0")
        if str(chat_id) != admin_id_str:
            await self.send_message(chat_id, "<i>[!] Access Denied: Forensic Audit restricted to System Admin.</i>")
            return

        import aiohttp
        ip = "Unknown"
        status_badge = "[OK] LOADED"
        
        # Actual Binance Check
        wallet = get_wallet()
        # Trigger an update to be sure
        await wallet.update()
        
        if wallet.connected:
            binance_link = "[OK] ONLINE"
        else:
            error_detail = getattr(wallet, 'last_error', 'Unknown')
            binance_link = f"[!] OFFLINE\n> Error: {error_detail}"

        # Fetch IPs (Dual Stack)
        ipv4 = None
        ipv6 = None
        
        try:
            async with aiohttp.ClientSession() as session:
                # IPv4 Check
                try:
                    async with session.get('https://api.ipify.org', timeout=3) as resp:
                        if resp.status == 200:
                            ipv4 = await resp.text()
                except: pass
                
                # IPv6 Check
                try:
                    async with session.get('https://api6.ipify.org', timeout=3) as resp:
                        if resp.status == 200:
                            ipv6 = await resp.text()
                except: pass
        except:
            status_badge = "[!] ERROR"
        
        # Format IP Display
        if ipv4 and ipv6 and ipv4 != ipv6:
            ip = f"{ipv4} (v4)\n{ipv6} (v6)"
        elif ipv4:
            ip = ipv4
        elif ipv6:
            ip = f"{ipv6} (v6)"
        else:
            ip = "Unreachable"

        # Diagnostics Logic
        diag_env = "[ ]"
        diag_creds = "[ ]"
        diag_ip = "[ ]"

        # Check for Environment Conflict
        # 1. Real Money in Non-Prod (Dangerous)
        # 2. Testnet in Prod (Confusing but safe)
        is_testnet = getattr(settings, "BINANCE_TESTNET", False)
        env_mode = getattr(settings, "ENV_MODE", "PRODUCTION").upper()
        
        if not is_testnet and env_mode != "PRODUCTION":
            diag_env = "[!] (SafeMode Risk)"
        elif is_testnet and env_mode == "PRODUCTION":
            diag_env = "[?] (Testnet in Prod)"

        if not getattr(settings, "BINANCE_API_KEY", None):
            diag_creds = "[x]"
        
        if not wallet.connected:
            diag_ip = "[x]"

        # Check Alpaca Status
        alpaca_status = "DISABLED"
        if getattr(settings, "ALPACA_ENABLED", False):
            # Check if we have an alpaca sub-wallet with data
            alpaca_wallet = wallet.wallets.get('alpaca')
            if alpaca_wallet and alpaca_wallet.source == "reconciled":
                alpaca_status = "[OK] ONLINE (Synced)"
                # If Binance is down but Alpaca is up, don't flag global IP/Creds as total failure
                if not wallet.connected:
                    diag_ip = "[~] (Partial)"
            else:
                 alpaca_status = "[!] CONNECTING..."

            
        # Swarm Status & Details
        swarm_details = "• No Satellites Detected"
        swarm_node_count = 0
        try:
            from routers.swarm import get_swarm_manager
            swarm = get_swarm_manager()
            swarm_node_count = len(swarm.active_nodes)
            
            if swarm_node_count > 0:
                swarm_mesh = f"[OK] {swarm_node_count} Active Nodes"
                # Generate List
                details = []
                for nid in swarm.active_nodes.keys():
                    meta = swarm.node_metadata.get(nid, {})
                    ip = meta.get("ip", "Unknown")
                    details.append(f"• <code>{nid}</code> ({ip})")
                swarm_details = "\n".join(details)
            else:
                swarm_mesh = "[!] DISCONNECTED"
        except:
            swarm_mesh = "[?] UNKNOWN"
            swarm_details = "• Error fetching swarm data"

        # Maintenance Logic (The "Doctor")
        actions = []
        
        # 1. Binance Check
        if not wallet.connected:
             actions.append(f"🔴 <b>Binance Offline</b>\n   ACTION: Whitelist IP <code>{ip}</code> on Binance API Management.")
        
        # 2. Swarm Check
        if swarm_node_count < 1:
             actions.append("🟡 <b>Swarm Offline</b>\n   ACTION: Restart Oracle Satellite Docker Container.")
        elif swarm_node_count < 2:
             actions.append("🔵 <b>Swarm Low</b>\n   NOTE: Minimum 2 nodes recommended for consensus.")

        # 3. Env Check
        if is_testnet and env_mode == "PRODUCTION":
             actions.append("🟡 <b>Config Mismatch</b>\n   ACTION: Check ENV_MODE variable in Railway.")

        if not actions:
             maintenance_action = "✅ <b>SYSTEM NOMINAL</b>\nNo manual intervention required."
        else:
             maintenance_action = "\n\n".join(actions)
            
        env_mode_str = "TESTNET (Paper)" if is_testnet else "PRODUCTION (Live)"
        
        msg = BotStrings.SECURITY_AUDIT.format(
            ip=ip, 
            swarm_mesh=swarm_mesh,
            swarm_details=swarm_details,
            status_badge=status_badge, 
            binance_link=binance_link,
            alpaca_status=alpaca_status,
            diag_env=diag_env,
            diag_creds=diag_creds,
            diag_ip=diag_ip,
            maintenance_action=maintenance_action,
            env_mode_str=env_mode_str
        )
        
        # Mode Toggle Button (Admin Only)
        keyboard = [
            [{"text": f"[ SWITCH MODE: {'LIVE' if not is_testnet else 'PAPER'} ]", "callback_data": "TOGGLE_TRADING_MODE"}],
            self._get_home_button()
        ]
        
        await self.send_markup(chat_id, msg, {"inline_keyboard": keyboard})

    async def handle_mode_switch(self, chat_id: int):
        from config import get_settings
        from services.wallet import get_wallet
        settings = get_settings()
        
        # Admin Check
        admin_id_str = getattr(settings, "TELEGRAM_CHAT_ID", "0")
        if str(chat_id) != admin_id_str:
            await self.send_message(chat_id, "[!] Access Denied.")
            return

        # Toggle
        current = getattr(settings, "BINANCE_TESTNET", False)
        new_state = not current
        settings.BINANCE_TESTNET = new_state
        
        # Notify
        mode_str = "PAPER (Testnet)" if new_state else "LIVE (Real Money)"
        await self.send_message(chat_id, f"<b>[SYSTEM] Switched to {mode_str}</b>\n<i>Reconnecting exchange...</i>")
        
        # Reconnect
        wallet = get_wallet()
        # Force re-init logic would go here.
        # For MVP, we just update state.
        await wallet.update() 
        
        # Refresh Audit
        await self.handle_ip(chat_id)

    def _get_home_button(self) -> list:
        """Returns a consistent row with the home button."""
        return [{"text": "○", "callback_data": "START"}]

    async def send_markup(self, chat_id: int, text: str, markup: dict, disable_web_page_preview: bool = True):
        # Helper to use bot.send_message with reply_markup
        await self.bot.send_message(chat_id, text, reply_markup=markup, disable_web_page_preview=disable_web_page_preview)

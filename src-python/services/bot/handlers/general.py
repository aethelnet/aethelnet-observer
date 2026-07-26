from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from telegram.ext import ContextTypes
import time
import math
import random
import hashlib
from datetime import datetime
from config.settings import get_settings, get_trading_symbols
import logging
import io
import random

try:
    from services.chart.mandelbrot import generate_mandelbrot_bytes
except Exception:
    generate_mandelbrot_bytes = None

logger = logging.getLogger("TelegramBot")
from services.bot.helpers.filters import BotIntelFilter
from services.data_manager import get_data_manager

class GeneralMixin:
    def _get_behelit_icon(self) -> str:
        """Fetch the current lore-based icon for the Behelit state."""
        try:
            from services.brain import get_engine
            engine = get_engine()
            btc_state = engine.states.get("BTCUSDT", {})
            regime = btc_state.get('regime', 'EQUI')
            
            # Lore-based Icon + Expanded Banner Decor (Strictly No Emojis)
            mapping = {
                "EQUI": "⨀",     # The Still Eye (Focused)
                "JOY": "⏀",      # The Rising Iris (Bull)
                "SAD": "⏁",      # The Sinking Iris (Bear)
                "ANGER": "⊗"     # The Shattered Core (Chaos)
            }
            
            # Technical Banner Decorations
            # Reduced dash-count for Mobile Compatibility (prevents truncation)
            crowns = {
                "EQUI": ("⫷ ─ ⟐ ─", "─ ⟐ ─ ⫸"), # Balanced
                "JOY": ("⫷ ─ ▴ ─", "─ ▴ ─ ⫸"), # Ascending
                "SAD": ("⫷ ─ ▾ ─", "─ ▾ ─ ⫸"), # Descending
                "ANGER": ("≪ ─ ◈ ─", "─ ◈ ─ ≫") # Chaos
            }
            
            main_sym = mapping.get(regime, "⟐")
            left, right = crowns.get(regime, ("·─", "─·"))
            
            return f"{left} {main_sym} {right}"
        except Exception:
            return "·─ ⟐ ─·"

    async def _send_main_menu(self, update: Update):
        """Centralized landing hub for all navigation"""
        message = update.effective_message

        # Build a short creative Mandelbrot snapshot to use as a visual banner.
        # The image parameters are randomized so each /start shows something different
        # and the caption includes a small "snapshot" of current tracked symbol count.
        try:
            settings = get_settings()
            total_symbols = len(settings.trading_symbols) if hasattr(settings, "trading_symbols") else 0
        except Exception:
            total_symbols = 0

        # Generate randomized parameters
        seed = int(time.time()) ^ random.getrandbits(16)
        palette = random.choice(["warm", "cool", "mono"])
        scale = round(random.uniform(0.7, 2.0), 3)
        max_iter = random.choice([100, 150, 200, 300])

        if generate_mandelbrot_bytes is not None:
            try:
                img_bytes = generate_mandelbrot_bytes(
                    width=480,
                    height=270,
                    max_iter=max_iter,
                    scale=scale,
                    seed=seed,
                    palette_style=palette,
                )
                bio = io.BytesIO(img_bytes)
                bio.name = "snapshot.png"
                bio.seek(0)
                caption = f"Snapshot — symbols={total_symbols} seed={seed} iter={max_iter} scale={scale} palette={palette}"
                # Send the image; we don't block editing the menu text — image is a creative extra.
                await message.reply_photo(photo=bio, caption=caption)
            except Exception as e:
                # If generation fails, log but continue to send the menu
                logger.debug(f"Snapshot generation failed: {e}")

        # Generate ASCII Mandelbrot with SLOW TIME DRIFT
        # "Slowly moving" - one character shift every few minutes
        # Period: ~24 hours for full cycle
        
        now = time.time()
        # Slow drift factor: 2pi every 86400s (24h)
        # Orbit radius: 0.1 to keep it within the interesting boundary
        t_drift = (now / 40000.0) % (2 * math.pi) 
        
        # Center of interesting Mandelbrot features
        base_x, base_y = -0.745, 0.1  # Seahorse valley region
        drift_radius = 0.05
        
        # Calculate drafting center
        drift_x = base_x + (math.cos(t_drift) * drift_radius)
        drift_y = base_y + (math.sin(t_drift) * drift_radius)
        
        from services.aesthetic_service import ASCIIArt
        fractal = ASCIIArt.generate_mandelbrot(
            width=32, 
            height=12, 
            iterations=40,  # Higher detail for zoomed view
            zoom=12.0,       # Zoomed in to see detail moving
            center_x=drift_x, 
            center_y=drift_y
        )

 
        # Fetch User Settings for UI state
        user_id = update.effective_user.id
        dm = get_data_manager()
        current_style = await asyncio.to_thread(dm.get_user_intel_style, user_id)
        simple_mode = await asyncio.to_thread(dm.get_user_simple_mode, user_id)

        if simple_mode == 1:
            # --- SIMPLE MODE ---
            msg = (
                f"<pre>{fractal}</pre>\n\n"
                "<b>[ AURATIC CORE ]</b>\n"
                "<code>════════════════════════════════</code>\n\n"
                "<i>Select target intelligence module:</i>\n"
                "<code>[ AWAITING_INPUT ]</code>"
            )
        elif simple_mode == 2:
            # --- ALL MODE (Information Overload) ---
            from services.system_metrics import SystemMetrics
            metrics = SystemMetrics.get_report()
            
            msg = (
                f"<pre>{fractal}</pre>\n\n"
                "<b>[ ALL :: INFORMATION OVERLOAD ]</b>\n"
                "<code>════════════════════════════════</code>\n"
                f"<b>UPTIME  ::</b> <code>{metrics.get('uptime', 'N/A')}</code>\n"
                f"<b>MEM     ::</b> <code>{metrics.get('mem_pct', 0):.1f}%</code>\n"
                f"<b>PULSE   ::</b> <code>{metrics.get('loop_latency', 0)*1000:.1f}ms</code>\n"
                "<code>════════════════════════════════</code>\n\n"
                "<b>TERMINAL_RAW_TELEMETRY</b>\n"
                "  <i>Advanced tools active. Filters bypassed.</i>\n"
                "  <code>BTC</code> <code>ETH</code> <code>GOLD</code> <code>SPX</code> <code>VIX</code> <code>DXY</code>\n\n"
                "<code>[ BROADCAST_ALL_FREQUENCIES_ACTIVE ]</code>"
            )
        else:
            # --- COMPLEX MODE ---
            msg = (
                f"<pre>{fractal}</pre>\n\n"
                "<b>[ AURATIC SYSTEMS ANALYTICS ]</b>\n"
                "<code>════════════════════════════════</code>\n\n"
                "<b>TERMINAL COMMANDS</b>\n"
                "  <code>/price</code>    <i>Direct asset lookup</i>\n"
                "  <code>/scan</code>     <i>ML divergence scan</i>\n"
                "  <code>/symbols</code>  <i>Asset universe</i>\n\n"
                "<b>QUICK ACCESS</b>\n"
                "  <i>Type any ticker directly:</i>\n"
                "  <code>BTC</code> <code>ETH</code> <code>GOLD</code> <code>SPX</code> <code>VIX</code> <code>DXY</code>\n\n"
                "<code>════════════════════════════════</code>\n"
                "<code>[ AWAITING_INPUT ]</code>"
            )
        
        # Admin Debug Info (Append IP for whitelist check)
        user_id = update.effective_user.id if update.effective_user else 0
        admin_id = int(self.settings.TELEGRAM_CHAT_ID)
        
        if user_id == admin_id:
             import aiohttp
             try:
                 async with aiohttp.ClientSession() as session:
                    async with session.get('https://api.ipify.org', timeout=2) as resp:
                        if resp.status == 200:
                            ip = await resp.text()
                            msg += f"\n\n<code>Server IP: {ip}</code>"
             except:
                 pass
        
        # Mode Toggle Label
        # Simple mode shows the active filter, Complex shows filter selector, ALL shows no filter
        if simple_mode == 1: 
            # Show active filter in Simple mode label
            toggle_label = f"[ {current_style} ]" if current_style != 'ALL' else "[ SIMPLE ]"
        elif simple_mode == 0: 
            toggle_label = "[ ADVANCED ]"
        else: 
            toggle_label = "[ ALL ]"
        
        toggle_btn = InlineKeyboardButton(toggle_label, callback_data="TOGGLE_SIMPLE_MODE")

        keyboard = []

        # 1. CORE ROW (Always present)
        keyboard.extend([
            [InlineKeyboardButton("PRICE [INTEL]", callback_data="PRICE_LANDING")],
            [InlineKeyboardButton("PERFORMANCE [SCAN]", callback_data="OPPORTUNITIES")],
            [InlineKeyboardButton("EVENTS [CALENDAR]", callback_data="CALENDAR"), 
             InlineKeyboardButton("NEWS [HUB]", callback_data="NEWS_HUB")],
        ])

        # 2. ADVANCED TOOLS (Complex and All Modes)
        if simple_mode != 1:
            keyboard.append([
                InlineKeyboardButton("SYMBOLS [LIST]", callback_data="SYMBOLS_TAB_CRYPTO"),
                InlineKeyboardButton("SUBS [ALERTS]", callback_data="my_subscriptions")
            ])
            
            # 3. INTEL STYLE FILTERS (Only in Complex Mode - Hides in ALL Mode)
            if simple_mode == 0:
                keyboard.append([
                    InlineKeyboardButton(f"{'●' if current_style == 'SPECTER' else '○'} SPECTER", callback_data="SET_STYLE_SPECTER"),
                    InlineKeyboardButton(f"{'●' if current_style == 'APEX' else '○'} APEX", callback_data="SET_STYLE_APEX")
                ])
                keyboard.append([
                    InlineKeyboardButton(f"{'●' if current_style == 'SHADOW' else '○'} SHADOW", callback_data="SET_STYLE_SHADOW"),
                    InlineKeyboardButton(f"{'●' if current_style == 'CORE' else '○'} CORE", callback_data="SET_STYLE_CORE")
                ])

        # 4. THE MODE TOGGLE (Above Help)
        keyboard.append([toggle_btn])

        # 5. HELP (Absolute Bottom)
        keyboard.append([InlineKeyboardButton("HELP [GUIDE]", callback_data="HELP")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        is_photo = bool(message.photo or message.caption)
        if update.callback_query and not is_photo:
            try:
                await message.edit_text(msg, parse_mode="HTML", reply_markup=reply_markup)
            except Exception:
                await message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)
 
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # KILL ALL ANIMATIONS ON START
        try:
            chat_id = update.effective_chat.id
            for job_name in [f"hyper_{chat_id}", f"cinema_{chat_id}"]:
                for job in context.job_queue.get_jobs_by_name(job_name):
                    job.schedule_removal()
        except: pass
        await self._send_main_menu(update)
 
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user_id = update.effective_user.id
        dm = get_data_manager()
        settings = get_settings()
        
        # Fetch settings asynchronously
        active_style = await asyncio.to_thread(dm.get_user_intel_style, user_id)
        simple_mode = await asyncio.to_thread(dm.get_user_simple_mode, user_id)
        
        if simple_mode:
            # --- SIMPLE MODE HELP ---
            header = "<b>[ AURATIC SIMPLE GUIDE ]</b>"
            content = (
                "<b>1. PRICE [INTEL]</b>\n"
                "Check any asset's current pulse. Use the buttons or type a symbol like <code>BTC</code>.\n\n"
                "<b>2. PERFORMANCE [SCAN]</b>\n"
                "Shows where the ML sees the biggest immediate opportunities. Focus on the Top 3.\n\n"
                "<b>3. EVENTS & NEWS</b>\n"
                "Stay aware of external market shocks. News is updated in real-time.\n\n"
                "<i>Switch to COMPLEX mode below to unlock advanced ML filters and tuning.</i>"
            )
        else:
            # --- COMPLEX MODE HELP (Dynamic based on Preset) ---
            presets = {
                "SPECTER": {
                    "Title": "SPECTER ENGINE (Momentum)",
                    "Manual": "Targets high-velocity breakouts. Best used in TRENDING markets. It ignores slow mean-reversion signals and hunts for pure speed."
                },
                "APEX": {
                    "Title": "APEX PREDATOR (Trend)",
                    "Manual": "High-conviction trend follower. Uses multi-timeframe confirmation to filter out noise. Slower entries, but higher win-rate on major moves."
                },
                "SHADOW": {
                    "Title": "SHADOW PROTOCOL (Reversals)",
                    "Manual": "Counter-trend hunter. Looks for extreme Z-Score deviations (Oversold/Overbought) to catch the 'Snap-Back'. Risky but rewarding during range-bound regimes."
                },
                "CORE": {
                    "Title": "CORE HARMONICS (Balanced)",
                    "Manual": "The default equilibrium. Blends Reservoir Computing (ESN) with Gaussian Regimes. Good for all-weather monitoring."
                }
            }
            
            p = presets.get(active_style, presets["CORE"])
            header = f"<b>[ {p['Title']} MANUAL ]</b>"
            content = (
                f"{p['Manual']}\n\n"
                "<b>ADVANCED COMMANDS</b>\n"
                "• <code>/scan</code> - Full ML divergence scan.\n"
                "• <code>/stats [SYM]</code> - Deep-dive into model alignment.\n\n"
                "<b>MECHANICS</b>\n"
                "• <b>GMM:</b> Classifies regimes (Calm/Volatile).\n"
                "• <b>ESN:</b> Predicts chaotic time-series moves.\n"
                "• <b>PCA:</b> Filters 'Cosmic Noise' from real Price Signal."
            )

        msg = (
            f"{header}\n"
            "<code>════════════════════════════════</code>\n\n"
            f"{content}\n\n"
            "<code>[ ACCESS TERMINAL ]</code>"
        )
        
        icon = self._get_behelit_icon()
        keyboard = [
            [
                InlineKeyboardButton("KNOWLEDGE", callback_data="KNOWLEDGE_HUB"),
                InlineKeyboardButton("SUPPORT", url=settings.DONATION_URL)
            ],
            [InlineKeyboardButton("○", callback_data="START")] # The Core
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            await message.edit_text(msg, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)


    async def _build_hyper_response(self):
        """Generates the Hyperstate message and keyboard."""
        try:
             # Aggregate System State
            from services.aesthetic_service import ASCIIArt
            from services.opportunity_cache import get_opportunity_cache
            from datetime import datetime
            
            cache = get_opportunity_cache()
            all_opps = cache.get_all_opportunities()
            opp_count = len(all_opps)
            
            # [DATA-LOCKED EVOLUTION]
            if all_opps:
                ids = sorted([str(o.get('id', '')) for o in all_opps])
                state_fingerprint = hashlib.md5("".join(ids).encode()).hexdigest()
                seed_val = int(state_fingerprint[:8], 16)
                orbit_angle = (seed_val % 1000) / 1000.0 * 2 * math.pi
            else:
                orbit_angle = 0
            
            # Hyperstate Flux (Jitter) - CHAOTIC MODE
            now = time.time()
            # Chaotic entropy to break the 10s sync rhythm
            flux_entropy = int(hashlib.md5(str(now).encode()).hexdigest(), 16) % 100
            flux_factor = (flux_entropy / 100.0) * 0.40 # Boosted for visibility
            
            # Application
            base_x, base_y = -0.75, 0.1
            orbit_radius = 0.05 + (flux_factor * 0.1) # Flux affects radius significantly
            
            # Add chaotic angle offset
            chaos_angle = flux_factor * math.pi 
            
            drift_x = base_x + (math.cos(orbit_angle + chaos_angle) * orbit_radius)
            drift_y = base_y + (math.sin(orbit_angle + chaos_angle) * orbit_radius)
            
            zoom = 0.8 + (opp_count * 0.3)
            iter_count = 35 + (opp_count * 8)
            
            fractal = ASCIIArt.generate_mandelbrot(
                width=48, height=18, iterations=int(iter_count), 
                zoom=zoom, center_x=drift_x, center_y=drift_y
            )
            
            # Intelligence
            from services.brain import get_engine
            engine = get_engine()
            btc_state = engine.states.get("BTCUSDT", {})
            current_regime = btc_state.get('regime', 'STABLE')
            
            top_opps = sorted(all_opps, key=lambda x: x.get('created_at', 0), reverse=True)[:3]
            intel_rows = ""
            if top_opps:
                intel_rows = "\n<b>LATEST INTELLIGENCE:</b>\n"
                for o in top_opps:
                    sym = o.get('symbol'); typ = o.get('opportunity_type'); conf = o.get('confidence', 0) * 100
                    intel_rows += f"· <code>{sym} {typ}</code> ({conf:.0f}% confidence)\n"
            else:
                intel_rows = "\n<i>Market intelligence idling...</i>\n"
            
            now_str = datetime.utcnow().strftime('%H:%M:%S') + ' UTC'
            msg = (
                f"<pre>{fractal}</pre>\n\n"
                f"<b>[ SYSTEM HYPER-STATE VISUALIZER ]</b>\n"
                f"<code>════════════════════════════════</code>\n"
                f"<code>BEHELIT      : {current_regime}</code>\n"
                f"<code>OPS DETECTED : {opp_count}</code>\n"
                f"<code>CACHE PULSE  : {iter_count} Hz</code>\n"
                f"<code>════════════════════════════════</code>\n"
                f"{intel_rows}\n"
                f"<b>LAST UPDATE: {now_str}</b>"
            )
            
            keyboard = [[InlineKeyboardButton("■", callback_data="GOTO_MENU_FROM_STATS"), InlineKeyboardButton("◬", callback_data="CINEMA_FRACTAL"), InlineKeyboardButton("○", callback_data="START")]]
            return msg, InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Hyper Build Error: {e}")
            return "ERROR", None

    async def watch_hyper_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Monitors Hyperstate for Flux/Data changes"""
        job = context.job
        data = job.data
        
        data['lifespan'] -= 1
        if data['lifespan'] <= 0:
            job.schedule_removal()
            return
            
        msg, kb = await self._build_hyper_response()
        if not kb: return
        
        # Hash Check
        current_hash = hashlib.md5(msg.encode()).hexdigest()
        last_hash = data.get('last_hash', 'none')
        
        if current_hash != last_hash:
            try:
                await context.bot.edit_message_text(
                    chat_id=job.chat_id,
                    message_id=data['message_id'],
                    text=msg,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                data['last_hash'] = current_hash
            except Exception as e:
                if "Message to edit not found" in str(e):
                    job.schedule_removal()

    async def callback_hyper_fractal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            msg, kb = await self._build_hyper_response()
            message = update.effective_message
            sent_msg = await message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
            
            # Kill existing (BOTH HYPER AND CINEMA)
            chat_id = update.effective_chat.id
            job_name = f"hyper_{chat_id}"
            
            for name in [job_name, f"cinema_{chat_id}"]:
                for job in context.job_queue.get_jobs_by_name(name):
                    job.schedule_removal()
            
            context.job_queue.run_repeating(
                self.watch_hyper_job,
                interval=10,
                first=10,
                data={'chat_id': chat_id, 'message_id': sent_msg.message_id, 'lifespan': 30, 'last_hash': hashlib.md5(msg.encode()).hexdigest()},
                name=job_name
            )
        except Exception as e:
            logger.error(f"Hyper Fractal Critical Error: {e}")
            try:
                await update.effective_message.answer("[WARN] Visualization Sync Failure.")
            except: pass

    # =========================================================================
    # CINEMA MODE: Pure Aesthetic Fractal Animation
    # =========================================================================
    
    async def _build_cinema_fractal(self, frame: int, user_id: int) -> tuple:
        """
        Generates a maximum-size animated fractal for pure visual pleasure.
        Uses Telegram's ~4096 char limit to create the largest possible fractal.
        Frame number creates animation drift for the 'movie' effect.
        Accepts user_id to filter market data based on user's intel style.
        """
        from services.aesthetic_service import ASCIIArt
        from services.opportunity_cache import get_opportunity_cache
        from services.brain import get_engine
        from services.data_manager import get_data_manager
        from services.bot.helpers.filters import BotIntelFilter
        from datetime import datetime
        import math
        import time
        
        # Logic: Evolution is driven by frame
        t = frame * 0.1
        
        # Mandelbrot journey
        journeys = [
            (-0.745, 0.186, 0.01),    # Seahorse Valley
            (-0.16, 1.0405, 0.005),   # Elephant Valley  
            (-1.25066, 0.02012, 0.02), # Mini-Mandelbrot
            (-0.77568377, 0.13646737, 0.004), # Deep spiral
        ]
        
        journey_idx = (frame // 40) % len(journeys)
        base_x, base_y, base_zoom = journeys[journey_idx]
        
        drift = math.sin(t) * 0.002
        center_x = base_x + drift
        center_y = base_y + (math.cos(t * 0.7) * 0.002)
        zoom = base_zoom * (1 + math.sin(t * 0.3) * 0.1)
        
        # Dimensions
        width = 48
        height = 22 # Reduced slightly to fit more data
        iterations = 70 + (frame % 25)
        
        fractal = ASCIIArt.generate_mandelbrot(
            width=width, height=height, iterations=iterations,
            zoom=1/zoom, center_x=center_x, center_y=center_y
        )
        
        # --- DATA INTEGRATION ---
        dm = get_data_manager()
        user_style = await asyncio.to_thread(dm.get_user_intel_style, user_id)

        # 1. Market Intel (Top Volatility/Trending)
        engine = get_engine()
        all_states = engine.states.items()
        
        # Filter symbols based on user style
        filtered_symbols_from_states = BotIntelFilter.filter_symbols([s[0] for s in all_states], user_style)
        
        # Re-filter states to only include filtered symbols
        filtered_states = {sym: state for sym, state in all_states if sym in filtered_symbols_from_states}

        top_symbols = sorted(filtered_states.items(), 
                           key=lambda x: x[1].get('volatility', 0), 
                           reverse=True)[:2]
        intel_str = ""
        for sym, state in top_symbols:
            regime = state.get('regime', 'STABLE')
            vol = state.get('volatility', 0) * 100
            intel_str += f"· {sym} [{regime}] (VOL {vol:.1f}%)\n"
            
        # 2. Subscribed / Pinned Intel
        cache = get_opportunity_cache()
        all_opps = cache.get_all_opportunities()

        # Filter opportunities based on user style
        filtered_opp_symbols = BotIntelFilter.filter_symbols([o.get('symbol') for o in all_opps], user_style)
        filtered_opps = [o for o in all_opps if o.get('symbol') in filtered_opp_symbols]

        subscribed_str = ""
        if filtered_opps:
            top_opp = sorted(filtered_opps, key=lambda x: x.get('confidence', 0), reverse=True)[:2]
            for o in top_opp:
                sym = o.get('symbol'); typ = o.get('opportunity_type'); conf = o.get('confidence', 0) * 100
                subscribed_str += f"· {sym} {typ} ({conf:.0f}% CONF)\n"
        
        now = datetime.utcnow().strftime('%H:%M:%S')
        location_names = ["SEAHORSE VALLEY", "ELEPHANT VALLEY", "MINI-MANDELBROT", "DEEP SPIRAL"]
        location = location_names[journey_idx]
        
        msg = (
            f"<pre>{fractal}</pre>\n"
            f"<b>[ NEURAL DREAM STATE :: {location} ]</b>\n"
            f"<b>INTELLIGENCE ({user_style}):</b>\n{intel_str or 'Waiting for market signal...'}"
            f"<b>SUBSCRIBED ({user_style}):</b>\n{subscribed_str or 'No pinned opportunities.'}\n"
            f"<code>FRAME {frame:04d} | {now} UTC | DREAMING</code>"
        )
        
        keyboard = [[
            InlineKeyboardButton("←", callback_data="HYPER_FRACTAL"),
            InlineKeyboardButton("○", callback_data="START")
        ]]
        
        return msg, InlineKeyboardMarkup(keyboard)

    async def watch_cinema_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Auto-updates the cinema fractal every 3 seconds for smooth animation."""
        job = context.job
        data = job.data
        
        logger.info(f"[CINEMA] Updating Frame {data['frame']} for Chat {job.chat_id}")
        
        data['frame'] += 1
        data['lifespan'] -= 1
        
        if data['lifespan'] <= 0:
            logger.info(f"[CINEMA] Job lifespan expired for Chat {job.chat_id}")
            job.schedule_removal()
            return
        
        try:
            msg, kb = await self._build_cinema_fractal(data['frame'], data['user_id'])
            
            await context.bot.edit_message_text(
                chat_id=job.chat_id,
                message_id=data['message_id'],
                text=msg,
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as e:
            if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
                logger.info(f"[CINEMA] Job loop broken (message lost/unchanged) for Chat {job.chat_id}")
                job.schedule_removal()
            else:
                logger.error(f"[CINEMA] Frame Update Error: {e}")

    async def callback_cinema_fractal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launches the cinematic fractal viewer - pure animated art."""
        try:
            message = update.effective_message
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            logger.info(f"[TRACE] Launching Cinema Mode for Chat {chat_id} (User {user_id})")
            
            # Generate initial frame
            msg, kb = await self._build_cinema_fractal(frame=0, user_id=user_id)
            
            # Try to edit current message for smoother transition
            try:
                sent_msg = await message.edit_text(
                    text=msg,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            except Exception:
                # Fallback to new message if edit fails
                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            
            job_name = f"cinema_{chat_id}"
            
            # Kill any existing (BOTH HYPER AND CINEMA)
            for name in [job_name, f"hyper_{chat_id}"]:
                for job in context.job_queue.get_jobs_by_name(name): 
                    job.schedule_removal()
            
            # Schedule
            context.job_queue.run_repeating(
                self.watch_cinema_job,
                interval=3,
                first=3,
                chat_id=chat_id,
                name=job_name,
                data={
                    'message_id': sent_msg.message_id,
                    'user_id': user_id,
                    'frame': 0,
                    'lifespan': 100
                }
            )
            
            await update.callback_query.answer("Neural Dream: Sequence started")
            
        except Exception as e:
            logger.error(f"[CINEMA] Launch Error: {e}")
            await update.callback_query.answer("Failed to launch journey")

    async def callback_knowledge_hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            from services.aesthetic_service import ASCIIArt
            from datetime import datetime
            import math
            
            # [MAX-SCALE-DRIFT]: High-Fidelity Asymmetry
            # Expanding the canvas and boosting depth to remove the minimalistic feel.
            now = datetime.now()
            week_num = now.isocalendar()[1]
            angle = math.sin((week_num / 52.0) * math.pi) * 2 * math.pi
            
            # Using deep 'Burning Ship' hull coordinates
            drift_x = -1.75 + (math.cos(angle) * 0.04)
            drift_y = -0.04 + (math.sin(angle) * 0.04)
            
            # GO BIG: Width 42, Height 15 for a truly 'Hyper' repository feel.
            fractal = ASCIIArt.generate_burning_ship(
                width=42, height=15,
                iterations=60, 
                zoom=3.0, center_x=drift_x, center_y=drift_y
            )
            fractal_header = f"<pre>{fractal}</pre>\n"
        except ImportError:
            fractal_header = ""
            
        message = update.effective_message
        msg = (
            f"{fractal_header}"
            "<b>[ KNOWLEDGE REPOSITORY ]</b>\n"
            "<code>══════════════════════════════</code>\n"
            "<b>tl;dr ALPHA TACTICS:</b>\n"
            "• <b>Rates:</b> If Market diverges from Fed Guidance → Volatility.\n"
            "• <b>Stocks:</b> Trust Insiders (Form 4) over Analysts.\n"
            "• <b>Crypto:</b> Price UP + Exchange Reserves DOWN = True Spot Bid.\n\n"
            
            "<b>1. MACRO & RATES (The Ocean)</b>\n"
            "• <b>CME FedWatch</b>\n"
            "  ↳ <i>Insight:</i> Using 30-Day Futures to predict hikes. If prob &gt; 70%, it's priced in.\n"
            "• <b>BLS (CPI/NFP)</b>\n"
            "  ↳ <i>Insight:</i> Sticky CPI &gt; 3% forces Fed liquidity withdrawal.\n"
            "• <b>FRED (St. Louis Fed)</b>\n"
            "  ↳ <i>Insight:</i> Watch '10Y-2Y Yield Curve'. Inversion signals impending recession.\n\n"
            
            "<b>2. EQUITIES (The Vessels)</b>\n"
            "• <b>Finviz Heatmap</b>\n"
            "  ↳ <i>Insight:</i> Relative Strength. Buy sectors that stay green when SPY is red.\n"
            "• <b>OpenInsider</b>\n"
            "  ↳ <i>Insight:</i> 'Cluster Buying' (3+ Execs buying) at 52w lows is the strongest automated buy signal.\n"
            "• <b>SEC EDGAR</b>\n"
            "  ↳ <i>Insight:</i> Read 'Risk Factors' in 10-K filings for the truth.\n\n"
            
            "<b>3. CRYPTO (The Current)</b>\n"
            "• <b>Dune Analytics</b>\n"
            "  ↳ <i>Insight:</i> Verify protocol revenue. Don't buy tokens with P/E &gt; 100.\n"
            "• <b>CryptoQuant (Reserves)</b>\n"
            "  ↳ <i>Insight:</i> Whales sending to exchanges = Sell Wall. Whales withdrawing = HODL.\n"
            "• <b>Glassnode (MVRV)</b>\n"
            "  ↳ <i>Insight:</i> MVRV Z-Score &lt; 0 is historically the accumulation zone.\n\n"
            
            "<code>[ SELECT DATASTREAM ]</code>"
        )
        
        # Compact Grid Layout
        keyboard = [
            # MACRO
            [
                InlineKeyboardButton("FRED", url="https://fred.stlouisfed.org/series/T10Y2Y"),
                InlineKeyboardButton("BLS (CPI)", url="https://www.bls.gov/cpi/"),
                InlineKeyboardButton("CME FEDWATCH", url="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html")
            ],
            # EQUITIES
            [
                InlineKeyboardButton("FINVIZ", url="https://finviz.com/map.ashx"),
                InlineKeyboardButton("OPENINSIDER", url="http://openinsider.com/"),
                InlineKeyboardButton("SEC EDGAR", url="https://www.sec.gov/edgar/searchedgar/companysearch")
            ],
            # CRYPTO
            [
                InlineKeyboardButton("GLASSNODE", url="https://glassnode.com/"),
                InlineKeyboardButton("CRYPTOQUANT", url="https://cryptoquant.com/"),
                InlineKeyboardButton("DUNE", url="https://dune.com/browse/dashboards")
            ],
            # NAVIGATION
            [
                InlineKeyboardButton("« BACK [GUIDE]", callback_data="HELP"),
                InlineKeyboardButton("○", callback_data="START")
            ]
        ]
        
        if update.callback_query:
            await message.edit_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


            



    async def cmd_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE, tab: str = "CRYPTO", page: int = 0):
        # Handle command arguments (e.g., /symbols GLOBAL)
        if context.args:
            arg = context.args[0].upper()
            if arg in ["CRYPTO", "GLOBAL"]:
                tab = arg

        try:
            settings = get_settings()
            all_symbols = settings.trading_symbols
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            # Authority Categorization (DB-backed)
            db = dm.SessionLocal()
            try:
                from services.data_manager import SymbolRegistry
                raw_syms = db.query(SymbolRegistry.symbol).filter(SymbolRegistry.category == tab).all()
                target_list_raw = [s[0] for s in raw_syms]
            finally:
                db.close()
            
            # Fetch user style and mode
            user_id = update.effective_user.id
            style = dm.get_user_intel_style(user_id)
            simple_mode = dm.get_user_simple_mode(user_id)
            
            # Apply Filter (ALL mode = no filtering)
            if simple_mode != 2:
                target_list = BotIntelFilter.filter_symbols(target_list_raw, style)
            else:
                target_list = target_list_raw
            
            # Pagination
            page_size = 20
            total_assets = len(target_list)
            total_pages = (total_assets + page_size - 1) // page_size
            page = max(0, min(page, total_pages - 1)) if total_pages > 0 else 0
            
            start_idx = page * page_size
            end_idx = start_idx + page_size
            paged_list = target_list[start_idx:end_idx]
            
            # Fallback if DB empty (unlikely after population)
            if not target_list:
                target_list = all_symbols[:10]
                paged_list = target_list
            
            msg = f"<b>[ {tab} UNIVERSE ]</b> <i>Page {page+1}/{total_pages}</i>\n"
            msg += "<code>══════════════════════════════════════</code>\n"
            msg += "<code>PRICE     24H    UPDATED  ASSET       </code>\n"


            
            # Get symbol aliases for display
            aliases = settings.SYMBOL_ALIASES
            # Build reverse lookup: nickname → real symbol
            reverse_aliases = {v: k for k, v in aliases.items()}
            
            for s in paged_list:
                stats = dm.get_ticker_stats(s)
                has_real_data = stats is not None and stats.get('price', 0) > 0
                
                if not stats:
                    stats = {'price': 0, 'change_pct': 0, 'timestamp': None}
                    
                price = stats.get('price', 0)
                change = stats.get('change_pct', 0)
                ts = stats.get('timestamp')
                
                # Timestamp display: Show HH:MM:SS or "--:--" if no real data
                if ts and has_real_data:
                    from datetime import datetime
                    ts_str = datetime.fromtimestamp(ts).strftime('%H:%M')
                    age = time.time() - ts
                    attention = " [!]" if age > 300 else ""  # Stale if >5min old
                else:
                    ts_str = "--:--"
                    attention = " [?]"  # No data available
                
                p_str = f"${price:,.0f}" if price > 1 else f"${price:,.4f}"
                c_str = f"{change:+.1f}%"
                
                # Get display name (nickname if available, else raw symbol)
                display_name = aliases.get(s, s)
                
                # Row format: $98,500    +2.5%  14:32  /GOLD
                row = f"{p_str:<10} {c_str:<6} {ts_str:<6} "
                msg += f"<code>{row}</code> /{display_name}{attention}\n"

            msg += "<code>══════════════════════════════════════</code>\n"
            msg += f"<i>{len(paged_list)} of {total_assets} assets in {tab} view.</i>"



            
            # Navigation Buttons
            nav_buttons = []
            if total_pages > 1:
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("[BACK]", callback_data=f"SYMBOLS_PAGE_{tab}_{page-1}"))
                if page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("[NEXT]", callback_data=f"SYMBOLS_PAGE_{tab}_{page+1}"))
            
            keyboard = []
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            keyboard.append([
                InlineKeyboardButton("CRYPTO" if tab != "CRYPTO" else "-- CRYPTO --", callback_data="SYMBOLS_TAB_CRYPTO"),
                InlineKeyboardButton("GLOBAL" if tab != "GLOBAL" else "-- GLOBAL --", callback_data="SYMBOLS_TAB_GLOBAL"),
            ])
            keyboard.append([InlineKeyboardButton("○", callback_data="START")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.message.edit_text(msg, parse_mode="HTML", reply_markup=reply_markup)
            else:
                await update.effective_message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            await update.effective_message.reply_text(f"[ERROR] Could not fetch symbols: {e}")

    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        [ADMIN] Adjust risk parameters dynamically.
        Usage: /risk [param] [value]
        Params: size (0.01-1.0), target (0.01+), stop (0.01+)
        """
        user_id = str(update.effective_user.id)
        
        # Verify Admin
        settings = get_settings()
        if user_id != settings.TELEGRAM_CHAT_ID: 
             await update.message.reply_text("⛔ ACCESS DENIED")
             return

        args = context.args
        dm = get_data_manager()
        
        # 1. READ Current Settings
        current_settings = {}
        try:
             # Fetch from DB (user_bot_settings)
             with dm.engine.connect() as conn:
                 from sqlalchemy import text
                 result = conn.execute(text("SELECT * FROM user_bot_settings WHERE user_id = :uid"), {"uid": user_id}).mappings().first()
                 if result:
                     current_settings = dict(result)
        except Exception as e:
             logger.error(f"Failed to fetch settings: {e}")
             
        # 2. SHOW Status (No Args)
        if not args:
            size_val = current_settings.get("max_position_size")
            if size_val is None: size_val = settings.MAX_POSITION_SIZE
            
            stop_val = current_settings.get("stop_loss")
            if stop_val is None: stop_val = getattr(settings, "STOP_LOSS", 0.05)
            
            target_val = current_settings.get("profit_target")
            if target_val is None: target_val = getattr(settings, "PROFIT_TARGET", 0.02)
            
            msg = "[ RISK PARADIGM ]\n"
            msg += f"> Position Size: {float(size_val)*100:.1f}%\n"
            msg += f"> Stop Loss: {float(stop_val)*100:.1f}%\n"
            msg += f"> Profit Target: {float(target_val)*100:.1f}%\n"
            msg += "\n[ PROTOCOL INPUT ]\n"
            msg += "/risk size 0.95\n"
            msg += "/risk stop 0.05\n"
            msg += "/risk target 0.10"
            
            await update.message.reply_text(msg, parse_mode="HTML")
            return

        # 3. UPDATE Settings
        param = args[0].lower()
        if len(args) < 2:
            await update.message.reply_text("Usage: /risk [param] [value]")
            return
            
        try:
            val = float(args[1])
        except ValueError:
            await update.message.reply_text("Invalid numeric format")
            return

        column = None
        if param == "size":
            if 0.01 <= val <= 1.0:
                column = "max_position_size"
                settings.MAX_POSITION_SIZE = val 
            else:
                 await update.message.reply_text("(!) FAILURE: Size must be 0.01 - 1.0")
                 return
        elif param == "stop":
            column = "stop_loss"
            settings.STOP_LOSS = val
        elif param == "target":
            column = "profit_target"
            settings.PROFIT_TARGET = val
        else:
            await update.message.reply_text("(!) UNKNOWN PARAMETER")
            return

        # Execute DB Update
        try:
            with dm.engine.connect() as conn:
                 from sqlalchemy import text
                 # Handle upsert for settings (PostgreSQL)
                 sql = text(f"""
                     INSERT INTO user_bot_settings (user_id, {column}) 
                     VALUES (:uid, :val)
                     ON CONFLICT (user_id) DO UPDATE SET {column} = :val
                 """)
                 conn.execute(sql, {"val": val, "uid": user_id})
                 conn.commit()
            
            await update.message.reply_text(f"[ PHOENIX CONFIG UPDATED ]\n>> {param.upper()}: {val}", parse_mode="HTML")
            
        except Exception as e:
            await update.message.reply_text(f"Database error: {e}")
